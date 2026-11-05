"""m31 helpers: ventricular removal, cycle length and honest uncertainty for AF recordings.

Samples are indices into the signal; fs in Hz; times in s unless a name says ms.
"""

import numpy as np


def beat_matrix(x, qrs, pre, post):
    """Stack segments x[n_k - pre : n_k + post] for QRS detections that fit inside the record."""
    x = np.asarray(x, dtype=float)
    keep = [n for n in qrs if n - pre >= 0 and n + post <= x.size]
    return np.array([x[n - pre:n + post] for n in keep]), np.array(keep, dtype=int)


def qrs_template(x, qrs, pre, post):
    """eq-m31-template: average of the beats aligned on QRS detections."""
    beats, _ = beat_matrix(x, qrs, pre, post)
    return beats.mean(axis=0)


def average_beat_subtraction(x, qrs, pre, post):
    """eq-m31-abs: subtract the average beat at every detection; returns the residual signal."""
    x = np.asarray(x, dtype=float)
    tpl = qrs_template(x, qrs, pre, post)
    out = x.copy()
    _, keep = beat_matrix(x, qrs, pre, post)
    for n in keep:
        out[n - pre:n + post] -= tpl
    return out


def cl_from_df(df_hz):
    """eq-m31-cl: cycle length in ms implied by a dominant frequency in Hz."""
    return 1000.0 / np.asarray(df_hz, dtype=float)


def coefficient_of_variation(values):
    """eq-m31-cl: standard deviation over mean (sample standard deviation)."""
    v = np.asarray(values, dtype=float)
    return float(np.std(v, ddof=1) / np.mean(v))


def sliding_windows(x, fs, length, step):
    """Windows of `length` s every `step` s. Returns (start times in s, [n_windows, n] array)."""
    n, s = int(round(length * fs)), int(round(step * fs))
    starts = np.arange(0, len(x) - n + 1, s)
    return starts / fs, np.array([x[i:i + n] for i in starts])


def block_bootstrap_ci(values, statistic=np.mean, block=1, n_boot=2000, alpha=0.05, rng=None):
    """eq-m31-block-bootstrap: percentile interval from resampling whole blocks of consecutive values.

    block = 1 is the ordinary bootstrap. Blocks are non-overlapping; the last partial block is dropped.
    """
    rng = rng or np.random.default_rng()
    v = np.asarray(values, dtype=float)
    nb = len(v) // block
    blocks = v[:nb * block].reshape(nb, block)
    stats = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, nb, nb)
        stats[b] = statistic(blocks[pick].ravel())
    return tuple(np.quantile(stats, [alpha / 2, 1 - alpha / 2]))
