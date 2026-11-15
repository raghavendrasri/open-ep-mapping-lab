"""m14 equation tests: CMRR, difference and instrumentation amplifiers, electrode imbalance, driven right leg,
noise, Wilson central terminal, oversampling."""

import numpy as np
import pytest
import sympy as sp

from epml import frontend as F


def test_cmrr():
    """eq-m14-cmrr: v+ = v_cm + v_d/2, v- = v_cm - v_d/2; CMRR = A_d / A_cm."""
    vp, vm = sp.symbols("v_p v_m")
    vd, vcm = F.split_modes(vp, vm)
    assert sp.simplify(vcm + vd / 2 - vp) == 0 and sp.simplify(vcm - vd / 2 - vm) == 0
    assert F.to_db(1000.0) == pytest.approx(60.0)


def test_diffamp():
    """eq-m14-diffamp: gain r2/r1 for matched resistors; worst-case CMRR (1 + G)/(4 tol)."""
    v1, v2, r1, r2, r3, r4, vx = sp.symbols("v1 v2 r1 r2 r3 r4 v_x")
    # Ideal op amp: both inputs at vx; KCL at the inverting node with feedback to the output.
    vout = sp.symbols("v_out")
    vx_val = v2 * r4 / (r3 + r4)
    sol = sp.solve(sp.Eq((v1 - vx_val) / r1, (vx_val - vout) / r2), vout)[0]
    assert sp.simplify(sol - F.diff_amp(v1, v2, r1, r2, r3, r4)) == 0
    G = sp.symbols("G", positive=True)
    assert sp.simplify(F.diff_amp(v1, v2, 1, G, 1, G) - G * (v2 - v1)) == 0
    # First-order CMRR with the worst-case pattern of tolerances.
    t = sp.symbols("t", positive=True)
    ad, acm = F.diff_amp_gains(1 + t, G * (1 - t), 1 - t, G * (1 + t))
    lead = sp.series(sp.simplify(acm / ad), t, 0, 2).removeO()
    assert sp.simplify(lead - 4 * t / (1 + G)) == 0
    rng = np.random.default_rng(0)
    c = F.random_cmrr(10.0, 0.01, 20000, rng)
    assert np.min(c) > 0.95 * F.worst_case_cmrr(10.0, 0.01)       # random resistors never beat the worst case by much


def test_inamp():
    """eq-m14-inamp: input stage gain 1 + 2R/R_G, common mode at unity; total CMRR = G1 x stage-2 CMRR."""
    vm, vp, R, Rg = sp.symbols("v_m v_p R R_G", positive=True)
    a, b = F.inamp_first_stage(vm, vp, R, Rg)
    assert sp.simplify((b - a) - (1 + 2 * R / Rg) * (vp - vm)) == 0
    assert sp.simplify((a + b) / 2 - (vp + vm) / 2) == 0
    t = 1e-3
    rs = (1 + t, 10 * (1 - t), 1 - t, 10 * (1 + t))
    base = abs(np.divide(*F.diff_amp_gains(*rs)))
    for rg in (2000.0, 200.0):
        g1 = 1 + 2 * 1e4 / rg
        assert F.inamp_cmrr(1e4, rg, *rs) == pytest.approx(g1 * base, rel=1e-3)


def test_imbalance():
    """eq-m14-imbalance: error ~ v_cm (z2 - z1)/z_cm; mismatches add to the amplifier's 1/CMRR."""
    v, z1, z2, zc, eps = sp.symbols("v z1 z2 z_c epsilon", positive=True)
    err = F.imbalance_error(v, eps * z1, eps * z2, zc)
    first = sp.series(err, eps, 0, 2).removeO()
    assert sp.simplify(first - v * eps * (z1 - z2) / zc) == 0
    assert F.imbalance_cmrr(1e4, 1e8) == pytest.approx(1e4)
    assert F.combined_cmrr(1e4, 1e4) == pytest.approx(5e3)
    # A capacitive input impedance works with complex numbers.
    zc_c = 1 / (2j * np.pi * 50 * 10e-12)
    assert abs(F.imbalance_error(1.0, 5e3, 15e3, zc_c)) == pytest.approx(1e4 / abs(zc_c), rel=1e-3)


def test_drl():
    """eq-m14-drl: feeding back -G times the common mode divides it by 1 + G."""
    i, z, G, vcm = sp.symbols("i_d Z_RL G v_cm", positive=True)
    sol = sp.solve(sp.Eq(vcm, i * z - G * vcm), vcm)[0]
    assert sp.simplify(sol - F.body_common_mode(i, z, G)) == 0


def test_noise():
    """eq-m14-noise: sources add in quadrature; the noise factor is smallest at R = e_n / i_n."""
    R, en, inn, k, T = sp.symbols("R e_n i_n k T", positive=True)
    Fn = (4 * k * T * R + en ** 2 + inn ** 2 * R ** 2) / (4 * k * T * R)
    assert sp.solve(sp.diff(Fn, R), R) == [en / inn]
    assert F.thermal_density(1e3) == pytest.approx(np.sqrt(4 * 1.380649e-23 * 310.15 * 1e3))
    rng = np.random.default_rng(14)
    n = 200000
    parts = [d * rng.standard_normal(n) for d in (3.0, 4.0, 12.0)]
    assert np.std(sum(parts)) == pytest.approx(13.0, rel=0.01)
    e_n, i_n = 4e-9, 1e-12
    r = np.logspace(2, 7, 400)
    assert r[np.argmin(F.noise_factor(r, e_n, i_n))] == pytest.approx(F.optimal_source_resistance(e_n, i_n), rel=0.05)
    # Halving an electrode's size doubles its spreading resistance (m13) and raises thermal noise by sqrt(2).
    assert F.thermal_density(2e3) / F.thermal_density(1e3) == pytest.approx(np.sqrt(2))


def test_wct():
    """eq-m14-wct: the terminal is a weighted mean; equal impedances give the plain mean."""
    p = sp.symbols("p1:4")
    z = sp.symbols("z1:4", positive=True)
    Rw = sp.symbols("R_w", positive=True)
    w = [1 / (Rw + zi) for zi in z]
    expr = sum(wi * pi for wi, pi in zip(w, p)) / sum(w)
    assert sp.simplify(expr.subs({z[1]: z[0], z[2]: z[0]}) - sum(p) / 3) == 0
    pots = [1.0, 0.5, -1.0]
    assert F.wct(pots, [1e3] * 3, 1e4) == pytest.approx(np.mean(pots))
    off = F.wct(pots, [1e3, 20e3, 1e3], 1e4)
    assert abs(off - np.mean(pots)) > 0.05
    assert abs(F.wct(pots, [1e3, 20e3, 1e3], 1e7) - np.mean(pots)) < 1e-3       # large Wilson resistors fix it


def test_oversampling():
    """eq-m14-oversampling: averaging m white-noise samples gains 10 log10 m dB."""
    assert F.input_lsb(2.0, 16, 100.0) == pytest.approx(2.0 / (100 * 65536))
    assert F.bits_needed(0.2, 1e-6) == 18
    rng = np.random.default_rng(7)
    x = rng.standard_normal(2 ** 20)
    for m in (4, 16, 64):
        gain = 20 * np.log10(np.std(x) / np.std(F.average_blocks(x, m)))
        assert gain == pytest.approx(F.oversampling_gain_db(m), abs=0.15)
