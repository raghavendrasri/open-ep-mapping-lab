"""m04 · Sampling, filtering and the EP recording chain: equation tests."""

import numpy as np
import pytest
import sympy as sp
from scipy import signal

from epml import recording as R


def test_sampling_and_aliasing():
    """eq-m04-sampling: a sinusoid at f sampled at fs is indistinguishable from one at |f - fs round(f / fs)|."""
    fs = 1000.0
    n = np.arange(200)
    for f in (10.0, 600.0, 950.0, 1050.0, 1490.0):
        fa = float(R.alias_frequency(f, fs))
        assert 0 <= fa <= fs / 2
        assert np.allclose(np.cos(2 * np.pi * f * n / fs), np.cos(2 * np.pi * fa * n / fs), atol=1e-9)
    assert float(R.alias_frequency(400.0, fs)) == 400.0


def test_quantization_noise():
    """eq-m04-quantization: rounding to an LSB of q adds noise of standard deviation q / sqrt(12); a full-scale sine
    then has an SQNR of 20 log10(2^N sqrt(3/2)) = 6.02 N + 1.76 dB."""
    q, N = sp.symbols("q N", positive=True)
    e = sp.symbols("e", real=True)
    var = sp.integrate(e ** 2 / q, (e, -q / 2, q / 2))
    assert sp.simplify(var - q ** 2 / 12) == 0
    sqnr = 10 * sp.log((2 ** N * q / 2) ** 2 / 2 / (q ** 2 / 12), 10)
    assert sp.N(sqnr.subs(N, 12)) == pytest.approx(float(R.sqnr_db(12)), abs=1e-9)
    assert float(R.sqnr_db(1)) == pytest.approx(6.0206 + 1.7609, abs=1e-3)
    t = np.arange(200000)
    x = 0.98 * np.sin(2 * np.pi * 0.01234567 * t)          # below full scale, so nothing clips
    for bits in (10, 12):
        xq, lsb = R.quantize(x, bits, 1.0)
        assert np.std(xq - x) == pytest.approx(lsb / np.sqrt(12), rel=0.02)
        snr = 10 * np.log10(np.mean(x ** 2) / np.mean((xq - x) ** 2))
        assert snr == pytest.approx(float(R.sqnr_db(bits)) + 20 * np.log10(0.98), abs=0.1)


def test_highpass_and_butterworth():
    """eq-m04-highpass and eq-m04-butterworth: the RC high-pass passes 1/sqrt(2) at fc with a 45 degree lead and acts
    as a differentiator far below fc; Butterworth magnitudes match scipy, and the hand-built digital filters equal
    scipy.signal.butter."""
    f, fc = sp.symbols("f f_c", positive=True)
    H = (sp.I * f / fc) / (1 + sp.I * f / fc)
    assert sp.simplify(sp.Abs(H.subs(f, fc)) - 1 / sp.sqrt(2)) == 0
    assert sp.simplify(sp.arg(H.subs(f, fc)) - sp.pi / 4) == 0
    assert sp.limit(H / (sp.I * f / fc), f, 0) == 1
    assert abs(R.rc_highpass(10.0, 10.0)) == pytest.approx(1 / np.sqrt(2))
    fs = 1000.0
    for order in (1, 2):
        for kind in ("low", "high"):
            b, a = R.butter_digital(30.0, fs, order, kind)
            bs, as_ = signal.butter(order, 30.0, btype=kind, fs=fs)
            assert np.allclose(b, bs, atol=1e-12) and np.allclose(a, as_, atol=1e-12)
            w, ha = signal.freqs(*signal.butter(order, 2 * np.pi * 30.0, btype=kind, analog=True), worN=2 * np.pi * np.array([3.0, 300.0]))
            assert np.abs(ha) == pytest.approx(R.butter_magnitude(np.array([3.0, 300.0]), 30.0, order, kind), rel=1e-9)


def test_delay_and_zero_phase():
    """eq-m04-delay: a causal low-pass delays slow features by its group delay, 1/(2 pi fc) (order 1) or
    sqrt(2)/(2 pi fc) (order 2); forward-backward filtering removes the delay."""
    s, W = sp.symbols("s W", positive=True)
    w = sp.symbols("omega", positive=True)
    for order, H in ((1, W / (s + W)), (2, W ** 2 / (s ** 2 + sp.sqrt(2) * W * s + W ** 2))):
        gd = sp.limit(-sp.diff(sp.atan2(sp.im(sp.expand_complex(H.subs(s, sp.I * w))), sp.re(sp.expand_complex(H.subs(s, sp.I * w)))), w), w, 0)
        assert sp.simplify(gd - {1: 1 / W, 2: sp.sqrt(2) / W}[order]) == 0
    fs = 20000.0
    t = np.arange(-0.2, 0.2, 1 / fs)
    x = np.exp(-(t / 0.01) ** 2)                         # a slow 10-ms bump
    for order in (1, 2):
        y = R.apply(*R.butter_digital(100.0, fs, order, "low"), x)
        shift = t[np.argmax(y)] - t[np.argmax(x)]
        assert shift == pytest.approx(R.lowpass_group_delay_dc(100.0, order), rel=0.1)
        z = R.apply(*R.butter_digital(100.0, fs, order, "low"), x, zero_phase=True)
        assert abs(t[np.argmax(z)] - t[np.argmax(x)]) < 2 / fs


def test_notch():
    """eq-m04-notch: the second-order notch removes f0 completely, passes DC and Nyquist with gain 1, and has a -3 dB
    bandwidth of f0 / Q; it equals scipy.signal.iirnotch."""
    fs = 1000.0
    for f0, q in ((50.0, 30.0), (60.0, 10.0)):
        b, a = R.notch(f0, q, fs)
        bs, as_ = signal.iirnotch(f0, q, fs)
        assert np.allclose(b, bs) and np.allclose(a, as_)
        w, h = signal.freqz(b, a, worN=[f0, 0.0, fs / 2 - 1e-9], fs=fs)
        assert abs(h[0]) < 1e-12 and abs(h[1]) == pytest.approx(1.0) and abs(h[2]) == pytest.approx(1.0, abs=1e-6)
        ff = np.linspace(f0 - 3 * f0 / q, f0 + 3 * f0 / q, 200001)
        _, hh = signal.freqz(b, a, worN=ff, fs=fs)
        below = ff[np.abs(hh) < 1 / np.sqrt(2)]
        assert below.max() - below.min() == pytest.approx(f0 / q, rel=0.02)


def test_unipolar_through_the_chain():
    """The m03 unipolar electrogram through the chain: zero-phase filtering keeps the steepest downstroke at the
    activation time; a causal 100-Hz high-pass (as for high-pass filtered unipolar recordings in Delacretaz et al.
    2001) moves it and shrinks the signal."""
    fs = 20000.0
    t = np.arange(-100, 100, 1000 / fs)                # ms
    x = R.unipolar_egm(t)
    assert R.steepest_downstroke(t, x) == pytest.approx(0.0, abs=1e-3)
    zp = R.chain(x, fs, hp=100.0, lp=500.0, zero_phase=True)
    assert R.steepest_downstroke(t, zp) == pytest.approx(0.0, abs=0.02)
    causal = R.chain(x, fs, hp=100.0, lp=500.0)
    assert abs(R.steepest_downstroke(t, causal)) > 0.1
    assert np.ptp(zp) < np.ptp(x)
    assert R.DELACRETAZ2001["bipolar"] == (30.0, 500.0) and R.IAFDB == {"fs_hz": 1000.0, "bits": 14}
