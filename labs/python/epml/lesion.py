"""m53 · Imaging ablation lesions and real-time MRI-guided EP: when blur hides a gap in a lesion line, a synthetic
ring lesion around a vein with gaps, agreement between image gaps and electrical reconnection, real-time imaging
frame budgets, and electrograms recorded during scanning. MIT License.

Sources for default values: spatial resolution of LGE (1.5-2 mm routinely, about 1 mm useful for thin walls) from
Kellman and Arai 2012; real-time frame rates (4-8 frames/s for passive catheter visualization, up to 50/s for active
tracking) and the filter chain for electrograms in the scanner (300 Hz low-pass, 30 Hz high-pass, 60 Hz notch;
best quality at a 120 Hz low-pass) from Tampakis et al. 2023. Lesion sizes, gap widths, noise, repetition times,
reconnection probabilities and the electrogram and artifact waveforms are illustrative."""
import numpy as np
from scipy.special import erf, erfinv

from .ml import cohen_kappa

FPS_PASSIVE = (4.0, 8.0)       # frames/s, real-time bSSFP for passive catheter visualization (Tampakis et al. 2023)
FPS_ACTIVE = 50.0              # frames/s, active tracking with micro-coils, upper value (Tampakis et al. 2023)
LGE_RESOLUTION_MM = {"routine": (1.5, 2.0), "thin walls": 1.0}   # Kellman and Arai 2012


def fwhm_to_sigma(fwhm):
    return fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))


# ---------------------------------------------------------------- a gap in a lesion line (eq-m53-gap)


def band_gap_image(x, y, band_width, gap_width, sigma):
    """eq-m53-gap: a straight lesion band of width w along x (|y| <= w/2) with a gap of width g centered at x = 0,
    blurred by an isotropic Gaussian of standard deviation sigma. The 2-D Gaussian is separable, so the image is
    B(y) [1 - G(x)], with B and G the blurred box profiles."""
    r = np.sqrt(2.0) * sigma
    B = 0.5 * (erf((np.asarray(y, float) + band_width / 2) / r) - erf((np.asarray(y, float) - band_width / 2) / r))
    G = 0.5 * (erf((np.asarray(x, float) + gap_width / 2) / r) - erf((np.asarray(x, float) - gap_width / 2) / r))
    return B * (1.0 - G)


def band_peak(band_width, sigma):
    """Signal on the center line of an unbroken band: erf(w / (2 sqrt 2 sigma))."""
    return float(erf(band_width / (2.0 * np.sqrt(2.0) * sigma)))


def gap_center(band_width, gap_width, sigma):
    """Signal at the center of the gap: band peak times (1 - erf(g / (2 sqrt 2 sigma)))."""
    return band_peak(band_width, sigma) * (1.0 - float(erf(gap_width / (2.0 * np.sqrt(2.0) * sigma))))


def min_visible_gap(band_width, sigma, threshold=0.5):
    """Smallest gap whose center falls below the threshold: 2 sqrt(2) sigma erfinv(1 - threshold / peak). Returns
    inf if the band itself never reaches the threshold (the whole line is invisible)."""
    peak = band_peak(band_width, sigma)
    if peak <= threshold:
        return float("inf")
    return float(2.0 * np.sqrt(2.0) * sigma * erfinv(1.0 - threshold / peak))


def apparent_gap(gap_width, edema_margin):
    """Acute imaging of edema: a margin e on each side of each lesion narrows a gap to max(0, g - 2e)."""
    return max(0.0, gap_width - 2.0 * edema_margin)


# ---------------------------------------------------------------- a ring lesion around a vein


def ring_lesion(gaps, pixel=0.25, radius=12.0, band_width=4.0, half=20.0):
    """A ring-shaped lesion (value 1) of the given width around a vein ostium of the given radius (mm), with gaps
    given as [(center angle in degrees, arc length in mm along the ring's center line), ...]. Shapes illustrative.
    Returns (image, x axis)."""
    x = np.arange(-half, half + pixel / 2, pixel)
    X, Y = np.meshgrid(x, x)
    r = np.hypot(X, Y)
    ang = np.degrees(np.arctan2(Y, X)) % 360
    img = (np.abs(r - radius) <= band_width / 2).astype(float)
    for center, arc in gaps:
        half_deg = np.degrees(arc / radius) / 2
        d = (ang - center + 180) % 360 - 180
        img[np.abs(d) <= half_deg] = 0.0
    return img, x


def blur(img, pixel, fwhm):
    from scipy.ndimage import gaussian_filter

    return gaussian_filter(img, fwhm_to_sigma(fwhm) / pixel, mode="constant")


def ring_profile(img, x, radius=12.0, n=720):
    """Sample the image along the ring's center line; returns (angles in degrees, values)."""
    from scipy.ndimage import map_coordinates

    ang = np.arange(n) * 360.0 / n
    px = radius * np.cos(np.radians(ang))
    py = radius * np.sin(np.radians(ang))
    dx = x[1] - x[0]
    vals = map_coordinates(img, [(py - x[0]) / dx, (px - x[0]) / dx], order=1)
    return ang, vals


def detect_gaps(angles, values, threshold=0.5):
    """Runs of the ring profile below the threshold, as [(center angle, angular width)], wrapping at 360."""
    below = np.asarray(values) < threshold
    if below.all():
        return [(0.0, 360.0)]
    if not below.any():
        return []
    n = below.size
    start = int(np.argmin(below))        # first sample above threshold; scan from there so runs do not wrap
    runs, k = [], 0
    while k < n:
        i = (start + k) % n
        if below[i]:
            j = k
            while j < n and below[(start + j) % n]:
                j += 1
            a0 = angles[(start + k) % n]
            width = (j - k) * 360.0 / n
            runs.append(((a0 + width / 2) % 360, width))
            k = j
        else:
            k += 1
    return runs


def matched(true_gaps, found, tol_deg=10.0):
    """Which true gaps have a detected gap within tol_deg of their center."""
    out = []
    for c, _ in true_gaps:
        out.append(any(abs((f - c + 180) % 360 - 180) <= tol_deg for f, _ in found))
    return np.array(out, bool)


# ---------------------------------------------------------------- image gaps against electrical reconnection


def simulate_veins(rng, n_veins=200, p_gap=0.45, gap_mm=(0.5, 6.0), conduct_mm=1.0, p_conduct=0.8,
                   p_other=0.15):
    """Veins after isolation, each with at most one true gap of random width (uniform in gap_mm) with probability
    p_gap. A gap at least conduct_mm wide reconnects with probability p_conduct; veins also reconnect for other
    reasons with probability p_other (for example a gap too thin to image, or a lesion that later recovers). All
    values illustrative. Returns (gap width in mm, 0 for none; reconnected booleans)."""
    has_gap = rng.random(n_veins) < p_gap
    width = np.where(has_gap, rng.uniform(*gap_mm, n_veins), 0.0)
    conducts = (width >= conduct_mm) & (rng.random(n_veins) < p_conduct)
    other = rng.random(n_veins) < p_other
    return width, conducts | other


def image_detects(widths, band_width, fwhm, threshold=0.5):
    """Whether the image shows each gap (eq-m53-gap)."""
    g = min_visible_gap(band_width, fwhm_to_sigma(fwhm), threshold)
    return np.asarray(widths) >= g


def kappa(a, b):
    """Cohen's kappa (m35)."""
    return float(cohen_kappa(np.asarray(a, int), np.asarray(b, int)))


# ---------------------------------------------------------------- real-time MRI (eq-m53-frame)


def frame_time_ms(n_lines, tr_ms, acceleration=1.0):
    """eq-m53-frame: one frame needs n_lines / R lines, each one repetition time TR apart."""
    return n_lines * tr_ms / acceleration


def fps(n_lines, tr_ms, acceleration=1.0):
    return 1e3 / frame_time_ms(n_lines, tr_ms, acceleration)


def motion_per_frame_mm(speed_mm_s, frame_ms):
    return speed_mm_s * frame_ms * 1e-3


# ---------------------------------------------------------------- electrograms during scanning


def synthetic_egm(fs=2000.0, duration=2.0, cycle_ms=250.0, rng=None):
    """An illustrative bipolar electrogram: a biphasic deflection (derivative of a Gaussian, 3 ms wide) every
    cycle_ms, amplitude 1 mV. Returns (t in s, signal in mV, onset times)."""
    t = np.arange(0, duration, 1 / fs)
    onsets = np.arange(0.1, duration - 0.05, cycle_ms / 1e3)
    s = np.zeros_like(t)
    w = 0.003
    for t0 in onsets:
        u = (t - t0) / w
        s += -u * np.exp(-0.5 * u**2) * np.exp(0.5)     # peak magnitude 1 mV
    return t, s, onsets


def gradient_artifact(t, tr_ms=3.0, amplitude=2.0, decay_ms=0.4, mhd_amp=0.3, heart_ms=800.0):
    """Illustrative scanner interference: a decaying spike at every gradient switch (each TR) and a slow bump once
    per heartbeat standing in for the magnetohydrodynamic voltage. Amplitudes in mV, illustrative."""
    a = np.zeros_like(t)
    for t0 in np.arange(0, t[-1], tr_ms / 1e3):
        dt = t - t0
        on = dt >= 0
        a[on] += amplitude * np.exp(-dt[on] / (decay_ms / 1e3)) * np.cos(2 * np.pi * 1500 * dt[on])
    phase = (t % (heart_ms / 1e3)) / (heart_ms / 1e3)
    a += mhd_amp * np.exp(-0.5 * ((phase - 0.35) / 0.06) ** 2)
    return a


def filter_chain(x, fs, low_pass=300.0, high_pass=30.0, notch=60.0, order=4):
    """The chain described by Tampakis et al. 2023: low-pass, high-pass and a mains notch (zero-phase here)."""
    from scipy.signal import butter, filtfilt, iirnotch

    y = x
    if low_pass:
        b, a = butter(order, low_pass / (fs / 2), "low")
        y = filtfilt(b, a, y)
    if high_pass:
        b, a = butter(2, high_pass / (fs / 2), "high")
        y = filtfilt(b, a, y)
    if notch:
        b, a = iirnotch(notch / (fs / 2), 30.0)
        y = filtfilt(b, a, y)
    return y


def peak_to_peak_at(signal, t, onsets, window_ms=12.0):
    """Mean peak-to-peak amplitude in a window around each onset."""
    out = []
    for t0 in onsets:
        m = np.abs(t - t0) <= window_ms / 2e3
        out.append(signal[m].max() - signal[m].min())
    return float(np.mean(out))
