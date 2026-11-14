"""m11 · The EP study: intervals, AV nodal conduction and Wenckebach periodicity, entrainment. MIT License.

Units: time ms, distance mm, velocity mm/ms (= m/s). Tissue kinetics are Mitchell-Schaeffer (epml.ionic, parameters
epml.membrane.MS_PARAMS). The AV node is a recovery-curve model with anterograde values measured in rabbit heart
preparations (Reid et al. 2003); its time constant is illustrative.
"""

import numpy as np

from epml import ionic
from epml.arrhythmia import PARAMS, traveling_pulse

# Rabbit anterograde AV nodal values in control (Reid et al. 2003): minimum and maximum nodal conduction time and
# nodal effective refractory period (ms). TAU is an illustrative recovery time constant.
AVN = {"nct_min": 57.0, "nct_max": 150.0, "erp": 91.0, "tau": 100.0}


# ---------------------------------------------------------------- eq-m11-intervals


def deflection(t, t0, width=2.0, amp=1.0):
    """A biphasic deflection (derivative of a Gaussian) whose steepest negative slope is at t0."""
    s = (t - t0) / width
    return -amp * s * np.exp(-0.5 * s**2) * np.sqrt(np.e)


def his_recording(t_a, t_h, t_v, fs=1000.0, duration=400.0, amps=(1.0, 0.3, 1.5), noise=0.0, seed=0):
    """A synthetic His-bundle recording: atrial, His and ventricular deflections at given times (ms)."""
    t = np.arange(0, duration, 1000.0 / fs)
    x = deflection(t, t_a, 3.0, amps[0]) + deflection(t, t_h, 1.0, amps[1]) + deflection(t, t_v, 4.0, amps[2])
    if noise:
        x = x + noise * np.random.default_rng(seed).standard_normal(t.size)
    return t, x


def local_time(t, x, window):
    """Local activation time in a window: the steepest negative slope, refined by parabolic interpolation."""
    sel = (t >= window[0]) & (t < window[1])
    d = np.gradient(x, t)
    idx = np.where(sel)[0]
    i = idx[np.argmin(d[sel])]
    if 0 < i < len(t) - 1:
        y0, y1, y2 = d[i - 1], d[i], d[i + 1]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den != 0 else 0.0
        return t[i] + off * (t[1] - t[0])
    return t[i]


def intervals(t_a, t_h, t_v):
    """eq-m11-intervals: AH = t_H - t_A and HV = t_V - t_H."""
    return t_h - t_a, t_v - t_h


# ---------------------------------------------------------------- eq-m11-avnode, eq-m11-wenckebach


def nodal_time(rt, p=AVN):
    """eq-m11-avnode: nodal conduction time after a recovery time rt (from the previous nodal output); NaN (block)
    below the nodal refractory period."""
    rt = np.asarray(rt, float)
    out = p["nct_min"] + (p["nct_max"] - p["nct_min"]) * np.exp(-(rt - p["erp"]) / p["tau"])
    return np.where(rt >= p["erp"], out, np.nan)


def av_sequence(cl, n=40, p=AVN):
    """Atrial beats every cl ms into the node; returns nodal conduction time per atrial beat (NaN when blocked).
    The recovery time is measured from the last conducted output."""
    out = []
    last_out = -np.inf
    for k in range(n):
        t_in = k * cl
        nct = float(nodal_time(t_in - last_out, p)) if np.isfinite(last_out) else p["nct_min"]
        if np.isfinite(nct):
            last_out = t_in + nct
        out.append(nct)
    return np.array(out)


def conduction_ratio(seq):
    """The repeating pattern of the steady sequence as (atrial beats, conducted beats) per cycle, e.g. (4, 3)."""
    blocked = np.where(np.isnan(seq))[0]
    if len(blocked) == 0:
        return (1, 1)
    if len(blocked) < 3:
        return None
    period = int(np.median(np.diff(blocked[-4:])))
    return (period, period - 1)


def wenckebach_cl(p=AVN):
    """eq-m11-wenckebach: the shortest cycle length with 1:1 conduction is ERP_N + NCT_max, provided the fixed point is
    stable there, i.e. (NCT_max - NCT_min) / tau < 1."""
    return p["erp"] + p["nct_max"], (p["nct_max"] - p["nct_min"]) / p["tau"]


# ---------------------------------------------------------------- eq-m11-ppi: entrainment of reentry on a ring


def ppi_outside(tcl, d, cv):
    """eq-m11-ppi: PPI - TCL = 2 d / CV for pacing a distance d (mm) away from the circuit along a path conducting at
    cv; zero inside the circuit (no decrement)."""
    return tcl + 2.0 * d / cv


def entrainment(ring=100.0, d=20.0, offset=20.0, n_pace=8, D=0.1, dx=0.5, dt=0.02, params=PARAMS, pulse=None):
    """Reentry on a Mitchell-Schaeffer ring with a dead-end branch of length d attached at one ring node; pace at the
    branch end (or on the ring when d = 0) at TCL - offset, then stop. Returns (TCL, PPI, cv_branch): TCL from the
    activations at the pacing site before pacing, PPI from the last stimulus to the next local activation, and the
    branch velocity measured during tachycardia."""
    if pulse is None:
        pulse = traveling_pulse(D, dx, dt, params=params)
    pv, ph, front = pulse
    nr = int(round(ring / dx))
    nc = int(round(d / dx))
    n = nr + nc
    v = np.zeros(n)
    h = np.ones(n)
    v[:nr] = pv[front - nr + 1: front + 1]
    h[:nr] = ph[front - nr + 1: front + 1]
    # neighbor lists: ring is periodic; branch node nr is attached to ring node 0
    nb = [[(i - 1) % nr, (i + 1) % nr] for i in range(nr)] + [[nr + j - 1, nr + j + 1] for j in range(nc)]
    if nc:
        nb[0].append(nr)
        nb[nr][0] = 0
        nb[n - 1] = [n - 2]                                  # sealed end
    width = max(len(x) for x in nb)
    idx = np.array([x + [i] * (width - len(x)) for i, x in enumerate(nb)])
    site = n - 1 if nc else 0
    mid = nr + nc // 2 if nc > 4 else None
    stim_nodes = np.arange(max(0, n - 3), n) if nc else np.array([0])

    def run(t0, t1, stims, v, h):
        act, act_mid = [], []
        for k in range(int(round((t1 - t0) / dt))):
            t = t0 + k * dt
            lap = (v[idx].sum(axis=1) - width * v) / dx**2
            dv, dh = ionic.ms_reaction(v, h, *params)
            stim = np.zeros(n)
            if any(s <= t < s + 1.0 for s in stims):
                stim[stim_nodes] = 1.0
            vn = v + dt * (D * lap + dv + stim)
            h = h + dt * dh
            if v[site] < 0.5 <= vn[site]:
                act.append(t)
            if mid is not None and v[mid] < 0.5 <= vn[mid]:
                act_mid.append(t)
            v = vn
        return v, h, np.array(act), np.array(act_mid)

    t_pre = 2500.0
    v, h, a0, m0 = run(0.0, t_pre, [], v, h)
    tcl = float(np.diff(a0)[-1])
    cv_b = np.nan
    if mid is not None and len(m0):
        last = a0[-1]
        mids = m0[m0 < last]
        if len(mids):
            cv_b = (nc - nc // 2 - 1) * dx / (last - mids[-1])
    pcl = tcl - offset
    first = a0[-1] + pcl
    stims = [first + k * pcl for k in range(n_pace)]
    v, h, a1, _ = run(t_pre, stims[-1] + 2.5 * tcl, stims, v, h)
    after = a1[a1 > stims[-1] + 5.0]
    ppi = float(after[0] - stims[-1]) if len(after) else np.nan
    return tcl, ppi, cv_b
