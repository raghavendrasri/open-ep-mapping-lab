"""m37 · AI on the surface ECG: the pieces of an ECG classifier, built from scratch.

Every function here implements one numbered equation of module m37 and is checked in
tests/test_m37_aiecg.py. The synthetic ECG is an approximate model for teaching: a sum of Gaussian
waves per beat, as in the morphology part of McSharry et al. (2003). Its wave sizes, times and
widths are illustrative values chosen to look like a lead-I ECG, not physiological reference values.
"""

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

# ---------------------------------------------------------------------------------------------
# Outputs and loss (eq-m37-softmax, eq-m37-ce-grad, eq-m37-logistic)


def softmax(z):
    """eq-m37-softmax: class probabilities from scores z (last axis), computed stably."""
    z = np.asarray(z, float)
    e = np.exp(z - z.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def cross_entropy(z, y):
    """Mean cross-entropy of scores z (n, C) against one-hot labels y (n, C)."""
    z = np.asarray(z, float)
    logp = z - z.max(axis=-1, keepdims=True)
    logp = logp - np.log(np.exp(logp).sum(axis=-1, keepdims=True))
    return float(-(np.asarray(y) * logp).sum(axis=-1).mean())


def ce_grad(z, y):
    """eq-m37-ce-grad: gradient of the per-example cross-entropy with respect to the scores, p - y."""
    return softmax(z) - np.asarray(y, float)


def sigmoid(u):
    u = np.asarray(u, float)
    out = np.empty_like(u)
    pos = u >= 0
    out[pos] = 1.0 / (1.0 + np.exp(-u[pos]))
    eu = np.exp(u[~pos])
    out[~pos] = eu / (1.0 + eu)
    return out


def logistic_prob(X, beta0, beta):
    """eq-m37-logistic: p = sigma(beta0 + X beta)."""
    return sigmoid(beta0 + np.asarray(X, float) @ np.asarray(beta, float))


# ---------------------------------------------------------------------------------------------
# Convolution as a learned filter (eq-m37-conv, eq-m37-kernel-response, eq-m37-receptive-field)


def conv1d(x, w, b=0.0, stride=1):
    """eq-m37-conv: y[n] = b + sum_k w[k] x[s n + k] ("valid" cross-correlation, as in deep-learning
    libraries). x has shape (..., T); w has shape (K,). Returns shape (..., floor((T - K)/s) + 1)."""
    x = np.asarray(x, float)
    w = np.asarray(w, float)
    win = sliding_window_view(x, w.size, axis=-1)[..., ::stride, :]
    return win @ w + b


def kernel_response(w, fs, f):
    """eq-m37-kernel-response: H(f) = sum_k w[k] exp(-i 2 pi f k / fs). |H| is the gain a kernel
    applies to a sinusoid of frequency f (Hz) sampled at fs (Hz)."""
    k = np.arange(len(w))
    f = np.atleast_1d(np.asarray(f, float))
    return np.exp(-2j * np.pi * np.outer(f, k) / fs) @ np.asarray(w, float)


def receptive_field(kernels, strides=None):
    """eq-m37-receptive-field: number of input samples that one output of a stack of convolutions sees.
    r = 1 + sum_l (k_l - 1) prod_{j<l} s_j."""
    strides = strides if strides is not None else [1] * len(kernels)
    r, jump = 1, 1
    for k, s in zip(kernels, strides):
        r += (k - 1) * jump
        jump *= s
    return r


def receptive_field_seconds(kernels, strides, fs):
    return receptive_field(kernels, strides) / fs


def empirical_receptive_field(kernels, strides, rng=None):
    """Count which input samples change the first output of a random linear conv stack (check for
    eq-m37-receptive-field)."""
    rng = np.random.default_rng(0) if rng is None else rng
    ws = [rng.normal(size=k) + 2.0 for k in kernels]  # offset keeps every weight away from zero
    T = receptive_field(kernels, strides) + 40

    def run(x):
        for w, s in zip(ws, strides):
            x = conv1d(x, w, stride=s)
        return x[0]

    x0 = rng.normal(size=T)
    base = run(x0)
    seen = []
    for i in range(T):
        x = x0.copy()
        x[i] += 1.0
        if abs(run(x) - base) > 1e-9:
            seen.append(i)
    return len(seen), seen


# ---------------------------------------------------------------------------------------------
# A synthetic ECG (approximate model, illustrative parameters)

# (name, time from the R peak in s, amplitude in mV, Gaussian width in s). Illustrative values.
WAVES = (
    ("P", -0.17, 0.12, 0.025),
    ("Q", -0.030, -0.10, 0.010),
    ("R", 0.0, 1.00, 0.012),
    ("S", 0.030, -0.20, 0.012),
    ("T", 0.25, 0.30, 0.050),
)


def beat(t, scale=1.0, p_wave=True, t_factor=1.0):
    """One beat centred on its R peak at t = 0: a sum of Gaussian waves (mV). t_factor scales the T
    wave alone (used for a "hidden" patient-level signal in the lab)."""
    t = np.asarray(t, float)
    out = np.zeros_like(t)
    for name, t0, a, b in WAVES:
        if name == "P" and not p_wave:
            continue
        k = t_factor if name == "T" else 1.0
        out += scale * k * a * np.exp(-((t - t0) ** 2) / (2 * b * b))
    return out


def rr_sequence(rhythm, hr_bpm, duration_s, rng, cv_sinus=0.03, cv_af=0.20, ectopic_rate=0.15):
    """RR intervals (s) for a rhythm. sinus: nearly regular. af: independent, irregular intervals.
    ectopy: sinus with early beats followed by a pause. All variability values are illustrative."""
    mean_rr = 60.0 / hr_bpm
    rr = []
    while sum(rr) < duration_s + 2 * mean_rr:
        if rhythm == "sinus":
            rr.append(mean_rr * (1 + cv_sinus * rng.normal()))
        elif rhythm == "af":
            # a gamma distribution with the chosen coefficient of variation, always positive
            k = 1.0 / cv_af**2
            rr.append(rng.gamma(k, mean_rr / k))
        elif rhythm == "ectopy":
            if rng.random() < ectopic_rate:
                rr += [0.65 * mean_rr, 1.35 * mean_rr]
            else:
                rr.append(mean_rr * (1 + cv_sinus * rng.normal()))
        else:
            raise ValueError(rhythm)
    return np.maximum(np.array(rr), 0.25)


def synth_ecg(rhythm="sinus", fs=100.0, duration_s=10.0, hr_bpm=70.0, scale=1.0, noise_mv=0.03,
              wander_mv=0.1, invert=False, rng=None, t_factor=1.0):
    """A single-lead synthetic ECG. Returns (signal in mV, R-peak sample indices).

    AF beats have no P wave and irregular RR intervals; fibrillatory waves are not modelled.
    Noise is white Gaussian plus a 0.3-Hz baseline wander (illustrative)."""
    rng = np.random.default_rng() if rng is None else rng
    n = int(round(duration_s * fs))
    t = np.arange(n) / fs
    rr = rr_sequence(rhythm, hr_bpm, duration_s, rng)
    r_times = np.cumsum(rr) - rr[0] * rng.random()
    r_times = r_times[(r_times > -0.5) & (r_times < duration_s + 0.5)]
    x = np.zeros(n)
    for tr in r_times:
        x += beat(t - tr, scale=scale, p_wave=(rhythm != "af"), t_factor=t_factor)
    x += wander_mv * np.sin(2 * np.pi * 0.3 * t + 2 * np.pi * rng.random())
    x += noise_mv * rng.normal(size=n)
    if invert:
        x = -x
    peaks = np.round(r_times[(r_times >= 0) & (r_times < duration_s)] * fs).astype(int)
    return x, peaks[(peaks >= 0) & (peaks < n)]


def make_cohort(n_patients, records_per_patient, fs=100.0, duration_s=10.0, rhythms=("sinus", "af"),
                rng=None, invert_prob=0.0, t_factors=None):
    """A synthetic cohort. Each patient has one class, their own heart rate and wave scale, and
    several records. Returns X (records, samples), y (class index), patient ids, R-peak lists.
    t_factors (one per class) scale the T wave by class: a small, "hidden" difference."""
    rng = np.random.default_rng(0) if rng is None else rng
    X, y, pid, peaks = [], [], [], []
    for p in range(n_patients):
        label = p % len(rhythms)
        hr = rng.uniform(55, 110)       # illustrative range
        scale = rng.uniform(0.6, 1.4)   # illustrative between-patient amplitude spread
        for _ in range(records_per_patient):
            x, pk = synth_ecg(rhythms[label], fs, duration_s, hr * rng.uniform(0.95, 1.05), scale,
                              invert=rng.random() < invert_prob, rng=rng,
                              t_factor=1.0 if t_factors is None else t_factors[label])
            X.append(x)
            y.append(label)
            pid.append(p)
            peaks.append(pk)
    return np.array(X), np.array(y), np.array(pid), peaks


# ---------------------------------------------------------------------------------------------
# Rhythm features (eq-m37-rr) and a simple R-peak detector for real recordings


def rr_features(peaks, fs):
    """eq-m37-rr: mean RR (s), coefficient of variation and normalised RMSSD of the RR intervals."""
    rr = np.diff(np.asarray(peaks, float)) / fs
    if rr.size < 3:
        return np.array([np.nan, np.nan, np.nan])
    mean = rr.mean()
    cv = rr.std(ddof=1) / mean
    nrmssd = np.sqrt(np.mean(np.diff(rr) ** 2)) / mean
    return np.array([mean, cv, nrmssd])


def detect_r_peaks(x, fs, refractory_s=0.25, threshold=0.35):
    """A simplified QRS detector in the spirit of Pan and Tompkins (1985): band-pass, differentiate,
    square, moving-window integrate, then peaks above a fraction of a robust maximum.
    Band edges, window, refractory period and threshold are illustrative choices."""
    from scipy.signal import butter, filtfilt, find_peaks

    x = np.asarray(x, float)
    hi = min(15.0, 0.45 * fs)
    b, a = butter(2, [5.0 / (fs / 2), hi / (fs / 2)], btype="band")
    y = filtfilt(b, a, x)
    e = np.convolve(np.diff(y, prepend=y[0]) ** 2, np.ones(max(1, int(0.12 * fs))), mode="same")
    level = np.percentile(e, 99)
    pk, _ = find_peaks(e, height=threshold * level, distance=max(1, int(refractory_s * fs)))
    # move each detection to the largest absolute deflection nearby, in the band-passed signal
    half = max(1, int(0.06 * fs))
    out = [i - half + int(np.argmax(np.abs(y[max(0, i - half): i + half + 1]))) if i >= half else
           int(np.argmax(np.abs(y[: i + half + 1]))) for i in pk]
    return np.unique(np.array(out, int))


def wave_amplitudes(x, peaks, fs, t_offset_s=0.25):
    """Median R-peak and T-wave amplitudes (mV) at the given R peaks; T is read t_offset_s after R."""
    x = np.asarray(x, float)
    d = int(round(t_offset_s * fs))
    pk = np.asarray(peaks)[np.asarray(peaks) + d < len(x)]
    base = np.median(x)
    return np.array([np.median(x[pk]) - base, np.median(x[pk + d]) - base])


# ---------------------------------------------------------------------------------------------
# Screening yield and prior shift (eq-m37-yield, eq-m37-prior-shift)


def screening_yield(n, prevalence, sensitivity, specificity):
    """eq-m37-yield: expected flagged, true-positive and false-positive counts when n people are
    screened, and the number flagged per true case found (= 1/PPV)."""
    tp = n * prevalence * sensitivity
    fp = n * (1 - prevalence) * (1 - specificity)
    flagged = tp + fp
    return {"flagged": flagged, "tp": tp, "fp": fp, "per_case": flagged / tp if tp > 0 else np.inf}


def prior_shift(p, prev_train, prev_new):
    """eq-m37-prior-shift (Saerens et al. 2002): re-weight a calibrated probability p, learned where
    the positive class had prevalence prev_train, for use where it has prevalence prev_new. Valid
    only if p(x | y) is the same in both places."""
    p = np.asarray(p, float)
    a = prev_new / prev_train * p
    b = (1 - prev_new) / (1 - prev_train) * (1 - p)
    return a / (a + b)


# ---------------------------------------------------------------------------------------------
# A tiny convolutional network in NumPy: conv -> ReLU -> global average pool -> logistic output


class TinyCNN:
    """Binary classifier for (n, T) signals: K filters of width k, ReLU, global average pooling,
    then a logistic output. Gradients are written out by hand; tests check them numerically."""

    def __init__(self, n_filters=8, width=15, rng=None):
        rng = np.random.default_rng(0) if rng is None else rng
        self.W = rng.normal(scale=1.0 / np.sqrt(width), size=(n_filters, width))
        self.b = np.zeros(n_filters)
        self.v = rng.normal(scale=1.0 / np.sqrt(n_filters), size=n_filters)
        self.c = 0.0

    def params(self):
        return [self.W, self.b, self.v]

    def _forward(self, X):
        win = sliding_window_view(X, self.W.shape[1], axis=-1)       # (n, L, k)
        a = win @ self.W.T + self.b                                    # (n, L, K)
        h = np.maximum(a, 0.0)
        g = h.mean(axis=1)                                             # (n, K)
        z = g @ self.v + self.c
        return win, a, g, z

    def predict_proba(self, X):
        return sigmoid(self._forward(np.asarray(X, float))[3])

    def loss_and_grads(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        win, a, g, z = self._forward(X)
        p = sigmoid(z)
        eps = 1e-12
        loss = float(-np.mean(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps)))
        dz = (p - y) / len(y)                                           # eq-m37-ce-grad, two classes
        dv = g.T @ dz
        dc = dz.sum()
        dg = np.outer(dz, self.v)                                       # (n, K)
        da = (a > 0) * dg[:, None, :] / a.shape[1]                      # (n, L, K)
        dW = np.einsum("nlk,nlw->kw", da, win)
        db = da.sum(axis=(0, 1))
        return loss, {"W": dW, "b": db, "v": dv, "c": dc}

    def fit(self, X, y, epochs=30, lr=0.05, batch=32, rng=None, momentum=0.9, optimizer="sgd"):
        """Mini-batch training. optimizer "sgd" (with momentum) or "adam" (Kingma and Ba's update with
        the usual defaults beta1 = 0.9, beta2 = 0.999). Returns the training loss after each epoch."""
        rng = np.random.default_rng(0) if rng is None else rng
        names = ("W", "b", "v", "c")
        m = {k: 0.0 for k in names}
        s = {k: 0.0 for k in names}
        history = []
        n = len(y)
        step = 0
        for _ in range(epochs):
            order = rng.permutation(n)
            for i in range(0, n, batch):
                idx = order[i: i + batch]
                loss, g = self.loss_and_grads(X[idx], y[idx])
                step += 1
                for k in names:
                    if optimizer == "adam":
                        m[k] = 0.9 * m[k] + 0.1 * g[k]
                        s[k] = 0.999 * s[k] + 0.001 * g[k] ** 2
                        upd = -lr * (m[k] / (1 - 0.9**step)) / (np.sqrt(s[k] / (1 - 0.999**step)) + 1e-8)
                    else:
                        m[k] = momentum * m[k] - lr * g[k]
                        upd = m[k]
                    if k == "c":
                        self.c += upd
                    else:
                        getattr(self, k)[...] += upd
            history.append(self.loss_and_grads(X, y)[0])
        return history


def standardize_records(X):
    """Remove each record's median and scale by its robust spread, so amplitude differences between
    devices matter less."""
    X = np.asarray(X, float)
    med = np.median(X, axis=-1, keepdims=True)
    mad = np.median(np.abs(X - med), axis=-1, keepdims=True) + 1e-9
    return (X - med) / (1.4826 * mad)
