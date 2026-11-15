"""m18 equation tests: affine and RBF correction of impedance coordinates, coverage, fusion, complex conductivity."""

import numpy as np
import pytest
import sympy as sp

from epml import hybrid as H


@pytest.fixture(scope="module")
def chamber():
    rng = np.random.default_rng(18)
    g = np.linspace(-45, 45, 10)
    test = np.stack(np.meshgrid(g, g, g), axis=-1).reshape(-1, 3)
    test = test[np.linalg.norm(test, axis=1) <= 45.0]
    return rng, test, H.impedance_coordinates(test)


def test_affine(chamber):
    """eq-m18-affine: least squares recovers an exact affine map and removes scale errors."""
    rng, test, ut = chamber
    A0, b0 = np.array([[1.1, 0.1, 0.0], [0.0, 0.9, 0.2], [0.05, 0.0, 1.0]]), np.array([3.0, -2.0, 1.0])
    u = rng.standard_normal((20, 3)) * 30
    A, b = H.fit_affine(u, u @ A0.T + b0)
    assert A == pytest.approx(A0) and b == pytest.approx(b0)
    cal = H.ball_points(100, 45.0, rng)
    A, b = H.fit_affine(H.impedance_coordinates(cal), cal)
    assert H.rms(H.apply_affine(A, b, ut) - test) < 0.5 * H.rms(ut - test)


def test_rbf(chamber):
    """eq-m18-rbf: interpolates calibration points exactly (lam = 0) and removes the nonlinearity with enough points."""
    rng, test, ut = chamber
    cal = H.ball_points(100, 45.0, rng)
    u = H.impedance_coordinates(cal)
    m = H.fit_rbf(u, cal, 30.0, 0.0)
    assert H.apply_rbf(m, u) == pytest.approx(cal, abs=1e-6)
    A, b = H.fit_affine(u, cal)
    m = H.fit_rbf(u, cal, 30.0, 1e-6)
    assert H.rms(H.apply_rbf(m, ut) - test) < 0.2 * H.rms(H.apply_affine(A, b, ut) - test)
    # A purely affine target is reproduced by the polynomial part alone.
    A0, b0 = np.array([[1.2, 0, 0], [0, 0.8, 0], [0, 0, 1.0]]), np.array([1.0, 2.0, 3.0])
    m = H.fit_rbf(u, u @ A0.T + b0, 30.0, 0.0)
    assert np.max(np.abs(m["w"])) < 1e-5 * np.max(np.abs(u @ A0.T + b0))


def test_coverage(chamber):
    """eq-m18-coverage: error grows with distance to the nearest calibration point; linear interpolation bound."""
    rng, test, ut = chamber
    cal = H.ball_points(25, 45.0, rng)
    m = H.fit_rbf(H.impedance_coordinates(cal), cal, 30.0, 1e-6)
    err = np.linalg.norm(H.apply_rbf(m, ut) - test, axis=1)
    dist = H.nearest_distance(test, cal)
    rank = lambda v: np.argsort(np.argsort(v))
    assert np.corrcoef(rank(err), rank(dist))[0, 1] > 0.3
    # The bound h^2 f''/8 for linear interpolation of f = x^2 (f'' = 2) on [0, h] is attained at the midpoint.
    h = 4.0
    xs = np.linspace(0, h, 401)
    assert np.max(np.abs(xs ** 2 - h * xs)) == pytest.approx(H.interp_error_bound(h, 2.0))


def test_fusion():
    """eq-m18-fusion: inverse-variance weights minimize the variance of the combination."""
    w, v1, v2 = sp.symbols("w v1 v2", positive=True)
    var = w ** 2 * v1 + (1 - w) ** 2 * v2
    wopt = sp.solve(sp.diff(var, w), w)[0]
    assert sp.simplify(wopt - v2 / (v1 + v2)) == 0
    assert sp.simplify(var.subs(w, wopt) - 1 / (1 / v1 + 1 / v2)) == 0
    rng = np.random.default_rng(1)
    a = 1.0 + 0.5 * rng.standard_normal(200000)
    b = 1.0 + 2.0 * rng.standard_normal(200000)
    est, var_f = H.fuse(a, 0.25, b, 4.0)
    assert np.var(est) == pytest.approx(var_f, rel=0.02)


def test_dielectric():
    """eq-m18-dielectric: sigma* = sigma + j w eps0 eps_r; impedance phase -atan(w eps0 eps_r / sigma) for real eps_r."""
    w, s, e = sp.symbols("omega sigma epsilon", positive=True)
    z = 1 / (s + sp.I * w * e)
    re, im = sp.simplify(sp.re(z)), sp.simplify(sp.im(z))
    assert sp.simplify(im / re + w * e / s) == 0 and sp.simplify(re - s / (s ** 2 + (w * e) ** 2)) == 0
    p = dict(sigma=0.5, eps_inf=60.0, delta_eps=0.0, tau=1e-6)
    f = 1e5
    assert H.impedance_phase_deg(f, **p) == pytest.approx(-np.degrees(np.arctan(2 * np.pi * f * H.EPS0 * 60.0 / 0.5)))
    # The illustrative tissues barely differ in phase at 1 kHz but clearly at 100 kHz.
    t = H.ILLUSTRATIVE_TISSUES
    dphi = lambda f: abs(H.impedance_phase_deg(f, **t["wall-like"]) - H.impedance_phase_deg(f, **t["blood-like"]))
    assert dphi(1e3) < 1.0 < 10.0 < dphi(1e5)
