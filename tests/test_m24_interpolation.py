"""m24 equation tests: linear interpolation error, IDW, harmonic interpolation, isochrones, block and coverage."""

import numpy as np
import pytest
import sympy as sp

from epml import interpolation as IP
from epml import meshes as M


def _boundary(n):
    ii, jj = np.meshgrid(np.arange(n), np.arange(n))
    ii, jj = ii.ravel(), jj.ravel()
    return np.nonzero((ii == 0) | (ii == n - 1) | (jj == 0) | (jj == n - 1))[0], ii, jj


def test_linear():
    """eq-m24-linear: barycentric interpolation is exact for linear fields; along a line the error is <= h^2 max|T''|/8."""
    x, h, f2 = sp.symbols("x h f2", positive=True)
    # error of linear interpolation of a quadratic with second derivative f2 on [0, h]: f2 x (x - h) / 2, largest at h/2
    e = f2 * x * (x - h) / 2
    assert sp.simplify(sp.Abs(e.subs(x, h / 2)) - h**2 * f2 / 8) == 0
    a, b, c = np.array([0.0, 0.0]), np.array([4.0, 1.0]), np.array([1.0, 3.0])
    lam = IP.barycentric([1.5, 1.2], a, b, c)
    f = lambda p: 2.0 + 0.3 * p[0] - 0.7 * p[1]
    assert lam.sum() == pytest.approx(1.0)
    assert lam @ np.array([f(a), f(b), f(c)]) == pytest.approx(f([1.5, 1.2]))
    # focal activation along a line 5 mm from the source: T'' = y0^2 / (c (x^2 + y0^2)^(3/2)) <= 1/(c y0)
    y0, cv = 5.0, 1.0
    xf = np.linspace(-30, 30, 6001)
    for hh in (2.0, 5.0):
        xd = np.arange(-30, 30 + 1e-9, hh)
        err = np.abs(IP.linear_1d(xd, IP.focal_time(xd, y0, cv), xf) - IP.focal_time(xf, y0, cv))
        assert err.max() <= IP.linear_error_bound(hh, 1 / (cv * y0)) + 1e-12
        assert err.max() > 0.5 * IP.linear_error_bound(hh, 1 / (cv * y0))


def test_idw():
    """eq-m24-idw: values stay within the data range and the gradient vanishes at data points for p > 1."""
    rng = np.random.default_rng(1)
    pts = rng.uniform(0, 20, (30, 2))
    vals = IP.focal_time(pts[:, 0], pts[:, 1], 1.0, 3.0, 4.0)
    q = rng.uniform(0, 20, (500, 2))
    est = IP.idw_points(pts, vals, q, 2.0)
    assert est.min() >= vals.min() - 1e-12 and est.max() <= vals.max() + 1e-12
    g_near = np.linalg.norm(IP.idw_gradient(pts, vals, pts[:5] + 1e-3, 2.0), axis=1)
    assert np.all(g_near < 0.05)                                  # true gradient magnitude is 1/c = 1 ms/mm
    g_p1 = np.linalg.norm(IP.idw_gradient(pts, vals, pts[:5] + 1e-3, 1.0), axis=1)
    assert np.mean(g_p1) > 5 * np.mean(g_near)
    # Symbolic: d/dr of w = r^-p times r -> 0 at r = 0 for p > 1 gives a flat spot (1D, two data points)
    r, p_, D = sp.symbols("r p D", positive=True)
    w1, w2 = r ** (-p_), (D - r) ** (-p_)
    T = (w1 * 0 + w2 * 1) / (w1 + w2)
    dT = sp.diff(T.subs(p_, 2), r)
    assert sp.limit(dT, r, 0, "+") == 0


def test_harmonic():
    """eq-m24-harmonic: with the boundary fixed, harmonic interpolation reproduces linear fields and obeys the
    maximum principle; a free boundary behaves as zero flux."""
    n = 21
    V, F = M.lattice_mesh(n, 1.0, jitter=0.2, seed=2)
    bd, ii, jj = _boundary(n)
    rng = np.random.default_rng(3)
    known = np.union1d(rng.choice(len(V), 15, replace=False), bd)
    lin = 0.5 * V[:, 0] - 0.2 * V[:, 1] + 3.0
    assert np.abs(IP.harmonic(V, F, known, lin[known]) - lin).max() < 1e-10
    foc = IP.focal_time(V[:, 0], V[:, 1], 1.0, 10.0, 9.0)
    T = IP.harmonic(V, F, known, foc[known])
    assert T.min() >= foc[known].min() - 1e-9 and T.max() <= foc[known].max() + 1e-9
    # Free boundary: the normal component of the gradient near the left edge is pulled toward zero
    free = rng.choice(np.setdiff1d(np.arange(len(V)), bd), 30, replace=False)
    T2 = IP.harmonic(V, F, free, lin[free])
    g = M.face_gradients(V, F, T2)
    left = np.isin(F, np.nonzero(ii == 0)[0]).any(1)
    assert np.abs(g[left, 0]).mean() < 0.6 * 0.5


def test_isochrones():
    """eq-m24-isochrone: crossings by linear interpolation along edges; spacing c * dtau for a plane wave."""
    assert IP.edge_crossing(10.0, 20.0, 12.5) == pytest.approx(0.25)
    assert IP.edge_crossing(10.0, 20.0, 25.0) is None
    n = 21
    V, F = M.lattice_mesh(n, 1.0, jitter=0.1, seed=4)
    c = 0.8
    T = V[:, 0] / c
    for tau in (5.0, 10.0, 15.0):
        segs = IP.isochrone_segments(V, F, T, tau)
        xs = np.array([p[0] for s in segs for p in s])
        assert len(segs) > 10 and np.allclose(xs, c * tau, atol=1e-9)
    assert IP.isochrone_spacing(c, 5.0) == pytest.approx(4.0)


def test_block_and_coverage():
    """eq-m24-block: a smeared block reads h / delta_t, and Poisson coverage is 1 - exp(-rho pi r^2)."""
    xd = np.array([0.0, 4.0, 8.0, 12.0])
    td = np.array([0.0, 4.0, 104.0, 108.0])                  # 1 m/s with a 96-ms jump between x = 4 and x = 8
    xf = np.linspace(4.0, 8.0, 101)
    slope = np.gradient(IP.linear_1d(xd, td, xf), xf).mean()
    assert 1 / slope == pytest.approx(IP.apparent_velocity_across_block(4.0, 100.0))
    rng = np.random.default_rng(5)
    g = np.stack(np.meshgrid(np.linspace(10, 90, 81), np.linspace(10, 90, 81)), -1).reshape(-1, 2)
    for n_pts, r in ((50, 5.0), (200, 3.0)):
        rho = n_pts / 100.0**2
        sims = [IP.coverage_simulated(rng.uniform(0, 100, (n_pts, 2)), r, g) for _ in range(60)]
        assert np.mean(sims) == pytest.approx(IP.coverage_fraction(rho, r), abs=0.02)
