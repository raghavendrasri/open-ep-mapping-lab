"""m21 · Image integration: threshold segmentation, overlap measures, landmark (Procrustes) registration, iterative
closest point, and the sliding ambiguity of surface registration. MIT License.

Units: lengths in mm; image intensities in relative units (illustrative Hounsfield-like values).
"""

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from scipy.special import ndtr


# ---- eq-m21-threshold: Otsu ----------------------------------------------------------------------------------------

def between_class_variance(hist, centers):
    """sigma_B^2(t) = w0 w1 (mu0 - mu1)^2 for every split point t (between bins t and t+1)."""
    p = hist / hist.sum()
    w0 = np.cumsum(p)
    m = np.cumsum(p * centers)
    mt = m[-1]
    w1 = 1.0 - w0
    with np.errstate(divide="ignore", invalid="ignore"):
        mu0, mu1 = m / w0, (mt - m) / w1
        sb = w0 * w1 * (mu0 - mu1) ** 2
    return np.nan_to_num(sb)


def otsu_threshold(values, bins=256):
    hist, edges = np.histogram(values, bins=bins)
    centers = 0.5 * (edges[:-1] + edges[1:])
    sb = between_class_variance(hist, centers)
    k = int(np.argmax(sb))
    return 0.5 * (centers[k] + centers[k + 1])


def largest_component(mask):
    lab, n = ndimage.label(mask)
    if n == 0:
        return mask
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


# ---- eq-m21-dice --------------------------------------------------------------------------------------------------

def dice(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    return 2.0 * np.sum(a & b) / (a.sum() + b.sum())


def jaccard(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    return np.sum(a & b) / np.sum(a | b)


def gaussian_dice(t, mu0, mu1, sigma, prevalence):
    """Expected Dice of thresholding at t when background ~ N(mu0, sigma), blood ~ N(mu1, sigma), blood fraction p."""
    tp = prevalence * (1.0 - ndtr((t - mu1) / sigma))
    fp = (1.0 - prevalence) * (1.0 - ndtr((t - mu0) / sigma))
    fn = prevalence * ndtr((t - mu1) / sigma)
    return 2.0 * tp / (2.0 * tp + fp + fn)


# ---- eq-m21-procrustes: rigid and similarity least squares (Umeyama) ------------------------------------------------

def procrustes(P, Q, scale=False):
    """Least-squares R, t (and s) with Q ~ s R P + t, rows paired. Returns (R, t, s)."""
    P, Q = np.asarray(P, float), np.asarray(Q, float)
    mp, mq = P.mean(0), Q.mean(0)
    X, Y = P - mp, Q - mq
    H = Y.T @ X / len(P)
    U, D, Vt = np.linalg.svd(H)
    S = np.eye(P.shape[1])
    S[-1, -1] = np.sign(np.linalg.det(U @ Vt)) or 1.0
    R = U @ S @ Vt
    s = float(np.trace(np.diag(D) @ S) / np.mean(np.sum(X ** 2, axis=1))) if scale else 1.0
    t = mq - s * R @ mp
    return R, t, s


def apply(R, t, s, P):
    return s * np.asarray(P) @ R.T + t


def rotation(angle_deg, axis=2, dim=3):
    a = np.radians(angle_deg)
    c, s = np.cos(a), np.sin(a)
    if dim == 2:
        return np.array([[c, -s], [s, c]])
    R = np.eye(3)
    i, j = [k for k in range(3) if k != axis]
    R[i, i], R[i, j], R[j, i], R[j, j] = c, -s, s, c
    return R


def rms(v):
    return float(np.sqrt(np.mean(np.sum(np.asarray(v) ** 2, axis=-1))))


# ---- eq-m21-icp -----------------------------------------------------------------------------------------------------

def icp(source, target, R0=None, t0=None, iters=60, tol=1e-9):
    """Point-to-point ICP: closest-point correspondences, then Procrustes; returns (R, t, mse history)."""
    dim = source.shape[1]
    R = np.eye(dim) if R0 is None else R0
    t = np.zeros(dim) if t0 is None else t0
    tree = cKDTree(target)
    hist = []
    for _ in range(iters):
        moved = source @ R.T + t
        d, idx = tree.query(moved)
        hist.append(float(np.mean(d ** 2)))
        R, t, _ = procrustes(source, target[idx])
        if len(hist) > 1 and hist[-2] - hist[-1] < tol:
            break
    d, _ = tree.query(source @ R.T + t)
    hist.append(float(np.mean(d ** 2)))
    return R, t, hist


# ---- eq-m21-sliding: what surface registration cannot see --------------------------------------------------------------

def ellipsoid_points(axes, n, rng):
    v = rng.standard_normal((n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v * np.asarray(axes, float)


def ellipsoid_normals(points, axes):
    g = points / np.asarray(axes, float) ** 2
    return g / np.linalg.norm(g, axis=1, keepdims=True)


def point_to_plane_hessian(points, normals):
    """J^T J for small rigid motions (rotation w, translation t): residual_i = n_i . (w x p_i + t) = (p_i x n_i) . w + n_i . t."""
    J = np.hstack([np.cross(points, normals), normals])
    return J.T @ J / len(points)
