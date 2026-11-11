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


def calibrate_regions(verts, tris, region, source, pts, t_meas, v_init, bounds=(0.05, 3.0), fixed=None,
                      max_nfev=None):
    """Fit one speed per region so eikonal times at vertex indices `pts` match `t_meas`.

    The offset is solved in closed form at every step (eq-m33-offset). `fixed` maps region index to
    a speed that is not fitted (for example 0 for block). Returns (speeds for all regions, t0, cost).
    """
    region = np.asarray(region, int)
    n_reg = region.max() + 1
    fixed = dict(fixed or {})
    free = np.array([r for r in range(n_reg) if r not in fixed], int)

    def speeds_of(log_v):
        v = np.empty(n_reg)
        for r, s in fixed.items():
            v[r] = s
        v[free] = np.exp(log_v)
        return v

    def predict(log_v):
        T = mapping.eikonal(verts, tris, source, speeds_of(log_v)[region])
        return T[pts]

    def residual(log_v):
        ts = predict(log_v)
        return ts + best_offset(ts, t_meas) - t_meas

    x0 = np.log(np.broadcast_to(np.asarray(v_init, float), (n_reg,))[free])
    lb, ub = np.log(bounds[0]), np.log(bounds[1])
    sol = least_squares(residual, x0, bounds=(lb, ub), diff_step=1e-3, max_nfev=max_nfev)
    ts = predict(sol.x)
    return speeds_of(sol.x), best_offset(ts, t_meas), float(np.sum(sol.fun**2))


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


# ---------------------------------------------------------------------------- openCARP files
# Formats from the CARP/openCARP file-format documentation: a node file (.pts) with a header line
# giving the number of nodes, then one "x y z" line per node in micrometres; an element file (.elem)
# with a header giving the number of elements, then "Tr n0 n1 n2 tag" per triangle (0-based node
# indices); a fibre file (.lon) with a header giving the number of fibre vectors per element (1 here),
# then one "fx fy fz" line per element.

def write_opencarp(basename, verts_mm, tris, tags, fibres):
    """Write basename.pts / .elem / .lon. Coordinates in mm are written in micrometres."""
    from pathlib import Path

    base = Path(basename)
    verts_um = np.asarray(verts_mm, float) * 1000.0
    with open(base.with_suffix(".pts"), "w") as f:
        f.write(f"{len(verts_um)}\n")
        for x, y, z in verts_um:
            f.write(f"{x:.3f} {y:.3f} {z:.3f}\n")
    with open(base.with_suffix(".elem"), "w") as f:
        f.write(f"{len(tris)}\n")
        for (a, b, c), t in zip(np.asarray(tris, int), np.asarray(tags, int)):
            f.write(f"Tr {a} {b} {c} {t}\n")
    fib = np.asarray(fibres, float)
    fib = fib / np.linalg.norm(fib, axis=1, keepdims=True)
    with open(base.with_suffix(".lon"), "w") as f:
        f.write("1\n")
        for x, y, z in fib:
            f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")
    return [base.with_suffix(s) for s in (".pts", ".elem", ".lon")]


def read_opencarp(basename):
    """Read files written by write_opencarp. Returns (verts in mm, tris, tags, fibres)."""
    from pathlib import Path

    base = Path(basename)
    pts = np.loadtxt(base.with_suffix(".pts"), skiprows=1, ndmin=2) / 1000.0
    rows = [line.split() for line in base.with_suffix(".elem").read_text().splitlines()[1:]]
    assert all(r[0] == "Tr" for r in rows)
    tris = np.array([[int(v) for v in r[1:4]] for r in rows])
    tags = np.array([int(r[4]) for r in rows])
    fib = np.loadtxt(base.with_suffix(".lon"), skiprows=1, ndmin=2)
    return pts, tris, tags, fib


def tangent_fibres(verts, tris):
    """A unit vector in the plane of each triangle (its first edge). Enough for an isotropic twin."""
    e = verts[tris[:, 1]] - verts[tris[:, 0]]
    return e / np.linalg.norm(e, axis=1, keepdims=True)
