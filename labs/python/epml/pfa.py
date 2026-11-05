"""m28 helpers: pulsed field ablation (induced membrane voltage, fields around electrodes, heating).

SI units: V, V/m, m, s, F/m^2, ohm m, S/m, J/(m^3 K).
"""

import numpy as np


def schwan_dpsi(E, R, theta):
    """eq-m28-schwan: steady induced transmembrane voltage 3/2 E R cos(theta) on a spherical cell."""
    return 1.5 * E * R * np.cos(theta)


def membrane_tau(R, Cm, rho_i, rho_e):
    """eq-m28-charging: tau_m = R C_m (rho_i + rho_e / 2)."""
    return R * Cm * (rho_i + 0.5 * rho_e)


def dpsi_step(E, R, theta, t, tau):
    """eq-m28-charging: response to a field switched on at t = 0."""
    return schwan_dpsi(E, R, theta) * (1.0 - np.exp(-np.asarray(t, dtype=float) / tau))


def sphere_potential(V, r0, r):
    """eq-m28-field-sphere: potential V r0 / r around an isolated sphere held at V."""
    return V * r0 / np.asarray(r, dtype=float)


def sphere_field(V, r0, r):
    """eq-m28-field-sphere: field magnitude V r0 / r^2."""
    return V * r0 / np.asarray(r, dtype=float) ** 2


def lesion_radius(V, r0, E_th):
    """eq-m28-lesion-radius: radius where the field falls to E_th, sqrt(V r0 / E_th)."""
    return np.sqrt(V * r0 / E_th)


def zone_radii(V, r0, E_rev, E_irr):
    """eq-m28-zones: outer radii of the reversible (E >= E_rev) and irreversible (E >= E_irr) zones."""
    return lesion_radius(V, r0, E_rev), lesion_radius(V, r0, E_irr)


def bipolar_potential(points, x1, V1, x2, V2, r0):
    """eq-m28-bipolar: superposition of two isolated-sphere potentials (well-separated electrodes)."""
    p = np.atleast_2d(points)
    d1 = np.linalg.norm(p - np.asarray(x1, float), axis=1)
    d2 = np.linalg.norm(p - np.asarray(x2, float), axis=1)
    return V1 * r0 / d1 + V2 * r0 / d2


def joule_bound(sigma, E, t_on, rho_c):
    """eq-m28-joule: adiabatic temperature rise sigma E^2 t_on / (rho c)."""
    return sigma * E**2 * t_on / rho_c
