"""Locating activation origins from the ECG: a forward model, regression features and active pace-mapping (m41).

Equations (module m41):
  eq-m41-integral  QRS integral of a lead as a solid-angle-weighted sum of activation times
  eq-m41-linear    least-squares map from ECG features to origin coordinates
  eq-m41-geodesic  geodesic error on a sphere and its relation to the chord
  eq-m41-corr      pace-map similarity: mean Pearson correlation over leads
  eq-m41-gp        Gaussian-process posterior mean and variance
  eq-m41-ei        expected improvement in closed form

Forward model (an approximate model chosen for intuition, used by the lab and demos): the left
ventricle is a closed ellipsoidal surface; when a surface element activates, a uniform double layer
switches on there. In an infinite homogeneous medium the potential at an electrode is then
proportional to the solid angle of the activated part of the surface. It ignores the torso boundary
and its inhomogeneities, wall thickness, fibre direction and repolarization. Positions in mm, times
in ms, potentials in arbitrary units.
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.stats import norm

from .mapping import icosphere

LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# Electrode positions (mm) in a torso frame: x to the patient's left, y anterior, z superior. The
# heart centre is at the origin. Limb electrodes are placed far away; precordial electrodes on the
# anterior chest. Illustrative positions, not measured anatomy.
ELECTRODES = {
    "RA": (-350.0, 0.0, 300.0), "LA": (350.0, 0.0, 300.0), "LL": (150.0, 0.0, -450.0),
    "V1": (-30.0, 110.0, 30.0), "V2": (20.0, 115.0, 30.0), "V3": (55.0, 110.0, 10.0),
    "V4": (85.0, 100.0, -10.0), "V5": (120.0, 75.0, -10.0), "V6": (145.0, 35.0, -10.0),
}


def rotation(axis, angle_deg):
    """Rotation matrix about a unit axis (Rodrigues)."""
    k = np.asarray(axis, float)
    k = k / np.linalg.norm(k)
    a = np.deg2rad(angle_deg)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


def lv_mesh(semi_axes=(45.0, 25.0, 25.0), subdivisions=3, R=None, centre=(0.0, 0.0, 0.0)):
    """Ellipsoidal left-ventricle surface: an icosphere scaled to the semi-axes (long axis first),
    rotated by R and moved to centre. Vertex order is the same for every call with the same
    subdivisions, so vertex i is the 'same' anatomical site in every virtual patient."""
    v, t = icosphere(1.0, subdivisions)
    v = v * np.asarray(semi_axes, float)
    if R is not None:
        v = v @ np.asarray(R).T
    return v + np.asarray(centre, float), t


def normals_areas(verts, tris):
    """Outward unit normals and areas per vertex (one third of each adjacent triangle)."""
    a, b, c = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    fn = np.cross(b - a, c - a)                          # length = 2 * triangle area
    centre = verts.mean(0)
    flip = np.einsum("ij,ij->i", fn, (a + b + c) / 3 - centre) < 0
    fn[flip] *= -1
    n = np.zeros_like(verts)
    area = np.zeros(len(verts))
    fa = np.linalg.norm(fn, axis=1) / 2
    for k in range(3):
        np.add.at(n, tris[:, k], fn)
        np.add.at(area, tris[:, k], fa / 3)
    return n / np.linalg.norm(n, axis=1, keepdims=True), area


def edge_distances(verts, tris, sources=None):
    """Shortest paths along mesh edges (mm) from each source vertex (all vertices if None). Edge paths
    differ from true geodesics: zig-zags add length, while straight chords cut a little off curved
    arcs. On the 642-vertex icosphere they are about 6% longer on average and at most about 20%
    (tests/test_m41_origins.py)."""
    e = np.unique(np.sort(np.vstack([tris[:, [0, 1]], tris[:, [1, 2]], tris[:, [2, 0]]]), axis=1), axis=0)
    w = np.linalg.norm(verts[e[:, 0]] - verts[e[:, 1]], axis=1)
    n = len(verts)
    G = coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
    return dijkstra(G, directed=False, indices=sources)


def solid_angles(verts, normals, areas, electrodes):
    """Omega[e, j] = A_j n_j . (x_j - e) / |x_j - e|^3: solid angle of surface element j seen from
    electrode e. For a closed surface and an electrode outside it, each row sums to about zero."""
    E = np.asarray(electrodes, float)
    d = verts[None, :, :] - E[:, None, :]
    return areas[None, :] * np.einsum("ejk,jk->ej", d, normals) / np.linalg.norm(d, axis=2) ** 3


def electrode_potentials(Omega, tau, t, rise=2.0, scale=1.0):
    """phi_e(t) = scale * sum_j Omega_ej * s(t - tau_j), with a smooth step s of 10-90% rise time
    about `rise` ms (illustrative)."""
    t = np.asarray(t, float)
    s = 0.5 * (1 + np.tanh((t[None, :] - np.asarray(tau)[:, None]) / (rise / 2.2)))
    return scale * Omega @ s


def leads12(phi_electrodes, names=tuple(ELECTRODES)):
    """Twelve standard leads from the nine electrode signals (rows ordered as names)."""
    p = dict(zip(names, phi_electrodes))
    wct = (p["RA"] + p["LA"] + p["LL"]) / 3
    out = [p["LA"] - p["RA"], p["LL"] - p["RA"], p["LL"] - p["LA"],
           p["RA"] - (p["LA"] + p["LL"]) / 2, p["LA"] - (p["RA"] + p["LL"]) / 2, p["LL"] - (p["RA"] + p["LA"]) / 2]
    out += [p[f"V{k}"] - wct for k in range(1, 7)]
    return np.array(out)


def qrs_integral(Omega, tau, T=120.0, scale=1.0):
    """eq-m41-integral for an ideal step: integral over [0, T] of phi_e is scale * sum_j Omega_ej (T - tau_j)_+.
    Returns the twelve lead integrals (units: potential x ms)."""
    w = np.clip(T - np.asarray(tau, float), 0, None)
    return leads12(scale * Omega @ w)


def pacemap_corr(a, b):
    """eq-m41-corr: mean over leads of the Pearson correlation between two (12, n_t) signals."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    a = a - a.mean(1, keepdims=True)
    b = b - b.mean(1, keepdims=True)
    num = (a * b).sum(1)
    den = np.sqrt((a * a).sum(1) * (b * b).sum(1))
    return float(np.mean(num / np.where(den > 0, den, 1)))


def fit_linear(X, Y, ridge=0.0):
    """eq-m41-linear: least-squares W, b with Y ~ X W + b (optional ridge on W)."""
    X = np.asarray(X, float)
    A = np.c_[X, np.ones(len(X))]
    P = np.eye(A.shape[1]) * ridge
    P[-1, -1] = 0.0
    coef = np.linalg.solve(A.T @ A + P, A.T @ np.asarray(Y, float))
    return coef[:-1], coef[-1]


def sphere_geodesic(u, v, R=1.0):
    """eq-m41-geodesic: great-circle distance between points u and v on a sphere of radius R."""
    u = np.asarray(u, float) / np.linalg.norm(u, axis=-1, keepdims=True)
    v = np.asarray(v, float) / np.linalg.norm(v, axis=-1, keepdims=True)
    return R * np.arccos(np.clip(np.sum(u * v, axis=-1), -1, 1))


# --------------------------------------------------------------------------------------------
# Gaussian process and expected improvement (Frazier 2018, eqs. 3 and 8)


def rbf(A, B, ell, sf):
    d2 = ((np.asarray(A)[:, None, :] - np.asarray(B)[None, :, :]) ** 2).sum(-1)
    return sf**2 * np.exp(-0.5 * d2 / ell**2)


def gp_posterior(Xtr, ytr, Xte, ell=15.0, sf=1.0, sn=1e-3, mean=0.0):
    """eq-m41-gp: posterior mean and variance of a zero-mean-plus-constant GP with an RBF kernel."""
    Xtr, Xte = np.atleast_2d(Xtr), np.atleast_2d(Xte)
    K = rbf(Xtr, Xtr, ell, sf) + sn**2 * np.eye(len(Xtr))
    Ks = rbf(Xte, Xtr, ell, sf)
    L = np.linalg.cholesky(K)
    alpha = np.linalg.solve(L.T, np.linalg.solve(L, np.asarray(ytr, float) - mean))
    mu = mean + Ks @ alpha
    v = np.linalg.solve(L, Ks.T)
    var = np.clip(sf**2 - (v * v).sum(0), 0, None)
    return mu, var


def expected_improvement(mu, sigma, best, xi=0.0):
    """eq-m41-ei for maximization: EI = d Phi(d/s) + s phi(d/s), d = mu - best - xi; EI = max(d, 0) when s = 0."""
    mu, sigma = np.asarray(mu, float), np.asarray(sigma, float)
    d = mu - best - xi
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(sigma > 0, d / sigma, 0.0)
        ei = d * norm.cdf(z) + sigma * norm.pdf(z)
    return np.where(sigma > 0, ei, np.maximum(d, 0.0))


def active_pacemap(similarity, coords, start, n_total, ell=15.0, sf=1.0, sn=1e-3, xi=0.0, rule="ei", rng=None, allowed=None):
    """Sequential pace-mapping on candidate sites `coords` (n, 3) with known similarity values.

    Starts from the indices in `start`; each further pacing site maximizes expected improvement of the
    GP posterior (rule='ei') or is drawn at random (rule='random') among allowed, unpaced sites.
    Returns the list of paced indices in order."""
    rng = rng or np.random.default_rng()
    paced = list(start)
    allowed = np.ones(len(coords), bool) if allowed is None else np.asarray(allowed, bool)
    while len(paced) < n_total:
        cand = np.flatnonzero(allowed & ~np.isin(np.arange(len(coords)), paced))
        if rule == "random":
            paced.append(int(rng.choice(cand)))
            continue
        y = similarity[paced]
        m = float(np.mean(y))
        mu, var = gp_posterior(coords[paced], y, coords[cand], ell, sf, sn, mean=m)
        ei = expected_improvement(mu, np.sqrt(var), float(np.max(y)), xi)
        paced.append(int(cand[np.argmax(ei)]))
    return paced


def sequential_patient_fit(X, coords, dist, target, n_remote=4, n_total=10, radius=15.0, rng=None):
    """Patient-specific localization (eq-m41-linear) with sequential pacing: pace n_remote random sites,
    fit, predict the target, then pace a random unpaced site within `radius` mm (mesh distance) of the
    current prediction, refit, and repeat until n_total sites. Returns the predicted vertex after each
    fit, starting with the fit on the remote sites."""
    rng = rng or np.random.default_rng()
    paced = list(rng.choice(len(coords), n_remote, replace=False))
    preds = []
    while True:
        W, b = fit_linear(X[paced], coords[paced])
        p = X[target] @ W + b
        idx = int(np.argmin(((coords - p) ** 2).sum(1)))
        preds.append(idx)
        if len(paced) >= n_total:
            return preds
        near = np.flatnonzero((dist[idx] <= radius) & ~np.isin(np.arange(len(coords)), paced))
        if len(near) == 0:
            near = np.flatnonzero(~np.isin(np.arange(len(coords)), paced))
        paced.append(int(rng.choice(near)))
