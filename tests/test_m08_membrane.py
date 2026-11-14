"""m08 · Action potentials and ionic models: equation tests."""

import numpy as np
import pytest
import sympy as sp

from epml import membrane as M

P = M.MS_PARAMS


def test_membrane():
    """eq-m08-membrane: with I_ion = V / R, a current step gives V = I R (1 - exp(-t / RC)); tau = RC."""
    t, I, R, C, V = sp.symbols("t I R C V", positive=True)
    Vt = I * R * (1 - sp.exp(-t / (R * C)))
    assert sp.simplify(C * sp.diff(Vt, t) + Vt / R - I) == 0 and Vt.subs(t, 0) == 0
    assert M.passive_step(2.0, 1.0, 10.0, 0.2) == pytest.approx(10 * (1 - np.exp(-1)))


def test_nernst():
    """eq-m08-nernst: RT/F = 26.7 mV at 37 C from the exact SI constants; 61.5 mV per tenfold gradient; sign
    and valence."""
    assert M.thermal_voltage(37.0) == pytest.approx(26.7267, abs=1e-4)
    assert M.nernst(10, 1) == pytest.approx(M.thermal_voltage() * np.log(10))
    assert M.thermal_voltage() * np.log(10) == pytest.approx(61.54, abs=0.01)
    assert M.nernst(1, 10) == pytest.approx(-M.nernst(10, 1))
    assert M.nernst(10, 1, z=2) == pytest.approx(M.nernst(10, 1) / 2)


def test_gating():
    """eq-m08-gating: under voltage clamp a gate relaxes exponentially to alpha / (alpha + beta) with time constant
    1 / (alpha + beta); forward Euler converges to it."""
    t, a, b, m0 = sp.symbols("t alpha beta m0", positive=True)
    m = a / (a + b) + (m0 - a / (a + b)) * sp.exp(-(a + b) * t)
    assert sp.simplify(sp.diff(m, t) - (a * (1 - m) - b * m)) == 0
    exact = M.gate_clamp(5.0, 0.1, 0.4, 0.1)
    assert abs(M.euler_gate(5.0, 1e-3, 0.1, 0.4, 0.1) - exact) < 1e-4
    assert M.gate_steady(0.4, 0.1) == pytest.approx((0.8, 2.0))


def test_fhn():
    """eq-m08-fhn: the rest state lies on both nullclines and is stable; kicks below the threshold decay, kicks above
    it give a full excursion (all or none); a second kick during recovery fails."""
    v, w = M.fhn_fixed_point()
    dv, dw = M.fhn_rhs(v, w)
    assert abs(dv) < 1e-12 and abs(dw) < 1e-12
    assert np.all(np.real(np.linalg.eigvals(M.fhn_jacobian(v))) < 0)
    th = M.fhn_threshold()
    assert M.fhn_simulate(60, 0.02, kick=0.9 * th)[1].max() < 0.5
    assert M.fhn_simulate(60, 0.02, kick=1.1 * th)[1].max() > 1.5
    t, vv, ww = M.fhn_simulate(10, 0.02, kick=1.1 * th)        # still excited / recovering at t = 10
    late = M.fhn_simulate(60, 0.02, v0=vv[-1] - 0.0, w0=ww[-1] + 0.0, kick=0.0)
    i = np.argmax(late[1] < 0)                               # back below zero, w still high: refractory
    again = M.fhn_simulate(60, 0.02, v0=late[1][i], w0=late[2][i], kick=1.1 * th)
    assert again[1].max() < late[1].max()


def test_hopf():
    """eq-m08-hopf: the trace of the Jacobian vanishes at v* = -sqrt(1 - eps b); the current that puts the rest
    state there is I_H; below it the rest state is stable, above it the cell fires repetitively."""
    a, b, eps, v = sp.symbols("a b epsilon v", real=True)
    J = sp.Matrix([[1 - v**2, -1], [eps, -eps * b]])
    sol = sp.solve(sp.Eq(J.trace(), 0), v)
    assert any(sp.simplify(s + sp.sqrt(1 - b * eps)) == 0 for s in sol)
    IH = M.fhn_hopf_current()
    vf, _ = M.fhn_fixed_point(IH)
    assert np.trace(M.fhn_jacobian(vf)) == pytest.approx(0, abs=1e-9)
    for I, osc in ((IH - 0.03, False), (IH + 0.03, True)):
        t, vv, _ = M.fhn_simulate(400, 0.02, current=I, kick=0.01)
        assert (np.ptp(vv[t > 250]) > 1.0) == osc


def test_ms_model():
    """eq-m08-ms: the excited state v(1 - v) = tau_in / (h tau_out) exists only for h >= h_min = 4 tau_in / tau_out;
    while v > v_gate the gate decays as exp(-t / tau_close), so it reaches h_min at tau_close ln(h_up / h_min)."""
    v, h, ti, to = sp.symbols("v h tau_in tau_out", positive=True)
    roots = sp.solve(sp.Eq(h * v * (1 - v) / ti, 1 / to), v)
    disc = sp.discriminant(sp.expand((h * v * (1 - v) / ti - 1 / to) * ti * to), v)
    assert sp.simplify(disc.subs(h, 4 * ti / to)) == 0 and len(roots) == 2
    t, vv, hh = M.ms_cell(600, [0.0], P, dt=0.01)
    up = np.argmax(vv > P["v_gate"])
    cross = np.argmax(hh < M.ms_h_min(**P))
    assert t[cross] - t[up] == pytest.approx(P["tau_close"] * np.log(hh[up] / M.ms_h_min(**P)), abs=0.2)


def test_ms_apd():
    """eq-m08-apd: the closed form gives when the excited state disappears (193 ms for a rested cell); the voltage
    reaches v_gate 25-40 ms later because it lingers near the vanished state, so the closed form runs short by that
    much at every diastolic interval of 40 ms or more; the restitution slope at DI -> 0 is
    tau_close (1 - h_min) / (tau_open h_min)."""
    assert M.ms_apd_closed(np.inf, **P) == pytest.approx(P["tau_close"] * np.log(5.0))
    res = M.s1s2(np.array([260.0, 300.0, 400.0, 600.0]), P)
    gap = res[:, 2] - M.ms_apd_closed(res[:, 1], **P)
    assert np.all((gap > 25) & (gap < 45))
    assert np.all(np.diff(res[:, 2]) > 0)
    hm = M.ms_h_min(**P)
    assert M.ms_restitution_slope(0.0, **P) == pytest.approx(P["tau_close"] * (1 - hm) / (P["tau_open"] * hm))
    d = sp.Symbol("d", positive=True)
    tc, top, hmin = sp.symbols("tau_c tau_o h_m", positive=True)
    apd = tc * sp.log((1 - (1 - hmin) * sp.exp(-d / top)) / hmin)
    assert sp.simplify(sp.diff(apd, d).subs(d, 0) - tc * (1 - hmin) / (top * hmin)) == 0
