"""m18 · Hybrid and dielectric localization: correcting impedance coordinates with magnetic references, fusing
estimates, and frequency-dependent (complex) conductivity. MIT License.

Units: lengths in mm; impedance coordinates in mm after a uniform-field map (m17); conductivities relative;
frequencies in Hz.
"""

import numpy as np

from . import impedance as Z

EPS0 = 8.8541878128e-12      # vacuum permittivity, F/m (CODATA 2018)


# ---- a distorted impedance coordinate system to correct ----------------------------------------------------------

ILLUSTRATIVE_SCALE = (1.12, 0.92, 1.05)    # per-axis field-scaling errors, illustrative (cf. 8-14% in m17)


def impedance_coordinates(points, d=150.0, scale=ILLUSTRATIVE_SCALE):
    """Impedance coordinates of true points: the m17 uniform-field map of three point-patch pairs at +/- d, with
    per-axis scale errors."""
    u = Z.linear_estimate(Z.potentials(points, Z.patch_pairs(d)), d)
    return u * np.asarray(scale, float)


def ball_points(n, radius, rng):
    """n points uniformly inside a ball (a stand-in for a chamber the magnetic catheter roams)."""
    v = rng.standard_normal((n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v * radius * rng.random((n, 1)) ** (1.0 / 3.0)


def rms(e):
    return float(np.sqrt(np.mean(np.sum(np.asarray(e) ** 2, axis=-1))))


# ---- eq-m18-affine ----------------------------------------------------------------------------------------------

def fit_affine(u, x):
    """Least-squares x ~ A u + b from paired points (rows). Returns (A, b)."""
    U = np.hstack([u, np.ones((len(u), 1))])
    coef = np.linalg.lstsq(U, x, rcond=None)[0]
    return coef[:-1].T, coef[-1]


def apply_affine(A, b, u):
    return u @ A.T + b


# ---- eq-m18-rbf -------------------------------------------------------------------------------------------------

def gaussian(r, scale):
    return np.exp(-0.5 * (r / scale) ** 2)


def fit_rbf(u, x, scale, lam=0.0):
    """x = A u + b + sum_j w_j phi(|u - u_j|): solve [[Phi + lam I, P], [P^T, 0]] [w; c] = [x; 0], P = [u, 1]."""
    n, dim = u.shape
    Phi = gaussian(np.linalg.norm(u[:, None, :] - u[None, :, :], axis=-1), scale)
    P = np.hstack([u, np.ones((n, 1))])
    K = np.block([[Phi + lam * np.eye(n), P], [P.T, np.zeros((dim + 1, dim + 1))]])
    rhs = np.vstack([x, np.zeros((dim + 1, x.shape[1]))])
    sol = np.linalg.solve(K, rhs)
    return {"centers": u, "w": sol[:n], "c": sol[n:], "scale": scale}


def apply_rbf(model, u):
    Phi = gaussian(np.linalg.norm(u[:, None, :] - model["centers"][None, :, :], axis=-1), model["scale"])
    P = np.hstack([u, np.ones((len(u), 1))])
    return Phi @ model["w"] + P @ model["c"]


# ---- eq-m18-coverage ---------------------------------------------------------------------------------------------

def nearest_distance(points, refs):
    """Distance from each point to its nearest reference point."""
    return np.min(np.linalg.norm(points[:, None, :] - refs[None, :, :], axis=-1), axis=1)


def interp_error_bound(h, second_derivative):
    """Linear interpolation error bound on a segment of length h: h^2 max|f''| / 8."""
    return h * h * second_derivative / 8.0


# ---- eq-m18-fusion -----------------------------------------------------------------------------------------------

def fuse(x1, var1, x2, var2):
    """Inverse-variance weighted combination of two independent estimates; returns (estimate, variance)."""
    w1, w2 = 1.0 / var1, 1.0 / var2
    return (w1 * x1 + w2 * x2) / (w1 + w2), 1.0 / (w1 + w2)


# ---- eq-m18-dielectric -------------------------------------------------------------------------------------------

def complex_conductivity(freq, sigma, eps_inf, delta_eps, tau):
    """sigma* = sigma + j w eps0 eps_r(w), with a single Debye relaxation eps_r = eps_inf + delta_eps / (1 + j w tau)."""
    w = 2.0 * np.pi * np.asarray(freq, float)
    eps_r = eps_inf + delta_eps / (1.0 + 1j * w * tau)
    return sigma + 1j * w * EPS0 * eps_r


def impedance_phase_deg(freq, sigma, eps_inf, delta_eps, tau):
    """Phase of an impedance proportional to 1/sigma*: -arg(sigma*), in degrees."""
    return -np.degrees(np.angle(complex_conductivity(freq, sigma, eps_inf, delta_eps, tau)))


# Illustrative tissue parameters: chosen to show the idea, not measured values.
ILLUSTRATIVE_TISSUES = {
    "blood-like": dict(sigma=0.70, eps_inf=60.0, delta_eps=3.0e3, tau=1.0e-6),
    "wall-like": dict(sigma=0.25, eps_inf=60.0, delta_eps=4.0e4, tau=1.5e-6),
}
