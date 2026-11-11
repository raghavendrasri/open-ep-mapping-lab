"""m43 equation tests: the InfoNCE loss and its gradient, the encoder's backward pass, attention and
the square-root scaling, and the label-efficiency result of the code lab on synthetic beats."""

import numpy as np
import pytest
import sympy as sp

from epml import foundation as fm
from epml.ml import auc_rank


def test_infonce_equal_similarities_gives_log_n():
    """eq-m43-infonce: with all similarities equal the positive is one of N equally likely candidates."""
    for n in (2, 8, 64):
        assert fm.infonce(np.full((n, n), 0.3), tau=0.1) == pytest.approx(np.log(n))


def test_infonce_limits_and_symbolic_form():
    """eq-m43-infonce: tends to 0 when positives win by a margin and tau -> 0; for N = 2 it is the
    logistic loss of the similarity gap (SymPy)."""
    S = np.eye(5) * 1.0 + 0.2
    assert fm.infonce(S, tau=0.01) < 1e-30
    a, b, tau = sp.symbols("a b tau", positive=True)
    # loss of one row = log of (sum of exponentials / positive's exponential) = log(1 + e^((b - a)/tau))
    ratio = (sp.exp(a / tau) + sp.exp(b / tau)) / sp.exp(a / tau)
    assert sp.simplify(sp.expand(ratio) - (1 + sp.exp((b - a) / tau))) == 0
    assert fm.infonce(np.array([[0.3, 0.7], [0.7, 0.3]]), 0.2) == pytest.approx(np.log1p(np.exp(2.0)))


def test_infonce_gradient_matches_finite_differences():
    """eq-m43-infonce-grad: dL/dS = (P - I) / (N tau)."""
    rng = np.random.default_rng(0)
    S = rng.uniform(-1, 1, (6, 6))
    G = fm.infonce_grad(S, 0.2)
    eps = 1e-6
    fd = np.zeros_like(S)
    for i in range(6):
        for k in range(6):
            E = np.zeros_like(S)
            E[i, k] = eps
            fd[i, k] = (fm.infonce(S + E, 0.2) - fm.infonce(S - E, 0.2)) / (2 * eps)
    assert np.allclose(G, fd, atol=1e-8)
    assert np.allclose(G.sum(axis=1), 0)


def test_encoder_backward_matches_finite_differences():
    """The chain rule through the normalization and tanh layer used to train with eq-m43-infonce."""
    rng = np.random.default_rng(1)
    enc = fm.Encoder(7, d_hidden=5, d_out=3, seed=3)
    X1, X2 = rng.normal(size=(4, 7)), rng.normal(size=(4, 7))

    def loss():
        return fm.symmetric_infonce(enc.embed(X1), enc.embed(X2), 0.5)[0]

    Z1, c1 = enc.forward(X1)
    Z2, c2 = enc.forward(X2)
    _, g1, g2 = fm.symmetric_infonce(Z1, Z2, 0.5)
    G1, G2 = enc.backward(g1, c1), enc.backward(g2, c2)
    eps = 1e-6
    for name in fm.Encoder.PARAMS:
        P = getattr(enc, name)
        analytic = G1[name] + G2[name]
        for idx in [tuple(rng.integers(0, s) for s in P.shape) for _ in range(5)]:
            old = P[idx]
            P[idx] = old + eps
            up = loss()
            P[idx] = old - eps
            down = loss()
            P[idx] = old
            assert analytic[idx] == pytest.approx((up - down) / (2 * eps), abs=1e-7)


def test_attention_weights_and_limits():
    """eq-m43-attention: rows of weights sum to 1; permuting the keys and values together leaves the
    output unchanged; a query matching one key far better than the rest returns that key's value."""
    rng = np.random.default_rng(2)
    Q, K, V = rng.normal(size=(3, 4)), rng.normal(size=(6, 4)), rng.normal(size=(6, 2))
    out, A = fm.attention(Q, K, V)
    assert np.allclose(A.sum(axis=1), 1) and (A > 0).all()
    perm = rng.permutation(6)
    assert np.allclose(fm.attention(Q, K[perm], V[perm])[0], out)
    K2 = np.zeros((6, 4))
    K2[2] = [50.0, 0, 0, 0]
    out2, _ = fm.attention(np.array([[1.0, 0, 0, 0]]), K2, V)
    assert np.allclose(out2[0], V[2], atol=1e-6)


def test_score_variance_scaling():
    """eq-m43-scaling: Var(q.k) = d for independent zero-mean, unit-variance entries (SymPy for the
    algebra, Monte Carlo for the numbers), so dividing by sqrt(d) gives unit variance."""
    from sympy.stats import E, Normal, variance

    q, k = Normal("q", 0, 1), Normal("k", 0, 1)
    assert E(q * k) == 0 and sp.simplify(variance(q * k)) == 1   # one term of the dot product
    for dim in (4, 64):
        raw, scaled = fm.score_variance(dim, n=40000, rng=np.random.default_rng(dim))
        assert raw == pytest.approx(dim, rel=0.05) and scaled == pytest.approx(1.0, rel=0.05)


def test_synthetic_recordings_are_patient_specific():
    """Two recordings of one patient are closer to each other than to another patient's, on average."""
    rng = np.random.default_rng(3)
    p = fm.patient_params(50, rng)
    a, b = fm.recordings(p, np.arange(50), rng), fm.recordings(p, np.arange(50), rng)
    same = np.linalg.norm(a - b, axis=1).mean()
    other = np.linalg.norm(a - np.roll(b, 1, axis=0), axis=1).mean()
    assert same < other


@pytest.fixture(scope="module")
def pretrained():
    rng = np.random.default_rng(1)
    params = fm.patient_params(2000, rng)
    std = fm.Standardizer(fm.recordings(params, np.arange(2000), rng))
    enc, losses = fm.pretrain(params, std, steps=300, seed=2)
    return std, enc, losses


def test_pretraining_lowers_the_loss_below_chance(pretrained):
    """Chance level of eq-m43-infonce with a batch of 128 is ln 128; training goes well below it."""
    _, _, losses = pretrained
    assert losses[-20:].mean() < 0.6 * np.log(128)


def test_linear_probe_beats_raw_features_with_few_labels(pretrained):
    """Lab part B: with 10 labelled patients, a linear probe on pretrained features has a higher AUC
    than the same logistic regression on the raw samples (mean of five draws)."""
    std, enc, _ = pretrained
    test = fm.patient_params(1000, np.random.default_rng(5))
    Xt = std(fm.recordings(test, np.arange(1000), np.random.default_rng(6)))
    yt = (test["width"] > 1.4).astype(float)
    raw, probe = [], []
    for rep in range(5):
        r = np.random.default_rng(100 + rep)
        lab = fm.patient_params(10, r)
        yl = (lab["width"] > 1.4).astype(float)
        if yl.min() == yl.max():
            continue
        Xl = std(fm.recordings(lab, np.arange(10), r))
        raw.append(auc_rank(fm.logistic_score(fm.fit_logistic(Xl, yl, lam=10.0), Xt), yt))
        w = fm.fit_logistic(enc.features(Xl), yl, lam=1.0)
        probe.append(auc_rank(fm.logistic_score(w, enc.features(Xt)), yt))
    assert np.mean(probe) > np.mean(raw) + 0.05
