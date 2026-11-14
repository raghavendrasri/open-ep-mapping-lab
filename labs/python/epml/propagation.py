"""m09 · Propagation: cable theory, monodomain and bidomain, anisotropy, curvature. MIT License.

Units: distance mm, time ms, conduction velocity mm/ms (= m/s). Reaction kinetics are Mitchell-Schaeffer
(epml.ionic, parameters epml.membrane.MS_PARAMS); diffusion coefficients D = sigma / (chi C_m) in mm^2/ms.
"""

import numpy as np

from epml import ionic
from epml.membrane import MS_PARAMS

PARAMS = tuple(MS_PARAMS[k] for k in ("tau_in", "tau_out", "tau_open", "tau_close", "v_gate"))

# Ratios measured in calf trabeculae by classical cable analysis (Clerc 1976): longitudinal / transverse conduction
# velocity 3.0; intracellular / extracellular resistance 3.6 (longitudinal) and 12.6 (transverse); intracellular
# transverse / longitudinal 9.4; extracellular transverse / longitudinal 2.7.
CLERC = {"cv_ratio": 3.0, "ri_re_L": 3.6, "ri_re_T": 12.6, "ri_T_L": 9.4, "re_T_L": 2.7}


# ---------------------------------------------------------------- eq-m09-cable


def length_constant(r_m, r_i, r_e=0.0):
    """lambda = sqrt(r_m / (r_i + r_e)) (membrane resistance x length, axial resistances per length)."""
    return np.sqrt(r_m / (r_i + r_e))


def cable_steady(x, v0, lam):
    """Steady response to a held voltage v0 at x = 0 of an infinite passive cable: v0 exp(-|x| / lambda)."""
    return v0 * np.exp(-np.abs(np.asarray(x, float)) / lam)


def cable_steady_fd(n, dx, lam, v0=1.0):
    """The same by finite differences on [0, n dx] with v(0) = v0 and a sealed far end (for checking)."""
    A = np.zeros((n, n))
    b = np.zeros(n)
    for i in range(n):
        A[i, i] = -2.0 / dx**2 - 1.0 / lam**2
        if i > 0:
            A[i, i - 1] = 1.0 / dx**2
        else:
            b[i] -= v0 / dx**2
        if i < n - 1:
            A[i, i + 1] = 1.0 / dx**2
        else:
            A[i, i - 1] += 1.0 / dx**2
    return np.linalg.solve(A, b)


# ---------------------------------------------------------------- eq-m09-monodomain, eq-m09-cv


def monodomain_conductivity(sigma_i, sigma_e):
    """Harmonic combination sigma_i sigma_e / (sigma_i + sigma_e), per principal direction."""
    sigma_i, sigma_e = np.asarray(sigma_i, float), np.asarray(sigma_e, float)
    return sigma_i * sigma_e / (sigma_i + sigma_e)


def clerc_conductivities():
    """Relative principal conductivities from Clerc's resistance ratios (intracellular longitudinal = 1)."""
    si_L = 1.0
    si_T = 1.0 / CLERC["ri_T_L"]
    se_L = CLERC["ri_re_L"]
    se_T = se_L / CLERC["re_T_L"]
    return si_L, si_T, se_L, se_T


def cv_ratio_from_conductivities(si_L, si_T, se_L, se_T):
    """eq-m09-cv: CV_L / CV_T = sqrt(sigma_m,L / sigma_m,T) for the monodomain conductivities."""
    return np.sqrt(monodomain_conductivity(si_L, se_L) / monodomain_conductivity(si_T, se_T))


def cable_cv(D, dx=0.1, dt=None, length=30.0, t_end=None, params=PARAMS):
    """Plane-wave conduction velocity on a 1D Mitchell-Schaeffer cable, from a fit of activation time against
    position over the middle third. Returns mm/ms."""
    if dt is None:
        dt = min(0.005, 0.2 * dx**2 / D)
    n = int(round(length / dx))
    if t_end is None:
        t_end = 3.0 * length / np.sqrt(D / 0.1) / 0.3 + 20.0
    _, ups, _ = ionic.ms_cable(n, dx, dt, t_end, D, params, [0.0], stim_cells=max(3, int(round(0.5 / dx))),
                               stim_amp=1.0, stim_dur=1.0)
    t = np.array([u[0] if len(u) else np.nan for u in ups])
    x = np.arange(n) * dx
    sel = (x > length / 3) & (x < 2 * length / 3)
    return 1.0 / np.polyfit(x[sel], t[sel], 1)[0]


def d_for_cv(target, D0=0.1, **kw):
    """eq-m09-cv used backwards: D = D0 (target / CV(D0))^2, then one correction step."""
    D = D0 * (target / cable_cv(D0, **kw)) ** 2
    return D * (target / cable_cv(D, **kw)) ** 2


# ---------------------------------------------------------------- eq-m09-anisotropy


def point_activation(x, y, cv_l, cv_t, angle=0.0):
    """Far-field activation time from a point at the origin in uniform anisotropic tissue with fibers at `angle`
    (radians): T = sqrt(x_l^2 / cv_l^2 + x_t^2 / cv_t^2)."""
    c, s = np.cos(angle), np.sin(angle)
    xl = c * np.asarray(x, float) + s * np.asarray(y, float)
    xt = -s * np.asarray(x, float) + c * np.asarray(y, float)
    return np.sqrt(xl**2 / cv_l**2 + xt**2 / cv_t**2)


def ray_speed(theta, cv_l, cv_t):
    """Apparent speed along a ray at angle theta to the fibers: cv_l cv_t / sqrt(cv_t^2 cos^2 + cv_l^2 sin^2)."""
    return cv_l * cv_t / np.sqrt(cv_t**2 * np.cos(theta) ** 2 + cv_l**2 * np.sin(theta) ** 2)


def sheet_activation(n, dx, dt, t_end, D_l, D_t, params=PARAMS, stim_radius=1.0):
    """Anisotropic Mitchell-Schaeffer sheet (fibers along x), stimulated in a disk at the center. Returns the
    activation time of each node (first upward crossing of v = 0.5, interpolated; NaN if never)."""
    if dt * 2 * (D_l + D_t) / dx**2 > 0.5:
        raise ValueError("explicit step unstable")
    v = np.zeros((n, n))
    h = np.ones((n, n))
    c = (n - 1) / 2
    yy, xx = np.mgrid[0:n, 0:n]
    stim = ((xx - c) ** 2 + (yy - c) ** 2) * dx**2 <= stim_radius**2
    act = np.full((n, n), np.nan)
    for k in range(int(round(t_end / dt))):
        t = k * dt
        p = np.pad(v, 1, mode="edge")
        lap = D_l * (p[1:-1, 2:] - 2 * v + p[1:-1, :-2]) + D_t * (p[2:, 1:-1] - 2 * v + p[:-2, 1:-1])
        dv, dh = ionic.ms_reaction(v, h, *params)
        vn = v + dt * (lap / dx**2 + dv + (1.0 if t < 1.0 else 0.0) * stim)
        h = h + dt * dh
        cross = np.isnan(act) & (v < 0.5) & (vn >= 0.5)
        act[cross] = t + dt * (0.5 - v[cross]) / (vn[cross] - v[cross])
        v = vn
    return act


# ---------------------------------------------------------------- eq-m09-curvature


def radial_wave(D, dr=0.05, dt=0.002, radius=12.0, t_end=30.0, r_stim=1.0, stim_amp=1.0, params=PARAMS):
    """A circular wave expanding from a disk stimulus, by the radially symmetric equation
    v_t = D (v_rr + v_r / r) + f(v, h). Returns (r, activation time) with NaN where it never arrives."""
    r = (np.arange(int(round(radius / dr))) + 0.5) * dr
    v = np.zeros_like(r)
    h = np.ones_like(r)
    act = np.full_like(r, np.nan)
    stim = r <= r_stim
    rp, rm = r + dr / 2, r - dr / 2
    for k in range(int(round(t_end / dt))):
        t = k * dt
        flux = np.zeros(len(r) + 1)                         # no flux at r = 0 and at the outer edge
        flux[1:-1] = (v[1:] - v[:-1]) / dr
        lap = (rp * flux[1:] - rm * flux[:-1]) / (r * dr)
        dv, dh = ionic.ms_reaction(v, h, *params)
        vn = v + dt * (D * lap + dv + (stim_amp if t < 1.0 else 0.0) * stim)
        h = h + dt * dh
        cross = np.isnan(act) & (v < 0.5) & (vn >= 0.5)
        act[cross] = t + dt * (0.5 - v[cross]) / (vn[cross] - v[cross])
        v = vn
    return r, act


def front_speed(r, act):
    """Local front speed dr/dT by central differences of the activation time."""
    return 1.0 / np.gradient(act, r)
