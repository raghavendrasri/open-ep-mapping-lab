"""m33 helpers: calibrating a simple twin to measured activation times.

Uses the eikonal solver in epml.mapping. Lengths in mm, times in ms, speeds in mm/ms.
"""

import numpy as np
from scipy.optimize import least_squares

from . import mapping


def aniso_eikonal_flat(points, origin, fibre, v_f, v_t):
    """eq-m33-eikonal-aniso: exact activation on a flat sheet with uniform fibres (2D points)."""
    f = np.asarray(fibre, float) / np.linalg.norm(fibre)
    n = np.array([-f[1], f[0]])
    d = np.asarray(points, float) - np.asarray(origin, float)
    a, b = d @ f, d @ n
    return np.sqrt((a / v_f) ** 2 + (b / v_t) ** 2)


def speed_tensor(fibre, v_f, v_t):
    """D = v_f^2 f f^T + v_t^2 (I - f f^T)."""
    f = np.asarray(fibre, float) / np.linalg.norm(fibre)
    P = np.outer(f, f)
    return v_f**2 * P + v_t**2 * (np.eye(len(f)) - P)


def best_offset(t_sim, t_meas):
    """eq-m33-offset: the timing offset that minimizes the squared misfit, mean(T_meas - T_sim)."""
    return float(np.mean(np.asarray(t_meas, float) - np.asarray(t_sim, float)))


def calibrate_regions(verts, tris, region, source, pts, t_meas, v_init, bounds=(0.05, 3.0)):
    """Fit one speed per region so eikonal times at vertex indices `pts` match `t_meas`.

    The offset is solved in closed form at every step (eq-m33-offset). Returns (speeds, t0, cost).
    """
    region = np.asarray(region, int)
    n_reg = region.max() + 1

    def predict(log_v):
        T = mapping.eikonal(verts, tris, source, np.exp(log_v)[region])
        return T[pts]

    def residual(log_v):
        ts = predict(log_v)
        return ts + best_offset(ts, t_meas) - t_meas

    x0 = np.log(np.broadcast_to(np.asarray(v_init, float), (n_reg,)))
    lb, ub = np.log(bounds[0]), np.log(bounds[1])
    sol = least_squares(residual, x0, bounds=(lb, ub), diff_step=1e-3)
    ts = predict(sol.x)
    return np.exp(sol.x), best_offset(ts, t_meas), float(np.sum(sol.fun**2))


def conductivity_for_speed(sigma_old, v_target, v_sim):
    """eq-m33-cv-scaling: sigma_new = sigma_old (v_target / v_sim)^2."""
    return sigma_old * (v_target / v_sim) ** 2


def kfold_rmse(fit, predict, X, y, k, rng):
    """eq-m33-holdout: cross-validated RMSE. `fit(X, y)` returns a model; `predict(model, X)` values."""
    idx = rng.permutation(len(y))
    folds = np.array_split(idx, k)
    sq = []
    for f in folds:
        train = np.setdiff1d(idx, f)
        model = fit(X[train], y[train])
        sq.append((predict(model, X[f]) - y[f]) ** 2)
    return float(np.sqrt(np.mean(np.concatenate(sq))))
