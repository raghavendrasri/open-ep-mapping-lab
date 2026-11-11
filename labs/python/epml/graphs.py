"""m39 · AI on intracardiac electrograms and maps: graph convolution on mapping meshes, overlap metrics,
focal loss and Gaussian mixtures.

Each function implements a numbered equation of module m39 and is checked in tests/test_m39_graphs.py.
"""

import numpy as np
import scipy.sparse as sps

# ---------------------------------------------------------------------------------------------
# Graphs on meshes (eq-m39-gcn, eq-m39-smoothing)


def mesh_adjacency(tris, n):
    """Symmetric 0/1 adjacency (scipy sparse) of the vertices of a triangle mesh."""
    tris = np.asarray(tris)
    i = np.concatenate([tris[:, 0], tris[:, 1], tris[:, 2], tris[:, 1], tris[:, 2], tris[:, 0]])
    j = np.concatenate([tris[:, 1], tris[:, 2], tris[:, 0], tris[:, 0], tris[:, 1], tris[:, 2]])
    A = sps.coo_matrix((np.ones(i.size), (i, j)), shape=(n, n)).tocsr()
    A.data[:] = 1.0
    A.eliminate_zeros()
    return A


def normalized_adjacency(A):
    """eq-m39-gcn: A_hat = D~^(-1/2) (A + I) D~^(-1/2), with D~ the degrees of A + I."""
    At = A + sps.identity(A.shape[0], format="csr")
    d = np.asarray(At.sum(axis=1)).ravel()
    Dm = sps.diags(1.0 / np.sqrt(d))
    return (Dm @ At @ Dm).tocsr()


def stationary_vector(A):
    """eq-m39-smoothing: A_hat v = v for v proportional to the square root of the degrees of A + I."""
    d = np.asarray((A + sps.identity(A.shape[0])).sum(axis=1)).ravel()
    v = np.sqrt(d)
    return v / np.linalg.norm(v)


def hop_reach(A, start, layers):
    """Vertices that can influence `start` after `layers` graph-convolution layers (its L-hop ball)."""
    reach = np.zeros(A.shape[0], bool)
    reach[start] = True
    for _ in range(layers):
        reach = reach | (A @ reach.astype(float) > 0)
    return reach


def vertex_areas(verts, tris):
    """One third of the area of each triangle, summed at its vertices (mm^2)."""
    v = np.asarray(verts, float)
    t = np.asarray(tris)
    if v.shape[1] == 2:
        v = np.c_[v, np.zeros(len(v))]
    area = 0.5 * np.linalg.norm(np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]), axis=1)
    out = np.zeros(len(v))
    for k in range(3):
        np.add.at(out, t[:, k], area / 3)
    return out


class GCN:
    """Two graph-convolution layers for per-vertex binary labels:
    H = ReLU(A_hat X W1 + b1),  z = A_hat H w2 + c,  p = sigmoid(z).
    Gradients written by hand; tests check them numerically. loss: "bce" or "focal"."""

    def __init__(self, n_in, n_hidden=8, rng=None):
        rng = np.random.default_rng(0) if rng is None else rng
        self.W1 = rng.normal(scale=1 / np.sqrt(n_in), size=(n_in, n_hidden))
        self.b1 = np.zeros(n_hidden)
        self.w2 = rng.normal(scale=1 / np.sqrt(n_hidden), size=n_hidden)
        self.c = 0.0

    def forward(self, Ah, X):
        AX = Ah @ X
        pre = AX @ self.W1 + self.b1
        H = np.maximum(pre, 0)
        AH = Ah @ H
        z = AH @ self.w2 + self.c
        return AX, pre, H, AH, z

    def predict_proba(self, Ah, X):
        return _sigmoid(self.forward(Ah, X)[4])

    def loss_and_grads(self, Ah, X, y, loss="bce", alpha=0.5, gamma=2.0, weight=None):
        AX, pre, H, AH, z = self.forward(Ah, X)
        if loss == "focal":
            L, dz = focal_loss(z, y, alpha, gamma, grad=True)
        else:
            L, dz = weighted_bce(z, y, weight, grad=True)
        n = len(y)
        L, dz = L / n, dz / n
        dw2 = AH.T @ dz
        dc = dz.sum()
        dH = Ah.T @ np.outer(dz, self.w2)
        dpre = dH * (pre > 0)
        dW1 = AX.T @ dpre
        db1 = dpre.sum(axis=0)
        return L, {"W1": dW1, "b1": db1, "w2": dw2, "c": dc}

    def fit(self, cases, epochs=200, lr=0.02, **loss_kw):
        """cases: list of (A_hat, X, y). Full-batch Adam over all cases. Returns the loss per epoch."""
        names = ("W1", "b1", "w2", "c")
        m = {k: 0.0 for k in names}
        s = {k: 0.0 for k in names}
        hist = []
        for step in range(1, epochs + 1):
            tot = 0.0
            g = {k: 0.0 for k in names}
            for Ah, X, y in cases:
                L, gi = self.loss_and_grads(Ah, X, y, **loss_kw)
                tot += L / len(cases)
                for k in names:
                    g[k] = g[k] + gi[k] / len(cases)
            for k in names:
                m[k] = 0.9 * m[k] + 0.1 * g[k]
                s[k] = 0.999 * s[k] + 0.001 * g[k] ** 2
                upd = -lr * (m[k] / (1 - 0.9**step)) / (np.sqrt(s[k] / (1 - 0.999**step)) + 1e-8)
                if k == "c":
                    self.c += upd
                else:
                    getattr(self, k)[...] += upd
            hist.append(tot)
        return hist


def _sigmoid(z):
    z = np.asarray(z, float)
    return np.where(z >= 0, 1 / (1 + np.exp(-np.abs(z))), np.exp(-np.abs(z)) / (1 + np.exp(-np.abs(z))))


# ---------------------------------------------------------------------------------------------
# Losses for rare classes (eq-m39-focal)


def weighted_bce(z, y, weight=None, grad=False):
    """Binary cross-entropy summed over items; weight (for the positive class) multiplies positive terms."""
    z = np.asarray(z, float)
    y = np.asarray(y, float)
    p = _sigmoid(z)
    w = np.where(y == 1, 1.0 if weight is None else weight, 1.0)
    eps = 1e-12
    L = float(-(w * (y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps))).sum())
    if not grad:
        return L
    return L, w * (p - y)


def focal_loss(z, y, alpha=0.25, gamma=2.0, grad=False):
    """eq-m39-focal (Lin et al. 2017): sum of -alpha_t (1 - p_t)^gamma log p_t, with p_t the probability of
    the true class and alpha_t = alpha for positives, 1 - alpha for negatives. Gradient with respect to z."""
    z = np.asarray(z, float)
    y = np.asarray(y, float)
    p = _sigmoid(z)
    eps = 1e-12
    pt = np.where(y == 1, p, 1 - p)
    at = np.where(y == 1, alpha, 1 - alpha)
    L = float(-(at * (1 - pt) ** gamma * np.log(pt + eps)).sum())
    if not grad:
        return L
    # d/dz of -(1 - pt)^g log pt, with d pt/dz = +pt(1 - pt) for y = 1 and -pt(1 - pt) for y = 0
    dpt = gamma * (1 - pt) ** (gamma - 1) * np.log(pt + eps) - (1 - pt) ** gamma / (pt + eps)
    sign = np.where(y == 1, 1.0, -1.0)
    return L, at * dpt * sign * pt * (1 - pt)


# ---------------------------------------------------------------------------------------------
# Overlap and location metrics (eq-m39-dice, eq-m39-lens)


def dice(pred, truth, weights=None):
    """eq-m39-dice: 2|P n T| / (|P| + |T|), with optional area weights per vertex."""
    pred = np.asarray(pred, bool)
    truth = np.asarray(truth, bool)
    w = np.ones(pred.size) if weights is None else np.asarray(weights, float)
    den = w[pred].sum() + w[truth].sum()
    return 2 * w[pred & truth].sum() / den if den > 0 else 1.0


def lens_area(R, r, d):
    """eq-m39-lens: area of the intersection of two discs with radii R and r whose centres are d apart."""
    R, r, d = float(R), float(r), float(d)
    if d >= R + r:
        return 0.0
    if d <= abs(R - r):
        return np.pi * min(R, r) ** 2
    a = r * r * np.arccos((d * d + r * r - R * R) / (2 * d * r))
    b = R * R * np.arccos((d * d + R * R - r * r) / (2 * d * R))
    c = 0.5 * np.sqrt((-d + r + R) * (d + r - R) * (d - r + R) * (d + r + R))
    return a + b - c


def disc_dice(R, r, d):
    """Dice of a true disc (radius R) and a predicted disc (radius r) whose centres are d apart."""
    return 2 * lens_area(R, r, d) / (np.pi * (R * R + r * r))


# ---------------------------------------------------------------------------------------------
# Gaussian mixtures (eq-m39-gmm)


def gmm_responsibilities(x, weights, means, sds):
    """eq-m39-gmm: posterior probability that each value came from each component of a 1-D mixture."""
    x = np.asarray(x, float)[:, None]
    w, m, s = (np.asarray(v, float)[None, :] for v in (weights, means, sds))
    dens = w * np.exp(-0.5 * ((x - m) / s) ** 2) / (s * np.sqrt(2 * np.pi))
    return dens / dens.sum(axis=1, keepdims=True)


def gmm_em(x, k=2, iters=200, rng=None):
    """Fit a 1-D Gaussian mixture by expectation-maximization. Returns (weights, means, sds)."""
    rng = np.random.default_rng(0) if rng is None else rng
    x = np.asarray(x, float)
    means = np.quantile(x, np.linspace(0.2, 0.8, k)) + 1e-3 * rng.normal(size=k)
    sds = np.full(k, x.std())
    weights = np.full(k, 1.0 / k)
    for _ in range(iters):
        g = gmm_responsibilities(x, weights, means, sds)
        nk = g.sum(axis=0)
        weights = nk / x.size
        means = (g * x[:, None]).sum(axis=0) / nk
        sds = np.sqrt((g * (x[:, None] - means) ** 2).sum(axis=0) / nk) + 1e-9
    order = np.argsort(means)
    return weights[order], means[order], sds[order]
