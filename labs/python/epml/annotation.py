"""m22 · Electrogram annotation: local activation time, window of interest, reference, far-field rejection.

Times in ms, lengths in mm, conduction velocity in mm/ms (= m/s), potentials in arbitrary units unless stated.
The electrogram model is the m03 arctangent front: a unipolar electrode at front distance s sees A s / (s^2 + a^2),
with a = w + h (front width plus electrode height). MIT License.
"""
from __future__ import annotations

import numpy as np

from .electrograms import unipolar

# ---------------------------------------------------------------- reference (eq-m22-lat)


def lat(t_local, t_ref):
    """Local activation time: the annotated local time minus the reference time of the same beat."""
    return np.asarray(t_local, float) - np.asarray(t_ref, float)


def lat_difference_sd(sigma_annot, sigma_ref, same_beat):
    """SD of the difference of two LATs. Within one beat the reference error cancels; across beats it adds twice."""
    v = 2 * sigma_annot**2 + (0.0 if same_beat else 2 * sigma_ref**2)
    return float(np.sqrt(v))


# ---------------------------------------------------------------- traces and annotation rules (eq-m22-intrinsic, eq-m22-onset)


def unipolar_trace(t, c=1.0, a=1.3, t0=0.0, amplitude=1.0):
    """Unipolar electrogram as a planar front passes the electrode at t0 (the front reaches s = 0 at t0)."""
    return unipolar(-c * (np.asarray(t, float) - t0), a, amplitude)


def bipolar_trace(t, c=1.0, a=1.3, d=2.0, theta=0.0, t0=0.0, amplitude=1.0):
    """Bipolar electrogram (distal minus proximal); the front passes the bipole midpoint at t0.

    The distal electrode lies (d/2) cos(theta) ahead along the propagation direction, so it activates later.
    """
    delta = 0.5 * d * np.cos(theta)
    s = -c * (np.asarray(t, float) - t0)
    return unipolar(s + delta, a, amplitude) - unipolar(s - delta, a, amplitude)


def _parabolic(t, y, i):
    if 0 < i < len(y) - 1:
        y0, y1, y2 = y[i - 1], y[i], y[i + 1]
        den = y0 - 2 * y1 + y2
        off = 0.5 * (y0 - y2) / den if den else 0.0
        return float(t[i] + off * (t[1] - t[0]))
    return float(t[i])


def steepest_downstroke(t, x):
    """Time of the most negative slope (the unipolar intrinsic deflection), parabolic refinement."""
    t = np.asarray(t, float)
    d = np.gradient(np.asarray(x, float), t)
    return _parabolic(t, d, int(np.argmin(d)))


def peak_time(t, x):
    """Time of the largest absolute value (a common bipolar annotation), parabolic refinement."""
    t = np.asarray(t, float)
    y = np.abs(np.asarray(x, float))
    return _parabolic(t, y, int(np.argmax(y)))


def onset_time(t, x, fraction):
    """First time before the absolute peak at which |x| rises through fraction * max|x| (linear interpolation)."""
    t = np.asarray(t, float)
    y = np.abs(np.asarray(x, float))
    k = int(np.argmax(y))
    level = fraction * y[k]
    j = k
    while j > 0 and y[j - 1] >= level:
        j -= 1
    if j == 0:
        return float(t[0])
    return float(t[j - 1] + (level - y[j - 1]) / (y[j] - y[j - 1]) * (t[j] - t[j - 1]))


def onset_lead_ratio(fraction):
    """Small-spacing limit: the bipolar onset at the given fraction of the peak precedes the midpoint activation by
    (a / c) * sqrt(x_f), with x_f the root of (1 - x) / (1 + x)^2 = fraction."""
    f = float(fraction)
    x = (-(2 * f + 1) + np.sqrt(8 * f + 1)) / (2 * f)
    return float(np.sqrt(x))


def onset_lead(a, c, fraction):
    """How long (ms) before the front reaches the bipole midpoint the onset annotation fires (small spacing)."""
    return a / c * onset_lead_ratio(fraction)


# ---------------------------------------------------------------- noise (eq-m22-jitter)


def crossing_jitter(sigma_noise, slope):
    """SD of a threshold-crossing time: noise SD divided by the signal's slope at the crossing."""
    return sigma_noise / abs(slope)


def threshold_crossing(t, x, level):
    """First upward crossing of a level (linear interpolation); NaN if none."""
    t = np.asarray(t, float)
    x = np.asarray(x, float)
    idx = np.nonzero((x[:-1] < level) & (x[1:] >= level))[0]
    if not len(idx):
        return float("nan")
    i = idx[0]
    return float(t[i] + (level - x[i]) / (x[i + 1] - x[i]) * (t[i + 1] - t[i]))


# ---------------------------------------------------------------- window of interest (eq-m22-woi)


def window_lat(t_rel, w0, width, cycle):
    """Assign a time relative to the reference to the window [w0, w0 + width), using the cycle length.

    A local activation recurs every cycle, so it is shifted by whole cycles into [w0, w0 + cycle); if it then falls
    beyond the window (width < cycle) it is not annotated (NaN).
    """
    t_rel = np.asarray(t_rel, float)
    v = w0 + np.mod(t_rel - w0, cycle)
    return np.where(v < w0 + width, v, np.nan)


def ring_activation(position, length, cycle, t_start=0.0):
    """Macroreentry around a circuit of the given length (mm) with uniform speed: time relative to the reference."""
    return t_start + cycle * np.asarray(position, float) / length


# ---------------------------------------------------------------- far field (eq-m22-farfield)


def sharpness(t, x):
    """Largest absolute slope divided by peak-to-peak amplitude (units 1/ms)."""
    t = np.asarray(t, float)
    x = np.asarray(x, float)
    return float(np.max(np.abs(np.gradient(x, t))) / (x.max() - x.min()))


def sharpness_model(a, c):
    """For the unipolar model A s / (s^2 + a^2) passing at speed c: max slope c A / a^2 over peak-to-peak A / a."""
    return c / a


def template_gain(x, template):
    """Least-squares gain of a far-field template in a recording."""
    x = np.asarray(x, float)
    f = np.asarray(template, float)
    return float(np.dot(x, f) / np.dot(f, f))


def remove_far_field(x, template):
    """Subtract the least-squares-scaled template; returns (residual, gain)."""
    g = template_gain(x, template)
    return np.asarray(x, float) - g * np.asarray(template, float), g


def gaussian_wave(t, t0, width, amplitude=1.0):
    """A smooth biphasic far-field deflection: the negative derivative of a Gaussian, peak-to-peak = amplitude."""
    t = np.asarray(t, float)
    z = (t - t0) / width
    return amplitude * np.sqrt(np.e) / 2 * (-z) * np.exp(-0.5 * z**2)


def blanked(t_annot, t_far, before, after):
    """True where an annotation falls in a blanking window [t_far - before, t_far + after]."""
    t_annot = np.asarray(t_annot, float)
    return (t_annot >= t_far - before) & (t_annot <= t_far + after)
