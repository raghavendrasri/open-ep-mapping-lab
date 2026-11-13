"""m04 · Sampling, filtering and the EP recording chain. MIT License.

Units: time ms or s as named, frequency Hz, potentials in relative units (the m03 unipolar model) or in LSB.
Filters are built by hand (bilinear transform with prewarping, first- and second-order sections) so the same
coefficients can be reproduced in the JS demos and the Octave lab; scipy.signal is used only to check them.
Filter settings quoted in docstrings come from Delacretaz et al. 2001; the database's sampling rate and resolution
from the PhysioNet Intracardiac Atrial Fibrillation Database page (as in m31).
"""

import numpy as np
from scipy import signal

from .electrograms import unipolar

# Settings used in one clinical mapping study (Delacretaz et al. 2001), in Hz.
DELACRETAZ2001 = {"unipolar minimally filtered": (0.5, 500.0), "unipolar high-pass": (100.0, None),
                  "bipolar": (30.0, 500.0)}
IAFDB = {"fs_hz": 1000.0, "bits": 14}     # PhysioNet iafdb page, checked 2026-11-04 (m31)


# ---------------------------------------------------------------- sampling and quantization


def alias_frequency(f, fs):
    """eq-m04-sampling: a sinusoid at f sampled at fs appears at |f - fs round(f / fs)|, in [0, fs / 2]."""
    f = np.asarray(f, float)
    return np.abs(f - fs * np.round(f / fs))


def quantize(x, n_bits, full_scale):
    """Round x to an n-bit converter spanning [-full_scale, full_scale); returns (quantized x, LSB)."""
    lsb = 2 * full_scale / 2 ** n_bits
    q = np.clip(np.round(np.asarray(x, float) / lsb), -2 ** (n_bits - 1), 2 ** (n_bits - 1) - 1)
    return q * lsb, lsb


def sqnr_db(n_bits):
    """eq-m04-quantization: signal-to-quantization-noise ratio of a full-scale sine, 6.02 N + 1.76 dB."""
    return 20 * np.log10(2.0 ** n_bits * np.sqrt(1.5))


# ---------------------------------------------------------------- analog responses


def rc_highpass(f, fc):
    """eq-m04-highpass: H(f) = (j f / fc) / (1 + j f / fc)."""
    x = 1j * np.asarray(f, float) / fc
    return x / (1 + x)


def butter_magnitude(f, fc, order, kind="low"):
    """eq-m04-butterworth: |H| = 1 / sqrt(1 + (f / fc)^(2n)) for a low-pass (f -> fc^2 / f for a high-pass)."""
    f = np.asarray(f, float)
    r = f / fc if kind == "low" else np.divide(fc, f, out=np.full_like(f, np.inf), where=f > 0)
    return 1 / np.sqrt(1 + r ** (2 * order))


def lowpass_group_delay_dc(fc, order):
    """eq-m04-delay: group delay at DC of an analog Butterworth low-pass, in s: 1 / (2 pi fc) for order 1,
    sqrt(2) / (2 pi fc) for order 2."""
    return {1: 1.0, 2: np.sqrt(2.0)}[order] / (2 * np.pi * fc)


# ---------------------------------------------------------------- digital filters (bilinear transform)


def _prewarp(fc, fs):
    return 2 * fs * np.tan(np.pi * fc / fs)


def butter_digital(fc, fs, order, kind):
    """First- or second-order Butterworth low- or high-pass by the bilinear transform with prewarping.
    Returns (b, a), normalized so a[0] = 1. Matches scipy.signal.butter."""
    W = _prewarp(fc, fs)
    K = 2 * fs
    if order == 1:
        if kind == "low":   # W / (s + W)
            b = np.array([W, W]); a = np.array([K + W, W - K])
        else:               # s / (s + W)
            b = np.array([K, -K]); a = np.array([K + W, W - K])
    elif order == 2:
        q = np.sqrt(2.0)
        a = np.array([K * K + q * W * K + W * W, 2 * (W * W - K * K), K * K - q * W * K + W * W])
        if kind == "low":   # W^2 / (s^2 + sqrt2 W s + W^2)
            b = W * W * np.array([1.0, 2.0, 1.0])
        else:               # s^2 / (...)
            b = K * K * np.array([1.0, -2.0, 1.0])
    else:
        raise ValueError("order 1 or 2")
    return b / a[0], a / a[0]


def notch(f0, q, fs):
    """eq-m04-notch: second-order notch at f0 with quality factor Q (bandwidth f0 / Q), as scipy.signal.iirnotch."""
    w0 = 2 * np.pi * f0 / fs
    bw = w0 / q
    gb = 1 / np.sqrt(2)
    beta = np.sqrt(1 - gb ** 2) / gb * np.tan(bw / 2)
    gain = 1 / (1 + beta)
    b = gain * np.array([1.0, -2 * np.cos(w0), 1.0])
    a = np.array([1.0, -2 * gain * np.cos(w0), 2 * gain - 1])
    return b, a


def apply(b, a, x, zero_phase=False):
    """Run a filter causally, or forward then backward (zero phase, squared magnitude). No edge padding, so the
    Octave and JS versions match exactly."""
    y = signal.lfilter(b, a, x)
    if zero_phase:
        y = signal.lfilter(b, a, y[::-1])[::-1]
    return y


def chain(x, fs, hp=None, lp=None, order=2, zero_phase=False, mains=None, q=30.0):
    """A recording chain: optional high-pass, low-pass and mains notch, in that order."""
    y = np.asarray(x, float)
    if hp:
        y = apply(*butter_digital(hp, fs, order, "high"), y, zero_phase)
    if lp:
        y = apply(*butter_digital(lp, fs, order, "low"), y, zero_phase)
    if mains:
        y = apply(*notch(mains, q, fs), y, zero_phase)
    return y


# ---------------------------------------------------------------- a test electrogram


def unipolar_egm(t_ms, c=1.0, w=0.3, h=1.0):
    """The m03 unipolar electrogram at a fixed electrode as the front passes at t = 0 (c in mm/ms)."""
    return unipolar(-c * np.asarray(t_ms, float), w + h, 1.0)


def steepest_downstroke(t, x):
    """Time of the most negative slope (the intrinsic deflection of m03), with parabolic refinement."""
    d = np.gradient(x, t)
    i = int(np.argmin(d))
    if 0 < i < len(d) - 1:
        y0, y1, y2 = d[i - 1], d[i], d[i + 1]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den else 0.0
        return float(t[i] + off * (t[1] - t[0]))
    return float(t[i])
