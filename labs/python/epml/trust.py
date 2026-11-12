"""m46 · Trustworthy AI in EP: explanations, conformal prediction, fairness, out-of-distribution
inputs and adversarial robustness, from scratch.

Every function implements one numbered equation of module m46 or a step of its lab, and is checked in
tests/test_m46_trust.py.
"""

import math

import numpy as np

# ---------------------------------------------------------------------------------------------
# Explanations: integrated gradients (eq-m46-ig)


def sigmoid(z):
    z = np.asarray(z, float)
    return 1 / (1 + np.exp(-np.clip(z, -60, 60)))


def integrated_gradients(grad, x, baseline, steps=64):
    """eq-m46-ig: (x - x') times the average of the gradient along the straight path from the
    baseline x' to x (midpoint rule with `steps` points). grad(z) returns dF/dz at a point z."""
    x, baseline = np.asarray(x, float), np.asarray(baseline, float)
    alphas = (np.arange(steps) + 0.5) / steps
    g = np.mean([grad(baseline + a * (x - baseline)) for a in alphas], axis=0)
    return (x - baseline) * g


def ig_logistic_exact(w, b, x, baseline):
    """Closed form of eq-m46-ig for F(x) = sigmoid(w.x + b): the path is a line in z = w.x + b, so
    IG_i = (x_i - x'_i) w_i [sigmoid(z) - sigmoid(z')] / (z - z')."""
    w, x, baseline = (np.asarray(a, float) for a in (w, x, baseline))
    z, z0 = w @ x + b, w @ baseline + b
    ratio = sigmoid(z) * (1 - sigmoid(z)) if abs(z - z0) < 1e-12 else (sigmoid(z) - sigmoid(z0)) / (z - z0)
    return (x - baseline) * w * ratio


class TinyMLP:
    """p(x) = sigmoid(v . tanh(W x + b) + c), trained by full-batch gradient descent on cross-entropy.
    Small enough to differentiate by hand, so attributions need no deep-learning library."""

    def __init__(self, d_in, d_hidden=16, seed=0):
        rng = np.random.default_rng(seed)
        self.W = rng.normal(0, 1 / np.sqrt(d_in), (d_hidden, d_in))
        self.b = np.zeros(d_hidden)
        self.v = rng.normal(0, 1 / np.sqrt(d_hidden), d_hidden)
        self.c = 0.0

    def prob(self, X):
        return sigmoid(np.tanh(np.atleast_2d(X) @ self.W.T + self.b) @ self.v + self.c)

    def grad_input(self, x):
        h = np.tanh(self.W @ x + self.b)
        p = sigmoid(self.v @ h + self.c)
        return p * (1 - p) * (self.W.T @ (self.v * (1 - h**2)))

    def fit(self, X, y, lr=0.05, epochs=400, l2=1e-3):
        X, y = np.asarray(X, float), np.asarray(y, float)
        n = len(y)
        for _ in range(epochs):
            H = np.tanh(X @ self.W.T + self.b)
            p = sigmoid(H @ self.v + self.c)
            r = (p - y) / n
            gv = H.T @ r + l2 * self.v
            gc = r.sum()
            dH = np.outer(r, self.v) * (1 - H**2)
            gW = dH.T @ X + l2 * self.W
            gb = dH.sum(axis=0)
            self.v -= lr * gv
            self.c -= lr * gc
            self.W -= lr * gW
            self.b -= lr * gb
        return self


def randomized_copy(model, seed=1):
    """The model-randomization sanity check (Adebayo et al. 2018): the same architecture with new
    random weights. An explanation that does not change is not explaining the trained model."""
    m = TinyMLP(model.W.shape[1], model.W.shape[0], seed=seed)
    m.c = model.c
    return m


def rank_correlation(a, b):
    from scipy.stats import spearmanr

    return float(spearmanr(a, b).correlation)


# ---------------------------------------------------------------------------------------------
# Uncertainty: split conformal prediction (eq-m46-conformal)


def conformal_quantile(scores, alpha):
    """eq-m46-conformal: the ceil((n + 1)(1 - alpha))-th smallest of n calibration scores (infinite
    if that rank exceeds n)."""
    s = np.sort(np.asarray(scores, float))
    n = len(s)
    k = math.ceil((n + 1) * (1 - alpha))
    return float("inf") if k > n else float(s[k - 1])


def conformal_sets(P_cal, y_cal, P_test, alpha, by_class=False):
    """Prediction sets {k : 1 - p_k(x) <= q}. by_class=True uses one threshold per true class
    (class-conditional, 'Mondrian' conformal), which gives each class its own coverage."""
    P_cal, P_test, y_cal = np.asarray(P_cal), np.asarray(P_test), np.asarray(y_cal)
    scores = 1 - P_cal[np.arange(len(y_cal)), y_cal]
    if not by_class:
        q = conformal_quantile(scores, alpha)
        return (1 - P_test) <= q
    K = P_cal.shape[1]
    qs = np.array([conformal_quantile(scores[y_cal == k], alpha) for k in range(K)])
    return (1 - P_test) <= qs[None, :]


def coverage(sets, y):
    return float(np.mean(np.asarray(sets)[np.arange(len(y)), np.asarray(y)]))


# ---------------------------------------------------------------------------------------------
# Fairness (eq-m46-fpr)


def group_rates(y, yhat, groups):
    """Prevalence, TPR, FPR and PPV in each group."""
    y, yhat, groups = (np.asarray(a) for a in (y, yhat, groups))
    out = {}
    for g in np.unique(groups):
        m = groups == g
        yy, pp = y[m].astype(bool), yhat[m].astype(bool)
        out[g] = {"n": int(m.sum()), "prevalence": float(yy.mean()),
                  "TPR": float(pp[yy].mean()) if yy.any() else float("nan"),
                  "FPR": float(pp[~yy].mean()) if (~yy).any() else float("nan"),
                  "PPV": float(yy[pp].mean()) if pp.any() else float("nan")}
    return out


def fpr_from_ppv(prevalence, ppv, tpr):
    """eq-m46-fpr: FPR = pi / (1 - pi) * (1 - PPV) / PPV * TPR. With PPV and TPR fixed, groups with
    different prevalence must have different false-positive rates."""
    return prevalence / (1 - prevalence) * (1 - ppv) / ppv * tpr


def ppv(prevalence, tpr, fpr):
    return tpr * prevalence / (tpr * prevalence + fpr * (1 - prevalence))


# ---------------------------------------------------------------------------------------------
# Out-of-distribution inputs (eq-m46-mahalanobis)


class Mahalanobis:
    """eq-m46-mahalanobis: d^2(x) = (x - mu)^T S^-1 (x - mu) with mean and (slightly shrunk) covariance
    of the training features. For Gaussian features d^2 follows a chi-square law with k degrees of
    freedom, which sets a threshold for a chosen false-alarm rate."""

    def __init__(self, F, shrink=1e-3):
        F = np.asarray(F, float)
        self.mu = F.mean(axis=0)
        S = np.cov(F, rowvar=False)
        S = np.atleast_2d(S)
        self.Sinv = np.linalg.inv(S + shrink * np.trace(S) / len(S) * np.eye(len(S)))
        self.k = F.shape[1]

    def score(self, F):
        D = np.atleast_2d(np.asarray(F, float)) - self.mu
        return np.einsum("ij,jk,ik->i", D, self.Sinv, D)

    def threshold(self, false_alarm=0.01):
        from scipy.stats import chi2

        return float(chi2.ppf(1 - false_alarm, self.k))


# ---------------------------------------------------------------------------------------------
# Adversarial robustness (eq-m46-fgsm)


def fgsm(x, grad_loss, eps):
    """eq-m46-fgsm (Goodfellow et al. 2015): x + eps * sign(dL/dx), the largest first-order increase
    of the loss for a perturbation bounded by eps in every sample (max norm)."""
    return np.asarray(x, float) + eps * np.sign(grad_loss)


def eps_to_flip_linear(w, b, x):
    """For a linear score z = w.x + b, a max-norm perturbation eps changes z by at most eps ||w||_1,
    so the smallest eps that can flip the decision is |z| / ||w||_1."""
    w = np.asarray(w, float)
    return float(abs(w @ np.asarray(x, float) + b) / np.abs(w).sum())


def smooth(v, width=9):
    """Moving-average smoothing, used to make a perturbation look physiological (a crude stand-in for
    the smoothed attacks of Han et al. 2020)."""
    k = np.ones(width) / width
    return np.convolve(v, k, mode="same")
