"""m10 · Arrhythmia mechanisms: equation tests."""

import numpy as np
import pytest
import sympy as sp

from epml import arrhythmia as A
from epml.membrane import MS_PARAMS as P


def test_wavelength_and_circuit():
    """eq-m10-wavelength and eq-m10-circuit: lambda = CV x ERP; CL = L / CV; the gap is L - lambda in space and
    CL - ERP in time, and the two agree (gap_mm = CV gap_ms)."""
    assert A.wavelength(1.0, 150.0) == pytest.approx(150.0)
    c = A.circuit(200.0, 0.8, 150.0)
    assert c["cycle_length"] == pytest.approx(250.0) and c["gap_mm"] == pytest.approx(80.0)
    assert c["gap_mm"] == pytest.approx(0.8 * c["gap_ms"]) and c["sustained"]
    assert not A.circuit(100.0, 0.8, 150.0)["sustained"]


def test_ring_reentry():
    """eq-m10-circuit in a Mitchell-Schaeffer ring: a pulse whose tail (v above v_gate) is about 75 mm long sustains
    reentry on rings of 90 mm and more and fails on 80 mm; on shorter rings the wave is slower (it travels into less
    recovered tissue), so CL > L / CV_long."""
    pulse = A.traveling_pulse()
    v, h, f = pulse
    tail = (f - np.max(np.where(v[:f] < P["v_gate"])[0])) * 0.5
    assert 70 < tail < 80
    long_ring = A.ring_reentry(200.0, t_end=2000.0, pulse=pulse)
    short_ring = A.ring_reentry(90.0, t_end=1500.0, pulse=pulse)
    failed = A.ring_reentry(80.0, t_end=1500.0, pulse=pulse)
    assert len(long_ring) >= 3 and len(short_ring) >= 3 and len(failed) < 2
    cv_long = 200.0 / np.diff(long_ring)[-1]
    cv_short = 90.0 / np.diff(short_ring)[-1]
    assert cv_short < cv_long


def test_restitution_map():
    """eq-m10-restitution: perturbations of the fixed point APD* = f(CL - APD*) evolve as delta_{n+1} = -f'(DI*)
    delta_n, so they decay when the slope is below 1 and alternate with growing amplitude above it."""
    d, s = sp.symbols("delta s")
    f = sp.Function("f")
    a, cl = sp.symbols("a CL")
    lin = sp.series(f(cl - (a + d)), d, 0, 2).removeO()
    assert sp.simplify(sp.diff(lin, d) - sp.diff(f(cl - a), a)) == 0   # slope -f'(DI*)
    for cl_, grows in ((200.0, False), (148.0, True)):
        apd, di = A.fixed_point(cl_)
        assert apd == pytest.approx(A.restitution(di), abs=1e-6)
        seq = A.iterate_map(cl_, apd + 2.0, 6)
        dev = np.abs(seq - apd)
        assert (dev[-1] > dev[0]) == grows
        assert (A.restitution_slope(di) > 1) == grows
        signs = np.sign(seq[:5] - apd)
        assert np.all(signs[1:] == -signs[:-1])            # deviations alternate in sign


def test_alternans_onset():
    """eq-m10-alternans: for the closed-form restitution the slope reaches 1 at
    DI_c = tau_open ln((1 - h_min)(1 + tau_close / tau_open)) = 54.7 ms, CL_c = 150.5 ms with the m08 parameters;
    a paced cell (whose APDs are longer than the closed form, m08) alternates at a longer cycle length."""
    di, apd, cl = A.alternans_onset()
    assert A.restitution_slope(di) == pytest.approx(1.0, abs=1e-12)
    assert di == pytest.approx(150 * np.log(1.44)) and cl == pytest.approx(150.52, abs=0.01)
    steady = A.paced_apds(300.0, 30)
    alt = A.paced_apds(210.0, 40)
    assert np.ptp(steady[-6:]) < 0.5
    assert abs(alt[-1] - alt[-2]) > 5 and abs(alt[-1] - alt[-3]) < 3


def test_spiral_charge():
    """Phase singularities (eq-m29-charge) of a Barkley spiral: exactly one, with charge +-1; the mirror-image start
    gives the opposite charge."""
    u, v = A.barkley_spiral(n=120, t_end=60.0)
    ps = A.singularities(A.phase_field(u, v))
    assert len(ps) == 1 and abs(ps[0, 2]) == 1
    um, vm = A.barkley_spiral(n=120, t_end=0.0)
    u2, v2 = A.barkley_spiral(n=120, t_end=60.0)
    ps_m = A.singularities(A.phase_field(u2[:, ::-1], v2[:, ::-1]))
    assert len(ps_m) == 1 and ps_m[0, 2] == -ps[0, 2]


def test_focal():
    """eq-m10-focal: centrifugal activation from a focus spans only the time to reach the farthest point; a circuit
    spans the whole cycle."""
    y, x = np.mgrid[-20:21, -20:21].astype(float)
    t = A.focal_activation(x, y, 0.0, 0.0, 1.0)
    assert A.activation_span(t, 300.0) == pytest.approx(np.hypot(20, 20) / 300.0)
    theta = np.linspace(0, 2 * np.pi, 361)[:-1]
    t_ring = theta * 30.0 / 0.5                              # radius 30 mm, 0.5 m/s: CL = 2 pi 30 / 0.5
    assert A.activation_span(t_ring, 2 * np.pi * 30 / 0.5) == pytest.approx(1.0, abs=0.01)
