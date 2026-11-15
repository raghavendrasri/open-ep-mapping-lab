"""m23 equation tests: amplitude, direction, noise floor and thresholds."""

import numpy as np
import pytest
import sympy as sp

from epml import voltage as VM


def test_amplitude():
    """eq-m23-amplitude: unipolar pp = A/a; bipolar pp -> (9/8) A d|cos|/a^2 for small spacing and -> A/a for large."""
    s, a, A = sp.symbols("s a A", positive=True)
    U = A * s / (s**2 + a**2)
    crit = sp.solve(sp.diff(U, s), s)
    assert crit == [a]
    assert sp.simplify(2 * U.subs(s, a) - A / a) == 0
    dU = sp.diff(U, s)
    # extremes of U': maximum A/a^2 at 0, minimum -A/(8 a^2) at s = sqrt(3) a
    assert sp.simplify(dU.subs(s, 0) - A / a**2) == 0
    assert sp.simplify(dU.subs(s, sp.sqrt(3) * a) + A / (8 * a**2)) == 0
    for aa in (1.3, 3.3):
        assert VM.bipolar_pp(aa, 0.05) == pytest.approx(VM.bipolar_pp_small(aa, 0.05), rel=2e-3)
        assert VM.bipolar_pp(aa, 400.0) == pytest.approx(VM.unipolar_pp(aa), rel=0.02)
    # A raised electrode loses more bipolar than unipolar amplitude (small spacing): exponents 2 and 1
    r_b = VM.bipolar_pp(2.3, 0.1) / VM.bipolar_pp(1.3, 0.1)
    r_u = VM.unipolar_pp(2.3) / VM.unipolar_pp(1.3)
    assert r_b == pytest.approx(VM.height_factor(1.3, 1.0, "bipolar"), rel=5e-3)
    assert r_u == pytest.approx(VM.height_factor(1.3, 1.0, "unipolar"))


def test_direction():
    """eq-m23-direction: P(|cos| < q) = (2/pi) arcsin q; orthogonal pair >= 1/sqrt2; field amplitude constant."""
    q = sp.symbols("q", positive=True)
    th = sp.symbols("theta", positive=True)
    # measure of {theta in [0, pi): |cos theta| < q} is pi - 2 acos(q)
    assert sp.simplify(((sp.pi - 2 * sp.acos(q)) / sp.pi - 2 / sp.pi * sp.asin(q)).rewrite(sp.asin)) == 0
    rng = np.random.default_rng(3)
    t = rng.uniform(0, np.pi, 400_000)
    for qq in (0.2, 1 / 3, 0.7):
        assert np.mean(np.abs(np.cos(t)) < qq) == pytest.approx(VM.below_fraction(qq), abs=3e-3)
    assert np.mean(np.abs(np.cos(t))) == pytest.approx(2 / np.pi, abs=2e-3)
    assert VM.pair_max_factor(np.linspace(0, np.pi, 1001)).min() == pytest.approx(1 / np.sqrt(2), abs=1e-6)
    # Small spacing: the largest projection of the pair equals an aligned bipole for every direction
    ref = VM.bipolar_pp(1.3, 0.1, 0.0)
    for ang in (0, 20, 45, 70, 90):
        assert VM.field_pp(1.3, 0.1, np.radians(ang)) == pytest.approx(ref, rel=5e-3)
    # A single bipole perpendicular to the front records nothing
    assert VM.bipolar_pp(1.3, 2.0, np.pi / 2) < 1e-12
    _ = sp.cos(th)


def test_noise_floor():
    """eq-m23-noise: expected peak-to-peak of n Gaussian samples."""
    rng = np.random.default_rng(4)
    for n in (10, 100, 1000):
        x = rng.normal(0, 1, (20_000, n))
        assert np.mean(x.max(1) - x.min(1)) == pytest.approx(VM.noise_pp_expected(n), rel=0.01)
    assert VM.noise_pp_expected(2) == pytest.approx(2 / np.sqrt(np.pi), rel=1e-6)   # E|X1 - X2| for unit normals


def test_thresholds():
    """eq-m23-threshold: log-normal sensitivity and specificity; Youden cutoff at the geometric mean."""
    rng = np.random.default_rng(5)
    ms, mn, sd = 0.2, 2.5, 0.7
    scar = np.exp(np.log(ms) + sd * rng.normal(size=200_000))
    norm = np.exp(np.log(mn) + sd * rng.normal(size=200_000))
    for cut in (0.5, 1.0, 1.5):
        sens, spec = VM.threshold_rates(cut, ms, mn, sd, sd)
        assert np.mean(scar < cut) == pytest.approx(sens, abs=3e-3)
        assert np.mean(norm >= cut) == pytest.approx(spec, abs=3e-3)
    cuts = np.exp(np.linspace(np.log(0.05), np.log(10), 4001))
    j = [sum(VM.threshold_rates(c, ms, mn, sd, sd)) for c in cuts]
    assert cuts[int(np.argmax(j))] == pytest.approx(VM.youden_cutoff_equal_sd(ms, mn), rel=2e-3)
    x, m1, m2 = sp.symbols("x m1 m2", positive=True)
    # equal densities of ln V at the midpoint of ln m1 and ln m2
    assert sp.simplify(sp.log(sp.sqrt(m1 * m2)) - (sp.log(m1) + sp.log(m2)) / 2) == 0
