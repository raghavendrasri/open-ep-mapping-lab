"""m32 helpers: forward models, Tikhonov regularization, choice of lambda and accuracy metrics.

The analytic model is a heart sphere (radius r_H) inside a homogeneous torso sphere (radius r_T)
with no current leaving the torso surface. Potentials that depend only on the polar angle are
expanded in Legendre polynomials.
"""

import numpy as np
from numpy.polynomial import legendre as leg


def sphere_transfer(l, rho):
    """eq-m32-sphere-transfer: torso/heart ratio of the degree-l potential, rho = r_H / r_T."""
    l = np.asarray(l, dtype=float)
    return (2 * l + 1) * rho ** (l + 1) / ((l + 1) * rho ** (2 * l + 1) + l)


def legendre_forward(theta_heart, theta_torso, rho, lmax):
    """eq-m32-forward: transfer matrix A for axisymmetric potentials on the two spheres.

    Heart samples are fitted with Legendre polynomials up to degree lmax (least squares), each
    degree is scaled by g_l, and the result is evaluated at the torso angles.
    """
    Vh = leg.legvander(np.cos(theta_heart), lmax)  # [n_heart, lmax + 1]
    Vt = leg.legvander(np.cos(theta_torso), lmax)
    G = np.diag(sphere_transfer(np.arange(lmax + 1), rho))
    return Vt @ G @ np.linalg.pinv(Vh)


def tikhonov(A, b, lam, L=None):
    """eq-m32-tikhonov: argmin ||A x - b||^2 + lam^2 ||L x||^2 via the normal equations."""
    L = np.eye(A.shape[1]) if L is None else L
    return np.linalg.solve(A.T @ A + lam**2 * (L.T @ L), A.T @ b)


def tikhonov_svd(A, b, lam):
    """eq-m32-filter-factors: the same solution (L = I) written with SVD filter factors."""
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    f = s**2 / (s**2 + lam**2)
    return Vt.T @ (f * (U.T @ b) / s)


def lcurve(A, b, lams):
    """Residual and solution norms for each lambda (L = I)."""
    res, sol = [], []
    for lam in lams:
        x = tikhonov_svd(A, b, lam)
        res.append(np.linalg.norm(A @ x - b))
        sol.append(np.linalg.norm(x))
    return np.array(res), np.array(sol)


def lcurve_corner(A, b, lams):
    """eq-m32-lambda: lambda at the point of maximum curvature of (log residual, log solution norm).

    `lams` must be increasing and evenly spaced in log. Curvature by finite differences in log lambda.
    """
    res, sol = lcurve(A, b, lams)
    x, y = np.log(res), np.log(sol)
    t = np.log(lams)
    dx, dy = np.gradient(x, t), np.gradient(y, t)
    ddx, ddy = np.gradient(dx, t), np.gradient(dy, t)
    kappa = (dx * ddy - dy * ddx) / (dx**2 + dy**2) ** 1.5
    inner = slice(2, -2)
    return lams[inner][np.argmax(kappa[inner])]


def discrepancy_lambda(A, b, noise_norm, lams):
    """eq-m32-lambda: largest lambda whose residual does not exceed the noise norm."""
    res, _ = lcurve(A, b, lams)
    ok = res <= noise_norm
    return lams[ok][-1] if ok.any() else lams[0]


def correlation(estimate, truth):
    """eq-m32-metrics: Pearson correlation coefficient."""
    return float(np.corrcoef(np.ravel(estimate), np.ravel(truth))[0, 1])


def relative_error(estimate, truth):
    """eq-m32-metrics: ||estimate - truth|| / ||truth||."""
    return float(np.linalg.norm(np.ravel(estimate) - np.ravel(truth)) / np.linalg.norm(truth))


def activation_time(signals, t):
    """eq-m32-metrics: time of the steepest downstroke of each signal (rows are signals)."""
    d = np.gradient(np.atleast_2d(signals), t, axis=1)
    return np.asarray(t)[np.argmin(d, axis=1)]
