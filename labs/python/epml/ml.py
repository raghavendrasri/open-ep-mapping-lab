"""Evaluation tools for module m35 (machine learning in EP mapping).

Plain NumPy/SciPy implementations, so each formula is visible; tests/test_m35_*.py checks them
against scikit-learn and against simulation. See modules/m35-machine-learning.qmd, Derivations.
"""

import numpy as np
from scipy import optimize
from scipy.special import expit, logit
from scipy.stats import rankdata

# ---------------------------------------------------------------- agreement and label noise


def cohen_kappa(a, b):
    """Cohen's kappa for two labelers: (p_o - p_e) / (1 - p_e)."""
    a, b = np.asarray(a), np.asarray(b)
    cats = np.union1d(a, b)
    p_o = np.mean(a == b)
    p_e = sum(np.mean(a == c) * np.mean(b == c) for c in cats)
    return (p_o - p_e) / (1.0 - p_e)


def measured_accuracy(true_accuracy, flip_rate):
    """Accuracy measured against labels that are wrong at rate eps, for a binary task where model
    errors and label errors are independent: a (1 - eps) + (1 - a) eps."""
    a, e = true_accuracy, flip_rate
    return a * (1 - e) + (1 - a) * e


def flip_labels(y, flip_rate, rng):
    """Binary labels with each one flipped independently with probability flip_rate."""
    y = np.asarray(y)
    return np.where(rng.random(y.shape) < flip_rate, 1 - y, y)


# ---------------------------------------------------------------- clustered records


def design_effect(records_per_patient, icc):
    """Design effect 1 + (m - 1) r for m records per patient with intracluster correlation r."""
    return 1.0 + (records_per_patient - 1) * icc


def effective_sample_size(n_records, records_per_patient, icc):
    """n / (1 + (m - 1) r): how many independent records the clustered records are worth."""
    return n_records / design_effect(records_per_patient, icc)


def clustered_values(n_patients, records_per_patient, icc, rng):
    """Unit-variance values with correlation icc between records of the same patient."""
    patient = rng.normal(0.0, np.sqrt(icc), (n_patients, 1))
    record = rng.normal(0.0, np.sqrt(1.0 - icc), (n_patients, records_per_patient))
    return patient + record


# ---------------------------------------------------------------- performance


def predictive_values(sensitivity, specificity, prevalence):
    """PPV and NPV from sensitivity, specificity and prevalence (Bayes' rule)."""
    se, sp, pi = sensitivity, specificity, prevalence
    ppv = se * pi / (se * pi + (1 - sp) * (1 - pi))
    npv = sp * (1 - pi) / (sp * (1 - pi) + (1 - se) * pi)
    return ppv, npv


def auc_rank(scores, labels):
    """AUC as the probability that a random positive outscores a random negative (ties count 1/2),
    computed from ranks (Mann-Whitney U / (n1 n0))."""
    scores, labels = np.asarray(scores, dtype=float), np.asarray(labels)
    ranks = rankdata(scores)  # average ranks for ties
    n1 = int(np.sum(labels == 1))
    n0 = len(labels) - n1
    u = ranks[labels == 1].sum() - n1 * (n1 + 1) / 2.0
    return u / (n1 * n0)


def roc_points(scores, labels):
    """False- and true-positive rates for every threshold, from (0, 0) to (1, 1)."""
    scores, labels = np.asarray(scores, dtype=float), np.asarray(labels)
    order = np.argsort(-scores, kind="stable")
    s, y = scores[order], labels[order]
    distinct = np.r_[np.nonzero(np.diff(s))[0], len(s) - 1]  # last index of each score value
    tp = np.cumsum(y == 1)[distinct]
    fp = np.cumsum(y == 0)[distinct]
    tpr = np.r_[0.0, tp / max(tp[-1], 1)]
    fpr = np.r_[0.0, fp / max(fp[-1], 1)]
    return fpr, tpr


# ---------------------------------------------------------------- probabilities


def brier_score(p, y):
    """Mean squared difference between predicted probability and outcome (binary form)."""
    p, y = np.asarray(p, dtype=float), np.asarray(y, dtype=float)
    return np.mean((p - y) ** 2)


def calibration_slope_intercept(p, y):
    """Fit logit P(y = 1) = alpha + beta logit(p) by maximum likelihood. Returns (alpha, beta)."""
    x = logit(np.clip(np.asarray(p, dtype=float), 1e-12, 1 - 1e-12))
    y = np.asarray(y, dtype=float)

    def nll(theta):
        z = theta[0] + theta[1] * x
        return np.sum(np.logaddexp(0.0, z) - y * z)

    def grad(theta):
        r = expit(theta[0] + theta[1] * x) - y
        return np.array([r.sum(), (r * x).sum()])

    res = optimize.minimize(nll, x0=[0.0, 1.0], jac=grad, method="BFGS")
    return float(res.x[0]), float(res.x[1])


def binormal_auc(separation):
    """AUC when negative scores are N(0, 1) and positive scores N(d, 1): Phi(d / sqrt(2)),
    because the difference of a positive and a negative score is N(d, 2)."""
    from scipy.stats import norm

    return float(norm.cdf(separation / np.sqrt(2.0)))
