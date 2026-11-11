"""m45 · Evidence and regulation of AI in EP: sample size, decision curves, drift monitoring and a
change-control check, for the Part VII capstone lab.

Every function implements one numbered equation of module m45 or a step of its lab, and is checked in
tests/test_m45_evidence.py. Nothing here is a regulatory tool: the "PCCP-style" check shows the idea
of acceptance criteria fixed before a model change, not any agency's requirements.
"""

import math

import numpy as np

from .ml import auc_rank, calibration_slope_intercept

Z95 = 1.959963984540054

# ---------------------------------------------------------------------------------------------
# How many patients? (eq-m45-n-sens)


def n_for_sensitivity(se, half_width, prevalence, z=Z95):
    """eq-m45-n-sens (Buderer 1996): patients to enrol so that the confidence interval for a
    sensitivity near `se` has half-width `half_width`, when a share `prevalence` has the condition:
    n = z^2 se (1 - se) / (d^2 * prevalence), rounded up."""
    return int(math.ceil(z * z * se * (1 - se) / (half_width**2 * prevalence)))


def n_for_specificity(sp, half_width, prevalence, z=Z95):
    """The same for specificity, which is estimated on the 1 - prevalence share without the condition."""
    return int(math.ceil(z * z * sp * (1 - sp) / (half_width**2 * (1 - prevalence))))


# ---------------------------------------------------------------------------------------------
# Decision curves (eq-m45-net-benefit)


def net_benefit(y, p, threshold):
    """eq-m45-net-benefit (Vickers and Elkin 2006): TP/n - FP/n * pt / (1 - pt) for the rule
    "act if p >= pt"."""
    y = np.asarray(y, bool)
    act = np.asarray(p, float) >= threshold
    n = len(y)
    tp = np.sum(act & y)
    fp = np.sum(act & ~y)
    return float(tp / n - fp / n * threshold / (1 - threshold))


def net_benefit_treat_all(prevalence, threshold):
    """Acting on everyone: prevalence - (1 - prevalence) pt / (1 - pt). Acting on no one gives 0."""
    return float(prevalence - (1 - prevalence) * threshold / (1 - threshold))


# ---------------------------------------------------------------------------------------------
# Drift monitoring (eq-m45-cusum)


def cusum(x, target, k, h):
    """eq-m45-cusum (Page 1954): S_t = max(0, S_{t-1} + (x_t - target) - k), S_0 = 0; an alarm when
    S_t > h. Detects an upward shift of x. Returns (S, index of the first alarm or None)."""
    s, out, alarm = 0.0, [], None
    for t, v in enumerate(np.asarray(x, float)):
        s = max(0.0, s + (v - target) - k)
        out.append(s)
        if alarm is None and s > h:
            alarm = t
    return np.array(out), alarm


def run_length(k, h, shift, rng, max_len=100_000, sd=1.0):
    """Number of observations until the CUSUM alarm for N(shift, sd) data with target 0."""
    s = 0.0
    for t in range(max_len):
        s = max(0.0, s + rng.normal(shift, sd) - k)
        if s > h:
            return t + 1
    return max_len


# ---------------------------------------------------------------------------------------------
# A model to evaluate and monitor: the RR-interval AF detector of m37 on synthetic ECGs


def regular_share(peaks, fs, tol=0.1):
    """Share of RR intervals within tol (10%) of the record's median RR: near 1 in sinus rhythm,
    lower with occasional early beats, lowest in AF. A new input for the lab's model version 3."""
    rr = np.diff(np.asarray(peaks, float)) / fs
    if rr.size < 2:
        return 0.0
    return float(np.mean(np.abs(rr / np.median(rr) - 1) <= tol))


def rr_feature_rows(records, peaks, fs, extra=False):
    """eq-m37-rr features (coefficient of variation and normalised RMSSD of the RR intervals) for
    each record; with extra=True, also regular_share."""
    from .aiecg import rr_features

    rows = [np.nan_to_num(rr_features(pk, fs)[1:], nan=0.0) for pk in peaks]
    if extra:
        rows = [np.r_[r, regular_share(pk, fs)] for r, pk in zip(rows, peaks)]
    return np.array(rows)


def fit_detector(X, y, lam=1e-3, iters=50):
    """Logistic regression (Newton steps, small ridge) on standardized features. Returns a predict
    function giving probabilities."""
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-12
    Z = np.c_[(X - mu) / sd, np.ones(len(X))]
    w = np.zeros(Z.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
        g = Z.T @ (p - y) + lam * np.r_[w[:-1], 0]
        H = Z.T @ (Z * (p * (1 - p))[:, None]) + lam * np.eye(len(w))
        w -= np.linalg.solve(H, g)

    def predict(Xn):
        Zn = np.c_[(np.asarray(Xn) - mu) / sd, np.ones(len(Xn))]
        return 1 / (1 + np.exp(-np.clip(Zn @ w, -30, 30)))

    return predict


def bootstrap_ci(stat, y, p, groups, n_boot=500, rng=None, level=0.95):
    """Percentile bootstrap interval of stat(y, p), resampling patients (groups), not recordings."""
    rng = np.random.default_rng(0) if rng is None else rng
    y, p, groups = np.asarray(y), np.asarray(p), np.asarray(groups)
    ids = np.unique(groups)
    rows = {g: np.flatnonzero(groups == g) for g in ids}
    vals = []
    for _ in range(n_boot):
        pick = np.concatenate([rows[g] for g in rng.choice(ids, size=len(ids), replace=True)])
        if y[pick].min() == y[pick].max():
            continue
        vals.append(stat(y[pick], p[pick]))
    a = (1 - level) / 2
    return float(np.quantile(vals, a)), float(np.quantile(vals, 1 - a))


def sens_spec(y, p, threshold):
    y = np.asarray(y, bool)
    pos = np.asarray(p) >= threshold
    return float(np.mean(pos[y])), float(np.mean(~pos[~y]))


def report_card(name, y, p, groups, threshold, subgroups=None, thresholds=(0.1, 0.2, 0.3), rng=None):
    """A TRIPOD+AI-style summary of a model's test results (the numbers only; the narrative items
    of the checklist are for the author to write): discrimination with a patient-level bootstrap
    interval, calibration, sensitivity and specificity at the operating threshold with Wilson
    intervals, net benefit at a few thresholds, and specificity in each subgroup that is mostly
    negative (for example each non-AF rhythm)."""
    from .retrieval import wilson_interval

    y = np.asarray(y, int)
    p = np.asarray(p, float)
    se, sp = sens_spec(y, p, threshold)
    n_pos, n_neg = int(y.sum()), int((1 - y).sum())
    intercept, slope = calibration_slope_intercept(np.clip(p, 1e-6, 1 - 1e-6), y)
    card = {
        "model": name,
        "n records": len(y), "n patients": int(len(np.unique(groups))), "prevalence": float(y.mean()),
        "AUC": auc_rank(p, y), "AUC 95% CI": bootstrap_ci(auc_rank_yp, y, p, groups, rng=rng),
        "calibration slope": slope, "calibration intercept": intercept,
        "threshold": threshold,
        "sensitivity": se, "sensitivity 95% CI": wilson_interval(round(se * n_pos), n_pos),
        "specificity": sp, "specificity 95% CI": wilson_interval(round(sp * n_neg), n_neg),
        "net benefit": {t: net_benefit(y, p, t) for t in thresholds},
        "net benefit, treat all": {t: net_benefit_treat_all(y.mean(), t) for t in thresholds},
    }
    if subgroups is not None:
        subgroups = np.asarray(subgroups)
        card["specificity by subgroup"] = {
            str(g): float(np.mean(p[(subgroups == g) & (y == 0)] < threshold))
            for g in np.unique(subgroups) if np.mean(y[subgroups == g] == 0) >= 0.5}
    return card


def auc_rank_yp(y, p):
    return auc_rank(p, y)


def card_markdown(card):
    """The report card as a Markdown table."""
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.3f}"
        if isinstance(v, tuple):
            return "–".join(f"{x:.3f}" for x in v)
        if isinstance(v, dict):
            return "; ".join(f"{k}: {fmt(x)}" for k, x in v.items())
        return str(v)
    lines = ["| Item | Value |", "| --- | --- |"]
    lines += [f"| {k} | {fmt(v)} |" for k, v in card.items()]
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# Change control: acceptance criteria fixed before a model update


def pccp_check(card, criteria):
    """Compare a report card with pre-specified acceptance criteria. criteria: {name: (key, op, value)}
    with op one of ">=", "<=", "between" (value = (lo, hi)). Uses interval lower bounds where the key
    names an interval. Returns ({name: (observed, passed)}, all passed)."""
    out = {}
    for name, (key, op, value) in criteria.items():
        obs = card[key]
        x = obs[0] if isinstance(obs, tuple) and op == ">=" else obs
        if op == ">=":
            ok = x >= value
        elif op == "<=":
            ok = x <= value
        elif op == "between":
            ok = value[0] <= x <= value[1]
        else:
            raise ValueError(op)
        out[name] = (x, bool(ok))
    return out, all(v[1] for v in out.values())
