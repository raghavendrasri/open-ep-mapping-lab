"""m25 equation tests: speed from a gradient, two points, triangles, plane fits and potential-based velocity."""

import numpy as np
import pytest
import sympy as sp

from epml import velocity as VE


def test_gradient():
    """eq-m25-gradient: v = grad T/|grad T|^2; noise inflates |grad T| (E|g|^2 = |g|^2 + 2 sigma^2), so speed reads low."""
    g = np.array([[0.6, 0.8], [2.0, 0.0]])
    assert np.allclose(VE.velocity_from_gradient(g), [[0.6, 0.8], [0.5, 0.0]])
    assert np.allclose(VE.speed_from_gradient(g), [1.0, 0.5])
    rng = np.random.default_rng(1)
    g0, sg = np.array([1.0, 0.0]), 0.3
    noisy = g0 + rng.normal(0, sg, (400_000, 2))
    assert np.sqrt(np.mean(np.sum(noisy**2, 1))) == pytest.approx(VE.inflated_gradient_rms(1.0, sg), rel=2e-3)
    assert np.median(VE.speed_from_gradient(noisy)) < 1.0
    gx, gy, s = sp.symbols("g_x g_y sigma", positive=True)
    from sympy.stats import Normal, E
    nx, ny = Normal("n_x", 0, s), Normal("n_y", 0, s)
    assert sp.simplify(E((gx + nx) ** 2 + (gy + ny) ** 2) - (gx**2 + gy**2 + 2 * s**2)) == 0


def test_pair():
    """eq-m25-pair: relative speed SD sqrt(2) sigma c / h for small errors."""
    h, dt, s = sp.symbols("h Delta_t sigma", positive=True)
    c = h / dt
    rel = sp.diff(c, dt) * sp.sqrt(2) * s / c                      # first-order propagation
    assert sp.simplify(sp.Abs(rel) - sp.sqrt(2) * s * (h / dt) / h) == 0
    rng = np.random.default_rng(2)
    hh, cc, st = 10.0, 1.0, 0.3
    t = hh / cc + rng.normal(0, st, 400_000) - rng.normal(0, st, 400_000)
    assert np.std(hh / t) / cc == pytest.approx(VE.pair_relative_error(st, cc, hh), rel=0.02)


def test_triangle():
    """eq-m25-triangle: gradient from three points; covariance sigma^2 E^-1 S E^-T; slivers blow up."""
    P = np.array([[0.0, 0.0], [4.0, 1.0], [1.0, 3.0]])
    gtrue = np.array([0.7, -0.4])
    T = P @ gtrue + 5.0
    assert np.allclose(VE.triangle_gradient(P, T), gtrue)
    rng = np.random.default_rng(3)
    est = np.array([VE.triangle_gradient(P, T + rng.normal(0, 0.5, 3)) for _ in range(100_000)])
    assert np.allclose(np.cov(est.T), VE.triangle_covariance(P, 0.5), rtol=0.03, atol=1e-4)
    # equilateral: isotropic with per-component variance 2 sigma^2 / h^2, as for a pair along the direction
    for ang in (0.0, 0.7):
        C = VE.triangle_covariance(VE.equilateral(4.0, ang), 1.0)
        assert np.allclose(C, 2 / 16 * np.eye(2), atol=1e-12)
    sliver = np.array([[0.0, 0.0], [4.0, 0.0], [2.0, 0.2]])
    assert np.trace(VE.triangle_covariance(sliver, 1.0)) > 50 * np.trace(VE.triangle_covariance(VE.equilateral(4.0), 1.0))


def test_planefit():
    """eq-m25-planefit: least-squares gradient covariance sigma^2 (Xc^T Xc)^-1, about (2 sigma / (R sqrt n))^2 for a disk."""
    rng = np.random.default_rng(4)
    n, R, st = 400, 5.0, 1.0
    r = R * np.sqrt(rng.uniform(0, 1, n))
    th = rng.uniform(0, 2 * np.pi, n)
    P = np.column_stack([r * np.cos(th), r * np.sin(th)])
    C = VE.plane_fit_covariance(P, st)
    assert np.sqrt(np.diag(C)) == pytest.approx([VE.disk_fit_sd(st, n, R)] * 2, rel=0.1)
    gtrue = np.array([1.0, 0.2])
    est = np.array([VE.plane_fit(P, P @ gtrue + rng.normal(0, st, n))[0] for _ in range(4000)])
    assert np.allclose(np.cov(est.T), C, rtol=0.08, atol=1e-5)
    # SymPy: for a uniform disk, E[x^2] = R^2 / 4
    rr, RR = sp.symbols("r R", positive=True)
    tt = sp.symbols("t")
    ex2 = sp.integrate(sp.integrate((rr * sp.cos(tt)) ** 2 * rr, (tt, 0, 2 * sp.pi)), (rr, 0, RR)) / (sp.pi * RR**2)
    assert sp.simplify(ex2 - RR**2 / 4) == 0


def test_potential_velocity():
    """eq-m25-omnipolar: v = -phi_t grad phi / |grad phi|^2 is exact for plane waves; a cross clique of spacing d reads
    c (1 + (d/2)^2 / a^2) along its axis when the front arrives."""
    s, a, A, c, t, x = sp.symbols("s a A c t x", positive=True)
    U = sp.Function("U")
    phi = U(x - c * t)
    v = -sp.diff(phi, t) * sp.diff(phi, x) / sp.diff(phi, x) ** 2
    assert sp.simplify(v - c) == 0
    Um = A * s / (s**2 + a**2)
    dl = sp.symbols("delta", positive=True)
    grad_est = (Um.subs(s, dl) - Um.subs(s, -dl)) / (2 * dl)
    ratio = sp.diff(Um, s).subs(s, 0) / grad_est
    assert sp.simplify(ratio - (1 + dl**2 / a**2)) == 0
    for th in (0.0, 0.4, 1.0):
        v = VE.clique_velocity(1.0, th, 1.3, 0.01, t=0.3)
        assert np.linalg.norm(v) == pytest.approx(1.0, rel=1e-4)
        assert np.arctan2(v[1], v[0]) == pytest.approx(th, abs=1e-4)
    assert np.linalg.norm(VE.clique_velocity(1.0, 0.0, 1.3, 2.0)) == pytest.approx(VE.clique_speed_ratio_axis(2.0, 1.3), rel=1e-6)
    # diagonal propagation: direction is still right by symmetry
    v = VE.clique_velocity(1.0, np.pi / 4, 1.3, 2.0)
    assert np.arctan2(v[1], v[0]) == pytest.approx(np.pi / 4, abs=1e-9)
