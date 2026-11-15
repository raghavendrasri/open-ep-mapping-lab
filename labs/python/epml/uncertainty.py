"""m26 · Map quality and uncertainty: point density, annotation error, interpolation error.

Times in ms, lengths in mm. Gaussian-process interpolation with a squared-exponential kernel and a constant prior mean.
MIT License.
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------- Gaussian-process interpolation (eq-m26-gp)


def se_kernel(X1, X2, ell, s2):
    """Squared-exponential covariance s2 exp(-|x - x'|^2 / (2 ell^2))."""
    X1 = np.atleast_2d(np.asarray(X1, float))
    X2 = np.atleast_2d(np.asarray(X2, float))
    d2 = np.sum((X1[:, None, :] - X2[None, :, :]) ** 2, axis=2)
    return s2 * np.exp(-0.5 * d2 / ell**2)


def gp_posterior(X, y, Xs, ell, s2, noise, mean=0.0):
    """Posterior mean and variance at Xs given noisy observations y at X (noise = observation SD)."""
    X = np.atleast_2d(np.asarray(X, float))
    A = se_kernel(X, X, ell, s2) + noise**2 * np.eye(len(X))
    L = np.linalg.cholesky(A)
    ks = se_kernel(X, Xs, ell, s2)
    alpha = np.linalg.solve(L.T, np.linalg.solve(L, np.asarray(y, float) - mean))
    mu = mean + ks.T @ alpha
    v = np.linalg.solve(L, ks)
    var = s2 - np.sum(v * v, axis=0)
    return mu, np.maximum(var, 0.0)


# ---------------------------------------------------------------- leave-one-out (eq-m26-loo)


def loo_residuals(X, y, ell, s2, noise, mean=0.0):
    """Closed-form leave-one-out residuals y_i - mu_{-i}(x_i) and predictive variances."""
    X = np.atleast_2d(np.asarray(X, float))
    A = se_kernel(X, X, ell, s2) + noise**2 * np.eye(len(X))
    Ai = np.linalg.inv(A)
    alpha = Ai @ (np.asarray(y, float) - mean)
    return alpha / np.diag(Ai), 1.0 / np.diag(Ai)


def loo_bruteforce(X, y, ell, s2, noise, mean=0.0):
    X = np.atleast_2d(np.asarray(X, float))
    y = np.asarray(y, float)
    r, v = np.zeros(len(X)), np.zeros(len(X))
    for i in range(len(X)):
        m = np.arange(len(X)) != i
        mu, var = gp_posterior(X[m], y[m], X[i:i + 1], ell, s2, noise, mean)
        r[i] = y[i] - mu[0]
        v[i] = var[0] + noise**2
    return r, v


# ---------------------------------------------------------------- error budget (eq-m26-budget)


def error_budget(sigma_annot, sigma_ref, sigma_pos, speed):
    """SD of one point's LAT error when annotation, reference (one beat per point) and position errors are independent;
    a position error sigma_pos (mm) moves the time by sigma_pos / speed. Use it as the GP observation noise."""
    return float(np.sqrt(sigma_annot**2 + sigma_ref**2 + (sigma_pos / speed) ** 2))


def single_point_variance(d, ell, s2, noise):
    """GP variance at distance d from a single observation (no other points)."""
    k = s2 * np.exp(-0.5 * np.asarray(d, float) ** 2 / ell**2)
    return s2 - k**2 / (s2 + noise**2)


# ---------------------------------------------------------------- point density (eq-m26-density)


def nn_distance_mean(density):
    """Mean distance from a random location to the nearest of Poisson points of the given density (2D)."""
    return 0.5 / np.sqrt(density)


def nn_distance_median(density):
    return np.sqrt(np.log(2.0) / (np.pi * density))


# ---------------------------------------------------------------- where to map next (eq-m26-adaptive)


def greedy_max_variance(candidates, n, ell, s2, noise, start=0):
    """Choose n sites one at a time, each where the current posterior variance is largest.

    The posterior variance does not depend on the measured values, so the plan needs no measurements."""
    cand = np.atleast_2d(np.asarray(candidates, float))
    chosen = [start]
    for _ in range(n - 1):
        _, var = gp_posterior(cand[chosen], np.zeros(len(chosen)), cand, ell, s2, noise)
        var[chosen] = -1.0
        chosen.append(int(np.argmax(var)))
    return np.array(chosen)
