"""m54 · Nuclear imaging in EP: equation tests (numeric, and symbolic with SymPy where feasible)."""

import numpy as np
import pytest
import sympy as sp

from epml import nuclear as N


def test_decay():
    """eq-m54-decay: A0 e^(-lambda t) with lambda = ln2/T halves every half-life; a 10-min clock error with F-18
    biases the decay correction by 2^(10/109.73) - 1, about 6.5% (Kinahan and Fletcher: ~6%)."""
    t, T = sp.symbols("t T", positive=True)
    A = sp.exp(-sp.log(2) / T * t)
    assert sp.simplify(A.subs(t, T) - sp.Rational(1, 2)) == 0
    assert sp.simplify(A.subs(t, 2 * T) - sp.Rational(1, 4)) == 0
    assert N.activity(100.0, N.F18_HALF_LIFE_MIN) == pytest.approx(50.0)
    assert N.clock_error_bias(10.0) == pytest.approx(0.0652, abs=1e-4)
    assert N.F18_HALF_LIFE_MIN == pytest.approx(109.73)


def test_suv():
    """eq-m54-suv: a tracer spread uniformly through the body gives SUV 1 whatever the dose and weight; decay
    correction and residual syringe activity enter through the net injected activity."""
    for dose, w in ((370.0, 70.0), (200.0, 95.0)):
        uniform = dose / w          # kBq per g, equal to kBq/mL at 1 g/mL
        assert N.suv(uniform, dose, w) == pytest.approx(1.0)
        later = N.activity(dose, 60.0) / w
        assert N.suv(later, dose, w, 60.0) == pytest.approx(1.0)
    assert N.suv(5.0, 370.0, 70.0, 60.0, residual_mbq=7.4) / N.suv(5.0, 370.0, 70.0, 60.0) == pytest.approx(370 / 362.6)


def test_recovery_coefficients():
    """eq-m54-recovery: for a blurred slab, the peak recovers erf(w/(2 sqrt2 sigma)) and the mean over the true slab
    erf(b) - (1 - e^(-b^2))/(b sqrt pi), b = w/(sqrt2 sigma); both checked by integration (SymPy and numeric)."""
    x, w, s = sp.symbols("x w sigma", positive=True)
    g = sp.Rational(1, 2) * (sp.erf((x + w / 2) / (sp.sqrt(2) * s)) - sp.erf((x - w / 2) / (sp.sqrt(2) * s)))
    mean = sp.integrate(g, (x, -w / 2, w / 2)) / w
    b = w / (sp.sqrt(2) * s)
    target = sp.erf(b) - (1 - sp.exp(-b**2)) / (b * sp.sqrt(sp.pi))
    for wv, sv in ((10, 2.3), (5, 3.0), (20, 1.5)):
        assert float(mean.subs({w: wv, s: sv})) == pytest.approx(float(target.subs({w: wv, s: sv})), rel=1e-10)
    xs = np.linspace(-40, 40, 160001)
    for wv in (3.0, 10.0, 16.0):
        sg = N.fwhm_to_sigma(5.5)
        prof = N.slab_profile(xs, wv, sg)
        inside = np.abs(xs) <= wv / 2
        assert prof.max() == pytest.approx(N.rc_peak(wv, sg), abs=1e-6)
        assert prof[inside].mean() == pytest.approx(N.rc_mean(wv, sg), abs=2e-4)
    assert N.rc_mean(10.0, N.fwhm_to_sigma(4.0)) > N.rc_mean(10.0, N.fwhm_to_sigma(7.0))
    assert N.rc_mean(200.0, 1.0) == pytest.approx(1.0, abs=0.01)


def test_partial_volume_correction_on_a_phantom():
    """On the synthetic ventricle, blur lowers SUVmean in a lesion that spans the wall; dividing by the slab recovery
    coefficient brings it back within 10%, while SUVmax stays closer to the truth than SUVmean."""
    img, x, m = N.lv_phantom()
    true = N.lesion_stats(img, m["lesion"])["mean"]
    b = N.blur(img, x[1] - x[0], 5.5)
    st = N.lesion_stats(b, m["lesion"], N.rc_mean(10.0, N.fwhm_to_sigma(5.5)))
    assert st["mean"] < 0.85 * true
    assert abs(st["pvc_mean"] - true) < 0.1 * true
    assert st["max"] > st["mean"]


def test_response_misclassification():
    """eq-m54-change: with 10% test-retest noise per scan, an unchanged lesion is called a response (a drop of at
    least 25%) about 2% of the time; the closed form matches simulation."""
    p0 = float(N.p_called_responder(1.0))
    assert p0 == pytest.approx(0.0207, abs=0.002)
    rng = np.random.default_rng(54)
    for r in (1.0, 0.8, 0.7, 0.5):
        assert N.simulate_called_responder(r, 0.10, rng) == pytest.approx(float(N.p_called_responder(r)), abs=0.005)
    assert float(N.p_called_responder(0.75)) == pytest.approx(0.5, abs=0.01)
