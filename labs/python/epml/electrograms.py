"""Electrogram models for module m03.

Units: distance mm, time ms, conduction velocity mm/ms (1 mm/ms = 1 m/s), potentials in
arbitrary units unless stated.

The model: a thin sheet of tissue in the plane z = 0, in an infinite homogeneous volume
conductor. A planar wavefront travels along the unit vector n at speed c. The transmembrane
voltage across the front has an arctangent profile of width w, so the membrane current
density has a closed form, and so does the potential at an electrode at height h:

    U(s) = A * s / (s**2 + a**2),   a = w + h,

where s is the signed distance from the front to the electrode's foot, measured along n
(s > 0: the front has not arrived yet). See modules/m03-electrograms.qmd, Derivations.
"""

import numpy as np
from scipy.special import j1


# ---------------------------------------------------------------- unipolar (planar wave)

def front_distance(points, n, t, c, s0=0.0):
    """Signed distance s from the wavefront to each point, along the propagation direction n.

    points: array (..., 2) in mm. n: unit vector (2,). t: time in ms (scalar or array).
    c: conduction velocity in mm/ms. The front passes the origin at t = 0 (shifted by s0).
    """
    points = np.asarray(points, dtype=float)
    n = np.asarray(n, dtype=float) / np.linalg.norm(n)
    proj = points @ n
    return np.subtract.outer(proj, c * np.asarray(t, dtype=float)) + s0


def unipolar(s, a, amplitude=1.0):
    """Unipolar potential U(s) = A s / (s^2 + a^2) for the arctangent-front model."""
    s = np.asarray(s, dtype=float)
    return amplitude * s / (s**2 + a**2)


def unipolar_ds(s, a, amplitude=1.0):
    """Spatial derivative dU/ds = A (a^2 - s^2) / (s^2 + a^2)^2."""
    s = np.asarray(s, dtype=float)
    return amplitude * (a**2 - s**2) / (s**2 + a**2) ** 2


def unipolar_amplitude(beta, delta_v, sigma):
    """Prefactor A = beta * dV / (2 pi sigma) of the arctangent-front model."""
    return beta * delta_v / (2.0 * np.pi * sigma)


# ---------------------------------------------------------------- bipolar

def bipolar_planar(s_center, d, theta, a, amplitude=1.0):
    """Bipolar signal U(s + delta) - U(s - delta), delta = (d/2) cos(theta).

    s_center: front distance at the bipole midpoint. d: spacing (mm).
    theta: angle between the bipole axis (pointing to electrode 1) and the propagation direction.
    """
    delta = 0.5 * d * np.cos(theta)
    return unipolar(np.asarray(s_center) + delta, a, amplitude) - unipolar(
        np.asarray(s_center) - delta, a, amplitude
    )


# ---------------------------------------------------------------- spatial transfer functions

def bipolar_transfer(k, d, theta=0.0):
    """Bipole transfer function H(k) = 2i sin(k d cos(theta) / 2) for a harmonic exp(i k n.r)."""
    return 2j * np.sin(0.5 * np.asarray(k, dtype=float) * d * np.cos(theta))


def height_transfer(k, h):
    """Low-pass factor exp(-|k| h) from recording at height h above the tissue sheet."""
    return np.exp(-np.abs(np.asarray(k, dtype=float)) * h)


def disk_transfer(k, radius):
    """Low-pass factor 2 J1(|k| r) / (|k| r) from averaging the potential over a disk of radius r."""
    x = np.abs(np.asarray(k, dtype=float)) * radius
    out = np.ones_like(x)
    nz = x > 0
    out[nz] = 2.0 * j1(x[nz]) / x[nz]
    return out


# ---------------------------------------------------------------- cliques and omnipoles

def clique_field(positions, potentials, pairs):
    """Least-squares electric field from the bipoles of a clique.

    positions: (m, 2) electrode positions in mm.
    potentials: (m, ...) unipolar signals, one row per electrode.
    pairs: list of (i, j); each bipole is b = phi_j - phi_i.

    The bipoles satisfy b = -D^T E, where column p of D is r_j - r_i, so
    E = -(D D^T)^-1 D b. Returns E with shape (2, ...).
    """
    positions = np.asarray(positions, dtype=float)
    potentials = np.asarray(potentials, dtype=float)
    D = np.stack([positions[j] - positions[i] for i, j in pairs], axis=1)  # (2, p)
    b = np.stack([potentials[j] - potentials[i] for i, j in pairs], axis=0)  # (p, ...)
    return -np.linalg.solve(D @ D.T, np.tensordot(D, b, axes=(1, 0)))


def loop_direction(E):
    """Principal axis of the E-field loop: unit vector of largest extent (sign arbitrary)."""
    E = np.asarray(E, dtype=float).reshape(2, -1)
    _, vecs = np.linalg.eigh(E @ E.T)
    return vecs[:, -1]


def omnipolar(E, d, direction=None):
    """Omnipolar signal: -d * E . omega, as if a bipole of spacing d pointed along omega.

    If direction is None, omega is the principal axis of the E loop. This is a simplification of
    the published method, which picks the direction that best matches the unipolar derivative.
    Returns (signal, omega).
    """
    omega = loop_direction(E) if direction is None else np.asarray(direction, dtype=float)
    omega = omega / np.linalg.norm(omega)
    return -d * np.tensordot(omega, np.asarray(E, dtype=float).reshape(2, -1), axes=1), omega


def peak_to_peak(x):
    """Peak-to-peak amplitude along the last axis."""
    x = np.asarray(x, dtype=float)
    return x.max(axis=-1) - x.min(axis=-1)
