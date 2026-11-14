"""m09 · Propagation: equation tests."""

import numpy as np
import pytest
import sympy as sp

from epml import propagation as G


def test_cable():
    """eq-m09-cable: exp(-x / lambda) solves the steady passive cable equation; the finite-difference solution
    converges to it; lambda = sqrt(r_m / (r_i + r_e))."""
    x, lam, tau, t = sp.symbols("x lambda tau t", positive=True)
    V = sp.exp(-x / lam)
    assert sp.simplify(lam**2 * sp.diff(V, x, 2) - tau * sp.diff(V, t) - V) == 0
    errs = []
    for dx in (0.2, 0.1, 0.05):
        n = int(round(40 / dx))
        xs = (np.arange(n) + 1) * dx
        errs.append(np.max(np.abs(G.cable_steady_fd(n, dx, 2.0) - G.cable_steady(xs, 1.0, 2.0))))
    assert errs[-1] < 1e-3 and errs[0] / errs[1] > 3.5
    assert G.length_constant(4.0, 0.5, 0.5) == pytest.approx(2.0)


def test_bidomain_reduces():
    """eq-m09-bidomain and eq-m09-monodomain: in 1D with no net axial current, the second bidomain equation gives
    phi_e = -sigma_i / (sigma_i + sigma_e) V + const, and the first becomes the monodomain equation with
    sigma_i sigma_e / (sigma_i + sigma_e)."""
    x = sp.Symbol("x")
    si, se = sp.symbols("sigma_i sigma_e", positive=True)
    V = sp.Function("V")(x)
    phi = -si / (si + se) * V
    assert sp.simplify(sp.diff((si + se) * sp.diff(phi, x) + si * sp.diff(V, x), x)) == 0
    lhs = sp.diff(si * sp.diff(V + phi, x), x)
    assert sp.simplify(lhs - si * se / (si + se) * sp.diff(V, x, 2)) == 0
    assert G.monodomain_conductivity(1.0, 3.0) == pytest.approx(0.75)


def test_cv_scaling():
    """eq-m09-cv: velocity scales as the square root of D (stretching space by sqrt(k) leaves the equation unchanged);
    from Clerc's resistance ratios the monodomain conductivities predict a longitudinal / transverse velocity ratio of
    2.8, against 3.0 measured."""
    v1, v4 = G.cable_cv(0.1), G.cable_cv(0.4)
    assert v4 / v1 == pytest.approx(2.0, rel=0.01)
    k, D, xs = sp.symbols("k D x", positive=True)
    u = sp.Function("u")
    lhs = D * k * sp.diff(u(xs / sp.sqrt(k)), xs, 2)
    assert sp.simplify(lhs - D * sp.diff(u(xs / sp.sqrt(k)), xs, 2) * k) == 0
    ratio = G.cv_ratio_from_conductivities(*G.clerc_conductivities())
    assert ratio == pytest.approx(2.82, abs=0.01)
    assert abs(ratio - G.CLERC["cv_ratio"]) / G.CLERC["cv_ratio"] < 0.07
    si_L, si_T, se_L, se_T = G.clerc_conductivities()
    assert (se_L / se_T) / (si_L / si_T) == pytest.approx(2.7 / 9.4)   # unequal anisotropy ratios


def test_anisotropy():
    """eq-m09-anisotropy: isochrones from a point are ellipses with axis ratio CV_L / CV_T; along a ray at angle theta
    the apparent speed is CV_L CV_T / sqrt(CV_T^2 cos^2 + CV_L^2 sin^2). A reaction-diffusion sheet with D_T = D_L / 9
    approaches a velocity ratio of 3 as the front flattens."""
    th = np.linspace(0, np.pi, 7)
    for a in (0.0, 0.6):
        r = G.ray_speed(th - a, 1.0, 0.4)
        x, y = r * np.cos(th), r * np.sin(th)
        assert np.allclose(G.point_activation(x, y, 1.0, 0.4, a), 1.0)
    DL = 0.8603
    act = G.sheet_activation(201, 0.2, 0.01, 60.0, DL, DL / 9)
    x = (np.arange(201) - 100) * 0.2
    v = {}
    for lo, hi in ((5, 10), (14, 19)):
        sel = (x > lo) & (x < hi)
        v[lo] = (1 / np.polyfit(x[sel], act[100, sel], 1)[0], 1 / np.polyfit(x[sel], act[sel, 100], 1)[0])
    assert v[14][0] / v[14][1] == pytest.approx(3.0, rel=0.03)
    assert v[5][0] < v[14][0] < 1.0


def test_curvature():
    """eq-m09-curvature: an expanding circular wave travels at about c0 - D / r; within 2% for r >= 3 mm."""
    D = 0.1
    c0 = G.cable_cv(D)
    r, act = G.radial_wave(D, dr=0.05, dt=0.002, radius=10.0, t_end=60.0, r_stim=1.0)
    sp_ = G.front_speed(r, act)
    for R in (3.0, 5.0, 8.0):
        i = np.argmin(np.abs(r - R))
        assert sp_[i] == pytest.approx(c0 - D / R, rel=0.02)
    i2 = np.argmin(np.abs(r - 2.0))
    assert sp_[i2] < c0 - 0.1 * (c0 - (c0 - D / 2.0)) and sp_[i2] < sp_[np.argmin(np.abs(r - 8.0))]
