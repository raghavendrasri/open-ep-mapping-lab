"""m43 · Foundation models: contrastive pretraining, linear probes and attention, from scratch.

Every function here implements one numbered equation of module m43 or a step of its code lab, and
is checked in tests/test_m43_foundation.py. The synthetic beats are an approximate model for
teaching: the Gaussian-wave beat of m37 (after the morphology part of McSharry et al. 2003) with
patient-level wave sizes and QRS width. All ranges are illustrative values chosen to give visibly
different beats, not physiological reference values.
"""

import numpy as np

from .aiecg import WAVES

FS = 250.0                                   # samples per second of the synthetic beats
BEAT_T = np.arange(-0.3, 0.5, 1.0 / FS)      # time from the R peak, s (200 samples)

# ---------------------------------------------------------------------------------------------
# Synthetic patients and recordings


def patient_params(n, rng, width_range=(0.8, 1.8), t_range=(0.2, 1.4)):
    """Latent beat parameters for n synthetic patients (all illustrative):
    scale (overall amplitude), width (QRS width factor), tf (T-wave factor), pf (P-wave factor) and
    sf (S-wave factor). Downstream labels in the lab are thresholds on width and tf."""
    return {
        "scale": rng.uniform(0.6, 1.4, n),
        "width": rng.uniform(*width_range, n),
        "tf": rng.uniform(*t_range, n),
        "pf": rng.uniform(0.0, 1.2, n),
        "sf": rng.uniform(0.3, 1.7, n),
    }


def beat_shape(t, scale=1.0, width=1.0, tf=1.0, pf=1.0, sf=1.0):
    """One beat (mV) centred on its R peak: the m37 Gaussian waves with the Q, R and S waves widened
    by `width` (and Q and S moved out with it) and the P, T and S waves scaled by pf, tf and sf."""
    t = np.asarray(t, float)
    out = np.zeros_like(t)
    for name, t0, a, b in WAVES:
        k = {"P": pf, "T": tf, "S": sf}.get(name, 1.0)
        bb = b * width if name in ("Q", "R", "S") else b
        tt = t0 * width if name in ("Q", "S") else t0
        out += scale * k * a * np.exp(-((t - tt) ** 2) / (2 * bb * bb))
    return out


def recordings(params, idx, rng, jitter=0.05, noise_mv=0.04, wander_mv=0.15, shift=3):
    """One recording per patient index in idx: the patient's beat with small recording-to-recording
    changes (each parameter times 1 + jitter * N(0, 1)), a time shift of up to `shift` samples, a
    random baseline offset and slope (wander_mv) and white noise (noise_mv). Values are illustrative.
    Returns an array (len(idx), len(BEAT_T))."""
    span = BEAT_T.max() - BEAT_T.min()
    X = np.empty((len(idx), BEAT_T.size))
    for row, i in enumerate(idx):
        p = {k: v[i] * (1 + jitter * rng.normal()) for k, v in params.items()}
        s = rng.integers(-shift, shift + 1) / FS
        x = beat_shape(BEAT_T - s, **p)
        x += wander_mv * (rng.normal() + rng.normal() * (BEAT_T - BEAT_T.mean()) / (span / 2))
        x += noise_mv * rng.normal(size=BEAT_T.size)
        X[row] = x
    return X


def augment(X, rng, noise_mv=0.04, wander_mv=0.15, gain=0.1):
    """Augment recordings that already exist (same-recording positives): a random gain of
    1 + gain * N(0, 1), a baseline offset and slope, and white noise."""
    X = np.asarray(X, float)
    n, m = X.shape
    ramp = np.linspace(-1, 1, m)
    out = X * (1 + gain * rng.normal(size=(n, 1)))
    out += wander_mv * (rng.normal(size=(n, 1)) + rng.normal(size=(n, 1)) * ramp)
    return out + noise_mv * rng.normal(size=(n, m))


class Standardizer:
    """Subtract the mean and divide by the standard deviation of each sample position."""

    def __init__(self, X):
        X = np.asarray(X, float)
        self.mu = X.mean(axis=0)
        self.sd = X.std(axis=0) + 1e-12

    def __call__(self, X):
        return (np.asarray(X, float) - self.mu) / self.sd


# ---------------------------------------------------------------------------------------------
# The contrastive loss (eq-m43-infonce, eq-m43-infonce-grad)


def l2_normalize(Z):
    """Scale each row to unit length. Returns (unit rows, row norms)."""
    Z = np.asarray(Z, float)
    n = np.linalg.norm(Z, axis=1, keepdims=True)
    return Z / n, n


def log_softmax_rows(A):
    A = np.asarray(A, float)
    A = A - A.max(axis=1, keepdims=True)
    return A - np.log(np.exp(A).sum(axis=1, keepdims=True))


def infonce(S, tau):
    """eq-m43-infonce: mean over rows i of -log( exp(S_ii / tau) / sum_k exp(S_ik / tau) ).
    S[i, k] is the similarity of anchor i and candidate k; the positive is on the diagonal."""
    return float(-np.mean(np.diag(log_softmax_rows(np.asarray(S, float) / tau))))


def infonce_grad(S, tau):
    """eq-m43-infonce-grad: dL/dS = (P - I) / (N tau), with P the row-wise softmax of S / tau."""
    S = np.asarray(S, float)
    n = S.shape[0]
    P = np.exp(log_softmax_rows(S / tau))
    return (P - np.eye(n)) / (n * tau)


def symmetric_infonce(Z1, Z2, tau):
    """The symmetric loss used for paired views: the mean of eq-m43-infonce with view 1 as anchors and
    with view 2 as anchors. Z1, Z2 are unit rows. Returns (loss, dL/dZ1, dL/dZ2)."""
    S = Z1 @ Z2.T
    loss = 0.5 * (infonce(S, tau) + infonce(S.T, tau))
    G = 0.5 * (infonce_grad(S, tau) + infonce_grad(S.T, tau).T)
    return loss, G @ Z2, G.T @ Z1


# ---------------------------------------------------------------------------------------------
# A small encoder trained with Adam


class Encoder:
    """x -> h = tanh(x W1 + b1) -> z = normalize(h W2). h is the feature used by a linear probe;
    z is the unit embedding used by the contrastive loss (a "projection head" as in SimCLR)."""

    PARAMS = ("W1", "b1", "W2")

    def __init__(self, d_in, d_hidden=64, d_out=16, seed=0):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 1 / np.sqrt(d_in), (d_in, d_hidden))
        self.b1 = np.zeros(d_hidden)
        self.W2 = rng.normal(0, 1 / np.sqrt(d_hidden), (d_hidden, d_out))
        self._m = {k: 0.0 for k in self.PARAMS}
        self._v = {k: 0.0 for k in self.PARAMS}
        self._t = 0

    def features(self, X):
        return np.tanh(np.asarray(X, float) @ self.W1 + self.b1)

    def forward(self, X):
        H = self.features(X)
        U = H @ self.W2
        Z, n = l2_normalize(U)
        return Z, (np.asarray(X, float), H, Z, n)

    def embed(self, X):
        return self.forward(X)[0]

    def backward(self, gZ, cache):
        """Gradients of the loss with respect to the parameters, given dL/dZ."""
        X, H, Z, n = cache
        gU = (gZ - Z * (gZ * Z).sum(axis=1, keepdims=True)) / n
        gH = (gU @ self.W2.T) * (1 - H**2)
        return {"W2": H.T @ gU, "W1": X.T @ gH, "b1": gH.sum(axis=0)}

    def adam_step(self, grads, lr=2e-3, beta1=0.9, beta2=0.999, eps=1e-8):
        self._t += 1
        for k in self.PARAMS:
            self._m[k] = beta1 * self._m[k] + (1 - beta1) * grads[k]
            self._v[k] = beta2 * self._v[k] + (1 - beta2) * grads[k] ** 2
            mh = self._m[k] / (1 - beta1**self._t)
            vh = self._v[k] / (1 - beta2**self._t)
            setattr(self, k, getattr(self, k) - lr * mh / (np.sqrt(vh) + eps))


def pretrain_pairs(sample, d_in, steps=400, batch=128, tau=0.1, lr=2e-3, seed=2, d_hidden=64, d_out=16,
                   snapshots=(), callback=None):
    """Contrastive pretraining on positive pairs drawn by sample(rng, batch) -> (X1, X2), two arrays of
    standardized inputs whose rows i form a positive pair; every other row is a negative.
    Returns (encoder, loss per step). callback(step, encoder) runs at the steps in `snapshots`."""
    rng = np.random.default_rng(seed)
    enc = Encoder(d_in, d_hidden, d_out, seed=seed)
    losses = []
    for step in range(steps + 1):
        if callback is not None and step in snapshots:
            callback(step, enc)
        if step == steps:
            break
        X1, X2 = sample(rng, batch)
        Z1, c1 = enc.forward(X1)
        Z2, c2 = enc.forward(X2)
        loss, g1, g2 = symmetric_infonce(Z1, Z2, tau)
        G1, G2 = enc.backward(g1, c1), enc.backward(g2, c2)
        enc.adam_step({k: G1[k] + G2[k] for k in G1}, lr=lr)
        losses.append(loss)
    return enc, np.array(losses)


def pretrain(params, standardize, steps=400, batch=128, tau=0.1, lr=2e-3, positives="patient",
             seed=2, d_hidden=64, d_out=16, snapshots=(), callback=None):
    """Contrastive pretraining on synthetic patients, without labels. Each step draws `batch` patients
    and two views each. positives="patient": two different recordings of the same patient
    (patient-level positives, as in [sangha2024] and [khattak2026]); positives="recording": two
    augmentations of one recording. Returns (encoder, loss per step)."""
    n_pat = len(next(iter(params.values())))
    if positives not in ("patient", "recording"):
        raise ValueError(positives)

    def sample(rng, b):
        idx = rng.choice(n_pat, size=b, replace=False)
        if positives == "patient":
            return standardize(recordings(params, idx, rng)), standardize(recordings(params, idx, rng))
        X0 = recordings(params, idx, rng, noise_mv=0.0, wander_mv=0.0)
        return standardize(augment(X0, rng)), standardize(augment(X0, rng))

    return pretrain_pairs(sample, BEAT_T.size, steps, batch, tau, lr, seed, d_hidden, d_out, snapshots, callback)


def beats_from_record(x, peaks, fs, before_s=0.3, after_s=0.5):
    """Windows of a recording around each R peak (peaks in samples), dropping beats too close to the
    ends. Returns an array (beats, samples)."""
    x = np.asarray(x, float)
    b, a = int(round(before_s * fs)), int(round(after_s * fs))
    rows = [x[p - b:p + a] for p in peaks if p - b >= 0 and p + a <= len(x)]
    return np.array(rows).reshape(-1, b + a)


# ---------------------------------------------------------------------------------------------
# Linear probe and evaluation helpers


def fit_logistic(X, y, lam=1.0, iters=50):
    """L2-penalized logistic regression by Newton's method (intercept not penalized).
    Returns weights with the intercept last."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    Xa = np.c_[X, np.ones(len(X))]
    w = np.zeros(Xa.shape[1])
    pen = lam * np.r_[np.ones(X.shape[1]), 0.0]
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Xa @ w, -30, 30)))
        g = Xa.T @ (p - y) + pen * w
        H = Xa.T @ (Xa * (p * (1 - p))[:, None]) + np.diag(pen) + 1e-9 * np.eye(len(w))
        step = np.linalg.solve(H, g)
        w -= step
        if np.max(np.abs(step)) < 1e-10:
            break
    return w


def logistic_score(w, X):
    return np.c_[np.asarray(X, float), np.ones(len(X))] @ w


def alignment(Z1, Z2):
    """Mean cosine similarity of positive pairs (rows of two unit-embedding arrays)."""
    return float(np.mean(np.sum(Z1 * Z2, axis=1)))


def nearest_neighbour_accuracy(Z, groups):
    """Share of embeddings whose nearest other embedding (by cosine) belongs to the same group."""
    Z = np.asarray(Z, float)
    S = Z @ Z.T
    np.fill_diagonal(S, -np.inf)
    groups = np.asarray(groups)
    return float(np.mean(groups[np.argmax(S, axis=1)] == groups))


# ---------------------------------------------------------------------------------------------
# Attention (eq-m43-attention) and the reason for the square root (eq-m43-scaling)


def attention(Q, K, V):
    """eq-m43-attention: softmax(Q K^T / sqrt(d)) V, with the softmax over keys (rows sum to 1).
    Returns (outputs, attention weights)."""
    Q, K, V = (np.asarray(a, float) for a in (Q, K, V))
    d = Q.shape[-1]
    A = np.exp(log_softmax_rows(Q @ K.T / np.sqrt(d)))
    return A @ V, A


def score_variance(d, n=20000, rng=None):
    """Monte Carlo check of eq-m43-scaling: the variance of q.k for q, k with independent zero-mean,
    unit-variance entries is d, so q.k / sqrt(d) has unit variance. Returns (var raw, var scaled)."""
    rng = np.random.default_rng(0) if rng is None else rng
    q = rng.normal(size=(n, d))
    k = rng.normal(size=(n, d))
    s = np.sum(q * k, axis=1)
    return float(s.var()), float((s / np.sqrt(d)).var())
