"""m35 equation checks: agreement, label noise, clustered data, performance and calibration.

Each test checks an equation in modules/m35-machine-learning.qmd against scikit-learn, SymPy or
simulation.
"""

import numpy as np
import pytest
import sympy as sp
from scipy.special import expit, logit
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, cohen_kappa_score, roc_auc_score, roc_curve

from epml import ml


def test_kappa_matches_sklearn():
    """eq-m35-kappa: kappa = (p_o - p_e) / (1 - p_e), against scikit-learn on random labels."""
    rng = np.random.default_rng(1)
    a = rng.integers(0, 3, 500)
    b = np.where(rng.random(500) < 0.7, a, rng.integers(0, 3, 500))
    assert ml.cohen_kappa(a, b) == pytest.approx(cohen_kappa_score(a, b), abs=1e-12)


def test_kappa_hand_worked():
    """eq-m35-kappa on a 2 x 2 table: 40 yes/yes, 10 yes/no, 10 no/yes, 40 no/no gives p_o = 0.8,
    p_e = 0.5 and kappa = 0.6."""
    a = np.r_[np.ones(50), np.zeros(50)]
    b = np.r_[np.ones(40), np.zeros(10), np.ones(10), np.zeros(40)]
    assert ml.cohen_kappa(a, b) == pytest.approx(0.6)


@pytest.mark.parametrize("acc,eps", [(1.0, 0.1), (0.9, 0.05), (0.8, 0.2)])
def test_label_noise_ceiling(acc, eps):
    """eq-m35-label-ceiling: measured accuracy = a (1 - eps) + (1 - a) eps; a perfect model scores 1 - eps."""
    rng = np.random.default_rng(int(100 * acc + 10 * eps))
    truth = rng.integers(0, 2, 400_000)
    pred = np.where(rng.random(truth.shape) < acc, truth, 1 - truth)
    labels = ml.flip_labels(truth, eps, rng)
    assert np.mean(pred == labels) == pytest.approx(ml.measured_accuracy(acc, eps), abs=3e-3)
    assert ml.measured_accuracy(1.0, eps) == pytest.approx(1 - eps)


@pytest.mark.parametrize("m,icc", [(5, 0.2), (20, 0.5)])
def test_design_effect_by_simulation(m, icc):
    """eq-m35-design-effect: the variance of a mean over n clustered records is (1 + (m - 1) r) times
    that over n independent records, so the records are worth n / (1 + (m - 1) r)."""
    rng = np.random.default_rng(m)
    n_patients, reps = 40, 20_000
    means = np.array([ml.clustered_values(n_patients, m, icc, rng).mean() for _ in range(reps)])
    n = n_patients * m
    assert means.var() * n == pytest.approx(ml.design_effect(m, icc), rel=0.04)
    assert ml.effective_sample_size(n, m, icc) == pytest.approx(n / (1 + (m - 1) * icc))


def test_ppv_symbolic_and_numeric():
    """eq-m35-ppv: PPV = Se pi / (Se pi + (1 - Sp)(1 - pi)) is Bayes' rule; check it by simulation too."""
    se, sp_, pi = sp.symbols("Se Sp pi", positive=True)
    p_pos = se * pi + (1 - sp_) * (1 - pi)  # total probability of a positive test
    assert sp.simplify(se * pi / p_pos - (se * pi / (se * pi + (1 - sp_) * (1 - pi)))) == 0
    rng = np.random.default_rng(4)
    disease = rng.random(1_000_000) < 0.05
    test_pos = np.where(disease, rng.random(disease.size) < 0.9, rng.random(disease.size) < 0.1)
    ppv, npv = ml.predictive_values(0.9, 0.9, 0.05)
    assert disease[test_pos].mean() == pytest.approx(ppv, abs=4e-3)
    assert (~disease[~test_pos]).mean() == pytest.approx(npv, abs=1e-3)


def test_auc_is_ranking_probability():
    """eq-m35-auc: rank-based AUC equals scikit-learn's ROC area and the trapezoidal area of our ROC
    points, with ties counted as one half."""
    rng = np.random.default_rng(5)
    y = rng.integers(0, 2, 2000)
    scores = np.round(rng.normal(y * 1.2, 1.0), 1)  # rounding creates ties
    auc = ml.auc_rank(scores, y)
    assert auc == pytest.approx(roc_auc_score(y, scores), abs=1e-12)
    fpr, tpr = ml.roc_points(scores, y)
    assert np.trapezoid(tpr, fpr) == pytest.approx(auc, abs=1e-12)
    fpr_sk, tpr_sk, _ = roc_curve(y, scores, drop_intermediate=False)
    assert np.allclose(fpr, fpr_sk) and np.allclose(tpr, tpr_sk)
    pairs = (scores[y == 1][:, None] > scores[y == 0][None, :]).mean() + 0.5 * (
        scores[y == 1][:, None] == scores[y == 0][None, :]).mean()
    assert pairs == pytest.approx(auc, abs=1e-12)


def test_brier_matches_sklearn_and_two_category_form():
    """eq-m35-brier: the binary Brier score matches scikit-learn; summing over both categories, as in
    Brier's multi-category form, gives exactly twice the binary value."""
    rng = np.random.default_rng(6)
    p = rng.random(1000)
    y = (rng.random(1000) < p).astype(int)
    bs = ml.brier_score(p, y)
    assert bs == pytest.approx(brier_score_loss(y, p), abs=1e-12)
    two_cat = np.mean((p - y) ** 2 + ((1 - p) - (1 - y)) ** 2)
    assert two_cat == pytest.approx(2 * bs)


@pytest.mark.parametrize("alpha,beta", [(0.0, 1.0), (0.0, 0.5), (0.5, 1.0), (-0.3, 1.6)])
def test_calibration_slope_and_intercept_recovered(alpha, beta):
    """eq-m35-calibration: outcomes drawn from logit P(y=1) = alpha + beta logit(p) give back alpha and
    beta, matching scikit-learn's unpenalized logistic regression."""
    rng = np.random.default_rng(7)
    p = expit(rng.normal(0.0, 1.5, 200_000))
    y = (rng.random(p.size) < expit(alpha + beta * logit(p))).astype(int)
    a_hat, b_hat = ml.calibration_slope_intercept(p, y)
    assert (a_hat, b_hat) == pytest.approx((alpha, beta), abs=0.03)
    sk = LogisticRegression(C=np.inf).fit(logit(p)[:, None], y)  # C = inf: unpenalized (scikit-learn >= 1.8)
    assert (a_hat, b_hat) == pytest.approx((sk.intercept_[0], sk.coef_[0, 0]), abs=1e-3)


def test_too_extreme_predictions_give_slope_below_one():
    """Text under eq-m35-calibration: predictions pushed too far towards 0 and 1 (true logit times k > 1)
    give a calibration slope of about 1/k < 1; too timid predictions give a slope above 1."""
    rng = np.random.default_rng(8)
    true_logit = rng.normal(0.0, 1.0, 200_000)
    y = (rng.random(true_logit.size) < expit(true_logit)).astype(int)
    for k in (2.0, 0.5):
        _, slope = ml.calibration_slope_intercept(expit(k * true_logit), y)
        assert slope == pytest.approx(1 / k, rel=0.05)


def test_label_ceiling_bound():
    """Text under eq-m35-label-ceiling: a (1 - eps) + (1 - a) eps = eps + a (1 - 2 eps) <= 1 - eps for
    0 <= a <= 1 and eps < 1/2."""
    a, e = sp.symbols("a epsilon", nonnegative=True)
    expr = a * (1 - e) + (1 - a) * e
    assert sp.expand(expr - (e + a * (1 - 2 * e))) == 0
    assert sp.simplify((1 - e) - expr - (1 - a) * (1 - 2 * e)) == 0  # gap is (1 - a)(1 - 2 eps) >= 0


def test_overfitting_gives_slope_below_one():
    """Key takeaway under eq-m35-calibration: an unpenalized logistic model fitted to 150 records with
    one informative and 30 noise features is too extreme on new data (calibration slope well below 1)."""
    rng = np.random.default_rng(9)

    def draw(n):
        x = rng.normal(size=(n, 31))
        y = (rng.random(n) < expit(1.0 * x[:, 0])).astype(int)
        return x, y

    x_tr, y_tr = draw(150)
    x_te, y_te = draw(100_000)
    model = LogisticRegression(C=np.inf, max_iter=5000).fit(x_tr, y_tr)
    _, slope = ml.calibration_slope_intercept(model.predict_proba(x_te)[:, 1], y_te)
    assert slope < 0.7


@pytest.mark.parametrize("d", [0.0, 0.8, 1.5, 3.0])
def test_binormal_auc(d):
    """Demo m35-d2: with negatives ~ N(0, 1) and positives ~ N(d, 1), AUC = Phi(d / sqrt 2)."""
    rng = np.random.default_rng(15)
    neg = rng.normal(0, 1, 4000)
    pos = rng.normal(d, 1, 4000)
    y = np.r_[np.zeros(4000), np.ones(4000)]
    assert roc_auc_score(y, np.r_[neg, pos]) == pytest.approx(ml.binormal_auc(d), abs=0.012)
