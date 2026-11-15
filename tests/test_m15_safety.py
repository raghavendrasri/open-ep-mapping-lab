"""m15 equation tests: leakage, current density, defibrillation protection, RF filtering and demodulation."""

import numpy as np
import pytest
import sympy as sp

from epml import safety as S
from epml import recording as REC


def test_leakage():
    """eq-m15-leakage: I = 2 pi f C V; in-phase leakages add; C_max = I_lim / (2 pi f V)."""
    t, f, C, V = sp.symbols("t f C V", positive=True)
    v = sp.sqrt(2) * V * sp.sin(2 * sp.pi * f * t)
    i = C * sp.diff(v, t)
    i_rms = sp.sqrt(f * sp.integrate(i ** 2, (t, 0, 1 / f)))
    assert sp.simplify(i_rms - 2 * sp.pi * f * C * V) == 0
    assert S.capacitive_current(230.0, 50.0, S.max_capacitance(50e-6, 230.0, 50.0)) == pytest.approx(50e-6)
    assert S.max_capacitance(50e-6, 230.0, 50.0) == pytest.approx(692e-12, rel=1e-3)
    assert S.total_leakage([10e-6, 10e-6, 10e-6]) == pytest.approx(30e-6)
    assert S.total_leakage([10e-6, 10e-6], [0, 180]) == pytest.approx(0.0, abs=1e-18)


def test_density():
    """eq-m15-density: current through a hemisphere of radius r; concentration ratio A / (2 pi a^2)."""
    I, r, sig = sp.symbols("I r sigma", positive=True)
    J = I / (2 * sp.pi * r ** 2)
    assert sp.simplify(J * 2 * sp.pi * r ** 2 - I) == 0                 # the same current crosses every hemisphere
    assert S.hemisphere_density(1e-3, 1e-3) == pytest.approx(1e-3 / (2 * np.pi * 1e-6))
    assert S.density_ratio(1e-3, 0.05) == pytest.approx(0.05 / (2 * np.pi * 1e-6))
    assert S.density_at(1.0, 2.0) == pytest.approx(S.density_at(1.0, 1.0) / 4)


def test_defib():
    """eq-m15-defib: clamp current (V - Vc)/R and resistor energy (V - Vc)^2 T / R."""
    v, vc, R, T = sp.symbols("v v_c R T", positive=True)
    i = (v - vc) / R
    assert sp.simplify(i ** 2 * R * T - (v - vc) ** 2 * T / R) == 0
    assert S.clamp_current(5.0, 10.0, 1e3) == 0.0                        # below the clamp nothing flows
    assert S.clamp_current(510.0, 10.0, 1e3) == pytest.approx(0.5)
    assert S.resistor_energy(510.0, 10.0, 1e3, 10e-3) == pytest.approx(0.5 ** 2 * 1e3 * 10e-3)
    assert S.diverted_fraction(510.0, 10.0, 1e3, 2000.0, 75.0) == pytest.approx(510 * 0.5 / (2000 ** 2 / 75))


def test_rf_filter():
    """eq-m15-rf-filter: Butterworth roll-off (fc/f)^n far above the corner; the m04 design agrees."""
    f, fc = 500e3, 500.0
    for n in (1, 2, 3, 4):
        assert S.lowpass_attenuation(f, fc, n) == pytest.approx((fc / f) ** n, rel=1e-6)
        assert S.lowpass_attenuation(f, fc, n) == pytest.approx(REC.butter_magnitude(np.array([f]), fc, n)[0], rel=1e-9)
    n = S.order_needed(10.0, 1e-6, 500e3, 500.0)
    assert n == 3
    assert 10.0 * S.lowpass_attenuation(500e3, 500.0, n - 1) > 1e-6


def test_demod():
    """eq-m15-demod: the time average of A cos + beta (A cos)^2 is beta A^2 / 2."""
    t, w, A, b = sp.symbols("t omega A beta", positive=True)
    y = A * sp.cos(w * t) + b * (A * sp.cos(w * t)) ** 2
    mean = sp.integrate(y, (t, 0, 2 * sp.pi / w)) * w / (2 * sp.pi)
    assert sp.simplify(mean - b * A ** 2 / 2) == 0
    tt = np.arange(0, 1e-3, 1e-8)
    x = 2.0 * np.cos(2 * np.pi * 500e3 * tt)
    assert np.mean(S.square_law(x, 0.01)) == pytest.approx(S.demodulated_offset(2.0, 0.01), rel=1e-3)


def test_swerdlow_values():
    """The cited thresholds are ordered as reported."""
    s = S.SWERDLOW_1999_UA
    assert s["intermittent_capture"] < s["continuous_capture"] < s["ventricular_fibrillation"] < s["us_standard_single_fault"]
