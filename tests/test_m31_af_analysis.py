"""m31 equation checks: beat template, average-beat subtraction, template noise, cycle length and
block bootstrap.

Each test checks an equation in modules/m31-capstone-af-electrograms.qmd on synthetic signals with a
known answer. No real recordings are needed for these tests; the code lab uses iafdb.
"""

import numpy as np
import pytest
import sympy as sp

from epml import afanalysis as af
from epml import complexmaps as cm

FS = 1000.0


def synthetic_record(n_beats, rng, af_amp=0.2, noise=0.02):
    """Atrial activity (a 6 Hz wave with slowly varying phase) plus a fixed ventricular complex at
    irregular RR intervals. Returns (x, atrial part, ventricular part, qrs indices, template)."""
    rr = rng.uniform(0.7, 1.2, n_beats)  # longer than the 600-ms template window: no overlap
    qrs = (np.cumsum(rr) * FS).astype(int) + 300
    n = qrs[-1] + 700
    t = np.arange(n) / FS
    atrial = af_amp * np.sin(2 * np.pi * 6.0 * t + 0.8 * np.sin(2 * np.pi * 0.13 * t))
    u = np.arange(-200, 400) / FS
    tpl = 1.0 * np.exp(-0.5 * (u / 0.012) ** 2) - 0.25 * np.exp(-0.5 * ((u - 0.03) / 0.015) ** 2) \
        + 0.3 * np.exp(-0.5 * ((u - 0.25) / 0.05) ** 2)
    vent = np.zeros(n)
    for q in qrs:
        vent[q - 200:q + 400] += tpl
    x = atrial + vent + rng.normal(0, noise, n)
    return x, atrial, vent, qrs, tpl


def test_template_recovers_the_repeated_complex():
    """eq-m31-template: averaging beats aligned on QRS recovers the ventricular complex; what is not
    time-locked to the QRS (atrial activity, noise) averages towards zero."""
    rng = np.random.default_rng(0)
    x, _, _, qrs, tpl = synthetic_record(200, rng)
    est = af.qrs_template(x, qrs, 200, 400)
    assert np.max(np.abs(est - tpl)) < 0.1 * np.max(np.abs(tpl))


def test_average_beat_subtraction_residual_falls_with_more_beats():
    """eq-m31-abs: subtracting the template leaves the atrial activity; averaged over records, the
    residual ventricular error shrinks as more beats go into the template."""
    counts = (5, 20, 160)
    errs = np.zeros(len(counts))
    for seed in range(8):
        rng = np.random.default_rng(seed)
        x, atrial, _, qrs, _ = synthetic_record(200, rng)
        for k, nb in enumerate(counts):
            tpl = af.qrs_template(x, qrs[:nb], 200, 400)
            out = x.copy()
            for q in qrs:
                out[q - 200:q + 400] -= tpl
            errs[k] += np.sqrt(np.mean((out - atrial) ** 2)) / 8
    assert errs[0] > errs[1] > errs[2]
    rng = np.random.default_rng(0)
    x, atrial, _, qrs, _ = synthetic_record(200, rng)
    full = af.average_beat_subtraction(x, qrs, 200, 400)
    tpl = af.qrs_template(x, qrs, 200, 400)
    manual = x.copy()
    for q in qrs:
        manual[q - 200:q + 400] -= tpl
    assert full == pytest.approx(manual)


def test_template_noise_variance():
    """eq-m31-template-noise: the mean of N independent values with variance sigma^2 has variance
    sigma^2 / N (SymPy), and a Monte Carlo template agrees."""
    N, s2 = sp.symbols("N sigma2", positive=True)
    # Var(sum X_k / N) = N * s2 / N^2 for independent X_k
    assert sp.simplify(N * s2 / N**2 - s2 / N) == 0
    rng = np.random.default_rng(2)
    for nb in (4, 16, 64):
        samples = rng.normal(0, 1.0, (4000, nb)).mean(axis=1)
        assert np.var(samples) == pytest.approx(1.0 / nb, rel=0.08)


def test_cycle_length_from_df_and_window_variability():
    """eq-m31-cl: a train with cycle length 180 ms has DF 1000/180 Hz, so CL_DF = 180 ms; DF is
    nearly constant across windows of a stationary signal and varies more when the rate drifts."""
    t_end, cl = 30.0, 0.180
    times = np.arange(0.05, t_end, cl)
    t = np.arange(int(t_end * FS)) / FS
    x = np.zeros_like(t)
    for t0 in times:
        u = (t - t0) / 0.004
        x += -u * np.exp(-0.5 * u**2)
    y = cm.preprocess_rectified(x, FS, band=(40.0, 250.0), lowpass=20.0)
    _, wins = af.sliding_windows(y, FS, length=4.0, step=2.0)
    dfs = np.array([cm.dominant_frequency(w, FS, 2.0, 15.0) for w in wins])
    assert af.cl_from_df(np.median(dfs)) == pytest.approx(180.0, rel=0.02)
    assert af.coefficient_of_variation(dfs) < 0.01
    drifting = np.cumsum(np.linspace(0.15, 0.22, 200))
    drifting = drifting[drifting < t_end]
    x2 = np.zeros_like(t)
    for t0 in drifting:
        u = (t - t0) / 0.004
        x2 += -u * np.exp(-0.5 * u**2)
    y2 = cm.preprocess_rectified(x2, FS, band=(40.0, 250.0), lowpass=20.0)
    _, w2 = af.sliding_windows(y2, FS, length=4.0, step=2.0)
    d2 = np.array([cm.dominant_frequency(w, FS, 2.0, 15.0) for w in w2])
    assert af.coefficient_of_variation(d2) > 5 * af.coefficient_of_variation(dfs)


def test_block_bootstrap_covers_better_on_correlated_windows():
    """eq-m31-block-bootstrap: for strongly correlated window values (AR(1), phi = 0.9), resampling
    single values gives intervals that miss the true mean far more often than the nominal 5 %;
    resampling whole blocks comes much closer."""
    rng = np.random.default_rng(3)
    n, phi, reps = 400, 0.9, 150
    hit_single = hit_block = 0
    for _ in range(reps):
        e = rng.normal(0, 1, n)
        v = np.empty(n)
        v[0] = e[0] / np.sqrt(1 - phi**2)
        for i in range(1, n):
            v[i] = phi * v[i - 1] + e[i]
        lo, hi = af.block_bootstrap_ci(v, block=1, n_boot=400, rng=rng)
        hit_single += lo <= 0 <= hi
        lo, hi = af.block_bootstrap_ci(v, block=40, n_boot=400, rng=rng)
        hit_block += lo <= 0 <= hi
    assert hit_single / reps < 0.6
    assert hit_block / reps > 0.75 and hit_block > 1.3 * hit_single
