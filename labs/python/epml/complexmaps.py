"""m29 helpers: fractionation, dominant frequency, organization, phase and phase singularities.

Times in s unless a name says ms; frequencies in Hz. Filter settings and detection thresholds are
always passed by the caller: published values are cited in the module, not hidden here.
"""

import numpy as np
from scipy import signal


def wrap(a):
    """Wrap angles to (-pi, pi]."""
    return np.angle(np.exp(1j * np.asarray(a, dtype=float)))


def fractionation_index(times):
    """eq-m29-fi: mean interval (t_N - t_1) / (N - 1) between detected deflections."""
    t = np.sort(np.asarray(times, dtype=float))
    if t.size < 2:
        return np.nan
    return (t[-1] - t[0]) / (t.size - 1)


def detect_deflections(x, fs, slope_threshold, refractory):
    """Times (s) of local minima of dx/dt below -slope_threshold, at least `refractory` s apart."""
    d = np.gradient(np.asarray(x, dtype=float)) * fs
    peaks, _ = signal.find_peaks(-d, height=slope_threshold, distance=max(1, int(refractory * fs)))
    return peaks / fs


def preprocess_rectified(x, fs, band, lowpass, order=3):
    """Band-pass, rectify, low-pass (the chain of Botteron and Smith; values passed by the caller)."""
    b, a = signal.butter(order, band, btype="band", fs=fs)
    y = np.abs(signal.filtfilt(b, a, x))
    b, a = signal.butter(order, lowpass, btype="low", fs=fs)
    return signal.filtfilt(b, a, y)


def spectrum(x, fs, nfft=None):
    """One-sided power spectrum with a Hann window. Returns (f, P)."""
    x = np.asarray(x, dtype=float) - np.mean(x)
    n = x.size
    nfft = nfft or 1 << int(np.ceil(np.log2(4 * n)))
    w = signal.windows.hann(n)
    X = np.fft.rfft(x * w, nfft)
    return np.fft.rfftfreq(nfft, 1 / fs), np.abs(X) ** 2


def dominant_frequency(x, fs, f_lo, f_hi, nfft=None):
    """eq-m29-df: frequency of the largest spectral peak within [f_lo, f_hi]."""
    f, P = spectrum(x, fs, nfft)
    band = (f >= f_lo) & (f <= f_hi)
    return f[band][np.argmax(P[band])]


def organization_index(x, fs, f_lo, f_hi, halfwidth, n_harmonics=4, nfft=None):
    """eq-m29-oi: area under the first n harmonic peaks (DF, 2 DF, ...) over the total area in band.

    Each peak's area is taken within +/- halfwidth Hz of the harmonic.
    """
    f, P = spectrum(x, fs, nfft)
    band = (f >= f_lo) & (f <= f_hi)
    df = f[band][np.argmax(P[band])]
    peak = np.zeros_like(f, dtype=bool)
    for h in range(1, n_harmonics + 1):
        peak |= np.abs(f - h * df) <= halfwidth
    total_band = (f >= f_lo) & (f <= max(f_hi, n_harmonics * df + halfwidth))
    return P[peak & total_band].sum() / P[total_band].sum()


def analytic_phase(x):
    """eq-m29-hilbert: phase of the analytic signal x + i H[x]."""
    return np.angle(signal.hilbert(np.asarray(x, dtype=float)))


def sinusoidal_recomposition(x, fs, period):
    """eq-m29-recomposition: sum of one-period sine wavelets weighted by the negative slope.

    Wavelet amplitudes follow Kuklik et al. (2015): proportional to the negative slope of the
    electrogram, zero where the slope is positive. The wavelet period (s) is chosen by the caller;
    this course uses the cycle length.
    """
    d = np.gradient(np.asarray(x, dtype=float)) * fs
    w = np.where(d < 0, -d, 0.0)
    half = int(round(period * fs / 2))
    u = np.arange(-half, half + 1) / fs
    psi = np.sin(2 * np.pi * u / period)
    return np.convolve(w, psi, mode="same") / fs


def ring_charge(phases):
    """eq-m29-charge: (1 / 2 pi) * sum of wrapped phase steps around a closed ring (in order)."""
    p = np.asarray(phases, dtype=float)
    steps = wrap(np.diff(np.concatenate([p, p[:1]])))
    return int(np.rint(steps.sum() / (2 * np.pi)))


def plaquette_charges(phase):
    """eq-m29-charge on every 2 x 2 square of a phase grid (counter-clockwise ring)."""
    a = phase[:-1, :-1]
    b = phase[:-1, 1:]
    c = phase[1:, 1:]
    d = phase[1:, :-1]
    s = wrap(b - a) + wrap(c - b) + wrap(d - c) + wrap(a - d)
    return np.rint(s / (2 * np.pi)).astype(int)


def ring_indices(i, j, size):
    """Grid indices of a square ring of side `size` with lower-left corner (i, j), counter-clockwise
    (rows increase along y)."""
    k = size - 1
    ring = [(i, j + c) for c in range(k)]
    ring += [(i + r, j + k) for r in range(k)]
    ring += [(i + k, j + k - c) for c in range(k)]
    ring += [(i + k - r, j) for r in range(k)]
    return ring


def spatial_wavelength(cv, cycle_length):
    """eq-m29-wavelength: lambda = v * CL (same length and time units as the inputs)."""
    return cv * cycle_length
