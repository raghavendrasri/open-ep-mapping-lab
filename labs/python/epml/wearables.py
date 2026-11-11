"""m38 · Wearables and implantable monitors: pulse timing, windowed detection and alert workload.

Each function implements a numbered equation of module m38 and is checked in tests/test_m38_wearables.py.
The synthetic PPG is an approximate model for teaching: one smooth pulse per heartbeat, arriving a variable
delay after the R peak. Its shape, delays and noise are illustrative values, not physiological references.
"""

import numpy as np

# ---------------------------------------------------------------------------------------------
# Pulse timing (eq-m38-hr, eq-m38-ibi, eq-m38-ibi-var)


def heart_rate(intervals_s):
    """eq-m38-hr: heart rate in beats per minute from beat-to-beat intervals in seconds."""
    return 60.0 / np.mean(intervals_s)


def ppg_intervals(rr, delays):
    """eq-m38-ibi: pulse-to-pulse intervals when beat i's pulse arrives delays[i] after its R peak.
    rr has n intervals, delays has n + 1 values (one per beat)."""
    rr = np.asarray(rr, float)
    d = np.asarray(delays, float)
    return rr + d[1:] - d[:-1]


def ppg_interval_variance(var_rr, var_delay, rho_delay=0.0):
    """eq-m38-ibi-var: variance of pulse intervals when delays are stationary, independent of the RR
    intervals, with variance var_delay and lag-one autocorrelation rho_delay."""
    return var_rr + 2.0 * var_delay * (1.0 - rho_delay)


def ar1_delays(n, mean_s, sd_s, rho, rng):
    """Stationary first-order autoregressive delays with the given mean, SD and lag-one correlation."""
    d = np.empty(n)
    d[0] = rng.normal(0, sd_s)
    e = rng.normal(0, sd_s * np.sqrt(1 - rho**2), size=n)
    for i in range(1, n):
        d[i] = rho * d[i - 1] + e[i]
    return mean_s + d


def pulse(t, width_s=0.12):
    """One illustrative PPG pulse starting at t = 0: a fast rise and slower fall (arbitrary units)."""
    t = np.asarray(t, float)
    out = np.zeros_like(t)
    on = t > 0
    out[on] = (t[on] / width_s) * np.exp(1 - t[on] / width_s)
    return out


def synth_ppg(r_times_s, delays_s, fs=25.0, duration_s=None, noise=0.02, motion=None, rng=None):
    """A synthetic PPG: a pulse delays_s[i] after each R peak, plus white noise and optional motion
    bursts given as (start_s, length_s, amplitude). Returns (signal, pulse onset times in s)."""
    rng = np.random.default_rng() if rng is None else rng
    r = np.asarray(r_times_s, float)
    on = r + np.asarray(delays_s, float)
    duration_s = duration_s or (on[-1] + 1.0)
    t = np.arange(int(duration_s * fs)) / fs
    x = np.zeros_like(t)
    for o in on:
        x += pulse(t - o)
    x += noise * rng.normal(size=t.size)
    for start, length, amp in motion or []:
        m = (t >= start) & (t < start + length)
        x[m] += amp * np.cumsum(rng.normal(size=m.sum())) / np.sqrt(max(1, m.sum()))
    return x, on


# ---------------------------------------------------------------------------------------------
# Windowed detection with a consecutive-window rule (eq-m38-runs, eq-m38-detect)


def window_cv(times_s, window_s, min_beats=10):
    """Coefficient of variation of the intervals inside consecutive, non-overlapping windows.
    times_s are beat (or pulse) times. Windows with fewer than min_beats beats give NaN."""
    times_s = np.asarray(times_s, float)
    n = int(np.floor((times_s[-1] - times_s[0]) / window_s))
    out = np.full(n, np.nan)
    edges = times_s[0] + window_s * np.arange(n + 1)
    idx = np.searchsorted(times_s, edges)
    for w in range(n):
        tw = times_s[idx[w]: idx[w + 1]]
        if tw.size >= min_beats:
            iv = np.diff(tw)
            out[w] = iv.std(ddof=1) / iv.mean()
    return out


def runs_at_least(flags, k):
    """Number of maximal runs of at least k consecutive True values: one notification per run."""
    count, run = 0, 0
    for f in np.asarray(flags, bool):
        run = run + 1 if f else 0
        if run == k:
            count += 1
    return count


def expected_runs(n, q, k):
    """eq-m38-runs: expected number of runs of >= k positives among n independent windows, each
    positive with probability q."""
    if n < k:
        return 0.0
    return q**k * (1.0 + (n - k) * (1.0 - q))


def detection_probability(L, p, k):
    """eq-m38-detect: probability that an episode lasting L windows, each flagged independently with
    probability p, contains a run of >= k flagged windows. a_m = P(no such run in m windows)."""
    a = np.ones(L + 1)
    for m in range(k, L + 1):
        a[m] = sum(p**j * (1 - p) * a[m - j - 1] for j in range(k))
    return 1.0 - a[L]


# ---------------------------------------------------------------------------------------------
# Alert workload and triage (eq-m38-workload, eq-m38-filter)


def alert_workload(n_patients, alerts_per_patient_day, ppv, minutes_per_alert):
    """eq-m38-workload: alerts, false alerts and review hours per day for a clinic."""
    alerts = n_patients * alerts_per_patient_day
    return {"alerts": alerts, "false": alerts * (1 - ppv), "true": alerts * ppv,
            "hours": alerts * minutes_per_alert / 60.0}


def filtered_alerts(ppv, keep_true, remove_false):
    """eq-m38-filter: a triage filter that keeps a share keep_true of true alerts and removes a share
    remove_false of false ones. Returns (new PPV, share of alerts still shown, share of true alerts lost)."""
    shown = keep_true * ppv + (1 - remove_false) * (1 - ppv)
    return keep_true * ppv / shown, shown, 1 - keep_true


# ---------------------------------------------------------------------------------------------
# A synthetic day of rhythm with AF episodes, for the windowed detector


def rhythm_day(hours=24.0, hr_bpm=70.0, af_episodes=(), rng=None, cv_sinus=0.03, cv_af=0.20):
    """Beat times (s) over `hours`, sinus outside the AF episodes [(start_h, length_h), ...] and AF inside.
    Variability values are illustrative. Returns (beat times, boolean array: beat is in AF)."""
    rng = np.random.default_rng() if rng is None else rng
    end = hours * 3600.0
    mean = 60.0 / hr_bpm
    eps = [(s * 3600.0, (s + l) * 3600.0) for s, l in af_episodes]
    t, times, in_af = 0.0, [], []
    k = 1.0 / cv_af**2
    while t < end:
        af = any(a <= t < b for a, b in eps)
        rr = rng.gamma(k, mean / k) if af else mean * (1 + cv_sinus * rng.normal())
        t += max(rr, 0.25)
        times.append(t)
        in_af.append(af)
    return np.array(times), np.array(in_af)
