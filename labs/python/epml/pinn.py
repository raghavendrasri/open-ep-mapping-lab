"""Physics-informed fitting of activation maps without a deep-learning library (m42).

An activation map T(x) and, optionally, a slowness map s(x) = 1/v(x) are written as sums of
Gaussian radial basis functions. Their coefficients are fitted by Levenberg-Marquardt to two kinds of
residual: misfit to measured activation times, and the eikonal residual s |grad T| - 1 at collocation
points (eq-m42-loss, eq-m42-eikonal). Gradients of the basis are analytic, so no automatic
differentiation is needed. Units: x in mm, t in ms, s in ms/mm (1 mm/ms = 1 m/s).

Equations (module m42):
  eq-m42-loss      L = mean data misfit^2 + lambda * mean eikonal residual^2
  eq-m42-eikonal   r(x) = s(x) |grad T(x)| - 1
  eq-m42-rbf       T(x) = a_0 + sum_k a_k exp(-|x - c_k|^2 / 2h^2), with analytic gradient
  eq-m42-lm        Levenberg-Marquardt step (J^T J + mu I) delta = -J^T r
  eq-m42-ensemble  ensemble mean and spread
"""

import numpy as np


def grid_centres(lo, hi, n):
    """n x n centres on a square [lo, hi]^2."""
    g = np.linspace(lo, hi, n)
    X, Y = np.meshgrid(g, g, indexing="ij")
    return np.c_[X.ravel(), Y.ravel()]


def rbf_basis(X, centres, h):
    """eq-m42-rbf: values (n, K + 1) and gradients (n, K + 1, 2); the last column is a constant."""
    X = np.atleast_2d(np.asarray(X, float))
    d = X[:, None, :] - centres[None, :, :]
    phi = np.exp(-0.5 * (d**2).sum(-1) / h**2)
    dphi = -d / h**2 * phi[..., None]
    n = len(X)
    return np.c_[phi, np.ones(n)], np.concatenate([dphi, np.zeros((n, 1, 2))], axis=1)


def eikonal_residual(grad_T, s):
    """eq-m42-eikonal: s |grad T| - 1 (zero where the map obeys the eikonal equation)."""
    return np.asarray(s, float) * np.linalg.norm(grad_T, axis=-1) - 1.0


class ActivationFit:
    """T(x) as an RBF expansion; slowness either fixed, one unknown scalar, or an RBF field.

    slowness: a float (fixed), "scalar" (one unknown value) or "field" (RBF expansion on
    s_centres with width s_h, kept near s_prior by a ridge penalty of weight s_ridge)."""

    def __init__(self, centres, h, slowness="scalar", s_centres=None, s_h=None, s_prior=1.0, s_ridge=1e-2, ridge=1e-6):
        self.c, self.h = np.asarray(centres, float), float(h)
        self.mode = slowness if isinstance(slowness, str) else "fixed"
        self.s_fixed = None if isinstance(slowness, str) else float(slowness)
        self.sc = None if s_centres is None else np.asarray(s_centres, float)
        self.sh = s_h
        self.s_prior, self.s_ridge, self.ridge = float(s_prior), float(s_ridge), float(ridge)
        self.a = np.zeros(len(self.c) + 1)
        self.b = np.zeros(0 if self.mode == "fixed" else (1 if self.mode == "scalar" else len(self.sc) + 1))
        if self.mode == "scalar":
            self.b[:] = s_prior
        elif self.mode == "field":
            self.b[-1] = s_prior

    # ---- model
    def T(self, X):
        return rbf_basis(X, self.c, self.h)[0] @ self.a

    def gradT(self, X):
        return np.einsum("nkd,k->nd", rbf_basis(X, self.c, self.h)[1], self.a)

    def s(self, X):
        n = len(np.atleast_2d(X))
        if self.mode == "fixed":
            return np.full(n, self.s_fixed)
        if self.mode == "scalar":
            return np.full(n, self.b[0])
        return rbf_basis(X, self.sc, self.sh)[0] @ self.b

    def speed(self, X):
        return 1.0 / np.clip(self.s(X), 1e-6, None)

    # ---- fitting
    def _residuals(self, Xd, td, Xc, lam, prior=None):
        Pd, _ = rbf_basis(Xd, self.c, self.h)
        Pc, Gc = rbf_basis(Xc, self.c, self.h)
        nd, nc = len(Xd), len(Xc)
        target = td - (0 if prior is None else prior[0])
        rd = (Pd @ self.a - target) / np.sqrt(nd)
        Jd = np.c_[Pd, np.zeros((nd, len(self.b)))] / np.sqrt(nd)
        g = np.einsum("nkd,k->nd", Gc, self.a) + (0 if prior is None else prior[1])
        gn = np.maximum(np.linalg.norm(g, axis=1), 1e-9)
        sv = self.s(Xc)
        w = np.sqrt(lam / nc)
        rc = w * (sv * gn - 1.0)
        dA = sv[:, None] * np.einsum("nkd,nd->nk", Gc, g / gn[:, None])
        if self.mode == "fixed":
            dB = np.zeros((nc, 0))
        elif self.mode == "scalar":
            dB = gn[:, None]
        else:
            dB = gn[:, None] * rbf_basis(Xc, self.sc, self.sh)[0]
        Jc = w * np.c_[dA, dB]
        R = [rd, rc, np.sqrt(self.ridge) * self.a[:-1]]
        J = [Jd, Jc, np.c_[np.sqrt(self.ridge) * np.eye(len(self.a))[:-1], np.zeros((len(self.a) - 1, len(self.b)))]]
        if self.mode == "field":
            sb = self.b.copy()
            sb[-1] -= self.s_prior
            R.append(np.sqrt(self.s_ridge) * sb)
            J.append(np.c_[np.zeros((len(self.b), len(self.a))), np.sqrt(self.s_ridge) * np.eye(len(self.b))])
        return np.concatenate(R), np.vstack(J)

    def loss(self, Xd, td, Xc, lam, prior=None):
        r, _ = self._residuals(Xd, td, Xc, lam, prior)
        return float(r @ r)

    def fit(self, Xd, td, Xc, lam=1.0, iters=60, mu=1e-3, prior=None, warm=True):
        """eq-m42-lm on eq-m42-loss. With lam = 0 this is a ridge least-squares fit to the data.
        prior: optional (values at Xd, gradients at Xc) of a fixed function added to T, for
        randomized-prior ensembles. Returns the loss history."""
        Xd, td, Xc = np.asarray(Xd, float), np.asarray(td, float), np.asarray(Xc, float)
        if warm:  # start from the data-only fit with a sensible slope
            Pd, _ = rbf_basis(Xd, self.c, self.h)
            A = np.vstack([Pd, np.sqrt(max(self.ridge, 1e-6) * len(Xd)) * np.eye(len(self.a))[:-1]])
            y = np.r_[td - (0 if prior is None else prior[0]), np.zeros(len(self.a) - 1)]
            self.a = np.linalg.lstsq(A, y, rcond=None)[0]
        hist = [self.loss(Xd, td, Xc, lam, prior)]
        for _ in range(iters):
            r, J = self._residuals(Xd, td, Xc, lam, prior)
            p0 = np.r_[self.a, self.b]
            JTJ, JTr = J.T @ J, J.T @ r
            while True:
                step = np.linalg.solve(JTJ + mu * np.diag(np.diag(JTJ) + 1e-12), -JTr)
                self.a, self.b = p0[: len(self.a)] + step[: len(self.a)], p0[len(self.a):] + step[len(self.a):]
                new = self.loss(Xd, td, Xc, lam, prior)
                if new <= hist[-1] or mu > 1e8:
                    break
                mu *= 10
            if new > hist[-1]:
                self.a, self.b = p0[: len(self.a)], p0[len(self.a):]
                break
            mu = max(mu / 3, 1e-9)
            hist.append(new)
            if hist[-2] - hist[-1] < 1e-10 * max(hist[-2], 1e-30):
                break
        return hist


def ensemble(Xd, td, Xc, members, make_fit, lam=1.0, noise=0.0, prior_scale=0.0, rng=None, Xeval=None, iters=60):
    """eq-m42-ensemble: fit `members` models, each to data perturbed by Gaussian noise of SD `noise`
    and with a fixed random prior function of scale `prior_scale` (randomized priors). Returns the
    member predictions at Xeval (members, n_eval)."""
    rng = rng or np.random.default_rng()
    preds = []
    for _ in range(members):
        fit = make_fit()
        prior = None
        pe = 0.0
        if prior_scale > 0:
            cp = rng.uniform(Xc.min(0), Xc.max(0), (25, 2))
            wp = rng.normal(0, prior_scale, 25)
            P = lambda X: rbf_basis(X, cp, 10.0)  # noqa: E731
            prior = (P(Xd)[0][:, :-1] @ wp, np.einsum("nkd,k->nd", P(Xc)[1][:, :-1], wp))
            pe = P(Xeval)[0][:, :-1] @ wp
        fit.fit(Xd, td + rng.normal(0, noise, len(td)) if noise > 0 else td, Xc, lam=lam, prior=prior, iters=iters)
        preds.append(fit.T(Xeval) + pe)
    return np.array(preds)


def ensemble_stats(preds):
    """eq-m42-ensemble: mean and sample standard deviation across members (axis 0)."""
    preds = np.asarray(preds, float)
    return preds.mean(0), preds.std(0, ddof=1)
