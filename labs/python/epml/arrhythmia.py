"""m10 · Arrhythmia mechanisms: wavelength, reentry, alternans, spiral waves, focal activation. MIT License.

Units: distance mm, time ms, velocity mm/ms (= m/s), unless a model is dimensionless (Barkley). Cardiac kinetics are
Mitchell-Schaeffer (epml.ionic, parameters epml.membrane.MS_PARAMS); the restitution function is the m08 closed form.
"""

import numpy as np

from epml import ionic
from epml.complexmaps import plaquette_charges
from epml.membrane import MS_PARAMS, apds, ms_apd_closed, ms_cell

PARAMS = tuple(MS_PARAMS[k] for k in ("tau_in", "tau_out", "tau_open", "tau_close", "v_gate"))


# ---------------------------------------------------------------- eq-m10-wavelength, eq-m10-circuit


def wavelength(cv, erp):
    """eq-m10-wavelength: lambda = CV x ERP (mm when CV is in mm/ms and ERP in ms)."""
    return cv * erp


def circuit(path_length, cv, erp):
    """eq-m10-circuit: a fixed circuit of length L conducting at CV has cycle length L / CV; reentry needs L > lambda;
    the excitable gap is L - lambda in space and CL - ERP in time."""
    lam = wavelength(cv, erp)
    cl = path_length / cv
    return {"wavelength": lam, "cycle_length": cl, "gap_mm": path_length - lam, "gap_ms": cl - erp,
            "sustained": path_length > lam}


# ---------------------------------------------------------------- eq-m10-restitution, eq-m10-alternans


def restitution(di, params=MS_PARAMS):
    """The m08 closed-form restitution APD = f(DI)."""
    return ms_apd_closed(di, **params)


def restitution_slope(di, params=MS_PARAMS):
    hm = 4.0 * params["tau_in"] / params["tau_out"]
    e = np.exp(-np.asarray(di, float) / params["tau_open"])
    return params["tau_close"] * (1 - hm) * e / (params["tau_open"] * (1 - (1 - hm) * e))


def fixed_point(cl, params=MS_PARAMS):
    """eq-m10-restitution: the steady APD at cycle length CL solves APD = f(CL - APD) (f increases, so the root is
    unique). Returns (APD*, DI*) or (nan, nan) when there is none with DI > 0."""
    lo, hi = 0.0, cl
    g = lambda a: restitution(cl - a, params) - a
    if g(lo) <= 0 or not np.isfinite(g(lo)):
        return np.nan, np.nan
    for _ in range(200):
        mid = (lo + hi) / 2
        val = g(mid)
        if not np.isfinite(val) or val < 0:
            hi = mid
        else:
            lo = mid
    return lo, cl - lo


def iterate_map(cl, apd0, n, params=MS_PARAMS):
    """APD_{k+1} = f(CL - APD_k), stopping (NaN) if the diastolic interval becomes negative."""
    out = [apd0]
    for _ in range(n):
        di = cl - out[-1]
        out.append(restitution(di, params) if di > 0 else np.nan)
    return np.array(out)


def alternans_onset(params=MS_PARAMS):
    """eq-m10-alternans for the closed form: f'(DI) = 1 at DI_c = tau_open ln((1 - h_min)(1 + tau_close / tau_open));
    returns (DI_c, APD_c, CL_c = APD_c + DI_c)."""
    hm = 4.0 * params["tau_in"] / params["tau_out"]
    di = params["tau_open"] * np.log((1 - hm) * (1 + params["tau_close"] / params["tau_open"]))
    apd = restitution(di, params)
    return di, apd, apd + di


def paced_apds(cl, n_beats=30, params=MS_PARAMS, dt=0.02):
    """Pace one Mitchell-Schaeffer cell at cycle length CL; returns the APD of every beat that captured."""
    times = np.arange(n_beats) * cl
    t, v, _ = ms_cell(times[-1] + cl, times, params, dt=dt)
    return apds(t, v, params["v_gate"])[:, 1]


# ---------------------------------------------------------------- reentry on a ring


def traveling_pulse(D=0.1, dx=0.5, dt=0.02, length=320.0, params=PARAMS):
    """A single pulse on a long cable, stopped when its front reaches 90% of the length. Returns (v, h, front index):
    the state of a fully developed traveling wave, with its recovering tail behind the front."""
    n = int(round(length / dx))
    v = np.zeros(n)
    h = np.ones(n)
    v[:10] = 1.0
    while True:
        p = np.concatenate(([v[1]], v, [v[-2]]))
        lap = (p[2:] - 2 * v + p[:-2]) / dx**2
        dv, dh = ionic.ms_reaction(v, h, *params)
        v = v + dt * (D * lap + dv)
        h = h + dt * dh
        front = np.max(np.where(v > 0.5)[0]) if np.any(v > 0.5) else 0
        if front >= int(0.9 * n):
            return v, h, front


def ring_reentry(length, D=0.1, dx=0.5, dt=0.02, t_end=3000.0, params=PARAMS, pulse=None):
    """1D periodic Mitchell-Schaeffer ring started with the last `length` mm of a traveling pulse (front at the
    end), so the front runs into whatever is left of its own tail. Returns the activation times at the probe (node
    0); fewer than two means reentry failed."""
    if pulse is None:
        pulse = traveling_pulse(D, dx, dt, params=params)
    pv, ph, front = pulse
    n = int(round(length / dx))
    v = pv[front - n + 1: front + 1].copy()
    h = ph[front - n + 1: front + 1].copy()
    times = []
    for k in range(int(round(t_end / dt))):
        lap = (np.roll(v, 1) - 2 * v + np.roll(v, -1)) / dx**2
        dv, dh = ionic.ms_reaction(v, h, *params)
        vn = v + dt * (D * lap + dv)
        h = h + dt * dh
        if v[0] < 0.5 <= vn[0]:
            times.append(k * dt + dt * (0.5 - v[0]) / (vn[0] - v[0]))
        v = vn
    return np.array(times)


# ---------------------------------------------------------------- spiral waves (Barkley, dimensionless)

BARKLEY = {"a": 0.75, "b": 0.02, "eps": 0.02}   # illustrative


def barkley_spiral(n=120, dx=0.5, dt=0.02, t_end=60.0, a=0.75, b=0.02, eps=0.02, D=1.0):
    """Barkley model u_t = D lap u + u(1 - u)(u - (v + b) / a) / eps, v_t = u - v on an n x n grid with no-flux
    edges, started by cross-field initial conditions (a half-plane excited, the other half of it refractory) so a
    single spiral forms at the center. Returns u, v at t_end."""
    u = np.zeros((n, n))
    v = np.zeros((n, n))
    u[: n // 2, :] = 1.0                      # excited lower half ...
    v[:, : n // 2] = a / 2 + 0.2              # ... with a refractory left half
    for _ in range(int(round(t_end / dt))):
        p = np.pad(u, 1, mode="edge")
        lap = (p[2:, 1:-1] + p[:-2, 1:-1] + p[1:-1, 2:] + p[1:-1, :-2] - 4 * u) / dx**2
        u, v = u + dt * (D * lap + u * (1 - u) * (u - (v + b) / a) / eps), v + dt * (u - v)
    return u, v


def phase_field(u, v, u0=0.5, v0=None, a=0.75, b=0.02):
    """Phase angle of the state around a reference point inside the excitation loop."""
    if v0 is None:
        v0 = a * u0 - b
    return np.arctan2(v - v0, u - u0)


def singularities(phase):
    """Plaquettes with nonzero topological charge (eq-m29-charge): array of (row, col, charge)."""
    q = plaquette_charges(phase)
    idx = np.argwhere(q != 0)
    return np.array([(i, j, q[i, j]) for i, j in idx]).reshape(-1, 3)


# ---------------------------------------------------------------- eq-m10-focal


def focal_activation(x, y, x0, y0, cv):
    """eq-m10-focal: centrifugal spread from a focus, T = |x - x0| / CV."""
    return np.hypot(np.asarray(x, float) - x0, np.asarray(y, float) - y0) / cv


def activation_span(times, cycle_length):
    """Fraction of the cycle covered by the activation times of one beat (focal: below 1; reentry: the whole
    cycle)."""
    t = np.asarray(times, float)
    t = t[np.isfinite(t)]
    return (t.max() - t.min()) / cycle_length
