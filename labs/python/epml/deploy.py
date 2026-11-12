"""m47 · Data and deployment engineering: units in file headers, checksums and manifests, labels from
several labellers, re-identification risk, integer quantization and model cards. MIT License.

Every numeric default here is illustrative unless a docstring names a source."""
import hashlib
import json
from math import comb
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- units (eq-m47-adu)


def adu_to_physical(d, gain, baseline=0):
    """eq-m47-adu: physical value v = (d - b) / g for stored integers d (analog-to-digital converter
    units, adu), gain g in adu per physical unit and baseline b in adu (WFDB header fields)."""
    return (np.asarray(d, float) - baseline) / gain


def physical_to_adu(v, gain, baseline=0, bits=16):
    """The inverse of eq-m47-adu, rounded to integers and clipped to a signed `bits`-bit range."""
    q = np.round(np.asarray(v, float) * gain + baseline)
    return np.clip(q, -(2 ** (bits - 1)), 2 ** (bits - 1) - 1).astype(np.int64)


def write_wfdb(signal_mv, fs, gain, folder, name="rec", baseline=0, sig_name="I"):
    """Write a one-lead WFDB record (format 16) from a signal in mV with the given gain and baseline.
    Returns the header path."""
    import wfdb

    d = physical_to_adu(signal_mv, gain, baseline)[:, None]
    wfdb.wrsamp(name, fs=fs, units=["mV"], sig_name=[sig_name], d_signal=d, fmt=["16"], adc_gain=[float(gain)],
                baseline=[int(baseline)], write_dir=str(folder))
    return Path(folder) / f"{name}.hea"


def edit_header(hea_path, gain=None, fs=None):
    """Change the gain of the first signal or the sampling frequency in a WFDB header, as a wrong
    export setting would. The signal file is not touched."""
    lines = Path(hea_path).read_text().splitlines()
    first = lines[0].split()
    if fs is not None:
        first[2] = f"{fs:g}"
        lines[0] = " ".join(first)
    if gain is not None:
        f = lines[1].split()
        rest = f[2][f[2].index("("):] if "(" in f[2] else f[2][f[2].index("/"):] if "/" in f[2] else ""
        f[2] = f"{gain:g}{rest}"
        lines[1] = " ".join(f)
    Path(hea_path).write_text("\n".join(lines) + "\n")


def read_wfdb(hea_path):
    """(signal in physical units of the first lead, sampling frequency, gain, units) as the header says."""
    import wfdb

    rec = wfdb.rdrecord(str(Path(hea_path).with_suffix("")))
    return rec.p_signal[:, 0], float(rec.fs), float(rec.adc_gain[0]), rec.units[0]


def record_stats(x, fs, window_s=0.05):
    """Median R amplitude (largest absolute value within window_s of each detected beat, in the
    signal's units) and median heart rate (beats per minute) of one recording."""
    from .aiecg import detect_r_peaks

    x = np.asarray(x, float)
    pk = detect_r_peaks(x, fs)
    if len(pk) < 2:
        return np.nan, np.nan
    w = max(1, int(window_s * fs))
    amp = np.median([np.max(np.abs(x[max(0, i - w): i + w + 1])) for i in pk])
    return float(amp), float(60.0 / np.median(np.diff(pk) / fs))


class Audit:
    """Plausibility ranges learned from the training recordings: the q-th and (100 - q)-th percentiles
    of the median R amplitude and heart rate. A new recording outside a range is flagged. The ranges
    come from the data, not from physiological limits."""

    def __init__(self, signals, fs, q=1.0):
        stats = np.array([record_stats(x, fs) for x in signals])
        stats = stats[np.all(np.isfinite(stats), axis=1)]
        self.amp = tuple(np.percentile(stats[:, 0], [q, 100 - q]))
        self.hr = tuple(np.percentile(stats[:, 1], [q, 100 - q]))

    def check(self, x, fs):
        amp, hr = record_stats(x, fs)
        return {"amp": amp, "hr": hr,
                "amp_ok": bool(self.amp[0] <= amp <= self.amp[1]),
                "hr_ok": bool(self.hr[0] <= hr <= self.hr[1])}


# ---------------------------------------------------------------- versions


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def manifest(folder, pattern="*"):
    """{relative path: SHA-256} for every file under folder that matches pattern, sorted by path."""
    folder = Path(folder)
    return {str(p.relative_to(folder)): sha256_file(p) for p in sorted(folder.rglob(pattern)) if p.is_file()}


def manifest_id(man):
    """One identifier for a whole dataset version: the SHA-256 of the manifest written canonically."""
    return hashlib.sha256(json.dumps(man, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def diff_manifest(old, new):
    return {"changed": sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
            "added": sorted(new.keys() - old.keys()),
            "removed": sorted(old.keys() - new.keys())}


# ---------------------------------------------------------------- labels (eq-m47-majority)


def majority_accuracy(p, m):
    """eq-m47-majority: probability that the majority of m labellers (m odd) is right when each is
    right independently with probability p (binary labels)."""
    if m % 2 == 0:
        raise ValueError("m must be odd")
    return sum(comb(m, j) * p**j * (1 - p) ** (m - j) for j in range(m // 2 + 1, m + 1))


def simulate_labels(y, m, p, rng, hard_share=0.0, p_hard=0.5):
    """Binary labels from m labellers. A shared share of 'hard' recordings (the same for everyone)
    is labelled correctly with probability p_hard, the rest with probability p, independently
    given the recording. Returns (labels of shape (n, m), hard mask)."""
    y = np.asarray(y, int)
    hard = rng.random(len(y)) < hard_share
    p_right = np.where(hard, p_hard, p)[:, None]
    right = rng.random((len(y), m)) < p_right
    return np.where(right, y[:, None], 1 - y[:, None]), hard


def majority_vote(L):
    L = np.asarray(L)
    return (L.sum(axis=1) * 2 > L.shape[1]).astype(int)


# ---------------------------------------------------------------- re-identification risk (eq-m47-risk)


def synthetic_registry(n, rng):
    """A synthetic procedure registry (no real people): record code, age (years), sex code (0/1),
    region (one of 30 codes, unevenly used), procedure date (day of one year) and device model.
    All distributions are illustrative."""
    region_w = 1.0 / np.arange(1, 31)
    return {
        "record": np.array([f"R{i:05d}" for i in range(n)]),
        "age": np.clip(np.round(rng.normal(65, 12, n)), 18, 95).astype(int),
        "sex": rng.integers(0, 2, n),
        "region": rng.choice(30, n, p=region_w / region_w.sum()),
        "day": rng.integers(0, 365, n),
        "device": rng.choice(3, n, p=[0.6, 0.3, 0.1]),
    }


def generalize(table, age_width=1, date="day", keep_region=True, age_bounds=None):
    """Coarsen quasi-identifiers: age into bins of age_width years (after top- and bottom-coding to
    age_bounds = (low, high), if given), the date to its day, month (30-day block) or nothing, and
    optionally drop the region. Direct identifiers are dropped."""
    age = np.asarray(table["age"])
    if age_bounds is not None:
        age = np.clip(age, *age_bounds)
    out = {"age": (age // age_width) * age_width, "sex": table["sex"], "device": table["device"]}
    if keep_region:
        out["region"] = table["region"]
    if date == "day":
        out["date"] = table["day"]
    elif date == "month":
        out["date"] = table["day"] // 30
    return out


def class_sizes(table, columns):
    """For each record, the size f_i of its equivalence class: records with the same values in
    `columns` (the quasi-identifiers)."""
    keys = list(zip(*(np.asarray(table[c]) for c in columns)))
    counts = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    return np.array([counts[k] for k in keys])


def reid_risk(sizes):
    """eq-m47-risk: an attacker who knows a person is in the data and knows their quasi-identifiers,
    and picks one matching record at random, is right with probability 1/f_i. Returns the largest
    risk (1/min f), the average risk (mean of 1/f_i, which equals classes/records) and the share of
    unique records."""
    s = np.asarray(sizes, float)
    return {"max": float(1 / s.min()), "average": float(np.mean(1 / s)), "unique": float(np.mean(s == 1)),
            "k": int(s.min())}


# ---------------------------------------------------------------- quantization (eq-m47-affine, eq-m47-qnoise)


def qparams(rmin, rmax, bits=8, signed=False):
    """eq-m47-affine: scale S and zero point Z so that r = S (q - Z) maps the integer range onto
    [rmin, rmax], widened if needed to contain 0 so that zero is exact (Jacob et al. 2018)."""
    rmin, rmax = min(float(rmin), 0.0), max(float(rmax), 0.0)
    qmin, qmax = (-(2 ** (bits - 1)), 2 ** (bits - 1) - 1) if signed else (0, 2**bits - 1)
    S = (rmax - rmin) / (qmax - qmin) or 1.0
    Z = int(np.clip(round(qmin - rmin / S), qmin, qmax))
    return S, Z, qmin, qmax


def quantize(r, S, Z, qmin, qmax):
    return np.clip(np.round(np.asarray(r, float) / S) + Z, qmin, qmax).astype(np.int64)


def dequantize(q, S, Z):
    return S * (np.asarray(q, float) - Z)


def fake_quant(r, bits=8, rmin=None, rmax=None, signed=False):
    """Quantize and dequantize; the range defaults to the data's own min and max."""
    r = np.asarray(r, float)
    S, Z, qmin, qmax = qparams(r.min() if rmin is None else rmin, r.max() if rmax is None else rmax, bits, signed)
    return dequantize(quantize(r, S, Z, qmin, qmax), S, Z), S


def sqnr_db(x, xq):
    """Signal-to-quantization-noise ratio in dB: 10 log10(mean x^2 / mean (x - xq)^2)."""
    x, xq = np.asarray(x, float), np.asarray(xq, float)
    return float(10 * np.log10(np.mean(x**2) / np.mean((x - xq) ** 2)))


def predicted_sqnr_db(x, S):
    """eq-m47-qnoise: rounding error uniform on [-S/2, S/2] has variance S^2 / 12."""
    return float(10 * np.log10(np.mean(np.asarray(x, float) ** 2) / (S**2 / 12)))


def quantize_mlp(mlp, bits=8, per_channel=False):
    """A copy of an epml.trust.TinyMLP whose weights (W and v) are quantized symmetrically (Z = 0),
    with one scale per tensor or one per hidden unit (row of W). Biases stay in floating point."""
    import copy

    q = copy.deepcopy(mlp)
    qmax = 2 ** (bits - 1) - 1

    def sym(w, axis=None):
        amax = np.max(np.abs(w), axis=axis, keepdims=axis is not None)
        S = np.where(amax > 0, amax / qmax, 1.0)
        return np.clip(np.round(w / S), -qmax, qmax) * S

    q.W = sym(mlp.W, axis=1 if per_channel else None)
    q.v = sym(mlp.v)
    return q


def model_bytes(mlp, bits=32):
    """Storage for the weights and biases at the given bit width (biases kept at 32 bits)."""
    n_w = mlp.W.size + mlp.v.size
    n_b = mlp.b.size + 1
    return (n_w * bits + n_b * 32) // 8


# ---------------------------------------------------------------- model card

CARD_SECTIONS = ["Model details", "Intended use", "Out of scope", "Training data", "Evaluation data", "Metrics",
                 "Metrics by group", "Limitations", "Version and checksums"]


def model_card(fields):
    """A Markdown model card in the spirit of Mitchell et al. (2019); the section list is this course's
    choice. fields: {section: text}. Raises ValueError if a section is missing or empty."""
    missing = [s for s in CARD_SECTIONS if not str(fields.get(s, "")).strip()]
    if missing:
        raise ValueError(f"model card is missing: {', '.join(missing)}")
    return "\n\n".join(f"## {s}\n\n{str(fields[s]).strip()}" for s in CARD_SECTIONS) + "\n"


def missing_sections(markdown):
    return [s for s in CARD_SECTIONS if f"## {s}\n" not in markdown]
