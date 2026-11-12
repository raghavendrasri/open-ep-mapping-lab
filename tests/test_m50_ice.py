"""Equation tests for m50 (intracardiac echocardiography: ultrasound essentials)."""
import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "labs" / "python"))
from epml import ice  # noqa: E402


def test_range_equation_and_speed_of_sound_error():
    """eq-m50-range: z = c t / 2; a scanner assuming c_a shows z c_a / c_t for a reflector at z."""
    c, t, ca, ct, z = sp.symbols("c t c_a c_t z", positive=True)
    t_echo = 2 * z / ct
    assert sp.simplify(ca * t_echo / 2 - z * ca / ct) == 0
    assert ice.depth_from_time(2 * 0.03 / 1540.0) == pytest.approx(0.03)
    # simulate: an echo from 35 mm in tissue at 1586 m/s, read by a scanner that assumes 1540 m/s
    d_axis, s = ice.a_line([35.0], [1.0], 7.5, 2, c=1586.0, max_depth_mm=45.0)
    t_peak = 2 * d_axis[np.argmax(ice.envelope(s))] * 1e-3 / 1586.0
    shown = ice.depth_from_time(t_peak) * 1e3
    assert shown == pytest.approx(ice.displayed_depth(35.0, 1586.0), abs=0.01)
    assert ice.displayed_depth(35.0, 1586.0) - 35.0 == pytest.approx(-1.015, abs=0.001)


def test_axial_resolution_is_half_the_pulse_length():
    """eq-m50-axial: lambda = c / f and echoes of an n-cycle burst stop overlapping at n lambda / 2."""
    assert ice.wavelength_mm(7.5) == pytest.approx(1540 / 7.5e6 * 1e3)
    for f, n in [(7.5, 2), (10.0, 3), (5.0, 1)]:
        r = ice.axial_resolution_mm(f, n)
        assert ice.echoes_overlap(20.0, 20.0 + 0.97 * r, f, n)
        assert not ice.echoes_overlap(20.0, 20.0 + 1.03 * r, f, n)
    assert ice.axial_resolution_mm(10.0, 2) == pytest.approx(ice.axial_resolution_mm(5.0, 1))


def test_round_trip_attenuation_and_depth_budget():
    """eq-m50-attenuation: loss = 2 alpha f z dB; the depth that uses a budget B is B / (2 alpha f)."""
    a, f, z, B = sp.symbols("alpha f z B", positive=True)
    zmax = sp.solve(sp.Eq(2 * a * f * z, B), z)[0]
    assert sp.simplify(zmax - B / (2 * a * f)) == 0
    alpha = ice.MYOCARDIUM_DB_PER_CM_MHZ["across fibers"]
    assert ice.round_trip_loss_db(alpha, 7.5, 4.0) == pytest.approx(2 * 0.52 * 7.5 * 4.0)
    zm = ice.max_depth_cm(60.0, alpha, 10.0)
    assert ice.round_trip_loss_db(alpha, 10.0, zm) == pytest.approx(60.0)
    assert ice.max_depth_cm(60.0, alpha, 7.5) > ice.max_depth_cm(60.0, alpha, 10.0)
    # amplitude after a round trip falls by 10^(-loss/20): halving the frequency doubles the depth for equal loss
    assert ice.max_depth_cm(60.0, alpha, 5.0) == pytest.approx(2 * ice.max_depth_cm(60.0, alpha, 10.0))


def test_phased_array_steering_grating_lobes_and_main_lobe():
    """eq-m50-steer: delays x_k sin(theta0) / c point the beam; grating lobes at sin(theta0) + m lambda / d;
    none for d <= lambda / 2; first null at lambda / (n d) from the main lobe."""
    psi, N = sp.symbols("psi N", positive=True)
    k = sp.symbols("k", integer=True, nonnegative=True)
    geometric = sp.summation(sp.exp(sp.I * k * psi), (k, 0, 7))
    numeric = abs(complex(geometric.subs(psi, 0.37)))
    assert numeric == pytest.approx(abs(np.sin(8 * 0.37 / 2) / np.sin(0.37 / 2)))
    theta = np.radians(np.linspace(-90, 90, 18001))
    for steer in (0.0, 20.0, 45.0):
        af = ice.array_factor(theta, 32, 0.5, np.radians(steer))
        assert np.degrees(theta[np.argmax(af)]) == pytest.approx(steer, abs=0.02)
        assert ice.grating_lobes_deg(0.5, np.radians(steer)) == []
    lobes = ice.grating_lobes_deg(1.0, np.radians(30.0))
    assert lobes == pytest.approx([-30.0])
    assert ice.array_factor(np.radians(np.array(lobes)), 32, 1.0, np.radians(30.0)) == pytest.approx([1.0])
    s_null = np.arcsin(np.sin(np.radians(20.0)) + ice.first_null_offset(32, 0.5))
    assert ice.array_factor(np.array([s_null]), 32, 0.5, np.radians(20.0))[0] < 1e-9
    # the delays line up a plane wave arriving from theta0 on every element
    lam = ice.wavelength_mm(7.5) * 1e-3
    tau = ice.steering_delays(16, lam / 2, np.radians(25.0))
    arrival = ice.element_positions(16, lam / 2) * np.sin(np.radians(25.0)) / ice.C_ASSUMED
    assert np.allclose(tau - arrival, (tau - arrival)[0])


def test_frame_rate():
    """eq-m50-frame-rate: c / (2 D N)."""
    c, D, Nl = sp.symbols("c D N", positive=True)
    assert sp.simplify(1 / (Nl * 2 * D / c) - c / (2 * D * Nl)) == 0
    assert ice.frame_rate(0.10, 90) == pytest.approx(1540 / (2 * 0.10 * 90))
    assert ice.frame_rate(0.05, 90) == pytest.approx(2 * ice.frame_rate(0.10, 90))


def test_delay_and_sum_finds_a_point_and_the_tent():
    lam = ice.wavelength_mm(7.5) * 1e-3
    ang = np.radians(np.linspace(-30, 30, 61))
    rad = np.linspace(0.015, 0.035, 401)
    t, ch = ice.simulate_channels([(0.0, 0.025)], [1.0], 32, lam / 2, 7.5, 2, max_depth_m=0.04)
    img = ice.das_sector(t, ch, 32, lam / 2, ang, rad)
    assert ice.peak_depth_on_axis(img, rad, ang) == pytest.approx(25.0, abs=0.1)
    pts, amp = ice.septum_scatterers(tent_mm=4.0)
    t, ch = ice.simulate_channels(pts, amp, 32, lam / 2, 7.5, 2, max_depth_m=0.04)
    img = ice.das_sector(t, ch, 32, lam / 2, ang, rad)
    assert ice.peak_depth_on_axis(img, rad, ang) - 25.0 == pytest.approx(4.0, abs=0.2)


def test_shell_from_tracked_planes():
    pts = ice.ellipsoid_contours(6)
    assert ice.distance_to_ellipsoid(pts).max() < 1e-9
    az = np.sort(np.mod(np.arctan2(pts[:, 1], pts[:, 0]), np.pi))
    gaps = np.diff(np.unique(np.round(az, 9)))
    assert gaps.max() == pytest.approx(np.pi / 6)
    assert ice.largest_gap_mm(6) == pytest.approx(np.pi * 25.0 / 6)
    noisy = ice.ellipsoid_contours(6, noise_mm=0.5, rng=np.random.default_rng(0))
    assert 0.2 < np.sqrt(np.mean(ice.distance_to_ellipsoid(noisy) ** 2)) < 0.6
