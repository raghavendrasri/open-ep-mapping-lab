"""m05 · Time-frequency tools: spectra, windows, the analytic signal and wavelets. MIT License.

Units: time s, frequency Hz, signals in relative units. The dominant-frequency, organization-index and
sinusoidal-recomposition methods built on these tools are in epml.complexmaps (m29). Everything here is standard
signal processing checked against our own code and scipy; electrogram-like signals are synthetic.
"""

import numpy as np
from scipy import signal


# ---------------------------------------------------------------- spectra (eq-m05-resolution, eq-m05-leakage)


def periodogram(x, fs, window="boxcar", nfft=None):
    """One-sided power spectral density estimate of one record (scipy.signal.periodogram)."""
    return signal.periodogram(x, fs, window=window, nfft=nfft, detrend=False, scaling="density")


def resolution(fs, n):
    """eq-m05-resolution: bin spacing f_s / N = 1 / T for a record of N samples."""
    return fs / n


def window_sidelobe_db(window, n=256, pad=64):
    """Highest sidelobe of a window's spectrum relative to its main lobe, in dB, and the main-lobe half width in bins
    (first null)."""
    w = signal.get_window(window, n, fftbins=True)
    W = np.abs(np.fft.rfft(w, n * pad))
    W /= W.max()
    i = 1
    while i < len(W) - 1 and W[i + 1] < W[i]:
        i += 1
    return 20 * np.log10(W[i:].max()), i / pad


def two_tone(fs, T, f1, f2, a2=1.0, phase=0.3):
    t = np.arange(int(round(fs * T))) / fs
    return t, np.cos(2 * np.pi * f1 * t) + a2 * np.cos(2 * np.pi * f2 * t + phase)


def resolved(f, P, f1, f2):
    """True if the spectrum shows two separate peaks between f1 and f2 (a dip between them below both)."""
    band = (f >= f1) & (f <= f2)
    if band.sum() < 3:
        return False
    p1 = P[np.argmin(np.abs(f - f1))]
    p2 = P[np.argmin(np.abs(f - f2))]
    return bool(P[band].min() < 0.5 * min(p1, p2))


# ---------------------------------------------------------------- variance (eq-m05-welch)


def periodogram_cv(fs=200.0, T=8.0, trials=200, seed=0, segments=1):
    """Coefficient of variation (std / mean across bins and trials) of the PSD of white noise, for a single
    periodogram (segments = 1) or Welch's average of `segments` non-overlapping segments."""
    rng = np.random.default_rng(seed)
    n = int(fs * T)
    ratios = []
    for _ in range(trials):
        x = rng.standard_normal(n)
        if segments == 1:
            f, P = signal.periodogram(x, fs, detrend=False)
        else:
            f, P = signal.welch(x, fs, window="boxcar", nperseg=n // segments, noverlap=0, detrend=False)
        ratios.append(P[1:-1])
    P = np.concatenate(ratios)
    return float(P.std() / P.mean())


# ---------------------------------------------------------------- pulse trains (eq-m05-pulse-train)


def biphasic_pulse(t, width):
    """A zero-mean biphasic deflection (derivative of a Gaussian), like a sharp bipolar electrogram."""
    return -t / width * np.exp(-0.5 * (t / width) ** 2)


def pulse_train(fs, T, cycle, width, jitter=0.0, seed=0):
    """Sum of biphasic pulses every `cycle` seconds (optionally with timing jitter)."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(round(fs * T))) / fs
    times = np.arange(cycle / 2, T, cycle) + jitter * rng.standard_normal(len(np.arange(cycle / 2, T, cycle)))
    x = np.zeros_like(t)
    for tk in times:
        x += biphasic_pulse(t - tk, width)
    return t, x, times


def pulse_spectrum_magnitude(f, width):
    """|P(f)| of the biphasic pulse: proportional to f exp(-2 pi^2 f^2 width^2), zero at DC; it peaks at
    f = 1 / (2 pi width)."""
    f = np.asarray(f, float)
    return np.abs(f) * np.exp(-2 * np.pi ** 2 * f ** 2 * width ** 2)


def rectify_lowpass(x, fs, band=(40.0, 250.0), lowpass=20.0, order=3):
    """Band-pass, rectify, low-pass: each sharp deflection becomes one smooth bump at the activation rate (as in
    epml.complexmaps.preprocess_rectified, m29)."""
    b, a = signal.butter(order, band, btype="band", fs=fs)
    y = np.abs(signal.filtfilt(b, a, x))
    b, a = signal.butter(order, lowpass, fs=fs)
    return signal.filtfilt(b, a, y)


def peak_frequency(x, fs, f_lo, f_hi, pad=8):
    """Frequency of the largest spectral peak in [f_lo, f_hi] (zero-padded periodogram, Hann window)."""
    f, P = periodogram(x - np.mean(x), fs, window="hann", nfft=pad * len(x))
    band = (f >= f_lo) & (f <= f_hi)
    return float(f[band][np.argmax(P[band])])


# ---------------------------------------------------------------- the analytic signal (eq-m05-analytic)


def analytic(x):
    """eq-m05-analytic: z = x + j H[x] by the FFT (scipy.signal.hilbert)."""
    return signal.hilbert(x)


def instantaneous_frequency(z, fs):
    """f_i = (1 / 2 pi) d(unwrapped phase)/dt."""
    return np.gradient(np.unwrap(np.angle(z))) * fs / (2 * np.pi)


def phase_cycles(x):
    """Number of full phase turns of the analytic signal over the record."""
    ph = np.unwrap(np.angle(analytic(x - np.mean(x))))
    return float((ph[-1] - ph[0]) / (2 * np.pi))


# ---------------------------------------------------------------- uncertainty and wavelets (eq-m05-uncertainty, eq-m05-morlet)


def spreads(t, g):
    """RMS duration sigma_t of |g|^2 and RMS bandwidth sigma_f of |G|^2 (numerically)."""
    dt = t[1] - t[0]
    p = np.abs(g) ** 2
    p /= p.sum()
    tm = (t * p).sum()
    st = np.sqrt(((t - tm) ** 2 * p).sum())
    G = np.fft.fftshift(np.fft.fft(g))
    f = np.fft.fftshift(np.fft.fftfreq(len(g), dt))
    q = np.abs(G) ** 2
    q /= q.sum()
    fm = (f * q).sum()
    sf = np.sqrt(((f - fm) ** 2 * q).sum())
    return st, sf


def morlet(t, w0=6.0):
    """eq-m05-morlet: psi(t) = pi^(-1/4) exp(j w0 t) exp(-t^2 / 2) (the small admissibility correction is
    neglected, which is accurate for w0 >= 5)."""
    return np.pi ** -0.25 * np.exp(1j * w0 * t) * np.exp(-t ** 2 / 2)


def scale_for_frequency(f, w0=6.0):
    """eq-m05-morlet: the scale whose wavelet is centered on f Hz, s = w0 / (2 pi f) (s in seconds)."""
    return w0 / (2 * np.pi * np.asarray(f, float))


def cwt(x, fs, freqs, w0=6.0):
    """Continuous wavelet transform with the Morlet wavelet at the scales matching `freqs` (direct convolution),
    normalized by 1/s so that a sinusoid of amplitude A gives the same peak magnitude at every scale, at exactly
    s = w0 / (2 pi f)."""
    out = np.empty((len(freqs), len(x)), complex)
    for i, f in enumerate(freqs):
        s = float(scale_for_frequency(f, w0))
        half = int(np.ceil(5 * s * fs))
        tt = np.arange(-half, half + 1) / fs
        psi = morlet(tt / s, w0) / s
        out[i] = np.convolve(x, np.conj(psi[::-1]), mode="same") / fs
    return out
