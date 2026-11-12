"""m46 tests: integrated gradients (eq-m46-ig), split conformal prediction (eq-m46-conformal), the
false-positive-rate identity (eq-m46-fpr), the Mahalanobis out-of-distribution score
(eq-m46-mahalanobis) and the max-norm attack on a linear score (eq-m46-fgsm)."""

import numpy as np
import pytest
import sympy as sp

from epml import trust as tr


def test_integrated_gradients_completeness_and_closed_form():
    """eq-m46-ig: attributions add up to F(x) - F(x'); for a logistic model the midpoint rule matches
    the closed form, and for an MLP completeness holds to the accuracy of the integral."""
    rng = np.random.default_rng(0)
    w, b = rng.normal(size=8), 0.3
    x, x0 = rng.normal(size=8), np.zeros(8)
    exact = tr.ig_logistic_exact(w, b, x, x0)
    assert exact.sum() == pytest.approx(tr.sigmoid(w @ x + b) - tr.sigmoid(b))

    def grad(z):
        p = tr.sigmoid(w @ z + b)
        return p * (1 - p) * w

    assert np.allclose(tr.integrated_gradients(grad, x, x0, steps=400), exact, atol=1e-5)
    mlp = tr.TinyMLP(8, 6, seed=2)
    ig = tr.integrated_gradients(mlp.grad_input, x, x0, steps=256)
    assert ig.sum() == pytest.approx(mlp.prob(x)[0] - mlp.prob(x0)[0], abs=1e-4)


def test_mlp_input_gradient_matches_finite_differences():
    rng = np.random.default_rng(1)
    mlp = tr.TinyMLP(5, 4, seed=3)
    x = rng.normal(size=5)
    eps = 1e-6
    fd = [(mlp.prob(x + eps * e)[0] - mlp.prob(x - eps * e)[0]) / (2 * eps) for e in np.eye(5)]
    assert np.allclose(mlp.grad_input(x), fd, atol=1e-8)


def test_conformal_quantile_and_coverage():
    """eq-m46-conformal: the rank ceil((n + 1)(1 - alpha)); marginal coverage is at least 1 - alpha
    (and below 1 - alpha + 1/(n + 1)) when calibration and test points are exchangeable."""
    assert tr.conformal_quantile(np.arange(1, 10), 0.1) == 9        # ceil(10 * 0.9) = 9
    assert tr.conformal_quantile(np.arange(1, 10), 0.05) == float("inf")
    rng = np.random.default_rng(4)
    n, alpha, covs = 200, 0.1, []
    for _ in range(300):
        logits = rng.normal(size=(2 * n, 3)) + 2 * np.eye(3)[rng.integers(0, 3, 2 * n)]
        y = np.argmax(logits + rng.normal(0, 1.5, logits.shape), axis=1)
        P = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
        sets = tr.conformal_sets(P[:n], y[:n], P[n:], alpha)
        covs.append(tr.coverage(sets, y[n:]))
    assert 1 - alpha - 0.005 <= np.mean(covs) <= 1 - alpha + 1 / (n + 1) + 0.005


def test_class_conditional_conformal_covers_each_class():
    rng = np.random.default_rng(5)
    n = 3000
    y = rng.integers(0, 3, 2 * n)
    logits = rng.normal(size=(2 * n, 3)) + np.array([3.0, 1.5, 0.5])[y][:, None] * np.eye(3)[y]
    P = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
    sets = tr.conformal_sets(P[:n], y[:n], P[n:], 0.1, by_class=True)
    for k in range(3):
        m = y[n:] == k
        assert tr.coverage(sets[m], y[n:][m]) == pytest.approx(0.9, abs=0.03)


def test_fpr_identity_symbolic_and_numeric():
    """eq-m46-fpr: from the definitions of PPV, TPR and FPR (SymPy), and the consequence that equal
    PPV and TPR force unequal FPR when prevalences differ."""
    pi, tpr, fpr = sp.symbols("pi tpr fpr", positive=True)
    ppv = tpr * pi / (tpr * pi + fpr * (1 - pi))
    assert sp.simplify(pi / (1 - pi) * (1 - ppv) / ppv * tpr - fpr) == 0
    a = tr.fpr_from_ppv(0.05, 0.75, 0.9)
    b = tr.fpr_from_ppv(0.25, 0.75, 0.9)
    assert b > a and tr.ppv(0.05, 0.9, a) == pytest.approx(0.75)
    rates = tr.group_rates([1, 0, 0, 1, 1, 0], [1, 1, 0, 1, 0, 0], ["a", "a", "a", "b", "b", "b"])
    assert rates["a"]["TPR"] == 1.0 and rates["a"]["FPR"] == 0.5 and rates["b"]["TPR"] == 0.5


def test_mahalanobis_chi_square_false_alarm_rate():
    """eq-m46-mahalanobis: for Gaussian features d^2 follows chi-square with k degrees of freedom, so the
    chi-square threshold sets the in-distribution false-alarm rate; shifted data score higher."""
    rng = np.random.default_rng(6)
    A = rng.normal(size=(4, 4))
    F = rng.normal(size=(20000, 4)) @ A + 3
    md = tr.Mahalanobis(F[:10000], shrink=0.0)
    assert np.mean(md.score(F[10000:]) > md.threshold(0.05)) == pytest.approx(0.05, abs=0.01)
    assert np.mean(md.score(F[10000:] + 2 * A[0])) > np.mean(md.score(F[10000:]))


def test_fgsm_on_a_linear_score():
    """eq-m46-fgsm: for z = w.x + b, the max-norm step eps*sign(w) changes z by exactly eps*||w||_1,
    and eps = |z| / ||w||_1 is just enough to reach the decision boundary."""
    rng = np.random.default_rng(7)
    w, b, x = rng.normal(size=50), -0.2, rng.normal(size=50)
    z = w @ x + b
    eps = 0.01
    x_adv = tr.fgsm(x, -np.sign(z) * w, eps)
    assert w @ x_adv + b == pytest.approx(z - np.sign(z) * eps * np.abs(w).sum())
    e = tr.eps_to_flip_linear(w, b, x)
    assert w @ tr.fgsm(x, -np.sign(z) * w, e) + b == pytest.approx(0, abs=1e-9)
    assert np.allclose(tr.smooth(np.ones(30))[5:-5], 1)
