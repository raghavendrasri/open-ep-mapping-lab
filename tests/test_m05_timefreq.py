"""m05 · Time-frequency tools: equation tests (numeric, and symbolic with SymPy where feasible)."""

import numpy as np
import pytest
import sympy as sp

from epml import timefreq as F


def test_resolution():
    """eq-m05-resolution: the DFT of N samples at f_s has bins f_s / N = 1 / T apart; two tones 1 Hz apart are
    resolved by a 1-s record but not by a 0.5-s one, however much the record is zero-padded."""
    assert F.resolution(200.0, 400) == pytest.approx(0.5)
    for T, ok in ((0.5, False), (1.0, True), (2.0, True)):
        t, x = F.two_tone(200.0, T, 6.0, 7.0)
        f, P = F.periodogram(x, 200.0, "boxcar", nfft=64 * len(x))
        assert F.resolved(f, P, 6.0, 7.0) == ok


def test_leakage_windows():
    """eq-m05-leakage: a rectangular window's highest sidelobe is about -13.3 dB with its first null 1 bin out; a Hann
    window's is about -31.5 dB with its first null 2 bins out. SymPy: the Hann window's transform has zeros at 2, 3, ...
    bins."""
    rect, rect_null = F.window_sidelobe_db("boxcar")
    hann, hann_null = F.window_sidelobe_db("hann")
    assert rect == pytest.approx(-13.26, abs=0.05) and rect_null == pytest.approx(1.0, abs=0.02)
    assert hann == pytest.approx(-31.47, abs=0.05) and hann_null == pytest.approx(2.0, abs=0.02)
    k, N = sp.symbols("k N", positive=True, integer=True)
    n = sp.symbols("n", integer=True)
    # DTFT of the periodic Hann window at bin offset m: W(m) = 1/2 D(m) - 1/4 D(m-1) - 1/4 D(m+1), with D the
    # rectangular-window Dirichlet kernel, which vanishes at nonzero integers.
    D = lambda m: sp.Integer(1) if m == 0 else sp.Integer(0)
    W = lambda m: sp.Rational(1, 2) * D(m) - sp.Rational(1, 4) * D(m - 1) - sp.Rational(1, 4) * D(m + 1)
    assert W(0) == sp.Rational(1, 2) and W(1) == -sp.Rational(1, 4) and all(W(m) == 0 for m in range(2, 6))


def test_periodogram_variance():
    """eq-m05-welch: the periodogram of white noise has a standard deviation equal to its mean at every bin, however
    long the record; averaging K independent segments divides it by sqrt(K)."""
    cv1 = F.periodogram_cv(segments=1, trials=200)
    assert cv1 == pytest.approx(1.0, abs=0.03)
    for K in (4, 8):
        assert F.periodogram_cv(segments=K, trials=200) == pytest.approx(1 / np.sqrt(K), rel=0.05)
    assert F.periodogram_cv(T=32.0, segments=1, trials=50) == pytest.approx(1.0, abs=0.04)


def test_pulse_train():
    """eq-m05-pulse-train: a train of identical pulses every T0 has spectral lines at k / T0 weighted by the pulse
    spectrum |P(k / T0)|. A zero-mean biphasic pulse has P(0) = 0 and |P| peaks at 1 / (2 pi w), so the raw spectrum
    peaks at a harmonic near there; after band-pass, rectification and low-pass it peaks at 1 / T0."""
    f, w = sp.symbols("f w", positive=True)
    t = sp.symbols("t", real=True)
    p = -t / w * sp.exp(-t ** 2 / (2 * w ** 2))
    P = sp.integrate(p * sp.exp(-2 * sp.pi * sp.I * f * t), (t, -sp.oo, sp.oo))
    mag = sp.simplify(sp.Abs(P))
    assert sp.simplify(mag / (f * sp.exp(-2 * sp.pi ** 2 * f ** 2 * w ** 2)) - 2 * sp.pi ** sp.Rational(3, 2) * sp.sqrt(2) * w ** 2) == 0
    fpk = sp.solve(sp.diff(f * sp.exp(-2 * sp.pi ** 2 * f ** 2 * w ** 2), f), f)
    assert sp.simplify(fpk[0] - 1 / (2 * sp.pi * w)) == 0
    fs, cycle, width = 1000.0, 0.18, 0.004
    tt, x, times = F.pulse_train(fs, 8.0, cycle, width)
    raw = F.peak_frequency(x, fs, 2.0, 400.0)
    k = round(raw * cycle)
    assert k > 3 and abs(raw - k / cycle) < 0.2                       # a harmonic, not the fundamental
    assert abs(raw - 1 / (2 * np.pi * width)) < 1 / cycle
    assert F.peak_frequency(F.rectify_lowpass(x, fs), fs, 3.0, 15.0) == pytest.approx(1 / cycle, abs=0.1)


def test_analytic_signal():
    """eq-m05-analytic: H[cos] = sin, so cos(w t) has analytic signal exp(j w t) and one phase turn per period; for an
    amplitude-modulated carrier whose envelope is slower than the carrier, |z| recovers the envelope. A train with two
    deflections per activation gives two phase turns per activation."""
    w, t, tau = sp.symbols("omega t tau", positive=True)
    # principal-value Hilbert transform of cos(w t) via its known Fourier multiplier -j sgn(f): check on z
    z = sp.cos(w * t) + sp.I * sp.sin(w * t)
    assert sp.simplify(z - sp.exp(sp.I * w * t)) == 0
    fs = 1000.0
    tt = np.arange(0, 4, 1 / fs)
    x = np.cos(2 * np.pi * 5 * tt)
    assert F.phase_cycles(x) == pytest.approx(20.0, abs=0.02)
    z = F.analytic(x)
    assert np.allclose(z.imag[200:-200], np.sin(2 * np.pi * 5 * tt)[200:-200], atol=1e-6)
    env = 1 + 0.5 * np.cos(2 * np.pi * 0.5 * tt)
    am = env * np.cos(2 * np.pi * 20 * tt)
    assert np.max(np.abs(np.abs(F.analytic(am)) - env)[200:-200]) < 1e-3
    fi = F.instantaneous_frequency(F.analytic(am), fs)
    assert np.median(fi[200:-200]) == pytest.approx(20.0, abs=0.01)
    width = 0.004
    g = lambda u: np.exp(-0.5 * (u / width) ** 2)
    single = sum(-(tt - tk) / width * g(tt - tk) for tk in np.arange(0.09, 4, 0.18))
    double = single + sum(-0.8 * (tt - tk - 0.04) / width * g(tt - tk - 0.04) for tk in np.arange(0.09, 4, 0.18))
    assert F.phase_cycles(single) == pytest.approx(22, abs=0.05)
    assert F.phase_cycles(double) == pytest.approx(44, abs=0.05)


def test_uncertainty_and_morlet():
    """eq-m05-uncertainty: sigma_t sigma_f >= 1 / (4 pi), with equality for a Gaussian (SymPy and numeric).
    eq-m05-morlet: the Morlet wavelet at scale s is centered on f = w0 / (2 pi s), so the (1/s-normalized) CWT of a
    sinusoid peaks exactly there; its time spread grows and frequency spread shrinks with s."""
    t, f, a = sp.symbols("t f a", positive=True)
    tt = sp.symbols("tt", real=True)
    g = sp.exp(-a * tt ** 2)
    norm_t = sp.integrate(g ** 2, (tt, -sp.oo, sp.oo))
    var_t = sp.integrate(tt ** 2 * g ** 2, (tt, -sp.oo, sp.oo)) / norm_t
    ff = sp.symbols("ff", real=True)
    G = sp.sqrt(sp.pi / a) * sp.exp(-sp.pi ** 2 * ff ** 2 / a)
    var_f = sp.integrate(ff ** 2 * G ** 2, (ff, -sp.oo, sp.oo)) / sp.integrate(G ** 2, (ff, -sp.oo, sp.oo))
    assert sp.simplify(sp.sqrt(var_t * var_f) - 1 / (4 * sp.pi)) == 0
    x = np.linspace(-20, 20, 40001)
    st, sf = F.spreads(x, np.exp(-x ** 2 / 2))
    assert st * sf == pytest.approx(1 / (4 * np.pi), rel=1e-4)
    st2, sf2 = F.spreads(x, np.where(np.abs(x) < 1, 1.0, 0.0) * (1 - x ** 2))
    assert st2 * sf2 > 1 / (4 * np.pi)
    fs = 1000.0
    tt_ = np.arange(0, 4, 1 / fs)
    freqs = np.linspace(4, 16, 121)
    for f0 in (6.0, 9.0, 12.0):
        W = F.cwt(np.cos(2 * np.pi * f0 * tt_), fs, freqs)
        assert freqs[np.argmax(np.abs(W[:, 2000]))] == pytest.approx(f0, abs=0.05)
    assert float(F.scale_for_frequency(1.0)) == pytest.approx(6 / (2 * np.pi))
