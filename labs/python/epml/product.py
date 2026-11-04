"""Verification and reliability arithmetic for module m36 (from prototype to product).

Checked by tests/test_m36_verification.py against SymPy, scipy.stats and simulation.
See modules/m36-prototype-to-product.qmd, Derivations.
"""

import math

import numpy as np
from scipy import stats


def success_run_n(reliability, confidence):
    """Smallest n with zero failures that shows reliability R at confidence C: ceil(ln(1-C) / ln R)."""
    return math.ceil(math.log(1.0 - confidence) / math.log(reliability) - 1e-12)


def acceptance_n(reliability, confidence, allowed_failures, n_max=100_000):
    """Smallest n such that, if the true reliability were only R, passing with at most c failures
    would happen with probability at most 1 - C."""
    p_fail = 1.0 - reliability
    for n in range(allowed_failures + 1, n_max + 1):
        if stats.binom.cdf(allowed_failures, n, p_fail) <= 1.0 - confidence:
            return n
    raise ValueError("n_max too small")


def clopper_pearson(successes, n, alpha=0.05):
    """Exact two-sided (1 - alpha) confidence interval for a proportion, from beta quantiles."""
    x = successes
    lower = 0.0 if x == 0 else stats.beta.ppf(alpha / 2, x, n - x + 1)
    upper = 1.0 if x == n else stats.beta.ppf(1 - alpha / 2, x + 1, n - x)
    return float(lower), float(upper)


def reliability(t, failure_rate):
    """Probability of surviving to time t with a constant failure rate: exp(-lambda t)."""
    return np.exp(-failure_rate * np.asarray(t, dtype=float))


def series_failure_rate(rates):
    """A series system fails when any part fails: its failure rate is the sum of the parts' rates."""
    return float(np.sum(rates))


def mtbf(failure_rate):
    """Mean time between failures for a constant failure rate: 1 / lambda."""
    return 1.0 / failure_rate


def harm_probability(p_hazardous_situation, p_harm_given_situation):
    """Probability of occurrence of harm P = P1 * P2 (ISO 14971:2019, Annex C)."""
    return p_hazardous_situation * p_harm_given_situation
