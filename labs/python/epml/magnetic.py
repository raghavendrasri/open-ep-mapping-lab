"""m16 · Magnetic localization: dipole fields, sensor-coil voltages, pose solving, precision and distortion.
MIT License.

Units: lengths in mm. Fields are in relative units with mu0/(4 pi) = 1 and generator moments of 1e6 (so fields are
of order 1 near 100 mm); sensor readings are n . B with unit gain. Noise is in the same relative units.
"""

import numpy as np
from scipy.optimize import least_squares

MU0 = 1.25663706212e-6        # vacuum permeability, N/A^2 (CODATA 2018)


# ---- eq-m16-dipole ---------------------------------------------------------------------------------------------

def dipole_field(m, r):
    """Field of a point dipole m at displacement r (rows allowed): (3 (m . rhat) rhat - m) / |r|^3, mu0/(4 pi) = 1."""
    r = np.asarray(r, float)
    d = np.linalg.norm(r, axis=-1, keepdims=True)
    rh = r / d
    return (3.0 * np.sum(m * rh, axis=-1, keepdims=True) * rh - m) / d ** 3


# ---- eq-m16-emf --------------------------------------------------------------------------------------------------

def emf_amplitude(freq, turns, area, b_normal):
    """Peak voltage of an N-turn coil of area A in a field oscillating at f with normal component amplitude B: 2 pi f N A B."""
    return 2.0 * np.pi * freq * turns * area * b_normal


# ---- the generator and the measurement model (eq-m16-coupling) ----------------------------------------------------

def generator(radius=150.0, moment=1e6, n_sites=3):
    """Illustrative field generator: n_sites coil trios (x, y, z moments) on a circle of the given radius at z = 0."""
    out = []
    for k in range(n_sites):
        a = 2.0 * np.pi * k / n_sites
        s = np.array([radius * np.cos(a), radius * np.sin(a), 0.0])
        for axis in np.eye(3):
            out.append((s, moment * axis))
    return out


def axis_from_angles(theta, phi):
    """Unit sensor axis from polar angle theta and azimuth phi (radians)."""
    return np.array([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)])


def field_matrix(p, gen):
    """Rows: the field of each generator coil at p. Readings are G(p) n."""
    return np.array([dipole_field(m, p - s) for s, m in gen])


def readings(params, gen):
    """Readings of a single-coil (5-DOF) sensor; params = (x, y, z, theta, phi)."""
    p, n = np.asarray(params[:3], float), axis_from_angles(params[3], params[4])
    return field_matrix(p, gen) @ n


def jacobian(params, gen, h=1e-4):
    """Numerical Jacobian of the readings with respect to (x, y, z, theta, phi)."""
    params = np.asarray(params, float)
    J = np.empty((len(gen), 5))
    for j in range(5):
        e = np.zeros(5)
        e[j] = h
        J[:, j] = (readings(params + e, gen) - readings(params - e, gen)) / (2 * h)
    return J


def solve_pose(v, gen, x0):
    """Nonlinear least squares for the 5-DOF pose."""
    res = least_squares(lambda q: readings(q, gen) - v, x0, method="lm", xtol=1e-12, ftol=1e-12)
    return res.x


# ---- eq-m16-crlb, eq-m16-sensitivity -----------------------------------------------------------------------------

def crlb(params, gen, sigma):
    """Covariance of the pose estimate for independent noise of SD sigma: sigma^2 (J^T J)^-1."""
    J = jacobian(params, gen)
    return sigma ** 2 * np.linalg.inv(J.T @ J)


def position_sd(params, gen, sigma):
    """RMS position error (mm): sqrt of the trace of the position block of the covariance."""
    return float(np.sqrt(np.trace(crlb(params, gen, sigma)[:3, :3])))


def axial_range_error(r, field, field_error):
    """On a dipole's axis |B| = 2m/r^3, so a field error dB moves the range by r dB / (3 |B|)."""
    return r * field_error / (3.0 * field)


# ---- eq-m16-5dof: roll is invisible to one coil -----------------------------------------------------------------

def rotate(v, axis, angle):
    """Rodrigues rotation of v about a unit axis."""
    axis = axis / np.linalg.norm(axis)
    return (v * np.cos(angle) + np.cross(axis, v) * np.sin(angle)
            + axis * np.dot(axis, v) * (1.0 - np.cos(angle)))


def rotation_jacobian_rank(p, n, gen, h=1e-5):
    """Rank of the readings' Jacobian with respect to position and a full 3-parameter rotation of the coil."""
    cols = []
    G = field_matrix(p, gen)
    for j in range(3):
        e = np.zeros(3); e[j] = h
        cols.append((field_matrix(p + e, gen) @ n - field_matrix(p - e, gen) @ n) / (2 * h))
    for axis in np.eye(3):
        cols.append((G @ rotate(n, axis, h) - G @ rotate(n, axis, -h)) / (2 * h))
    J = np.stack(cols, axis=1)
    s = np.linalg.svd(J, compute_uv=False)
    return int(np.sum(s > 1e-8 * s[0]))


# ---- eq-m16-distortion: an induced dipole in a nearby conductor ----------------------------------------------------

def distorted_readings(params, gen, q, alpha):
    """Readings when a small conductor at q responds to each generator coil with an induced dipole alpha B_k(q)."""
    p, n = np.asarray(params[:3], float), axis_from_angles(params[3], params[4])
    out = []
    for s, m in gen:
        mq = alpha * dipole_field(m, q - s)
        out.append(n @ (dipole_field(m, p - s) + dipole_field(mq, p - q)))
    return np.array(out)


def linear_bias(params, gen, dv):
    """First-order pose bias from a reading error dv: (J^T J)^-1 J^T dv."""
    J = jacobian(params, gen)
    return np.linalg.lstsq(J, dv, rcond=None)[0]
