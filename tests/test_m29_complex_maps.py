"""m29 equation checks: fractionation, dominant frequency, organization, phase, singularities and
spatial wavelength.

Each test checks an equation in modules/m29-complex-maps.qmd on synthetic data with a known answer.
Filter bands, thresholds and model parameters here are test inputs, not recommended settings.
"""

import numpy as np
import pytest

from epml import complexmaps as cm
from epml import ionic

FS = 1000.0


def pulse_train(times, fs, duration, width=0.004, amp=1.0, shape="biphasic"):
    """Synthetic electrogram: one deflection per activation time."""
    t = np.arange(int(duration * fs)) / fs
    x = np.zeros_like(t)
    for t0 in times:
        u = (t - t0) / width
        if shape == "biphasic":
            x += -amp * u * np.exp(-0.5 * u**2)  # positive then negative: a downstroke at t0
        else:
            x += amp * np.exp(-0.5 * u**2)
    return t, x


def test_fractionation_index_and_threshold_dependence():
    """eq-m29-fi: the mean interval of deflections at known times is recovered; raising the
    detection threshold drops small deflections and lengthens the interval."""
    times = np.arange(0.1, 2.0, 0.05)
    amps = np.where(np.arange(times.size) % 2 == 0, 1.0, 0.3)
    t = np.arange(int(2.1 * FS)) / FS
    x = np.zeros_like(t)
    for t0, a in zip(times, amps):
        u = (t - t0) / 0.004
        x += -a * u * np.exp(-0.5 * u**2)
    assert cm.fractionation_index(times) == pytest.approx(0.05)
    low = cm.detect_deflections(x, FS, slope_threshold=10.0, refractory=0.02)
    high = cm.detect_deflections(x, FS, slope_threshold=120.0, refractory=0.02)
    assert cm.fractionation_index(low) == pytest.approx(0.05, abs=0.002)
    assert cm.fractionation_index(high) == pytest.approx(0.10, abs=0.002)


@pytest.mark.parametrize("cl", [0.150, 0.200, 0.250])
def test_dominant_frequency_recovers_activation_rate(cl):
    """eq-m29-df: after band-pass, rectification and low-pass, the largest peak of a regular train
    sits at 1 / CL, even though the raw biphasic deflections put most energy at higher harmonics."""
    times = np.arange(0.05, 8.0, cl)
    _, x = pulse_train(times, FS, 8.0)
    y = cm.preprocess_rectified(x, FS, band=(40.0, 250.0), lowpass=20.0)
    df = cm.dominant_frequency(y, FS, 2.0, 15.0)
    assert df == pytest.approx(1.0 / cl, abs=0.05)


def test_organization_index_regular_vs_irregular():
    """eq-m29-oi: a regular train concentrates power in its harmonics (OI near 1); random timing
    spreads it out (lower OI)."""
    rng = np.random.default_rng(0)
    regular = np.arange(0.05, 8.0, 0.2)
    irregular = np.cumsum(rng.uniform(0.08, 0.32, 60))
    irregular = irregular[irregular < 8.0]
    oi = []
    for times in (regular, irregular):
        _, x = pulse_train(times, FS, 8.0)
        y = cm.preprocess_rectified(x, FS, band=(40.0, 250.0), lowpass=20.0)
        oi.append(cm.organization_index(y, FS, 2.0, 15.0, halfwidth=0.5))
    assert oi[0] > 0.8
    assert oi[1] < oi[0] - 0.3


def test_hilbert_phase_of_a_cosine_is_linear():
    """eq-m29-hilbert: the analytic signal of cos(w t) is exp(i w t), so its phase advances linearly
    (checked away from the edges, where a finite record distorts it)."""
    t = np.arange(0, 2.0, 1 / FS)
    w = 2 * np.pi * 5.0
    ph = cm.analytic_phase(np.cos(w * t))
    inner = slice(100, -100)
    assert np.max(np.abs(cm.wrap(ph[inner] - w * t[inner]))) < 1e-2


def test_recomposition_gives_one_cycle_per_activation():
    """eq-m29-recomposition: unipolar-like signals with mixed R/S morphology and noise get exactly one
    phase cycle per activation after sinusoidal recomposition and the Hilbert transform."""
    rng = np.random.default_rng(1)
    cl = 0.18
    times = np.arange(0.2, 3.8, cl) + rng.normal(0, 0.005, 20)
    t = np.arange(int(4.0 * FS)) / FS
    x = np.zeros_like(t)
    for t0 in times:
        r = rng.uniform(0.2, 1.0)  # R-wave share varies from beat to beat
        u = (t - t0) / 0.006
        x += r * np.exp(-0.5 * (u + 1.2) ** 2) - (1 - r + 0.3) * np.exp(-0.5 * (u - 1.2) ** 2)
    x += rng.normal(0, 0.02, x.size)
    s = cm.sinusoidal_recomposition(x, FS, period=cl)
    ph = cm.analytic_phase(s)
    inner = (t > times[0] + cl / 2) & (t < times[-1] - cl / 2)
    unwrapped = np.unwrap(ph[inner])
    cycles = (unwrapped[-1] - unwrapped[0]) / (2 * np.pi)
    expected = np.sum((times > t[inner][0]) & (times < t[inner][-1]))
    assert abs(cycles) == pytest.approx(expected, abs=0.6)


def test_topological_charge_of_spirals_and_plane_waves():
    """eq-m29-charge: around a spiral tip the wrapped phase steps sum to +-2 pi (charge +-1), only in
    the square that contains the tip; a plane wave has charge 0 everywhere."""
    x, y = np.meshgrid(np.linspace(-1, 1, 41), np.linspace(-1, 1, 41))
    x0, y0 = 0.013, -0.027
    spiral = np.arctan2(y - y0, x - x0) - 1.3
    q = cm.plaquette_charges(spiral)
    assert q.sum() == 1 and np.count_nonzero(q) == 1
    assert cm.plaquette_charges(-spiral).sum() == -1
    plane = 7.0 * x - 2.0
    assert np.count_nonzero(cm.plaquette_charges(cm.wrap(plane))) == 0
    ring = cm.ring_indices(15, 15, 9)  # a larger ring around the tip gives the same charge
    assert cm.ring_charge([spiral[i, j] for i, j in ring]) == 1


def test_spatial_wavelength_on_a_paced_cable():
    """eq-m29-wavelength: in a cable paced 1:1 at cycle length CL, the distance between successive
    wavefronts equals conduction velocity times CL. Mitchell-Schaeffer kinetics with illustrative
    parameters (ms, mm), explicit time stepping."""
    params = (0.3, 6.0, 120.0, 50.0, 0.13)  # tau_in, tau_out, tau_open, tau_close, v_gate
    n, dx, dt, D, cl = 800, 0.05, 0.01, 0.01, 250.0  # cells, mm, ms, mm^2/ms, ms
    stims = np.arange(0.0, 1000.0, cl)
    _, ups, _ = ionic.ms_cable(n, dx, dt, 900.0, D, params, stims, stim_cells=10, stim_amp=1.0,
                               stim_dur=2.0, record_every=10.0)
    i1, i2, beat = 50, 450, 2  # a later beat, after restitution has settled
    assert len(ups[i1]) >= beat + 2  # 1:1 capture
    cv = (i2 - i1) * dx / (ups[i2][beat] - ups[i1][beat])  # mm/ms
    cycle = ups[i1][beat + 1] - ups[i1][beat]
    assert cycle == pytest.approx(cl, rel=0.01)
    # when the next beat reaches cell i1, how far ahead is this beat?
    t_star = ups[i1][beat + 1]
    reached = [i for i, u in enumerate(ups) if len(u) > beat]  # cells this beat has reached
    front = np.interp(t_star, np.array([ups[i][beat] for i in reached]), np.array(reached) * dx)
    assert front < reached[-1] * dx  # the front is inside the recorded part of the cable
    assert front - i1 * dx == pytest.approx(cm.spatial_wavelength(cv, cycle), rel=0.01)
