"""m08 · Action potentials and ionic models. MIT License.

Membrane as an RC circuit, Nernst potentials, Hodgkin-Huxley-type gating, the FitzHugh-Nagumo model and the
Mitchell-Schaeffer two-current model of the cardiac action potential (reaction terms from epml.ionic), with a
closed-form estimate of its action potential duration (APD) and restitution.

Units: time ms, voltage mV for the dimensional parts; FitzHugh-Nagumo and Mitchell-Schaeffer use dimensionless
voltage. Physical constants are the exact SI values used in CODATA 2018 (Tiesinga et al. 2021).
"""

import numpy as np

from epml.ionic import ms_reaction

# ---------------------------------------------------------------- constants (exact in the revised SI)
E_CHARGE = 1.602176634e-19        # C
K_BOLTZMANN = 1.380649e-23        # J / K
N_AVOGADRO = 6.02214076e23        # 1 / mol
FARADAY = N_AVOGADRO * E_CHARGE   # C / mol
R_GAS = N_AVOGADRO * K_BOLTZMANN  # J / (mol K)

# Mitchell-Schaeffer parameters (ms; v_gate dimensionless) as reported by Nieto Ramos et al. 2023 (arXiv 2311.10114),
# who state that they are based on the original paper (Mitchell and Schaeffer 2003).
MS_PARAMS = {"tau_in": 0.3, "tau_out": 6.0, "tau_open": 150.0, "tau_close": 120.0, "v_gate": 0.13}

# FitzHugh-Nagumo parameters: illustrative (dimensionless).
FHN_PARAMS = {"a": 0.7, "b": 0.8, "eps": 0.08}


# ---------------------------------------------------------------- eq-m08-membrane, eq-m08-nernst


def passive_step(t, current, resistance, capacitance):
    """eq-m08-membrane with I_ion = V / R: the response to a current step from rest, V(t) = I R (1 - exp(-t / RC))."""
    return current * resistance * (1.0 - np.exp(-np.asarray(t, float) / (resistance * capacitance)))


def thermal_voltage(temp_c=37.0):
    """RT / F in mV."""
    return 1e3 * R_GAS * (temp_c + 273.15) / FARADAY


def nernst(c_out, c_in, z=1, temp_c=37.0):
    """eq-m08-nernst: E = (RT / zF) ln(c_out / c_in), in mV."""
    return thermal_voltage(temp_c) / z * np.log(np.asarray(c_out, float) / np.asarray(c_in, float))


# ---------------------------------------------------------------- eq-m08-gating


def gate_steady(alpha, beta):
    """m_inf = alpha / (alpha + beta) and tau = 1 / (alpha + beta)."""
    return alpha / (alpha + beta), 1.0 / (alpha + beta)


def gate_clamp(t, m0, alpha, beta):
    """A gate under voltage clamp (constant alpha, beta): m(t) = m_inf + (m0 - m_inf) exp(-t / tau)."""
    m_inf, tau = gate_steady(alpha, beta)
    return m_inf + (m0 - m_inf) * np.exp(-np.asarray(t, float) / tau)


def euler_gate(t_end, dt, m0, alpha, beta):
    """The same by forward Euler, for checking."""
    m = m0
    for _ in range(int(round(t_end / dt))):
        m += dt * (alpha * (1 - m) - beta * m)
    return m


# ---------------------------------------------------------------- eq-m08-fhn, eq-m08-hopf


def fhn_rhs(v, w, current=0.0, a=0.7, b=0.8, eps=0.08):
    """eq-m08-fhn: dv/dt = v - v^3/3 - w + I, dw/dt = eps (v + a - b w)."""
    return v - v**3 / 3 - w + current, eps * (v + a - b * w)


def fhn_fixed_point(current=0.0, a=0.7, b=0.8, eps=0.08):
    """The unique fixed point (for b < 1 the cubic v - v^3/3 - (v + a)/b + I = 0 has one real root)."""
    roots = np.roots([-1 / 3, 0.0, 1 - 1 / b, current - a / b])
    v = float(np.real(roots[np.argmin(np.abs(np.imag(roots)))]))
    return v, (v + a) / b


def fhn_jacobian(v, a=0.7, b=0.8, eps=0.08):
    return np.array([[1 - v**2, -1.0], [eps, -eps * b]])


def fhn_hopf_current(a=0.7, b=0.8, eps=0.08):
    """eq-m08-hopf: the rest state loses stability when the trace 1 - v*^2 - eps b vanishes, at the left fixed point
    v* = -sqrt(1 - eps b), so I_H = v*^3 / 3 - v* + (v* + a) / b."""
    v = -np.sqrt(1 - eps * b)
    return v**3 / 3 - v + (v + a) / b


def fhn_simulate(t_end, dt=0.01, v0=None, w0=None, current=0.0, a=0.7, b=0.8, eps=0.08, kick=0.0):
    """RK4 integration from rest (or v0, w0) with an instantaneous kick added to v at t = 0. Returns t, v, w."""
    vr, wr = fhn_fixed_point(current, a, b, eps)
    v = (vr if v0 is None else v0) + kick
    w = wr if w0 is None else w0
    n = int(round(t_end / dt))
    out = np.empty((n + 1, 2))
    out[0] = v, w
    f = lambda v, w: fhn_rhs(v, w, current, a, b, eps)
    for i in range(n):
        k1 = f(v, w)
        k2 = f(v + dt / 2 * k1[0], w + dt / 2 * k1[1])
        k3 = f(v + dt / 2 * k2[0], w + dt / 2 * k2[1])
        k4 = f(v + dt * k3[0], w + dt * k3[1])
        v += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        w += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        out[i + 1] = v, w
    return np.arange(n + 1) * dt, out[:, 0], out[:, 1]


def fhn_threshold(current=0.0, a=0.7, b=0.8, eps=0.08, lo=0.0, hi=2.0, iters=40, t_end=60.0):
    """Smallest kick that produces a full excursion (peak v > 1), by bisection."""
    for _ in range(iters):
        mid = (lo + hi) / 2
        _, v, _ = fhn_simulate(t_end, 0.02, current=current, a=a, b=b, eps=eps, kick=mid)
        if v.max() > 1.0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- eq-m08-ms, eq-m08-apd


def ms_h_min(tau_in, tau_out, **_):
    """The smallest gate value that keeps the excited state: h_min = 4 tau_in / tau_out."""
    return 4.0 * tau_in / tau_out


def ms_apd_closed(di, tau_in, tau_out, tau_open, tau_close, **_):
    """eq-m08-apd: APD = tau_close ln(h0 / h_min), h0 = 1 - (1 - h_min) exp(-DI / tau_open). DI = inf gives the
    longest APD, tau_close ln(1 / h_min). An asymptotic estimate (tau_in << tau_out << tau_open, tau_close)."""
    hm = 4.0 * tau_in / tau_out
    h0 = 1.0 - (1.0 - hm) * np.exp(-np.asarray(di, float) / tau_open)
    return tau_close * np.log(h0 / hm)


def ms_restitution_slope(di, tau_in, tau_out, tau_open, tau_close, **_):
    """d APD / d DI of the closed form."""
    hm = 4.0 * tau_in / tau_out
    e = np.exp(-np.asarray(di, float) / tau_open)
    return tau_close * (1 - hm) * e / (tau_open * (1 - (1 - hm) * e))


def ms_cell(t_end, stim_times, params=None, dt=0.01, stim_amp=0.5, stim_dur=1.0, v0=0.0, h0=1.0):
    """Single Mitchell-Schaeffer cell by forward Euler with square stimuli (dimensionless current per ms; the
    amplitude 0.5 for 1 ms is an illustrative choice that captures reliably). Returns t, v, h."""
    p = dict(MS_PARAMS if params is None else params)
    args = (p["tau_in"], p["tau_out"], p["tau_open"], p["tau_close"], p["v_gate"])
    n = int(round(t_end / dt))
    t = np.arange(n + 1) * dt
    stim = np.zeros(n + 1)
    for s in np.atleast_1d(stim_times):
        stim[(t >= s) & (t < s + stim_dur)] = stim_amp
    v = np.empty(n + 1)
    h = np.empty(n + 1)
    v[0], h[0] = v0, h0
    for i in range(n):
        dv, dh = ms_reaction(v[i], h[i], *args)
        v[i + 1] = v[i] + dt * (dv + stim[i])
        h[i + 1] = h[i] + dt * dh
    return t, v, h


def apds(t, v, level):
    """Upstroke times, APDs and the diastolic intervals before each AP, measured at a crossing level."""
    up = np.where((v[:-1] < level) & (v[1:] >= level))[0]
    down = np.where((v[:-1] >= level) & (v[1:] < level))[0]
    rows = []
    for i, u in enumerate(up):
        d = down[down > u]
        if len(d) == 0:
            break
        prev = down[down < u]
        di = t[u] - t[prev[-1]] if len(prev) else np.nan
        rows.append((t[u], t[d[0]] - t[u], di))
    return np.array(rows).reshape(-1, 3)


def s1s2(s2_intervals, params=None, s1=500.0, n_s1=4, dt=0.02, stim_amp=0.5, stim_dur=1.0):
    """S1-S2 protocol: n_s1 beats at interval s1, then one premature beat. Returns rows (S2 interval, DI, APD of
    S2), APD and DI measured at v_gate; NaN APD when S2 fails to capture."""
    p = dict(MS_PARAMS if params is None else params)
    out = []
    for s2 in np.atleast_1d(s2_intervals):
        times = [k * s1 for k in range(n_s1)] + [(n_s1 - 1) * s1 + s2]
        t, v, _ = ms_cell(times[-1] + 600.0, times, p, dt, stim_amp, stim_dur)
        rows = apds(t, v, p["v_gate"])
        if len(rows) == n_s1 + 1:
            out.append((s2, rows[-1, 2], rows[-1, 1]))
        else:
            out.append((s2, np.nan, np.nan))
    return np.array(out)
