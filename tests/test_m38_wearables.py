"""m38 equation tests: each numbered equation in modules/m38-wearables-monitoring.qmd is checked here."""

import itertools

import numpy as np
import pytest
import sympy as sp

from epml import ml
from epml import wearables as wr


def test_heart_rate_from_intervals():
    """eq-m38-hr"""
    assert wr.heart_rate([0.8, 0.8, 0.8]) == pytest.approx(75)
    assert wr.heart_rate([0.5, 1.0]) == pytest.approx(80)


def test_ppg_intervals_identity():
    """eq-m38-ibi: pulse intervals are RR intervals plus the change in pulse delay."""
    rng = np.random.default_rng(1)
    r = np.cumsum(rng.uniform(0.6, 1.2, size=50))
    d = rng.uniform(0.15, 0.3, size=50)
    onsets = r + d
    assert np.allclose(np.diff(onsets), wr.ppg_intervals(np.diff(r), d))


@pytest.mark.parametrize("rho", [0.0, 0.5, 0.9])
def test_ppg_interval_variance_matches_simulation(rho):
    """eq-m38-ibi-var: Var(IBI) = Var(RR) + 2 Var(delay) (1 - rho)."""
    rng = np.random.default_rng(2)
    n = 400_000
    rr = 0.85 + 0.03 * rng.normal(size=n - 1)
    d = wr.ar1_delays(n, 0.2, 0.02, rho, rng)
    ibi = wr.ppg_intervals(rr, d)
    assert ibi.var() == pytest.approx(wr.ppg_interval_variance(rr.var(), d.var(), rho), rel=0.02)


def test_ppg_interval_variance_symbolic():
    """eq-m38-ibi-var from Var(RR + D2 - D1) with independent RR and stationary delays."""
    vr, vd, rho = sp.symbols("v_r v_d rho", positive=True)
    # Var(a + b - c) = Var a + Var b + Var c - 2 Cov(b, c) for a independent of b, c
    expr = vr + vd + vd - 2 * rho * vd
    assert sp.simplify(expr - wr.ppg_interval_variance(vr, vd, rho)) == 0


def test_synthetic_ppg_onsets_follow_the_delays():
    rng = np.random.default_rng(3)
    r = np.cumsum(np.full(20, 0.8))
    d = np.full(20, 0.2)
    x, on = wr.synth_ppg(r, d, fs=100, noise=0.0, rng=rng)
    assert np.allclose(on, r + 0.2)
    peak = np.argmax(x[: int(1.3 * 100)]) / 100
    assert peak == pytest.approx(r[0] + 0.2 + 0.12, abs=0.02)  # each pulse peaks one width after onset


def brute_force_runs(n, q, k):
    total = 0.0
    for bits in itertools.product([0, 1], repeat=n):
        prob = np.prod([q if b else 1 - q for b in bits])
        total += prob * wr.runs_at_least(bits, k)
    return total


@pytest.mark.parametrize("n,q,k", [(6, 0.3, 2), (8, 0.5, 3), (7, 0.1, 1), (5, 0.6, 5), (3, 0.4, 4)])
def test_expected_runs_exact(n, q, k):
    """eq-m38-runs, by enumerating every sequence."""
    assert wr.expected_runs(n, q, k) == pytest.approx(brute_force_runs(n, q, k), abs=1e-12)


def test_expected_runs_simulation_for_a_day_of_windows():
    """eq-m38-runs for 288 five-minute windows."""
    rng = np.random.default_rng(4)
    n, q, k = 288, 0.15, 3
    sims = [wr.runs_at_least(rng.random(n) < q, k) for _ in range(4000)]
    assert np.mean(sims) == pytest.approx(wr.expected_runs(n, q, k), rel=0.05)


@pytest.mark.parametrize("L,p,k", [(5, 0.7, 2), (8, 0.5, 3), (4, 0.9, 4), (6, 0.3, 1), (3, 0.8, 5)])
def test_detection_probability_exact(L, p, k):
    """eq-m38-detect, by enumerating every sequence of L windows."""
    total = 0.0
    for bits in itertools.product([0, 1], repeat=L):
        prob = np.prod([p if b else 1 - p for b in bits])
        total += prob * (wr.runs_at_least(bits, k) > 0)
    assert wr.detection_probability(L, p, k) == pytest.approx(total, abs=1e-12)


def test_alert_workload():
    """eq-m38-workload"""
    w = wr.alert_workload(500, 0.1, 0.25, 3)
    assert w["alerts"] == pytest.approx(50)
    assert w["false"] == pytest.approx(37.5)
    assert w["true"] + w["false"] == pytest.approx(w["alerts"])
    assert w["hours"] == pytest.approx(2.5)


def test_filter_is_bayes_with_ppv_as_prevalence():
    """eq-m38-filter equals eq-m35-ppv with prevalence = PPV, sensitivity = share of true alerts kept and
    specificity = share of false alerts removed."""
    for ppv, kt, rf in [(0.25, 0.95, 0.8), (0.6, 0.99, 0.5), (0.1, 0.9, 0.95)]:
        new, shown, lost = wr.filtered_alerts(ppv, kt, rf)
        assert new == pytest.approx(ml.predictive_values(kt, rf, ppv)[0])
        assert shown == pytest.approx(kt * ppv + (1 - rf) * (1 - ppv))
        assert lost == pytest.approx(1 - kt)
    P, k, r = sp.symbols("P k r", positive=True)
    new = k * P / (k * P + (1 - r) * (1 - P))
    assert sp.simplify(new.subs(r, 0) - k * P / (k * P + 1 - P)) == 0
    assert sp.simplify(new.subs(r, 1) - 1) == 0


def test_window_cv_separates_af_from_sinus():
    rng = np.random.default_rng(5)
    t, in_af = wr.rhythm_day(hours=4, af_episodes=[(2.0, 1.0)], rng=rng)
    cv = wr.window_cv(t, 300)
    starts = t[0] + 300 * np.arange(cv.size)
    af_win = (starts >= 2 * 3600 + 300) & (starts < 3 * 3600 - 300)
    assert np.nanmin(cv[af_win]) > 3 * np.nanmax(cv[~af_win & ((starts < 2 * 3600 - 300) | (starts > 3 * 3600 + 300))])
