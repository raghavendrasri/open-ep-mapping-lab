"""m03 equation checks: the unipolar electrogram.

Each test checks one equation in modules/m03-electrograms.qmd by a route that does not use
the closed-form result it is checking (symbolic algebra, direct quadrature or FFTs).
"""

import numpy as np
import pytest
import sympy as sp

from epml.electrograms import unipolar

# Model parameters used only as test inputs (not physiological claims).
BETA, DELTA_V, SIGMA = 1.0, 1.0, 1.0
W, H = 1.5, 1.0  # front width and electrode height, mm
A = BETA * DELTA_V / (2 * np.pi * SIGMA)
a = W + H


def membrane_current(x, w=W):
    """i_m = beta * d2Vm/dx2 for the arctangent front Vm = dV (1/2 - atan(x/w)/pi), front at x = 0."""
    return BETA * DELTA_V * 2 * w * x / (np.pi * (x**2 + w**2) ** 2)


def potential_by_quadrature(x_e, h=H, half_width_y=1e5, half_width_x=2000.0, n=400_001):
    """Volume-conductor integral over a finite sheet (|y| < Y), with the y-integral done exactly.

    phi(x_e) = 1/(4 pi sigma) * integral of i_m(x') * 2 asinh(Y / r) dx',  r^2 = (x_e - x')^2 + h^2.
    """
    x = np.linspace(-half_width_x, half_width_x, n)
    dx = x[1] - x[0]
    i_m = membrane_current(x)
    r = np.sqrt((x_e - x) ** 2 + h**2)
    return float(np.sum(i_m * 2 * np.arcsinh(half_width_y / r)) * dx / (4 * np.pi * SIGMA))


def potential_by_fft(h=H, w=W, length=4096.0, n=2**18):
    """phi(x) from the height filter: phi_hat = exp(-|k| h) / (2 sigma |k|) * i_m_hat. Returns x, phi."""
    x = (np.arange(n) - n // 2) * (length / n)
    i_m = membrane_current(x, w)
    k = 2 * np.pi * np.fft.fftfreq(n, d=length / n)
    i_hat = np.fft.fft(np.fft.ifftshift(i_m))
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.where(k == 0, 0.0, np.exp(-np.abs(k) * h) / (2 * SIGMA * np.abs(k)))
    phi = np.fft.fftshift(np.real(np.fft.ifft(i_hat * g)))
    return x, phi


# ------------------------------------------------------------------ symbolic checks

def test_height_filter_hankel_transform():
    """eq-m03-height-filter: the 2D Fourier transform of 1/sqrt(rho^2 + h^2) is 2 pi exp(-k h) / k."""
    k, h, rho = sp.symbols("k h rho", positive=True)
    hankel = sp.hankel_transform(1 / sp.sqrt(rho**2 + h**2), rho, k, 0)
    assert sp.simplify(2 * sp.pi * hankel - 2 * sp.pi * sp.exp(-k * h) / k) == 0


def test_cable_membrane_current():
    """eq-m03-cable: with I_i = -beta dVm/dx, conservation i_m = -dI_i/dx gives i_m = beta d2Vm/dx2."""
    x = sp.symbols("x", real=True)
    beta = sp.symbols("beta", positive=True)
    vm = sp.Function("V_m")(x)
    intracellular = -beta * sp.diff(vm, x)
    assert sp.simplify(-sp.diff(intracellular, x) - beta * sp.diff(vm, x, 2)) == 0


def test_front_profile_derivatives():
    """eq-m03-front: dVm/ds is a Lorentzian of width w; d2Vm/ds2 is odd (source ahead, sink behind)."""
    s = sp.symbols("s", real=True)
    w, dv = sp.symbols("w DeltaV", positive=True)
    vm = dv * (sp.Rational(1, 2) - sp.atan(s / w) / sp.pi)
    assert sp.simplify(sp.diff(vm, s) + dv * w / (sp.pi * (s**2 + w**2))) == 0
    assert sp.simplify(sp.diff(vm, s, 2) - 2 * dv * w * s / (sp.pi * (s**2 + w**2) ** 2)) == 0


def test_inverse_fourier_of_signed_exponential():
    """eq-m03-unipolar-closed: (1/2pi) * integral of i sgn(k) e^{-a|k|} e^{ikx} dk = -x / (pi (x^2 + a^2)).

    The integral reduces to -(1/pi) * integral_0^inf e^{-ak} sin(kx) dk. Checked for x > 0;
    both sides are odd in x, so x < 0 follows.
    """
    k, a_, x = sp.symbols("k a x", positive=True)
    lhs = -sp.integrate(sp.exp(-a_ * k) * sp.sin(k * x), (k, 0, sp.oo)) / sp.pi
    assert sp.simplify(lhs + x / (sp.pi * (x**2 + a_**2))) == 0


def test_unipolar_peaks_and_peak_to_peak():
    """eq-m03-unipolar-closed: peaks at s = +/- a, peak-to-peak A / a, steepest slope A / a^2 at s = 0."""
    s = sp.symbols("s", real=True)
    amp, a_ = sp.symbols("A a", positive=True)
    u = amp * s / (s**2 + a_**2)
    assert set(sp.solve(sp.diff(u, s), s)) == {-a_, a_}
    assert sp.simplify(u.subs(s, a_) - u.subs(s, -a_) - amp / a_) == 0
    assert sp.simplify(sp.diff(u, s).subs(s, 0) - amp / a_**2) == 0


# ------------------------------------------------------------------ numeric checks

@pytest.mark.parametrize("x_e", [-5.0, -2.5, -1.0, 0.0, 1.0, 2.5, 5.0])
def test_closed_form_matches_volume_conductor_quadrature(x_e):
    """eq-m03-volume-conductor + eq-m03-unipolar-closed: direct quadrature equals A s / (s^2 + a^2)."""
    expected = float(unipolar(x_e, a, A))
    assert potential_by_quadrature(x_e) == pytest.approx(expected, abs=1e-5 * A / a)


def test_closed_form_matches_fft_route():
    """eq-m03-height-filter: the FFT route gives the same potential profile."""
    x, phi = potential_by_fft()
    window = np.abs(x) < 20
    assert np.max(np.abs(phi[window] - unipolar(x[window], a, A))) < 1e-4 * A / a


def test_positive_ahead_negative_behind():
    """The electrode sees positive potential before the front arrives (s > 0) and negative after."""
    assert potential_by_quadrature(2.0) > 0 > potential_by_quadrature(-2.0)


def test_amplitude_falls_with_height_and_front_width():
    """eq-m03-unipolar-closed: peak-to-peak = A / (w + h), checked by the FFT route."""
    for w, h in [(1.0, 0.5), (1.5, 1.0), (2.0, 3.0)]:
        _, phi = potential_by_fft(h=h, w=w)
        assert phi.max() - phi.min() == pytest.approx(A / (w + h), rel=1e-3)


@pytest.mark.parametrize("c", [0.5, 1.0])
def test_intrinsic_deflection_marks_activation(c):
    """eq-m03-intrinsic-deflection: the steepest negative slope of U(t) falls at the activation time.

    The electrode sits at x = 0; the front passes it at t = 0. U(t) comes from the FFT route.
    """
    x, phi = potential_by_fft()
    t = np.linspace(-20, 20, 40_001)
    u_t = np.interp(-c * t, x, phi)  # s = x_e - c t with x_e = 0
    du_dt = np.gradient(u_t, t)
    # Resolution is set by the FFT grid spacing (in time: dx / c), not by the time step.
    resolution = max(2 * (t[1] - t[0]), 1.5 * (x[1] - x[0]) / c)
    assert abs(t[np.argmin(du_dt)]) < resolution


def test_unipolar_slope_scales_with_velocity():
    """eq-m03-unipolar-slope: dU/dt = -c dU/ds, so the steepest slope doubles when c doubles."""
    x, phi = potential_by_fft()
    t = np.linspace(-20, 20, 40_001)
    slopes = []
    for c in (0.5, 1.0):
        u_t = np.interp(-c * t, x, phi)
        slopes.append(-np.min(np.gradient(u_t, t)))
    assert slopes[1] / slopes[0] == pytest.approx(2.0, rel=1e-3)
    assert slopes[1] == pytest.approx(1.0 * A / a**2, rel=1e-3)
