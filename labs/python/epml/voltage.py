"""m23 · Voltage mapping: amplitude, thresholds, dependence on wavefront direction.

Lengths in mm, potentials relative to the m03 source strength A unless stated, voltages in mV for the threshold
models. The electrogram model is the m03 arctangent front U(s) = A s / (s^2 + a^2), a = w + h. MIT License.
"""
from __future__ import annotations

import numpy as np
from scipy import integrate, special

from .electrograms import unipolar

# ---------------------------------------------------------------- amplitude (eq-m23-amplitude)


def unipolar_pp(a, A=1.0):
    """Peak-to-peak of the m03 unipolar signal: maximum A/(2a) at s = a, minimum -A/(2a) at s = -a."""
    return A / np.asarray(a, float)


def _grid(a, d):
    """A wide grid plus fine grids around each electrode, so peaks are resolved at any spacing."""
    L = 60.0 * (a + d)
    fine = [np.linspace(c - 12 * a, c + 12 * a, 6001) for c in (-0.5 * d, 0.0, 0.5 * d)]
    return np.unique(np.concatenate([np.linspace(-L, L, 12001)] + fine))


def bipolar_pp(a, d, theta=0.0, A=1.0):
    """Peak-to-peak of U(s + delta) - U(s - delta), delta = (d/2) cos(theta), found on a fine grid."""
    s = _grid(a, d)
    delta = 0.5 * d * np.cos(theta)
    b = unipolar(s + delta, a, A) - unipolar(s - delta, a, A)
    return float(b.max() - b.min())


def bipolar_pp_small(a, d, theta=0.0, A=1.0):
    """Small-spacing limit: d |cos theta| (max U' - min U') = (9/8) A d |cos theta| / a^2."""
    return 9.0 / 8.0 * A * d * np.abs(np.cos(theta)) / np.asarray(a, float) ** 2


# ---------------------------------------------------------------- direction (eq-m23-direction)


def below_fraction(q):
    """Fraction of uniformly distributed in-plane directions for which |cos theta| < q (q in [0, 1])."""
    return 2.0 / np.pi * np.arcsin(np.clip(q, 0.0, 1.0))


def pair_max_factor(theta):
    """Largest of two orthogonal bipoles, relative to an aligned one, in the small-spacing limit."""
    return np.maximum(np.abs(np.cos(theta)), np.abs(np.sin(theta)))


def pair_signals(a, d, theta, A=1.0):
    """Two orthogonal bipoles (x and y) sharing a center, as a plane front crosses at angle theta to x."""
    s = _grid(a, d)
    dx, dy = 0.5 * d * np.cos(theta), 0.5 * d * np.sin(theta)
    bx = unipolar(s + dx, a, A) - unipolar(s - dx, a, A)
    by = unipolar(s + dy, a, A) - unipolar(s - dy, a, A)
    return bx, by


def field_pp(a, d, theta, A=1.0, n_dir=360):
    """Largest peak-to-peak over all projections cos(w) Bx + sin(w) By: an orientation-free amplitude."""
    bx, by = pair_signals(a, d, theta, A)
    w = np.linspace(0, np.pi, n_dir, endpoint=False)
    proj = np.cos(w)[:, None] * bx[None, :] + np.sin(w)[:, None] * by[None, :]
    return float(np.max(proj.max(axis=1) - proj.min(axis=1)))


# ---------------------------------------------------------------- noise floor (eq-m23-noise)


def noise_pp_expected(n, sigma=1.0):
    """Expected peak-to-peak of n independent Gaussian samples: 2 sigma E[max of n standard normals]."""
    f = lambda x: x * n * np.exp(-0.5 * x * x) / np.sqrt(2 * np.pi) * special.ndtr(x) ** (n - 1)
    m, _ = integrate.quad(f, -10, 10, limit=200)
    return 2 * sigma * m


# ---------------------------------------------------------------- thresholds (eq-m23-threshold)


def lognormal_cdf(v, median, log_sd):
    """P(V < v) for a log-normal voltage with the given median (mV) and SD of ln V."""
    return special.ndtr((np.log(v) - np.log(median)) / log_sd)


def threshold_rates(cutoff, med_scar, med_normal, sd_scar, sd_normal):
    """Sensitivity (scar read below the cutoff) and specificity (normal read at or above it)."""
    sens = lognormal_cdf(cutoff, med_scar, sd_scar)
    spec = 1.0 - lognormal_cdf(cutoff, med_normal, sd_normal)
    return sens, spec


def youden_cutoff_equal_sd(med_scar, med_normal):
    """With equal log-SDs, sensitivity + specificity is largest at the geometric mean of the medians."""
    return float(np.sqrt(med_scar * med_normal))


def height_factor(a, extra_h, kind="bipolar"):
    """How much a voltage shrinks when the electrode lifts by extra_h (small-spacing bipolar ~ 1/a^2, unipolar ~ 1/a)."""
    p = 2 if kind == "bipolar" else 1
    return (np.asarray(a, float) / (np.asarray(a, float) + extra_h)) ** p
