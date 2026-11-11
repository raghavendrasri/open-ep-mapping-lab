"""m37 equation tests: each numbered equation in modules/m37-ai-ecg.qmd is checked here."""

import numpy as np
import pytest
import sympy as sp

from epml import aiecg as ai
from epml import ml


def test_softmax_sums_to_one_and_is_shift_invariant():
    """eq-m37-softmax"""
    rng = np.random.default_rng(1)
    z = rng.normal(size=(5, 4)) * 10
    p = ai.softmax(z)
    assert np.allclose(p.sum(axis=1), 1)
    assert np.allclose(ai.softmax(z + 123.0), p)
    assert np.allclose(ai.softmax(np.array([[1000.0, 0.0]])), [[1.0, 0.0]])  # no overflow


def test_cross_entropy_gradient_is_p_minus_y_symbolic_and_numeric():
    """eq-m37-ce-grad: d/dz_c of -sum_j y_j log softmax_j(z) equals p_c - y_c."""
    z = sp.symbols("z0:3")
    y = sp.symbols("y0:3")
    denom = sum(sp.exp(zi) for zi in z)
    loss = -sum(yi * sp.log(sp.exp(zi) / denom) for yi, zi in zip(y, z))
    for c in range(3):
        grad = sp.diff(loss, z[c])
        expected = sp.exp(z[c]) / denom - y[c]
        # holds when the labels sum to one
        diff = sp.simplify((grad - expected).subs(y[2], 1 - y[0] - y[1]))
        assert diff == 0
    rng = np.random.default_rng(2)
    zz = rng.normal(size=(1, 4))
    yy = np.eye(4)[[2]]
    num = np.zeros(4)
    for c in range(4):
        e = np.zeros((1, 4))
        e[0, c] = 1e-6
        num[c] = (ai.cross_entropy(zz + e, yy) - ai.cross_entropy(zz - e, yy)) / 2e-6
    assert np.allclose(num, ai.ce_grad(zz, yy)[0], atol=1e-7)


def test_logistic_is_two_class_softmax_and_matches_sklearn():
    """eq-m37-logistic: sigma(u) equals the softmax of scores (0, u); a fitted logistic regression's
    probabilities come from this formula."""
    from sklearn.linear_model import LogisticRegression

    u = np.linspace(-30, 30, 13)
    assert np.allclose(ai.sigmoid(u), ai.softmax(np.c_[np.zeros_like(u), u])[:, 1])
    rng = np.random.default_rng(3)
    X = rng.normal(size=(200, 3))
    y = (X @ [1.0, -2.0, 0.5] + rng.normal(size=200) > 0).astype(int)
    m = LogisticRegression(C=1e6, max_iter=1000).fit(X, y)
    assert np.allclose(ai.logistic_prob(X, m.intercept_[0], m.coef_[0]), m.predict_proba(X)[:, 1])


def test_conv1d_matches_numpy_correlate_and_stride():
    """eq-m37-conv"""
    rng = np.random.default_rng(4)
    x = rng.normal(size=50)
    w = rng.normal(size=7)
    y = ai.conv1d(x, w, b=0.5)
    assert np.allclose(y, np.correlate(x, w, mode="valid") + 0.5)
    y2 = ai.conv1d(x, w, stride=3)
    assert np.allclose(y2, np.correlate(x, w, mode="valid")[::3])
    assert len(y2) == (50 - 7) // 3 + 1


def test_kernel_response_is_the_gain_on_a_sinusoid():
    """eq-m37-kernel-response: a sinusoid through the kernel comes out scaled by |H(f)|."""
    fs = 100.0
    w = np.array([1.0, 0.0, -1.0]) / 2  # a central difference: a high-pass shape
    for f in [1.0, 5.0, 12.5, 25.0]:
        n = np.arange(2000)
        x = np.cos(2 * np.pi * f * n / fs)
        y = ai.conv1d(x, w)
        amp = np.sqrt(2 * np.mean(y[100:-100] ** 2))
        assert amp == pytest.approx(abs(ai.kernel_response(w, fs, f)[0]), rel=2e-3)
    # closed form for this kernel: |H| = |sin(2 pi f / fs)|
    f = np.linspace(0, 50, 11)
    assert np.allclose(np.abs(ai.kernel_response(w, fs, f)), np.abs(np.sin(2 * np.pi * f / fs)))


@pytest.mark.parametrize("kernels,strides", [([3], [1]), ([5, 5, 5], [1, 1, 1]), ([7, 5, 3], [2, 2, 1]),
                                             ([15, 9, 9, 9], [1, 2, 2, 2])])
def test_receptive_field_formula_matches_perturbation(kernels, strides):
    """eq-m37-receptive-field: perturbing input samples one at a time shows exactly r of them reach the
    first output."""
    r = ai.receptive_field(kernels, strides)
    count, seen = ai.empirical_receptive_field(kernels, strides)
    assert count == r
    assert seen == list(range(r))


def test_receptive_field_closed_form_for_equal_layers():
    """eq-m37-receptive-field: L layers of width k and stride 1 give r = 1 + L(k - 1)."""
    k, L = sp.symbols("k L", positive=True, integer=True)
    for kk in [3, 5, 9]:
        for LL in [1, 4, 7]:
            assert ai.receptive_field([kk] * LL) == 1 + LL * (kk - 1)
    assert sp.simplify(1 + sp.Sum(k - 1, (sp.Symbol("l"), 1, L)).doit() - (1 + L * (k - 1))) == 0


def test_rr_features_closed_forms():
    """eq-m37-rr: regular beats give zero variability; alternating intervals a, b give RMSSD = |a - b|."""
    fs = 100.0
    regular = np.arange(0, 1000, 80)
    m, cv, nr = ai.rr_features(regular, fs)
    assert m == pytest.approx(0.8) and cv == pytest.approx(0) and nr == pytest.approx(0)
    a, b = 0.6, 1.0
    rr = np.array([a, b] * 10)
    peaks = np.concatenate([[0], np.cumsum(rr)]) * fs
    m, cv, nr = ai.rr_features(peaks, fs)
    assert m == pytest.approx((a + b) / 2)
    assert nr * m == pytest.approx(abs(a - b))
    assert cv == pytest.approx(np.std(rr, ddof=1) / rr.mean())


def test_synthetic_af_is_irregular_and_sinus_is_regular():
    """eq-m37-rr on the synthetic generator: AF intervals vary far more than sinus intervals."""
    rng = np.random.default_rng(5)
    cv_sinus = np.median([ai.rr_features(ai.synth_ecg("sinus", rng=rng)[1], 100)[1] for _ in range(30)])
    cv_af = np.median([ai.rr_features(ai.synth_ecg("af", rng=rng)[1], 100)[1] for _ in range(30)])
    assert cv_af > 3 * cv_sinus


def test_detector_finds_synthetic_r_peaks():
    rng = np.random.default_rng(6)
    for rhythm in ["sinus", "af"]:
        x, truth = ai.synth_ecg(rhythm, fs=300, duration_s=20, rng=rng)
        found = ai.detect_r_peaks(x, 300)
        matched = sum(np.min(np.abs(found - t)) <= 0.05 * 300 for t in truth)
        assert matched >= 0.95 * len(truth)
        assert len(found) <= 1.05 * len(truth) + 1


def test_screening_yield_matches_ppv():
    """eq-m37-yield: flagged per true case found equals 1/PPV (eq-m35-ppv)."""
    for prev, se, sp_ in [(0.01, 0.9, 0.95), (0.1, 0.8, 0.8), (0.3, 0.95, 0.99)]:
        y = ai.screening_yield(1000, prev, se, sp_)
        assert y["tp"] + y["fp"] == pytest.approx(y["flagged"])
        ppv = ml.predictive_values(se, sp_, prev)[0]
        assert y["per_case"] == pytest.approx(1 / ppv)


def test_prior_shift_recovers_the_bayes_posterior():
    """eq-m37-prior-shift: for binormal scores, adjusting the posterior learned at one prevalence gives
    exactly the posterior at another (same class-conditional densities)."""
    from scipy.stats import norm

    s = np.linspace(-3, 5, 41)
    d = 1.7

    def posterior(prev):
        a = prev * norm.pdf(s, d, 1)
        return a / (a + (1 - prev) * norm.pdf(s, 0, 1))

    assert np.allclose(ai.prior_shift(posterior(0.5), 0.5, 0.05), posterior(0.05))
    assert np.allclose(ai.prior_shift(posterior(0.05), 0.05, 0.3), posterior(0.3))
    assert np.allclose(ai.prior_shift(posterior(0.2), 0.2, 0.2), posterior(0.2))


def test_tiny_cnn_gradients_match_finite_differences():
    """The hand-written backward pass of the NumPy network (eq-m37-conv, eq-m37-ce-grad)."""
    rng = np.random.default_rng(7)
    X = rng.normal(size=(6, 40))
    y = np.array([0, 1, 0, 1, 1, 0])
    net = ai.TinyCNN(n_filters=3, width=5, rng=rng)
    net.b += 0.3  # keep pre-activations away from the ReLU kink
    _, g = net.loss_and_grads(X, y)
    for name, arr in [("W", net.W), ("b", net.b), ("v", net.v)]:
        flat = arr.reshape(-1)
        for i in range(0, flat.size, max(1, flat.size // 6)):
            old = flat[i]
            flat[i] = old + 1e-6
            lp = net.loss_and_grads(X, y)[0]
            flat[i] = old - 1e-6
            lm = net.loss_and_grads(X, y)[0]
            flat[i] = old
            assert (lp - lm) / 2e-6 == pytest.approx(g[name].reshape(-1)[i], abs=1e-6)


def test_tiny_cnn_learns_synthetic_af_without_p_waves():
    """End to end: the small network separates synthetic AF from sinus on held-out patients."""
    rng = np.random.default_rng(8)
    X, y, pid, _ = ai.make_cohort(60, 2, duration_s=6, rng=rng)
    Xs = ai.standardize_records(X)
    train = pid < 40
    net = ai.TinyCNN(n_filters=8, width=31, rng=rng)
    hist = net.fit(Xs[train], y[train], epochs=60, lr=0.15, rng=rng)
    assert hist[-1] < hist[0]
    auc = ml.auc_rank(net.predict_proba(Xs[~train]), y[~train])
    assert auc > 0.85


def test_tiny_cnn_adam_lowers_the_loss():
    rng = np.random.default_rng(9)
    X, y, pid, _ = ai.make_cohort(30, 2, duration_s=6, rng=rng)
    net = ai.TinyCNN(n_filters=4, width=21, rng=rng)
    hist = net.fit(ai.standardize_records(X), y, epochs=30, lr=0.05, rng=rng, optimizer="adam")
    assert hist[-1] < hist[0]
