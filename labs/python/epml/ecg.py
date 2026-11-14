"""m12 · The surface ECG and the forward problem. MIT License.

A homogeneous, insulated spherical torso of radius R and conductivity sigma. Frontal-plane coordinates: x to the
patient's left, y inferior (toward the feet), z anterior. Potentials in units of (current x length) / (sigma x
length^2) unless sigma and lengths are given in SI units. Limb electrodes sit at the corners of Einthoven's
equilateral triangle on the sphere's frontal circle.
"""

import numpy as np
from scipy.special import eval_legendre

# Einthoven's idealization: right arm, left arm and foot on the frontal circle, 120 degrees apart (x left, y down)
LIMBS = {
    "R": np.array([-np.cos(np.pi / 6), -0.5, 0.0]),
    "L": np.array([np.cos(np.pi / 6), -0.5, 0.0]),
    "F": np.array([0.0, 1.0, 0.0]),
}


# ---------------------------------------------------------------- eq-m12-sphere, eq-m12-series


def centric_surface(p, rhat, sigma=1.0, R=1.0):
    """eq-m12-sphere: surface potential of a dipole p at the center of an insulated homogeneous sphere,
    3 p . rhat / (4 pi sigma R^2)."""
    return 3.0 * np.dot(rhat, p) / (4 * np.pi * sigma * R**2)


def centric_interior(p, x, sigma=1.0, R=1.0):
    """Interior potential: (p . rhat / 4 pi sigma) (1 / r^2 + 2 r / R^3)."""
    x = np.asarray(x, float)
    r = np.linalg.norm(x)
    return np.dot(p, x / r) / (4 * np.pi * sigma) * (1 / r**2 + 2 * r / R**3)


def source_surface(current, r0, x, sigma=1.0, R=1.0, lmax=200):
    """eq-m12-series: surface potential at x (|x| = R) of a point current source at r0 inside an insulated sphere,
    sum over l >= 1 of ((2l + 1) / l) r0^l / R^(l + 1) P_l(cos gamma), times I / (4 pi sigma); the l = 0 term is a
    constant that cancels for a source-sink pair."""
    r0 = np.asarray(r0, float)
    x = np.asarray(x, float)
    a = np.linalg.norm(r0)
    if a == 0:
        return 0.0
    c = np.dot(r0, x) / (a * R)
    ls = np.arange(1, lmax + 1)
    terms = (2 * ls + 1) / ls * a**ls / R ** (ls + 1) * eval_legendre(ls, c)
    return current / (4 * np.pi * sigma) * terms.sum()


def dipole_surface(p, r0, x, sigma=1.0, R=1.0, lmax=200, h=1e-4):
    """Surface potential of a dipole p at r0 (|r0| < R), as a source-sink pair a small distance h apart."""
    p = np.asarray(p, float)
    m = np.linalg.norm(p)
    if m == 0:
        return 0.0
    u = p / m
    r0 = np.asarray(r0, float)
    return (source_surface(m / h, r0 + u * h / 2, x, sigma, R, lmax)
            - source_surface(m / h, r0 - u * h / 2, x, sigma, R, lmax))


# ---------------------------------------------------------------- eq-m12-lead


def lead_vector(a, b, r0=(0.0, 0.0, 0.0), sigma=1.0, R=1.0, lmax=200):
    """eq-m12-lead: the lead vector of the electrode pair (a minus b) for a dipole at r0: the lead voltage for unit
    dipoles along x, y and z. For r0 at the center it is 3 (a_hat - b_hat) / (4 pi sigma R^2)."""
    a = np.asarray(a, float) * R / np.linalg.norm(a)
    b = np.asarray(b, float) * R / np.linalg.norm(b)
    r0 = np.asarray(r0, float)
    out = []
    for e in np.eye(3):
        if np.allclose(r0, 0):
            out.append(centric_surface(e, a / R, sigma, R) - centric_surface(e, b / R, sigma, R))
        else:
            out.append(dipole_surface(e, r0, a, sigma, R, lmax) - dipole_surface(e, r0, b, sigma, R, lmax))
    return np.array(out)


# ---------------------------------------------------------------- eq-m12-einthoven, eq-m12-augmented, eq-m12-axis


def limb_leads(phi_r, phi_l, phi_f):
    """eq-m12-einthoven and eq-m12-augmented: leads I, II, III, aVR, aVL, aVF and the Wilson central terminal."""
    I = phi_l - phi_r
    II = phi_f - phi_r
    III = phi_f - phi_l
    wct = (phi_r + phi_l + phi_f) / 3
    return {"I": I, "II": II, "III": III, "aVR": phi_r - (phi_l + phi_f) / 2, "aVL": phi_l - (phi_r + phi_f) / 2,
            "aVF": phi_f - (phi_r + phi_l) / 2, "WCT": wct}


def frontal_axis(lead_i, avf):
    """eq-m12-axis: frontal-plane axis (degrees; 0 = lead I, +90 = inferior) in Einthoven's equilateral
    idealization, where aVF's lead vector is sqrt(3)/2 as long as lead I's: atan2(2 aVF / sqrt(3), I)."""
    return np.degrees(np.arctan2(2 * np.asarray(avf, float) / np.sqrt(3), np.asarray(lead_i, float)))


def leads_for_dipole(p, r0=(0.0, 0.0, 0.0), sigma=1.0, R=1.0, limbs=LIMBS):
    """Limb leads for one dipole (centric closed form or the series for an eccentric dipole)."""
    r0 = np.asarray(r0, float)
    if np.allclose(r0, 0):
        phi = {k: centric_surface(p, v, sigma, R) for k, v in limbs.items()}
    else:
        phi = {k: dipole_surface(p, r0, v * R, sigma, R) for k, v in limbs.items()}
    return limb_leads(phi["R"], phi["L"], phi["F"])


# ---------------------------------------------------------------- eq-m12-forward


def front_heart_vector(t, direction, radius=30.0, cv=0.6, strength=1.0):
    """eq-m12-forward for a planar activation front crossing a ball of tissue (radius mm) at cv (mm/ms) along a unit
    direction: the heart vector is the front's dipole moment, strength x front area x direction, with front area
    pi (a^2 - s^2) where s is the front's position from the center. Returns p(t) as an array (n_times, 3)."""
    u = np.asarray(direction, float)
    u = u / np.linalg.norm(u)
    s = -radius + cv * np.asarray(t, float)
    area = np.where(np.abs(s) < radius, np.pi * (radius**2 - s**2), 0.0)
    return strength * area[:, None] * u[None, :]


def lead_signals(p_t, lead_vectors):
    """Lead voltages over time, V(t) = L . p(t), for a dict of lead vectors."""
    return {k: p_t @ np.asarray(v, float) for k, v in lead_vectors.items()}
