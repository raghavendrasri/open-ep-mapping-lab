"""m19 · Motion and drift: a breathing model, respiratory gating, reference catheters and surrogates, drift
estimation, and averaging filters. MIT License.

Units: lengths in mm, times in s unless a name says ms.
"""

import numpy as np


# ---- eq-m19-breathing -------------------------------------------------------------------------------------------

def breathing(t, period, amplitude, n=2, z_exhale=0.0):
    """Asymmetric periodic breathing: z_exhale - amplitude cos^(2n)(pi t / period); flat near exhale for larger n."""
    return z_exhale - amplitude * np.cos(np.pi * np.asarray(t) / period) ** (2 * n)


# ---- eq-m19-gating ----------------------------------------------------------------------------------------------

def gating_duty_cycle(window, amplitude, n=2):
    """Fraction of time within `window` of end-exhale: 1 - (2/pi) arccos((window/amplitude)^(1/(2n)))."""
    return 1.0 - (2.0 / np.pi) * np.arccos(np.clip(window / amplitude, 0.0, 1.0) ** (1.0 / (2 * n)))


def gating_numeric(period, amplitude, window, n=2, samples=200000):
    """Duty cycle and RMS displacement from exhale of the accepted samples, by sampling one period."""
    t = np.linspace(0.0, period, samples, endpoint=False)
    z = breathing(t, period, amplitude, n)
    keep = -z <= window
    return float(np.mean(keep)), float(np.sqrt(np.mean(z[keep] ** 2)))


# ---- eq-m19-reference: subtracting a reference ----------------------------------------------------------------------

def difference_sd(sd_x, sd_r, rho):
    """SD of x - r for SDs sd_x, sd_r and correlation rho."""
    return np.sqrt(sd_x ** 2 + sd_r ** 2 - 2.0 * rho * sd_x * sd_r)


def reference_helps(sd_x, sd_r, rho):
    """Subtracting the reference lowers the SD exactly when rho > sd_r / (2 sd_x)."""
    return rho > sd_r / (2.0 * sd_x)


# ---- eq-m19-surrogate: regression on a surrogate --------------------------------------------------------------------

def fit_slope(surrogate, target):
    """Least-squares slope and intercept of target on surrogate."""
    s, y = np.asarray(surrogate, float), np.asarray(target, float)
    k = np.cov(s, y, bias=True)[0, 1] / np.var(s)
    return k, y.mean() - k * s.mean()


def residual_sd(sd_x, rho):
    """SD left after the best linear correction from a surrogate with correlation rho: sd_x sqrt(1 - rho^2)."""
    return sd_x * np.sqrt(1.0 - rho ** 2)


# ---- eq-m19-drift ---------------------------------------------------------------------------------------------------

def drift_fit(times, positions):
    """Least-squares drift rate (slope) and its standard error from revisits to a landmark."""
    t, x = np.asarray(times, float), np.asarray(positions, float)
    tc = t - t.mean()
    slope = np.sum(tc * (x - x.mean())) / np.sum(tc ** 2)
    resid = x - x.mean() - slope * tc
    sigma = np.sqrt(np.sum(resid ** 2) / (len(t) - 2))
    return slope, sigma / np.sqrt(np.sum(tc ** 2))


def drift_se(times, sigma):
    """Standard error of the slope for measurement noise sigma: sigma / sqrt(sum (t - tbar)^2)."""
    t = np.asarray(times, float)
    return sigma / np.sqrt(np.sum((t - t.mean()) ** 2))


# ---- eq-m19-average -------------------------------------------------------------------------------------------------

def moving_average_gain(freq, width):
    """Amplitude gain of a boxcar average of duration `width` at frequency f: |sin(pi f W)/(pi f W)|; delay W/2."""
    x = np.pi * np.asarray(freq, float) * width
    return np.abs(np.sinc(x / np.pi))


def moving_average(x, n):
    """Causal boxcar average over n samples (the first n-1 outputs average what is available)."""
    c = np.cumsum(np.insert(np.asarray(x, float), 0, 0.0))
    out = np.empty(len(x))
    for i in range(len(x)):
        lo = max(0, i + 1 - n)
        out[i] = (c[i + 1] - c[lo]) / (i + 1 - lo)
    return out
