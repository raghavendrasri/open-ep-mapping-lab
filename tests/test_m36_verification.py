"""m36 equation checks: verification sample sizes, confidence bounds, reliability and harm probability.

Each test checks an equation in modules/m36-prototype-to-product.qmd against SymPy, scipy.stats,
brute force or simulation.
"""

import math

import numpy as np
import pytest
import sympy as sp
from scipy import stats

from epml import product as pr


def test_success_run_derivation():
    """eq-m36-success-run: P(n passes | reliability R) = R^n <= 1 - C  <=>  n >= ln(1 - C) / ln R."""
    n, R, C = sp.symbols("n R C", positive=True)
    # Take logs of R^n = 1 - C (ln R < 0 flips the inequality when dividing).
    boundary = sp.solve(sp.Eq(n * sp.log(R), sp.log(1 - C)), n)[0]
    assert sp.simplify(boundary - sp.log(1 - C) / sp.log(R)) == 0


@pytest.mark.parametrize("R,C,expected", [(0.95, 0.95, 59), (0.90, 0.90, 22), (0.99, 0.95, 299)])
def test_success_run_values(R, C, expected):
    """eq-m36-success-run: n passes with zero failures; n - 1 would not be enough."""
    n = pr.success_run_n(R, C)
    assert n == expected
    assert R**n <= 1 - C < R ** (n - 1)
    assert pr.acceptance_n(R, C, 0) == n  # the c = 0 case of the acceptance plan


@pytest.mark.parametrize("R,C,c", [(0.95, 0.95, 1), (0.95, 0.90, 2), (0.90, 0.95, 3)])
def test_acceptance_plan_brute_force(R, C, c):
    """eq-m36-acceptance: the smallest n with sum_{k<=c} binom(n,k)(1-R)^k R^(n-k) <= 1 - C."""
    n = pr.acceptance_n(R, C, c)

    def p_pass(m):
        return sum(math.comb(m, k) * (1 - R) ** k * R ** (m - k) for k in range(c + 1))

    assert p_pass(n) <= 1 - C < p_pass(n - 1)


def test_clopper_pearson_coverage():
    """eq-m36-clopper-pearson: the exact interval covers the true proportion at least 1 - alpha of the time."""
    rng = np.random.default_rng(12)
    for p, n in [(0.9, 30), (0.97, 60), (0.5, 15)]:
        xs = rng.binomial(n, p, 20_000)
        covered = np.mean([lo <= p <= hi for lo, hi in (pr.clopper_pearson(x, n) for x in xs)])
        assert covered >= 0.95 - 0.004  # Monte Carlo tolerance


def test_clopper_pearson_all_pass_matches_success_run():
    """With all n trials passing, the one-sided lower bound at confidence C is (1 - C)^(1/n), the same
    statement as the success-run formula: n = 59 passes show R >= 0.95 at 95% confidence."""
    n, C = 59, 0.95
    lower_one_sided = stats.beta.ppf(1 - C, n, 1)  # Clopper-Pearson lower bound with x = n
    assert lower_one_sided == pytest.approx((1 - C) ** (1 / n))
    assert lower_one_sided >= 0.95
    lo, _ = pr.clopper_pearson(n, n, alpha=2 * (1 - C))  # two-sided at alpha gives one-sided at alpha/2
    assert lo == pytest.approx(lower_one_sided)


def test_series_reliability_by_simulation():
    """eq-m36-reliability: parts with constant failure rates lambda_i in series give
    R(t) = exp(-t sum lambda_i), and MTBF = 1 / sum lambda_i."""
    rng = np.random.default_rng(13)
    rates = np.array([1e-4, 5e-5, 2e-4])  # test inputs, per hour
    lifetimes = rng.exponential(1 / rates, size=(400_000, 3)).min(axis=1)  # first part to fail
    lam = pr.series_failure_rate(rates)
    assert lifetimes.mean() == pytest.approx(pr.mtbf(lam), rel=0.01)
    for t in (500.0, 2000.0, 8000.0):
        assert np.mean(lifetimes > t) == pytest.approx(pr.reliability(t, lam), abs=3e-3)


def test_harm_probability_two_stages():
    """eq-m36-harm: if a hazardous situation occurs with probability P1, and leads to harm with
    probability P2 when it does, harm occurs with probability P1 P2."""
    rng = np.random.default_rng(14)
    p1, p2 = 0.02, 0.3  # test inputs
    situation = rng.random(2_000_000) < p1
    harm = situation & (rng.random(situation.size) < p2)
    assert harm.mean() == pytest.approx(pr.harm_probability(p1, p2), rel=0.03)


def test_acceptance_values_quoted_in_text():
    """Values quoted under eq-m36-acceptance: to show R = 0.95 at C = 0.95, allowing 0, 1 or 2 failures
    needs 59, 93 or 124 units."""
    assert [pr.acceptance_n(0.95, 0.95, c) for c in (0, 1, 2)] == [59, 93, 124]
