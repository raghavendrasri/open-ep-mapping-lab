"""m42 equation tests: RBF maps, eikonal residual, physics-informed loss and its Levenberg-Marquardt fit,
ensembles, and the slowness scaling of activation times."""

import numpy as np
import pytest
import sympy as sp

from epml import mapping as mp
from epml import pinn

CENT = pinn.grid_centres(0, 60, 6)
XC = pinn.grid_centres(0, 60, 9)


def test_rbf_gradient_matches_finite_differences():
    """eq-m42-rbf: analytic gradients of the basis, and the constant column."""
    rng = np.random.default_rng(0)
    X = rng.uniform(0, 60, (15, 2))
    P, G = pinn.rbf_basis(X, CENT, 9.0)
    assert np.allclose(P[:, -1], 1) and np.allclose(G[:, -1], 0)
    eps = 1e-6
    for k, e in enumerate(np.eye(2)):
        fd = (pinn.rbf_basis(X + eps * e, CENT, 9.0)[0] - pinn.rbf_basis(X - eps * e, CENT, 9.0)[0]) / (2 * eps)
        assert np.allclose(fd, G[:, :, k], atol=1e-8)


def test_eikonal_residual_of_exact_maps():
    """eq-m42-eikonal: zero for a point source and a plane wave with s = 1/v (SymPy and numbers)."""
    x, y, x0, y0, v = sp.symbols("x y x0 y0 v", positive=True)
    T = sp.sqrt((x - x0) ** 2 + (y - y0) ** 2) / v
    assert sp.simplify(sp.sqrt(sp.diff(T, x) ** 2 + sp.diff(T, y) ** 2) - 1 / v) == 0
    n = np.array([0.6, 0.8])
    grad = np.tile(n / 0.7, (5, 1))
    assert np.allclose(pinn.eikonal_residual(grad, 0.7), 0)
    assert np.allclose(pinn.eikonal_residual(grad, 1.4), 1.0)


@pytest.mark.parametrize("mode", ["fixed", "scalar", "field"])
def test_jacobian_matches_finite_differences(mode):
    """eq-m42-lm uses the Jacobian of the stacked residuals of eq-m42-loss."""
    rng = np.random.default_rng(1)
    kw = {"fixed": dict(slowness=0.9), "scalar": dict(slowness="scalar"), "field": dict(slowness="field", s_centres=pinn.grid_centres(0, 60, 3), s_h=20.0)}[mode]
    f = pinn.ActivationFit(CENT, 9.0, **kw)
    f.a = rng.normal(0, 5, len(f.a))
    f.b = f.b + rng.normal(0, 0.05, len(f.b))
    Xd, td = rng.uniform(0, 60, (10, 2)), rng.uniform(0, 60, 10)
    r0, J = f._residuals(Xd, td, XC, 3.0)
    p0 = np.r_[f.a, f.b]
    eps = 1e-6
    for j in range(len(p0)):
        p = p0.copy(); p[j] += eps
        f.a, f.b = p[: len(f.a)], p[len(f.a):]
        r1, _ = f._residuals(Xd, td, XC, 3.0)
        assert np.allclose((r1 - r0) / eps, J[:, j], atol=1e-4, rtol=1e-3)
    f.a, f.b = p0[: len(f.a)], p0[len(f.a):]
    assert f.loss(Xd, td, XC, 3.0) == pytest.approx(r0 @ r0)


def test_fit_decreases_loss_and_lambda_zero_is_ridge_least_squares():
    """eq-m42-loss and eq-m42-lm: the history never increases; with lambda = 0 the fit is ridge LS."""
    rng = np.random.default_rng(2)
    Xd = rng.uniform(0, 60, (20, 2))
    td = np.linalg.norm(Xd - [10, 30], axis=1) + rng.normal(0, 1, 20)
    f = pinn.ActivationFit(CENT, 9.0, "scalar", s_prior=1.2)
    hist = f.fit(Xd, td, XC, lam=50, iters=60)
    assert np.all(np.diff(hist) <= 1e-12)
    assert 0.85 < 1 / f.b[0] < 1.15
    g = pinn.ActivationFit(CENT, 9.0, "scalar", ridge=1e-4)
    g.fit(Xd, td, XC, lam=0)
    P, _ = pinn.rbf_basis(Xd, CENT, 9.0)
    k = P.shape[1]
    A = P.T @ P / 20 + 1e-4 * np.diag(np.r_[np.ones(k - 1), 0])
    assert np.allclose(g.a, np.linalg.solve(A, P.T @ td / 20), atol=1e-6)


def test_ensemble_statistics():
    """eq-m42-ensemble: mean and sample SD; identical members give zero spread."""
    rng = np.random.default_rng(3)
    P = rng.normal(size=(7, 40))
    m, s = pinn.ensemble_stats(P)
    assert np.allclose(m, P.mean(0)) and np.allclose(s, P.std(0, ddof=1))
    Xd = rng.uniform(0, 60, (12, 2)); td = rng.uniform(0, 50, 12)
    preds = pinn.ensemble(Xd, td, XC, 3, lambda: pinn.ActivationFit(CENT, 9.0, 1.0), lam=0, noise=0, prior_scale=0, rng=rng, Xeval=XC)
    assert np.allclose(pinn.ensemble_stats(preds)[1], 0, atol=1e-9)
    preds = pinn.ensemble(Xd, td, XC, 3, lambda: pinn.ActivationFit(CENT, 9.0, 1.0), lam=0, noise=1, prior_scale=2, rng=rng, Xeval=XC)
    assert pinn.ensemble_stats(preds)[1].mean() > 0.1


def test_activation_times_scale_with_slowness():
    """eq-m42-scaling: multiplying every slowness by k multiplies every activation time by k."""
    verts, tris = mp.plane_mesh(15, 15, 2.0)
    speed = np.where(verts[tris].mean(1)[:, 0] > 14, 0.6, 1.0)
    T1 = mp.eikonal(verts, tris, [0], speed)
    for k in (0.5, 2.0, 3.0):
        assert np.allclose(mp.eikonal(verts, tris, [0], speed / k), k * T1, rtol=1e-9, atol=1e-9)
    s1, s2, L1, L2 = sp.symbols("s1 s2 L1 L2", positive=True)
    kk = sp.Symbol("k", positive=True)
    path = L1 * s1 + L2 * s2
    assert sp.simplify(path.subs({s1: kk * s1, s2: kk * s2}, simultaneous=True) - kk * path) == 0
