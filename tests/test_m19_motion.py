"""m19 equation tests: breathing model, gating, reference subtraction, surrogate regression, drift, averaging."""

import numpy as np
import pytest
import sympy as sp

from epml import motion as MO


def test_breathing():
    """eq-m19-breathing: period T, exhale z0, inhale z0 - b; larger n spends more time near exhale."""
    T, b = 4.0, 12.0
    assert MO.breathing(0.0, T, b) == pytest.approx(-b)
    assert MO.breathing(T / 2, T, b) == pytest.approx(0.0)
    t = np.linspace(0, 3 * T, 7)
    assert MO.breathing(t + T, T, b) == pytest.approx(MO.breathing(t, T, b))
    near = [np.mean(MO.breathing(np.linspace(0, T, 10000), T, b, n) > -0.1 * b) for n in (1, 2, 3)]
    assert near[0] < near[1] < near[2]


def test_gating():
    """eq-m19-gating: duty cycle 1 - (2/pi) arccos((delta/b)^(1/(2n))); numeric sampling agrees."""
    u, d, b, n = sp.symbols("u delta b n", positive=True)
    # cos^(2n)(u) <= d/b  <=>  |cos u| <= (d/b)^(1/(2n)); on (0, pi) that is u in [acos(c), pi - acos(c)]
    c = (d / b) ** (1 / (2 * n))
    frac = (sp.pi - 2 * sp.acos(c)) / sp.pi
    assert sp.simplify(frac - (1 - 2 * sp.acos(c) / sp.pi)) == 0
    for n_, w in ((1, 1.0), (2, 2.0), (3, 0.5)):
        duty, rms = MO.gating_numeric(4.0, 12.0, w, n_)
        assert duty == pytest.approx(MO.gating_duty_cycle(w, 12.0, n_), abs=1e-4)
        assert rms <= w
    assert MO.gating_duty_cycle(12.0, 12.0) == pytest.approx(1.0)


def test_reference():
    """eq-m19-reference: var(x - r) = sx^2 + sr^2 - 2 rho sx sr; helps iff rho > sr / (2 sx)."""
    sx, sr, rho = sp.symbols("s_x s_r rho", positive=True)
    v = sx ** 2 + sr ** 2 - 2 * rho * sx * sr
    assert sp.solve(sp.Eq(v, sx ** 2), rho) == [sr / (2 * sx)]
    rng = np.random.default_rng(19)
    z1, z2 = rng.standard_normal((2, 200000))
    for r_ in (0.2, 0.7, 0.95):
        x = 3.0 * z1
        r = 2.0 * (r_ * z1 + np.sqrt(1 - r_ ** 2) * z2)
        assert np.std(x - r) == pytest.approx(MO.difference_sd(3.0, 2.0, r_), rel=0.01)
        assert (np.std(x - r) < np.std(x)) == MO.reference_helps(3.0, 2.0, r_)


def test_surrogate():
    """eq-m19-surrogate: the best linear correction leaves sd sqrt(1 - rho^2)."""
    k, sx, ss, rho = sp.symbols("k s_x s_s rho", real=True)
    var = sx ** 2 - 2 * k * rho * sx * ss + k ** 2 * ss ** 2
    kopt = sp.solve(sp.diff(var, k), k)[0]
    assert sp.simplify(var.subs(k, kopt) - sx ** 2 * (1 - rho ** 2)) == 0
    rng = np.random.default_rng(3)
    s = rng.standard_normal(100000) * 10
    x = 0.6 * s + rng.standard_normal(100000) * 3
    kk, cc = MO.fit_slope(s, x)
    assert kk == pytest.approx(0.6, abs=0.01)
    rho_ = np.corrcoef(s, x)[0, 1]
    assert np.std(x - (kk * s + cc)) == pytest.approx(MO.residual_sd(np.std(x), rho_), rel=1e-6)


def test_drift():
    """eq-m19-drift: least-squares slope and its standard error sigma / sqrt(sum (t - tbar)^2)."""
    t = np.arange(0, 120, 10.0)                    # minutes
    rng = np.random.default_rng(4)
    slopes = []
    for _ in range(4000):
        x = 0.02 * t + 0.8 * rng.standard_normal(t.size)
        slopes.append(MO.drift_fit(t, x)[0])
    assert np.mean(slopes) == pytest.approx(0.02, abs=5e-4)
    assert np.std(slopes) == pytest.approx(MO.drift_se(t, 0.8), rel=0.05)


def test_average():
    """eq-m19-average: a boxcar of width W has gain |sinc(f W)| and removes a period-W oscillation."""
    f, W = sp.symbols("f W", positive=True)
    t = sp.symbols("t", real=True)
    avg = sp.integrate(sp.cos(2 * sp.pi * f * t), (t, -W / 2, W / 2)) / W      # the sine part integrates to zero
    assert sp.simplify(avg - sp.sin(sp.pi * f * W) / (sp.pi * f * W)) == 0
    assert sp.integrate(sp.sin(2 * sp.pi * f * t), (t, -W / 2, W / 2)) == 0
    assert MO.moving_average_gain(0.25, 4.0) == pytest.approx(0.0, abs=1e-12)
    fs, T = 100.0, 4.0
    tt = np.arange(0, 40, 1 / fs)
    x = np.sin(2 * np.pi * tt / T)
    y = MO.moving_average(x, int(T * fs))
    assert np.max(np.abs(y[int(T * fs):])) < 1e-9
    g = MO.moving_average_gain(1 / T, 1.0)
    y1 = MO.moving_average(x, int(1.0 * fs))
    assert np.max(np.abs(y1[1000:])) == pytest.approx(g, rel=0.01)
