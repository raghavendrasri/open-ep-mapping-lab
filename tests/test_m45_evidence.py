"""m45 tests: sample size for sensitivity (eq-m45-n-sens), net benefit (eq-m45-net-benefit), the CUSUM
drift alarm (eq-m45-cusum), the report card and the change-control check."""

import numpy as np
import pytest
import sympy as sp

from epml import evidence as ev
from epml.retrieval import wilson_interval


def test_n_for_sensitivity_formula_and_coverage():
    """eq-m45-n-sens: n = z^2 se(1 - se) / (d^2 prevalence); SymPy confirms it is the normal-approximation
    half-width equation solved for n, and simulated studies of that size give the target half-width."""
    n, se, d, prev, z = sp.symbols("n se d prev z", positive=True)
    sol = sp.solve(sp.Eq(z * sp.sqrt(se * (1 - se) / (n * prev)), d), n)
    assert sp.simplify(sol[0] - z**2 * se * (1 - se) / (d**2 * prev)) == 0
    assert ev.n_for_sensitivity(0.9, 0.05, 0.2) == 692
    assert ev.n_for_specificity(0.9, 0.05, 0.2) == 173
    rng = np.random.default_rng(0)
    n_tot = ev.n_for_sensitivity(0.85, 0.05, 0.3)
    widths = []
    for _ in range(400):
        n_pos = rng.binomial(n_tot, 0.3)
        k = rng.binomial(n_pos, 0.85)
        lo, hi = wilson_interval(k, n_pos)
        widths.append((hi - lo) / 2)
    assert np.mean(widths) == pytest.approx(0.05, rel=0.08)


def test_net_benefit_reference_strategies():
    """eq-m45-net-benefit: a perfect model has net benefit = prevalence; acting on everyone gives the
    treat-all line; acting on no one gives 0."""
    rng = np.random.default_rng(1)
    y = rng.random(2000) < 0.2
    prev = y.mean()
    for pt in (0.05, 0.2, 0.5):
        assert ev.net_benefit(y, y.astype(float), pt) == pytest.approx(prev)
        assert ev.net_benefit(y, np.ones(len(y)), pt) == pytest.approx(ev.net_benefit_treat_all(prev, pt))
        assert ev.net_benefit(y, np.zeros(len(y)), pt) == 0.0
    assert ev.net_benefit_treat_all(0.2, 0.2) == pytest.approx(0.0)


def test_cusum_recursion_by_hand():
    """eq-m45-cusum: S_t = max(0, S_{t-1} + x_t - target - k)."""
    S, alarm = ev.cusum([0.2, 1.5, 1.5, -3.0, 2.0, 2.0], target=0.0, k=0.5, h=2.5)
    assert np.allclose(S, [0.0, 1.0, 2.0, 0.0, 1.5, 3.0])
    assert alarm == 5
    S, alarm = ev.cusum(np.zeros(100), 0.0, 0.5, 1.0)
    assert alarm is None and S.max() == 0


def test_cusum_run_lengths():
    """Raising h lengthens the in-control run length; a larger shift is detected sooner; for a large
    shift the delay is close to h / (shift - k), the drift of S (simulation)."""
    rng = np.random.default_rng(2)
    in_ctrl = [np.mean([ev.run_length(0.5, h, 0.0, rng, max_len=20000) for _ in range(150)]) for h in (2.0, 4.0)]
    assert in_ctrl[1] > 3 * in_ctrl[0]
    d1 = np.mean([ev.run_length(0.5, 5.0, 1.0, rng) for _ in range(300)])
    d3 = np.mean([ev.run_length(0.5, 5.0, 3.0, rng) for _ in range(300)])
    assert d3 < d1
    assert d3 == pytest.approx(5.0 / (3.0 - 0.5) + 1, abs=0.6)


def test_report_card_and_pccp_check():
    rng = np.random.default_rng(3)
    y = (rng.random(400) < 0.4).astype(int)
    p = np.clip(0.4 + 0.35 * (2 * y - 1) + rng.normal(0, 0.15, 400), 0.01, 0.99)
    groups = np.repeat(np.arange(200), 2)
    kinds = np.where(y == 1, "af", np.where(rng.random(400) < 0.5, "sinus", "ectopy"))
    card = ev.report_card("test", y, p, groups, 0.5, subgroups=kinds, rng=rng)
    assert card["AUC 95% CI"][0] <= card["AUC"] <= card["AUC 95% CI"][1]
    assert card["n patients"] == 200 and set(card["specificity by subgroup"]) == {"ectopy", "sinus"}
    assert "| AUC |" in ev.card_markdown(card)
    criteria = {"AUC": ("AUC 95% CI", ">=", 0.8), "slope": ("calibration slope", "between", (0.0, 10.0)),
                "sens": ("sensitivity 95% CI", ">=", 0.99)}
    res, ok = ev.pccp_check(card, criteria)
    assert res["AUC"][1] and res["slope"][1] and not res["sens"][1] and not ok


def test_regular_share():
    fs = 100.0
    regular = np.arange(0, 1000, 80)
    assert ev.regular_share(regular, fs) == 1.0
    rr = np.array([80, 52, 108] * 4)            # an early beat and a pause, repeated
    assert ev.regular_share(np.cumsum(rr), fs) == pytest.approx(1 / 3, abs=0.1)
