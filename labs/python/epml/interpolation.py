"""m24 · Interpolation, activation maps and isochrones.

Times in ms, lengths in mm, conduction velocity in mm/ms (= m/s). Meshes are (V, F) arrays as in m06. MIT License.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from .meshes import cotan_matrix

# ---------------------------------------------------------------- linear interpolation (eq-m24-linear)


def linear_1d(x_data, t_data, x):
    """Piecewise-linear interpolation along a line (x_data increasing)."""
    return np.interp(x, x_data, t_data)


def linear_error_bound(h, max_second_derivative):
    """Largest error of piecewise-linear interpolation with spacing h: h^2 max|T''| / 8."""
    return h**2 * max_second_derivative / 8.0


def focal_time(x, y, c=1.0, x0=0.0, y0=0.0):
    """Activation time from a point source in a uniform sheet."""
    return np.hypot(np.asarray(x, float) - x0, np.asarray(y, float) - y0) / c


def barycentric(p, a, b, c):
    """Barycentric coordinates of 2D point p in triangle (a, b, c)."""
    T = np.array([[a[0] - c[0], b[0] - c[0]], [a[1] - c[1], b[1] - c[1]]])
    l1, l2 = np.linalg.solve(T, np.asarray(p, float)[:2] - np.asarray(c, float)[:2])
    return np.array([l1, l2, 1 - l1 - l2])


# ---------------------------------------------------------------- inverse-distance weighting (eq-m24-idw)


def idw_points(points, values, query, p=2.0):
    """Inverse-distance-weighted values at query points (2D or 3D Euclidean distances)."""
    points = np.asarray(points, float)
    query = np.atleast_2d(np.asarray(query, float))
    d = np.linalg.norm(query[:, None, :] - points[None, :, :], axis=2)
    out = np.empty(len(query))
    for i in range(len(query)):
        hit = d[i] < 1e-12
        if hit.any():
            out[i] = np.mean(np.asarray(values)[hit])
        else:
            w = d[i] ** -p
            out[i] = np.dot(w, values) / w.sum()
    return out


def idw_gradient(points, values, query, p=2.0, eps=1e-4):
    """Central-difference gradient of the IDW field."""
    query = np.atleast_2d(np.asarray(query, float))
    g = np.zeros_like(query)
    for k in range(query.shape[1]):
        e = np.zeros(query.shape[1])
        e[k] = eps
        g[:, k] = (idw_points(points, values, query + e, p) - idw_points(points, values, query - e, p)) / (2 * eps)
    return g


# ---------------------------------------------------------------- harmonic interpolation (eq-m24-harmonic)


def harmonic(V, F, known_idx, known_values):
    """Solve L T = 0 on unknown vertices with T fixed at the known ones (cotangent Laplacian, m06)."""
    n = len(V)
    L = cotan_matrix(V, F).tocsr()
    known_idx = np.asarray(known_idx)
    unknown = np.setdiff1d(np.arange(n), known_idx)
    T = np.zeros(n)
    T[known_idx] = known_values
    rhs = -L[unknown][:, known_idx] @ np.asarray(known_values, float)
    T[unknown] = spsolve(L[unknown][:, unknown].tocsc(), rhs)
    return T


# ---------------------------------------------------------------- isochrones (eq-m24-isochrone)


def edge_crossing(ti, tj, tau):
    """Fraction along an edge (from i to j) where linear interpolation reaches tau; None if it does not."""
    if (ti - tau) * (tj - tau) > 0 or ti == tj:
        return None
    return (tau - ti) / (tj - ti)


def isochrone_segments(V, F, T, tau):
    """Line segments of the level set T = tau on a triangle mesh (marching triangles)."""
    segs = []
    for f in F:
        pts = []
        for a, b in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            lam = edge_crossing(T[a], T[b], tau)
            if lam is not None and 0 <= lam <= 1:
                pts.append(V[a] + lam * (V[b] - V[a]))
        if len(pts) >= 2:
            segs.append((pts[0], pts[1]))
    return segs


def isochrone_spacing(c, dtau):
    """Distance between isochrones dtau apart for a front at speed c."""
    return c * dtau


# ---------------------------------------------------------------- block and coverage (eq-m24-block)


def apparent_velocity_across_block(h, delta_t):
    """Linear interpolation across a line of block with a jump delta_t between points h apart reads speed h / delta_t."""
    return h / delta_t


def coverage_fraction(density, radius):
    """Expected fraction of a surface within a fill radius of at least one of randomly (Poisson) placed points."""
    return 1.0 - np.exp(-density * np.pi * radius**2)


def coverage_simulated(points, radius, grid):
    """Fraction of grid points within the radius of at least one point."""
    d = np.min(np.linalg.norm(grid[:, None, :] - np.asarray(points)[None, :, :], axis=2), axis=1)
    return float(np.mean(d <= radius))
