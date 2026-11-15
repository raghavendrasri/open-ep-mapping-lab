"""m15 · Patient safety: leakage through isolation, microshock current density, defibrillation protection,
RF-ablation filtering and demodulation. MIT License.

Units: SI (volts, amperes, ohms, farads, hertz, seconds, metres) unless a name says otherwise.
"""

import numpy as np

SWERDLOW_1999_UA = {             # minimum 60-Hz intracardiac currents in 40 patients (Swerdlow et al. 1999), microamperes
    "intermittent_capture": 20.0,
    "continuous_capture": 32.0,
    "ventricular_fibrillation": 49.0,
    "us_standard_single_fault": 50.0,
}


# ---- eq-m15-leakage: current through isolation capacitance ----------------------------------------------------

def capacitive_current(voltage, freq, capacitance):
    """RMS current through a capacitance driven by an RMS voltage: 2 pi f C V."""
    return 2.0 * np.pi * freq * capacitance * voltage


def total_leakage(currents, phases_deg=None):
    """Magnitude of the phasor sum of several leakage currents (in phase by default: the worst case on one mains)."""
    currents = np.asarray(currents, float)
    ph = np.zeros_like(currents) if phases_deg is None else np.radians(np.asarray(phases_deg, float))
    return float(np.abs(np.sum(currents * np.exp(1j * ph))))


def max_capacitance(limit, voltage, freq):
    """Largest isolation capacitance that keeps the capacitive current within `limit`: limit / (2 pi f V)."""
    return limit / (2.0 * np.pi * freq * voltage)


# ---- eq-m15-density: microshock against macroshock -------------------------------------------------------------

def hemisphere_density(current, radius):
    """Current density at the surface of a hemispherical electrode: I / (2 pi a^2)."""
    return current / (2.0 * np.pi * radius ** 2)


def density_ratio(radius, area):
    """How much more concentrated current is at a small intracardiac electrode than spread over a cross-section `area`."""
    return area / (2.0 * np.pi * radius ** 2)


def density_at(current, r):
    """Current density at distance r from a hemispherical electrode (r >= a): I / (2 pi r^2)."""
    return current / (2.0 * np.pi * r ** 2)


# ---- eq-m15-defib: series resistor and clamp ------------------------------------------------------------------

def clamp_current(v_in, v_clamp, r_series):
    """Current into a protection network (series resistor, then a clamp to v_clamp): (v_in - v_clamp)/R, or 0."""
    return np.maximum(np.abs(v_in) - v_clamp, 0.0) / r_series


def resistor_energy(v_in, v_clamp, r_series, duration):
    """Energy dissipated in the series resistor for a rectangular pulse: (v_in - v_clamp)^2 T / R."""
    return np.maximum(np.abs(v_in) - v_clamp, 0.0) ** 2 * duration / r_series


def diverted_fraction(v_in, v_clamp, r_series, v_body, r_body):
    """Fraction of the power delivered to the body (v_body^2 / r_body) taken by one protection network that sees v_in."""
    return v_in * clamp_current(v_in, v_clamp, r_series) / (v_body ** 2 / r_body)


# ---- eq-m15-rf-filter: attenuating RF before the amplifier ---------------------------------------------------

def lowpass_attenuation(freq, corner, order):
    """Butterworth magnitude 1/sqrt(1 + (f/fc)^(2n)); far above the corner it falls as (fc/f)^n."""
    return 1.0 / np.sqrt(1.0 + (freq / corner) ** (2 * order))


def order_needed(rf_amplitude, allowed, freq, corner):
    """Smallest Butterworth order that brings an RF amplitude below `allowed`."""
    n = 1
    while rf_amplitude * lowpass_attenuation(freq, corner, n) > allowed:
        n += 1
    return n


# ---- eq-m15-demod: a nonlinearity turns RF into a baseband shift -----------------------------------------------

def square_law(x, beta):
    """A weak second-order nonlinearity: y = x + beta x^2."""
    return x + beta * x * x


def demodulated_offset(amplitude, beta):
    """Baseband (time-average) shift that y = x + beta x^2 makes from A cos(wt): beta A^2 / 2."""
    return 0.5 * beta * amplitude ** 2
