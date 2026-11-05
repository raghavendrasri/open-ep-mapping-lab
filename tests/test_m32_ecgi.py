"""m32 equation checks: forward model, sphere transfer, Tikhonov regularization, filter factors,
choice of lambda and accuracy metrics.

Each test checks an equation in modules/m32-capstone-ecg-imaging.qmd with SymPy, an independent
numerical solve or a synthetic problem with known truth.
"""

import numpy as np
import pytest
import sympy as sp
from scipy.integrate import solve_bvp

from epml import ecgi


@pytest.mark.parametrize("l", [0, 1, 2, 3, 5])
def test_sphere_transfer_from_laplace(l):
    """eq-m32-sphere-transfer: phi_l(r) = a r^l + b r^-(l+1) solves Laplace's equation for degree l;
    no flux at r_T fixes b, and the ratio phi(r_T) / phi(r_H) is (2l+1) rho^(l+1) / ((l+1) rho^(2l+1) + l)."""
    r, rH, rT, a, b = sp.symbols("r r_H r_T a b", positive=True)
    phi = a * r**l + b * r ** (-(l + 1))
    # radial part of Laplace's equation for degree l
    assert sp.simplify(sp.diff(r**2 * sp.diff(phi, r), r) - l * (l + 1) * phi) == 0
    bsol = sp.solve(sp.Eq(sp.diff(phi, r).subs(r, rT), 0), b)
    bsol = bsol[0] if bsol else 0  # l = 0: the condition holds for any b; take the bounded case
    phi = phi.subs(b, bsol)
    ratio = sp.simplify(phi.subs(r, rT) / phi.subs(r, rH))
    rho = rH / rT
    expected = (2 * l + 1) * rho ** (l + 1) / ((l + 1) * rho ** (2 * l + 1) + l)
    assert sp.simplify(ratio - expected) == 0


def test_sphere_transfer_matches_a_boundary_value_solve():
    """eq-m32-sphere-transfer: solving (r^2 phi')' = l(l+1) phi numerically with phi(r_H) = 1 and
    phi'(r_T) = 0 gives phi(r_T) = g_l; high degrees are attenuated almost to zero."""
    rH, rT = 0.4, 1.0
    for l in (1, 4, 8):
        def f(r, y):
            return np.vstack([y[1], l * (l + 1) * y[0] / r**2 - 2 * y[1] / r])

        def bc(ya, yb):
            return np.array([ya[0] - 1.0, yb[1]])

        rr = np.linspace(rH, rT, 200)
        sol = solve_bvp(f, bc, rr, np.vstack([np.ones_like(rr), np.zeros_like(rr)]), tol=1e-8)
        assert sol.sol(rT)[0] == pytest.approx(ecgi.sphere_transfer(l, rH / rT), rel=1e-5)
    assert ecgi.sphere_transfer(20, 0.4) < 1e-7


def test_forward_matrix_maps_each_degree():
    """eq-m32-forward: the Legendre forward matrix sends P_l on the heart to g_l P_l on the torso."""
    th = np.linspace(0, np.pi, 60)
    A = ecgi.legendre_forward(th, th, 0.5, 12)
    from numpy.polynomial import legendre as leg

    for l in (0, 2, 5):
        c = np.zeros(l + 1)
        c[l] = 1
        heart = leg.legval(np.cos(th), c)
        assert A @ heart == pytest.approx(ecgi.sphere_transfer(l, 0.5) * heart, abs=1e-9)


def problem(noise=1e-3, seed=0):
    th = np.linspace(0, np.pi, 80)
    A = ecgi.legendre_forward(th, th, 0.45, 25)
    from numpy.polynomial import legendre as leg

    truth = leg.legval(np.cos(th), np.r_[0.0, 1.0, 0.6, -0.4, 0.3, 0.2, -0.1])
    rng = np.random.default_rng(seed)
    e = noise * rng.normal(size=th.size)
    return A, truth, A @ truth + e, e


def test_tikhonov_normal_equations_and_gradient():
    """eq-m32-tikhonov: the normal-equation solution makes the gradient of the objective zero, and it
    beats the unregularized pseudo-inverse on noisy data."""
    A, truth, b, _ = problem()
    lam = 1e-2
    x = ecgi.tikhonov(A, b, lam)
    grad = 2 * A.T @ (A @ x - b) + 2 * lam**2 * x
    assert np.max(np.abs(grad)) < 1e-10
    naive = np.linalg.pinv(A, rcond=1e-15) @ b
    assert ecgi.relative_error(x, truth) < ecgi.relative_error(naive, truth)


def test_filter_factors_equal_tikhonov():
    """eq-m32-filter-factors: the SVD form with f_i = s_i^2 / (s_i^2 + lam^2) equals the normal
    equations."""
    A, _, b, _ = problem()
    for lam in (1e-4, 1e-2, 1.0):
        # the normal equations lose digits when lam is small (they square the condition number)
        assert ecgi.tikhonov_svd(A, b, lam) == pytest.approx(ecgi.tikhonov(A, b, lam), rel=1e-6, abs=1e-7)


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_lambda_rules_land_near_the_best_lambda(seed):
    """eq-m32-lambda: on a synthetic ill-posed problem, the L-curve corner and the discrepancy
    principle choose lambdas whose error is within a factor of 3 of the best error on the grid."""
    A, truth, b, e = problem(noise=1e-3, seed=seed)
    lams = np.logspace(-7, 0, 141)
    errs = np.array([ecgi.relative_error(ecgi.tikhonov_svd(A, b, l), truth) for l in lams])
    best = errs.min()
    lc = ecgi.lcurve_corner(A, b, lams)
    dp = ecgi.discrepancy_lambda(A, b, np.linalg.norm(e), lams)
    assert ecgi.relative_error(ecgi.tikhonov_svd(A, b, lc), truth) < 3 * best
    assert ecgi.relative_error(ecgi.tikhonov_svd(A, b, dp), truth) < 3 * best


def test_metrics():
    """eq-m32-metrics: perfect reconstruction gives CC = 1 and RE = 0; a scaled copy keeps CC = 1
    but not RE; the steepest downstroke recovers known activation times."""
    rng = np.random.default_rng(4)
    truth = rng.normal(size=50)
    assert ecgi.correlation(truth, truth) == pytest.approx(1.0)
    assert ecgi.relative_error(truth, truth) == 0.0
    assert ecgi.correlation(0.5 * truth, truth) == pytest.approx(1.0)
    assert ecgi.relative_error(0.5 * truth, truth) == pytest.approx(0.5)
    t = np.linspace(0, 400, 4001)
    act = np.array([120.0, 175.5, 260.2])
    sig = -np.tanh((t[None, :] - act[:, None]) / 3.0)
    assert ecgi.activation_time(sig, t) == pytest.approx(act, abs=0.1)
