"""m25 · Conduction velocity estimation: triangulation, surface fitting, omnipolar methods.

Times in ms, lengths in mm, speeds in mm/ms (= m/s). Gradients of activation time in ms/mm. MIT License.
"""
from __future__ import annotations

import numpy as np

from .electrograms import unipolar

# ---------------------------------------------------------------- speed from a gradient (eq-m25-gradient)


def velocity_from_gradient(g):
    """v = grad T / |grad T|^2 for each row of g."""
    g = np.atleast_2d(np.asarray(g, float))
    return g / np.sum(g * g, axis=1, keepdims=True)


def speed_from_gradient(g):
    g = np.atleast_2d(np.asarray(g, float))
    return 1.0 / np.linalg.norm(g, axis=1)


def inflated_gradient_rms(g_mag, sigma_g, dim=2):
    """Root-mean-square magnitude of a gradient with isotropic noise of SD sigma_g per component."""
    return float(np.sqrt(g_mag**2 + dim * sigma_g**2))


# ---------------------------------------------------------------- two points and triangles (eq-m25-pair, eq-m25-triangle)


def pair_relative_error(sigma_t, c, h):
    """Relative SD of speed from two points h apart along propagation, each timed with SD sigma_t (small errors)."""
    return np.sqrt(2.0) * sigma_t * c / h


def triangle_gradient(P, T):
    """Gradient of the linear interpolant on a 2D triangle with vertices P (3 x 2) and times T (3)."""
    P = np.asarray(P, float)
    E = np.array([P[1] - P[0], P[2] - P[0]])
    return np.linalg.solve(E, np.array([T[1] - T[0], T[2] - T[0]]))


def triangle_covariance(P, sigma_t):
    """Covariance of the triangle gradient for independent timing errors of SD sigma_t."""
    P = np.asarray(P, float)
    E = np.array([P[1] - P[0], P[2] - P[0]])
    Ei = np.linalg.inv(E)
    S = np.array([[2.0, 1.0], [1.0, 2.0]])
    return sigma_t**2 * Ei @ S @ Ei.T


def equilateral(h, angle=0.0):
    a = np.array([[0.0, 0.0], [h, 0.0], [0.5 * h, 0.5 * np.sqrt(3) * h]])
    R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    return a @ R.T


# ---------------------------------------------------------------- local plane fit (eq-m25-planefit)


def plane_fit(P, T):
    """Least-squares T = t0 + g . x over the points; returns (g, t0)."""
    P = np.asarray(P, float)
    X = np.column_stack([np.ones(len(P)), P])
    coef, *_ = np.linalg.lstsq(X, np.asarray(T, float), rcond=None)
    return coef[1:], coef[0]


def plane_fit_covariance(P, sigma_t):
    """Covariance of the fitted gradient: sigma^2 (Xc^T Xc)^-1 with centered coordinates."""
    Xc = np.asarray(P, float) - np.mean(P, axis=0)
    return sigma_t**2 * np.linalg.inv(Xc.T @ Xc)


def disk_fit_sd(sigma_t, n, radius):
    """Per-component gradient SD for n points spread uniformly over a disk: 2 sigma / (R sqrt(n))."""
    return 2.0 * sigma_t / (radius * np.sqrt(n))


def local_plane_speeds(P, T, centers, radius):
    """Speed at each center from a plane fit to the points within the radius (NaN if fewer than 3)."""
    out = np.full(len(centers), np.nan)
    for k, c0 in enumerate(centers):
        m = np.linalg.norm(P - c0, axis=1) <= radius
        if m.sum() >= 3:
            g, _ = plane_fit(P[m], T[m])
            out[k] = 1.0 / np.linalg.norm(g)
    return out


# ---------------------------------------------------------------- potential-based (omnipolar) velocity (eq-m25-omnipolar)


def potential_velocity(phi_t, grad_phi):
    """v = -phi_t grad(phi) / |grad(phi)|^2: exact for a plane wave phi(x, t) = U(n . x - c t), any waveform U."""
    grad_phi = np.atleast_2d(np.asarray(grad_phi, float))
    phi_t = np.atleast_1d(np.asarray(phi_t, float))
    return -phi_t[:, None] * grad_phi / np.sum(grad_phi**2, axis=1, keepdims=True)


def plane_wave_phi(x, y, t, c, theta, a, A=1.0):
    """m03 plane wave: phi = U(s) with s = n . x - c t (the front reaches the origin at t = 0)."""
    s = np.cos(theta) * np.asarray(x, float) + np.sin(theta) * np.asarray(y, float) - c * np.asarray(t, float)
    return unipolar(s, a, A)


def clique_velocity(c, theta, a, d, t=0.0, A=1.0, dt=1e-4):
    """Velocity from a cross-shaped clique: a center electrode (time derivative) and four electrodes at +-d/2 along x
    and y (central-difference gradient), evaluated at time t."""
    h = 0.5 * d
    f = lambda x, y, tt: plane_wave_phi(x, y, tt, c, theta, a, A)
    gx = (f(h, 0.0, t) - f(-h, 0.0, t)) / d
    gy = (f(0.0, h, t) - f(0.0, -h, t)) / d
    phi_t = (f(0.0, 0.0, t + dt) - f(0.0, 0.0, t - dt)) / (2 * dt)
    return potential_velocity(phi_t, [[gx, gy]])[0]


def clique_speed_ratio_axis(d, a):
    """At the front's arrival, along an axis: estimated / true speed = 1 + (d/2)^2 / a^2 for the cross clique."""
    return 1.0 + (0.5 * d) ** 2 / a**2
