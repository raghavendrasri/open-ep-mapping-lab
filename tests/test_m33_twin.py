"""m33 equation checks: anisotropic eikonal, closed-form timing offset, conductivity scaling and
cross-validated error, plus a small regional calibration.

Each test checks an equation in modules/m33-capstone-digital-twin.qmd. Parameter values are test
inputs (mm, ms), not physiological claims.
"""

import numpy as np
import pytest
import sympy as sp

from epml import ionic
from epml import mapping as mp
from epml import twin


def test_anisotropic_eikonal_exact_solution():
    """eq-m33-eikonal-aniso: on a flat sheet with uniform fibre direction f, T = sqrt((x.f)^2/v_f^2 +
    (x.n)^2/v_t^2) satisfies sqrt(grad T^T D grad T) = 1 with D = v_f^2 f f^T + v_t^2 (I - f f^T)."""
    x, y, vf, vt, th = sp.symbols("x y v_f v_t theta", positive=True)
    f = sp.Matrix([sp.cos(th), sp.sin(th)])
    n = sp.Matrix([-sp.sin(th), sp.cos(th)])
    p = sp.Matrix([x, y])
    T = sp.sqrt((p.dot(f) / vf) ** 2 + (p.dot(n) / vt) ** 2)
    g = sp.Matrix([sp.diff(T, x), sp.diff(T, y)])
    D = vf**2 * f * f.T + vt**2 * (sp.eye(2) - f * f.T)
    assert sp.simplify((g.T * D * g)[0, 0] - 1) == 0
    # isochrones are ellipses with axis ratio v_f / v_t
    pts = np.array([[3.0, 0.0], [0.0, 3.0]])
    t = twin.aniso_eikonal_flat(pts, [0, 0], [1, 0], 0.9, 0.3)
    assert t[1] / t[0] == pytest.approx(0.9 / 0.3)
    assert twin.speed_tensor([1, 0], 0.9, 0.3) == pytest.approx(np.diag([0.81, 0.09]))


def test_best_offset_closed_form():
    """eq-m33-offset: dJ/dt0 = 0 gives t0* = mean(T_meas - T_sim); a numerical minimizer agrees."""
    N = 5
    ts = sp.symbols(f"s0:{N}")
    tm = sp.symbols(f"m0:{N}")
    t0 = sp.symbols("t0")
    J = sum((s + t0 - m) ** 2 for s, m in zip(ts, tm))
    sol = sp.solve(sp.diff(J, t0), t0)[0]
    assert sp.simplify(sol - sum(m - s for s, m in zip(ts, tm)) / N) == 0
    rng = np.random.default_rng(0)
    sim, meas = rng.uniform(0, 80, 30), rng.uniform(0, 80, 30)
    from scipy.optimize import minimize_scalar

    num = minimize_scalar(lambda c: np.sum((sim + c - meas) ** 2)).x
    assert twin.best_offset(sim, meas) == pytest.approx(num, abs=1e-6)


def cable_cv(D, dx=0.025):
    params = (0.3, 6.0, 120.0, 150.0, 0.13)  # illustrative Mitchell-Schaeffer constants (ms)
    n = int(round(12.0 / dx))
    dt = min(0.01, 0.2 * dx**2 / D)  # explicit diffusion is stable for D dt / dx^2 < 1/2
    _, ups, _ = ionic.ms_cable(n, dx, dt, 150.0, D, params, [0.0], stim_cells=max(3, n // 60),
                               stim_amp=1.0, stim_dur=2.0, record_every=50.0)
    i1, i2 = n // 4, 3 * n // 4
    return (i2 - i1) * dx / (ups[i2][0] - ups[i1][0])


def test_conduction_velocity_scales_with_square_root_of_conductivity():
    """eq-m33-cv-scaling: in the monodomain equation, multiplying the diffusion (conductivity) by k
    and lengths by sqrt(k) leaves the equation unchanged, so speed scales as sqrt(k). A cable with 4x
    the diffusion conducts about 2x faster, and one correction step hits a target speed."""
    v1 = cable_cv(0.01)
    v4 = cable_cv(0.04)
    assert v4 / v1 == pytest.approx(2.0, rel=0.03)
    target = 1.5 * v1
    D_new = twin.conductivity_for_speed(0.01, target, v1)
    assert cable_cv(D_new) == pytest.approx(target, rel=0.03)


def test_regional_calibration_recovers_speeds():
    """eq-m33-offset with eq-m33-eikonal-aniso (isotropic case): fitting one speed per region to
    noisy activation times with an unknown offset recovers the true speeds."""
    V, F = mp.plane_mesh(21, 21, 1.0)
    cent = V[F].mean(axis=1)
    region = (cent[:, 0] > 10.0).astype(int)  # left half fast, right half slow
    true_v = np.array([0.8, 0.35])
    src = 10 * 21  # left edge, middle row
    T = mp.eikonal(V, F, src, true_v[region])
    rng = np.random.default_rng(1)
    pts = rng.choice(len(V), 60, replace=False)
    meas = T[pts] + 37.0 + rng.normal(0, 0.3, pts.size)
    v, t0, _ = twin.calibrate_regions(V, F, region, src, pts, meas, v_init=0.5)
    assert v == pytest.approx(true_v, rel=0.06)
    assert t0 == pytest.approx(37.0, abs=1.0)


def test_kfold_error_exposes_overfitting():
    """eq-m33-holdout: with an exact model and no noise the cross-validated error is near zero; a
    model with too many parameters fits its training data better but predicts held-out data worse."""
    rng = np.random.default_rng(2)
    X = np.sort(rng.uniform(-1, 1, 40))
    y_exact = 2.0 + 3.0 * X

    def fit_deg(d):
        return lambda Xt, yt: np.polyfit(Xt, yt, d)

    pred = np.polyval
    assert twin.kfold_rmse(fit_deg(1), pred, X, y_exact, 5, rng) < 1e-9
    y = y_exact + rng.normal(0, 0.3, X.size)
    cv_simple = twin.kfold_rmse(fit_deg(1), pred, X, y, 5, np.random.default_rng(3))
    cv_complex = twin.kfold_rmse(fit_deg(15), pred, X, y, 5, np.random.default_rng(3))
    in_complex = np.sqrt(np.mean((np.polyval(np.polyfit(X, y, 15), X) - y) ** 2))
    in_simple = np.sqrt(np.mean((np.polyval(np.polyfit(X, y, 1), X) - y) ** 2))
    assert in_complex < in_simple
    assert cv_complex > cv_simple


def test_opencarp_export_round_trip(tmp_path):
    """openCARP export used by the m33 lab: headers give the counts, coordinates are written in
    micrometres, elements are 'Tr n0 n1 n2 tag' with 0-based nodes, and everything reads back."""
    V, F = mp.icosphere(20.0, 1)
    tags = np.arange(len(F)) % 3
    fib = twin.tangent_fibres(V, F)
    pts_f, elem_f, lon_f = twin.write_opencarp(tmp_path / "case", V, F, tags, fib)
    pts_lines = pts_f.read_text().splitlines()
    assert int(pts_lines[0]) == len(V)
    assert float(pts_lines[1].split()[0]) == pytest.approx(V[0, 0] * 1000, abs=1e-3)
    elem_lines = elem_f.read_text().splitlines()
    assert int(elem_lines[0]) == len(F) and elem_lines[1].split()[0] == "Tr"
    assert lon_f.read_text().splitlines()[0] == "1"
    V2, F2, t2, f2 = twin.read_opencarp(tmp_path / "case")
    assert V2 == pytest.approx(V, abs=1e-6)
    assert np.array_equal(F2, F) and np.array_equal(t2, tags)
    assert np.linalg.norm(f2, axis=1) == pytest.approx(np.ones(len(F)), abs=1e-5)
    # fibres lie in the plane of their triangle
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    assert np.abs(np.einsum("ij,ij->i", n, f2)).max() < 1e-4 * np.linalg.norm(n, axis=1).max()


def test_calibration_with_a_fixed_block_region():
    """eq-m33-offset with a region held at speed 0 (block): the other speeds are still recovered and
    the fixed region keeps its value."""
    V, F = mp.plane_mesh(21, 21, 1.0)
    c = V[F].mean(axis=1)
    region = np.where((np.abs(c[:, 0] - 10) < 1) & (c[:, 1] < 14), 2, (c[:, 0] > 10).astype(int))
    true_v = np.array([1.0, 0.6, 0.0])
    src = 10 * 21
    T = mp.eikonal(V, F, src, true_v[region])
    rng = np.random.default_rng(6)
    pts = rng.choice(np.flatnonzero(np.isfinite(T)), 60, replace=False)
    meas = T[pts] + 12.0 + rng.normal(0, 0.3, pts.size)
    v, t0, _ = twin.calibrate_regions(V, F, region, src, pts, meas, v_init=0.8, fixed={2: 0.0})
    assert v[2] == 0.0
    assert v[:2] == pytest.approx(true_v[:2], rel=0.06)
    assert t0 == pytest.approx(12.0, abs=1.0)
