"""Mitchell-Schaeffer two-current membrane model on 1D cables and 2D sheets (m29, m33).

Mitchell CC, Schaeffer DG. Bull Math Biol 2003;65:767-793. The model uses a dimensionless voltage
v in [0, 1] and one gate h. Time constants are in ms. No default parameter values are given here:
callers pass them, with a source or a label saying they are illustrative.
"""

import numpy as np


def ms_reaction(v, h, tau_in, tau_out, tau_open, tau_close, v_gate):
    """Right-hand sides of the Mitchell-Schaeffer equations (without diffusion or stimulus)."""
    dv = h * v**2 * (1.0 - v) / tau_in - v / tau_out
    dh = np.where(v < v_gate, (1.0 - h) / tau_open, -h / tau_close)
    return dv, dh


def laplacian_1d(v, dx):
    """Second difference with no-flux ends."""
    out = np.empty_like(v)
    out[1:-1] = v[2:] - 2 * v[1:-1] + v[:-2]
    out[0] = 2 * (v[1] - v[0])
    out[-1] = 2 * (v[-2] - v[-1])
    return out / dx**2


def laplacian_2d(v, dx):
    """Five-point Laplacian with no-flux edges."""
    p = np.pad(v, 1, mode="edge")
    return (p[2:, 1:-1] + p[:-2, 1:-1] + p[1:-1, 2:] + p[1:-1, :-2] - 4 * v) / dx**2


def ms_cable(n, dx, dt, t_end, D, params, stim_times, stim_cells=3, stim_amp=0.5,
             stim_dur=1.0, record_every=1.0):
    """Paced 1D cable. Returns (times, upstroke times per cell as a list of arrays, v snapshots).

    D is the diffusion coefficient (length^2 / ms, in the units of dx). Upstroke time = first time
    v crosses 0.5 upward in each beat, linearly interpolated.
    """
    if D * dt / dx**2 > 0.5:
        raise ValueError("explicit diffusion step is unstable: need D dt / dx^2 <= 1/2")
    v = np.zeros(n)
    h = np.ones(n)
    steps = int(round(t_end / dt))
    rec = int(round(record_every / dt))
    ups = [[] for _ in range(n)]
    snaps, times = [], []
    stim_times = np.asarray(stim_times, dtype=float)
    for k in range(steps):
        t = k * dt
        dv, dh = ms_reaction(v, h, *params)
        stim = np.zeros(n)
        if np.any((t >= stim_times) & (t < stim_times + stim_dur)):
            stim[:stim_cells] = stim_amp
        v_new = v + dt * (D * laplacian_1d(v, dx) + dv + stim)
        h = h + dt * dh
        crossed = np.where((v < 0.5) & (v_new >= 0.5))[0]
        for i in crossed:
            frac = (0.5 - v[i]) / (v_new[i] - v[i])
            ups[i].append(t + frac * dt)
        v = v_new
        if k % rec == 0:
            snaps.append(v.copy())
            times.append(t)
    return np.array(times), [np.array(u) for u in ups], np.array(snaps)


def ms_sheet(nx, ny, dx, dt, t_end, D, excitable, params, stim_mask, stim_amp=1.0, stim_dur=2.0):
    """2D sheet with node-wise diffusion D (length^2/ms) and a mask of excitable nodes.

    Non-excitable nodes (scar) carry no current: faces touching them have zero conductance, so the
    scar is an insulating obstacle. Face conductances are the mean of the two nodes. Returns the
    activation time of each node (first upward crossing of v = 0.5, interpolated), NaN if never.
    """
    D = np.where(excitable, np.asarray(D, dtype=float), 0.0)
    if np.max(D) * dt / dx**2 > 0.25:
        raise ValueError("explicit 2D diffusion step is unstable: need D dt / dx^2 <= 1/4")
    ex = np.asarray(excitable, dtype=bool)
    Dx = 0.5 * (D[:, 1:] + D[:, :-1]) * (ex[:, 1:] & ex[:, :-1])
    Dy = 0.5 * (D[1:, :] + D[:-1, :]) * (ex[1:, :] & ex[:-1, :])
    v = np.zeros((ny, nx))
    h = np.ones((ny, nx))
    act = np.full((ny, nx), np.nan)
    steps = int(round(t_end / dt))
    stim = np.where(stim_mask & ex, stim_amp, 0.0)
    for k in range(steps):
        t = k * dt
        fx = Dx * (v[:, 1:] - v[:, :-1])
        fy = Dy * (v[1:, :] - v[:-1, :])
        div = np.zeros_like(v)
        div[:, :-1] += fx
        div[:, 1:] -= fx
        div[:-1, :] += fy
        div[1:, :] -= fy
        dv, dh = ms_reaction(v, h, *params)
        dv = np.where(ex, dv, 0.0)
        dh = np.where(ex, dh, 0.0)
        v_new = v + dt * (div / dx**2 + dv + (stim if t < stim_dur else 0.0))
        h = h + dt * dh
        up = np.isnan(act) & (v < 0.5) & (v_new >= 0.5)
        if up.any():
            frac = (0.5 - v[up]) / (v_new[up] - v[up])
            act[up] = t + frac * dt
        v = v_new
    return act
