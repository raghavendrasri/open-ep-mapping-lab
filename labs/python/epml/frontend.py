"""m14 · Biopotential front ends: differential amplifiers, CMRR, electrode imbalance, driven right leg, noise,
the Wilson central terminal and analog-to-digital conversion. MIT License.

Units: SI (volts, ohms, amperes, hertz, kelvin) unless a name says otherwise. Impedances may be complex.
"""

import numpy as np

K_B = 1.380649e-23          # Boltzmann constant, J/K (exact in the SI; CODATA 2018)
T_BODY = 310.15             # 37 degrees C in kelvin


# ---- eq-m14-cmrr --------------------------------------------------------------------------------------------

def split_modes(v_plus, v_minus):
    """Differential and common-mode parts: v_d = v+ - v-, v_cm = (v+ + v-)/2."""
    return v_plus - v_minus, 0.5 * (v_plus + v_minus)


def to_db(ratio):
    """20 log10 |ratio|."""
    return 20.0 * np.log10(np.abs(ratio))


# ---- eq-m14-diffamp: the four-resistor difference amplifier ----------------------------------------------------

def diff_amp(v_minus, v_plus, r1, r2, r3, r4):
    """Ideal op amp; v- through r1 to the inverting input with feedback r2; v+ through r3 to the
    noninverting input with r4 to ground."""
    return v_plus * (r4 / (r3 + r4)) * (1.0 + r2 / r1) - v_minus * (r2 / r1)


def diff_amp_gains(r1, r2, r3, r4):
    """Differential and common-mode gains of the difference amplifier."""
    a_plus = (r4 / (r3 + r4)) * (1.0 + r2 / r1)
    a_minus = -r2 / r1
    return 0.5 * (a_plus - a_minus), a_plus + a_minus      # v+ = v_cm + v_d/2, v- = v_cm - v_d/2


def worst_case_cmrr(gain, tol):
    """Worst-case CMRR of a difference amplifier of gain r2/r1 with resistor tolerance tol: (1 + gain)/(4 tol)."""
    return (1.0 + gain) / (4.0 * tol)


def random_cmrr(gain, tol, n, rng):
    """CMRR of n difference amplifiers whose resistors are uniform within +/- tol."""
    r1, r3 = (1.0 + tol * rng.uniform(-1, 1, (2, n)))
    r2, r4 = gain * (1.0 + tol * rng.uniform(-1, 1, (2, n)))
    ad, acm = diff_amp_gains(r1, r2, r3, r4)
    return np.abs(ad / acm)


# ---- eq-m14-inamp: the three-op-amp instrumentation amplifier ---------------------------------------------------

def inamp_first_stage(v_minus, v_plus, r, r_gain):
    """Outputs of the input stage: the difference gains 1 + 2r/r_gain, the common mode passes at unity."""
    i = (v_plus - v_minus) / r_gain
    return v_minus - r * i, v_plus + r * i


def inamp(v_minus, v_plus, r, r_gain, r1, r2, r3, r4):
    a, b = inamp_first_stage(v_minus, v_plus, r, r_gain)
    return diff_amp(a, b, r1, r2, r3, r4)


def inamp_cmrr(r, r_gain, r1, r2, r3, r4):
    """CMRR of the whole instrumentation amplifier, from its response to unit differential and common-mode inputs."""
    ad = inamp(-0.5, 0.5, r, r_gain, r1, r2, r3, r4)
    acm = inamp(1.0, 1.0, r, r_gain, r1, r2, r3, r4)
    return abs(ad / acm)


# ---- eq-m14-imbalance: electrode impedance imbalance ------------------------------------------------------------

def imbalance_error(v_cm, z1, z2, z_cm):
    """Differential voltage created from v_cm by electrode impedances z1, z2 into input impedances z_cm to ground."""
    return v_cm * (z_cm / (z_cm + z2) - z_cm / (z_cm + z1))


def imbalance_cmrr(dz, z_cm):
    """Equivalent CMRR of an electrode impedance mismatch dz: |z_cm / dz| (for |z| << |z_cm|)."""
    return np.abs(z_cm / dz)


def combined_cmrr(*cmrrs):
    """Worst case: common-mode-to-differential conversions add, so 1/CMRR values add."""
    return 1.0 / sum(1.0 / np.asarray(c, float) for c in cmrrs)


# ---- eq-m14-drl: driven right leg -------------------------------------------------------------------------------

def body_common_mode(i_d, z_rl, loop_gain=0.0):
    """Common-mode voltage from displacement current i_d through the right-leg electrode: i_d z_rl / (1 + G)."""
    return i_d * z_rl / (1.0 + loop_gain)


# ---- eq-m14-noise: input noise ------------------------------------------------------------------------------------

def thermal_density(r, temp=T_BODY):
    """Thermal (Nyquist) noise voltage density of a resistance, V/sqrt(Hz): sqrt(4 k T R)."""
    return np.sqrt(4.0 * K_B * temp * np.real(r))


def total_density(r_source, e_n, i_n, temp=T_BODY):
    """Input-referred noise density: thermal, amplifier voltage noise and current noise through the source, in quadrature."""
    return np.sqrt(thermal_density(r_source, temp) ** 2 + e_n ** 2 + (i_n * r_source) ** 2)


def rms_noise(density, bandwidth):
    """RMS noise over a band, for a white density."""
    return density * np.sqrt(bandwidth)


def optimal_source_resistance(e_n, i_n):
    """Source resistance that minimizes the noise factor: e_n / i_n."""
    return e_n / i_n


def noise_factor(r_source, e_n, i_n, temp=T_BODY):
    """Total noise power over the source's own thermal noise power."""
    return total_density(r_source, e_n, i_n, temp) ** 2 / thermal_density(r_source, temp) ** 2


# ---- eq-m14-wct: Wilson central terminal with electrode impedances -----------------------------------------------

def wct(potentials, z_electrodes, r_wilson):
    """Central terminal of three limb electrodes joined through resistors r_wilson, with electrode impedances z."""
    w = 1.0 / (r_wilson + np.asarray(z_electrodes, complex))
    return np.real_if_close(np.sum(w * np.asarray(potentials)) / np.sum(w))


# ---- eq-m14-oversampling: quantization and averaging ------------------------------------------------------------

def input_lsb(full_scale, bits, gain=1.0):
    """Input-referred step of an N-bit converter after a gain: full_scale / (gain 2^N)."""
    return full_scale / (gain * 2.0 ** bits)


def bits_needed(span, resolution):
    """Bits to span `span` with steps of `resolution`: ceil(log2(span / resolution))."""
    return int(np.ceil(np.log2(span / resolution)))


def oversampling_gain_db(m):
    """SNR gain from averaging m samples of white noise: 10 log10 m dB (half a bit per doubling)."""
    return 10.0 * np.log10(m)


def average_blocks(x, m):
    """Average consecutive blocks of m samples (decimate by m)."""
    n = (len(x) // m) * m
    return x[:n].reshape(-1, m).mean(axis=1)
