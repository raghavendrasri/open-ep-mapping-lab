"""m17 · Impedance (current-based) localization: patch-pair fields, nonlinearity, linear maps, field scaling from
known electrode spacing, inhomogeneity and precision. MIT License.

Units: lengths in mm; currents and potentials in relative units with I/(4 pi sigma) = 1 unless stated.
"""

import numpy as np


# ---- eq-m17-pair: a current pair in a homogeneous medium ---------------------------------------------------------

def pair_potential(r, a, b, k=1.0):
    """Potential of +I at a and -I at b, k = I/(4 pi sigma): k (1/|r - a| - 1/|r - b|)."""
    r = np.asarray(r, float)
    return k * (1.0 / np.linalg.norm(r - a, axis=-1) - 1.0 / np.linalg.norm(r - b, axis=-1))


def patch_pairs(d):
    """Three orthogonal patch pairs at +/- d along x, y and z (illustrative, a homogeneous unbounded torso)."""
    e = np.eye(3)
    return [(d * e[i], -d * e[i]) for i in range(3)]


def potentials(r, pairs, k=1.0):
    """Potentials of each pair (driven separately, e.g. at different frequencies) at points r: shape (..., 3)."""
    return np.stack([pair_potential(r, a, b, k) for a, b in pairs], axis=-1)


# ---- eq-m17-axis: the nonlinearity along the axis ---------------------------------------------------------------

def axis_potential(x, d, k=1.0):
    """On the axis between patches at +/- d: k (1/(d - x) - 1/(d + x)) = 2 k x / (d^2 - x^2)."""
    return 2.0 * k * x / (d * d - x * x)


def center_field(d, k=1.0):
    """Potential gradient at the center on the axis: 2 k / d^2."""
    return 2.0 * k / (d * d)


def linear_estimate(phi, d, k=1.0):
    """Position from a linear map phi / E0, each axis separately."""
    return phi / center_field(d, k)


# ---- eq-m17-metric: field scaling from known electrode spacing ---------------------------------------------------

def local_jacobian(r, pairs, k=1.0, h=1e-3):
    """J[i, j] = d phi_i / d x_j at r."""
    J = np.empty((3, 3))
    for j in range(3):
        e = np.zeros(3); e[j] = h
        J[:, j] = (potentials(r + e, pairs, k) - potentials(r - e, pairs, k)) / (2 * h)
    return J


def fit_metric(dphis, lengths):
    """Least-squares symmetric M with dphi^T M dphi = length^2 for each electrode pair (needs >= 6 independent pairs)."""
    rows = []
    for v in dphis:
        rows.append([v[0] ** 2, v[1] ** 2, v[2] ** 2, 2 * v[0] * v[1], 2 * v[0] * v[2], 2 * v[1] * v[2]])
    m = np.linalg.lstsq(np.array(rows), np.asarray(lengths, float) ** 2, rcond=None)[0]
    return np.array([[m[0], m[3], m[4]], [m[3], m[1], m[5]], [m[4], m[5], m[2]]])


def metric_distance(dphi, M):
    """Distance implied by a potential difference under the metric M."""
    return float(np.sqrt(dphi @ M @ dphi))


# ---- eq-m17-interface: inhomogeneity ----------------------------------------------------------------------------

def interface_stretch(sigma_ref, sigma_local):
    """Normal current is continuous, so the field (and apparent distance) scales as sigma_ref / sigma_local."""
    return sigma_ref / sigma_local


def layered_positions(x, edges, sigmas, current_density=1.0):
    """1D: potential along x through layers [edges[i], edges[i+1]) of conductivity sigmas[i]; returns the apparent
    position phi / E_ref, with E_ref the field in the first layer."""
    x = np.asarray(x, float)
    phi = np.zeros_like(x)
    for i, s in enumerate(sigmas):
        lo, hi = edges[i], edges[i + 1]
        phi += current_density / s * (np.clip(x, lo, hi) - lo)
    return phi / (current_density / sigmas[0]) + edges[0]


# ---- eq-m17-precision ------------------------------------------------------------------------------------------

def position_noise(voltage_noise, field):
    """Position noise from voltage noise: delta phi / |E|."""
    return voltage_noise / field
