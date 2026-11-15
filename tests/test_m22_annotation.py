"""m22 equation tests: reference, annotation rules, onset bias, noise jitter, window of interest, far field."""

import numpy as np
import pytest
import sympy as sp
from scipy import ndimage

from epml import annotation as AN


def test_lat_reference():
    """eq-m22-lat: the reference error cancels within a beat and adds across beats."""
    rng = np.random.default_rng(1)
    n = 200_000
    sa, sr = 1.0, 2.0
    true_i, true_j = 10.0, 25.0
    ref = rng.normal(0, sr, (n, 2))                      # reference error on two different beats
    ti = true_i + rng.normal(0, sa, n)
    tj = true_j + rng.normal(0, sa, n)
    same = AN.lat(ti, ref[:, 0]) - AN.lat(tj, ref[:, 0])
    diff = AN.lat(ti, ref[:, 0]) - AN.lat(tj, ref[:, 1])
    assert np.std(same) == pytest.approx(AN.lat_difference_sd(sa, sr, True), rel=0.01)
    assert np.std(diff) == pytest.approx(AN.lat_difference_sd(sa, sr, False), rel=0.01)
    assert np.mean(same) == pytest.approx(true_i - true_j, abs=0.02)
    # Symbolic: variances of (ti - r1) - (tj - r1) and (ti - r1) - (tj - r2) with independent errors
    from sympy.stats import Normal, variance
    s_a, s_r = sp.symbols("sigma_a sigma_r", positive=True)
    ei, ej = Normal("e_i", 0, s_a), Normal("e_j", 0, s_a)
    r1, r2 = Normal("r_1", 0, s_r), Normal("r_2", 0, s_r)
    assert sp.simplify(variance((ei - r1) - (ej - r1)) - 2 * s_a**2) == 0
    assert sp.simplify(variance((ei - r1) - (ej - r2)) - (2 * s_a**2 + 2 * s_r**2)) == 0


def test_intrinsic_deflection_and_bipolar_peak():
    """eq-m22-intrinsic: steepest downstroke at the electrode's activation; bipolar peak at the midpoint
    when d cos(theta) < 2 sqrt(3) a."""
    s, a, A, dl = sp.symbols("s a A delta", positive=True)
    U = A * s / (s**2 + a**2)
    dU = sp.diff(U, s)
    assert sp.simplify(dU - A * (a**2 - s**2) / (s**2 + a**2) ** 2) == 0
    assert sp.diff(dU, s).subs(s, 0) == 0 and sp.simplify(sp.diff(dU, s, 2).subs(s, 0)) == -6 * A / a**4
    # The bipolar B(s) = U(s + delta) - U(s - delta) has B''(0) = 2 U''(delta) < 0 iff delta < sqrt(3) a
    U2 = sp.diff(U, s, 2)
    assert sp.simplify(U2 - 2 * A * s * (s**2 - 3 * a**2) / (s**2 + a**2) ** 3) == 0
    t = np.arange(-30, 30, 0.005)
    c = 1.0
    for h in (0.5, 1.0, 3.0):
        aa = 0.3 + h
        assert AN.steepest_downstroke(t, AN.unipolar_trace(t, c, aa, t0=2.0)) == pytest.approx(2.0, abs=1e-3)
        assert AN.peak_time(t, AN.bipolar_trace(t, c, aa, 2.0, t0=-1.5)) == pytest.approx(-1.5, abs=1e-3)
    # Beyond the limit the bipolar peak splits away from the midpoint
    aa = 0.5
    d = 2.2 * 2 * np.sqrt(3) * aa
    assert abs(AN.peak_time(t, AN.bipolar_trace(t, c, aa, d))) > 0.5 * (0.5 * d / c) - 1e-9


def test_onset_bias():
    """eq-m22-onset: the onset annotation leads the midpoint activation by (a/c) sqrt(x_f)."""
    x, f = sp.symbols("x f", positive=True)
    root = (-(2 * f + 1) + sp.sqrt(8 * f + 1)) / (2 * f)
    assert sp.simplify(((1 - x) / (1 + x) ** 2 - f).subs(x, root)) == 0
    t = np.arange(-30, 30, 0.002)
    for h in (0.5, 1.0, 3.0):
        aa = 0.3 + h
        for frac in (0.1, 0.25):
            on = AN.onset_time(t, AN.bipolar_trace(t, 1.0, aa, 0.02), frac)
            assert -on == pytest.approx(AN.onset_lead(aa, 1.0, frac), rel=2e-3)
    # Finite spacing leads further; the lead grows with electrode height
    leads = [-AN.onset_time(t, AN.bipolar_trace(t, 1.0, 0.3 + h, 2.0), 0.1) for h in (0.5, 1.0, 3.0)]
    assert leads[0] < leads[1] < leads[2]
    assert leads[1] > AN.onset_lead(1.3, 1.0, 0.1)


def test_jitter():
    """eq-m22-jitter: a threshold crossing moves by noise / slope."""
    rng = np.random.default_rng(2)
    dt, slope, sn = 0.1, 0.5, 0.05
    t = np.arange(-20, 20, dt)
    times = []
    for _ in range(3000):
        n = ndimage.gaussian_filter1d(rng.normal(0, 1, t.size), 20)   # smooth noise (2 ms correlation)
        n *= sn / n.std()
        times.append(AN.threshold_crossing(t, slope * t + n, 0.0))
    assert np.std(times) == pytest.approx(AN.crossing_jitter(sn, slope), rel=0.08)


def test_window_of_interest():
    """eq-m22-woi: times are wrapped by whole cycles into the window; a reentry shows a jump of one cycle."""
    T, L = 250.0, 100.0
    p = np.linspace(0, L, 1001)[:-1]
    t_true = AN.ring_activation(p, L, T, t_start=-120.0)
    w = AN.window_lat(t_true, -150.0, T, T)
    assert np.all(np.isfinite(w)) and np.all((w >= -150) & (w < 100))
    r = np.mod(w - t_true, T)
    assert np.allclose(np.minimum(r, T - r), 0, atol=1e-9)
    jumps = np.diff(w)
    assert np.sum(np.abs(jumps) > T / 2) == 1 and np.min(jumps) == pytest.approx(-T + T / 1000, abs=1e-6)
    # Moving the window start moves the line of block-like discontinuity, not the local differences
    w2 = AN.window_lat(t_true, -100.0, T, T)
    k1, k2 = np.argmin(jumps), np.argmin(np.diff(w2))
    assert k1 != k2
    # A window shorter than the cycle leaves part of the circuit unannotated
    w3 = AN.window_lat(t_true, -150.0, 0.8 * T, T)
    assert np.mean(np.isnan(w3)) == pytest.approx(0.2, abs=0.002)


def test_far_field():
    """eq-m22-farfield: sharpness c/a; least-squares template gain and its bias from overlap."""
    s, a, A, c = sp.symbols("s a A c", positive=True)
    U = A * s / (s**2 + a**2)
    slope0 = sp.diff(U, s).subs(s, 0) * c
    pp = 2 * U.subs(s, a)
    assert sp.simplify(slope0 / pp - c / a) == 0
    t = np.arange(-100, 100, 0.01)
    for aa in (1.3, 5.0, 20.0):
        assert AN.sharpness(t, AN.unipolar_trace(t, 1.0, aa)) == pytest.approx(AN.sharpness_model(aa, 1.0), rel=2e-3)
    far = AN.gaussian_wave(t, 40.0, 10.0)
    assert far.max() - far.min() == pytest.approx(1.0, rel=1e-6)
    local_apart = AN.unipolar_trace(t, 1.0, 1.3, t0=-30.0, amplitude=0.5)
    local_over = AN.unipolar_trace(t, 1.0, 1.3, t0=40.0, amplitude=0.5)
    g = 3.0
    for local in (local_apart, local_over):
        x = local + g * far
        gh = AN.template_gain(x, far)
        assert gh == pytest.approx(g + np.dot(local, far) / np.dot(far, far), rel=1e-9)
    assert abs(AN.template_gain(local_apart + g * far, far) - g) < 0.01 * g
    assert abs(AN.template_gain(local_over + g * far, far) - g) > 10 * abs(AN.template_gain(local_apart + g * far, far) - g)
    res, _ = AN.remove_far_field(local_apart + g * far, far)
    assert AN.steepest_downstroke(t, res) == pytest.approx(-30.0, abs=0.02)
    assert AN.blanked(np.array([40.0, -30.0]), 40.0, 30.0, 60.0).tolist() == [True, False]
