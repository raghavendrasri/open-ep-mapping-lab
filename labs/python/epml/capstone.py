"""m55 · Capstone: a multimodal image-guided procedure on a digital phantom. C-arm projection, segmentation of a
synthetic left atrium, landmark and surface registration to simulated map points, predicted and simulated target
registration error, overlay of the model on a projection, and an error and dose budget. MIT License.

Registration is derived in m21 (planned); here we only use it. The TRE prediction is from Fitzpatrick, West and
Maurer 1998 as restated by Danilchenko and Fitzpatrick 2011. Geometry, noise levels, landmark choices and dose rates
are illustrative unless a source is named in the lab."""
import numpy as np
from scipy.spatial import cKDTree

from .imaging import surface


# ---------------------------------------------------------------- C-arm projection (eq-m55-projection)


def rotate_z(points, angle_deg):
    """Rotate points (N, 3) about the z (head-foot) axis by angle_deg."""
    a = np.radians(angle_deg)
    R = np.array([[np.cos(a), -np.sin(a), 0.0], [np.sin(a), np.cos(a), 0.0], [0.0, 0.0, 1.0]])
    return np.asarray(points, float) @ R.T


def project(points, sod=750.0, sid=1100.0, angle_deg=0.0):
    """eq-m55-projection: a point source at distance SOD before the isocenter, a flat detector at SID from the
    source, beam along +y after rotating the C-arm by angle_deg about z. A point (x, y, z) in the C-arm frame maps
    to (u, v) = SID/(SOD + y) (x, z) on the detector. Distances in mm; SOD and SID are illustrative. Returns
    (uv (N, 2), magnification (N,))."""
    p = rotate_z(points, -angle_deg)
    m = sid / (sod + p[:, 1])
    return np.c_[m * p[:, 0], m * p[:, 2]], m


def visible_error(error_vec, angle_deg=0.0):
    """Split a 3-D error into the part across the beam (seen on one projection) and the part along it (not seen)."""
    e = rotate_z(np.atleast_2d(error_vec), -angle_deg)[0]
    return float(np.hypot(e[0], e[2])), float(abs(e[1]))


# ---------------------------------------------------------------- rigid registration (derived in m21)


def kabsch(P, Q):
    """Least-squares rotation R and translation t with R P + t ~ Q (rows are points); no reflection."""
    P, Q = np.asarray(P, float), np.asarray(Q, float)
    cp, cq = P.mean(0), Q.mean(0)
    H = (P - cp).T @ (Q - cq)
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    return R, cq - R @ cp


def apply(R, t, P):
    return np.asarray(P, float) @ R.T + t


def rms(v):
    return float(np.sqrt(np.mean(np.sum(np.asarray(v, float) ** 2, axis=-1))))


def icp(source, target, R0=None, t0=None, iters=50, tol=1e-6):
    """Iterative closest point: move `source` points onto the `target` cloud. Returns (R, t, mean distance)."""
    tree = cKDTree(target)
    R = np.eye(3) if R0 is None else R0
    t = np.zeros(3) if t0 is None else t0
    prev = np.inf
    for _ in range(iters):
        moved = apply(R, t, source)
        d, idx = tree.query(moved)
        R, t = kabsch(source, target[idx])
        err = float(np.mean(d))
        if abs(prev - err) < tol:
            break
        prev = err
    d, _ = tree.query(apply(R, t, source))
    return R, t, float(np.mean(d))


def random_rotation(rng, max_deg):
    """A rotation about a random axis by an angle up to max_deg."""
    axis = rng.normal(size=3)
    axis /= np.linalg.norm(axis)
    a = np.radians(rng.uniform(-max_deg, max_deg))
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


# ---------------------------------------------------------------- predicted registration error (eq-m55-tre)


def principal_axes(fiducials):
    """Unit principal axes (columns) of the centered fiducial configuration."""
    F = np.asarray(fiducials, float) - np.mean(fiducials, axis=0)
    _, vecs = np.linalg.eigh(F.T @ F)
    return vecs


def predicted_tre(fiducials, targets, fle_rms):
    """eq-m55-tre: <TRE^2(r)> ~ <FLE^2>/N (1 + 1/3 sum_k d_k^2 / f_k^2), with d_k the distance of the target from
    principal axis k of the fiducials and f_k^2 the mean squared distance of the fiducials from that axis. Returns the
    RMS TRE at each target."""
    F = np.asarray(fiducials, float)
    c = F.mean(0)
    E = principal_axes(F)
    Fc = F - c
    T = np.atleast_2d(np.asarray(targets, float)) - c
    n = len(F)
    total = np.ones(len(T))
    for k in range(3):
        e = E[:, k]
        f2 = np.mean(np.sum(Fc**2, 1) - (Fc @ e) ** 2)
        d2 = np.sum(T**2, 1) - (T @ e) ** 2
        total += d2 / f2 / 3.0
    return np.sqrt(fle_rms**2 / n * total)


def predicted_fre(n, fle_rms):
    """eq-m55-tre: <FRE^2> = (1 - 2/N) <FLE^2>, independent of the configuration."""
    return float(np.sqrt((1.0 - 2.0 / n) * fle_rms**2))


def simulate_tre(fiducials, targets, fle_rms, rng, trials=2000):
    """Monte Carlo of landmark registration: isotropic Gaussian localization error (RMS fle_rms in 3-D) on the
    fiducials, true transform the identity. Returns (RMS TRE per target, FRE per trial, TRE of target 0 per trial)."""
    F = np.asarray(fiducials, float)
    T = np.atleast_2d(np.asarray(targets, float))
    s = fle_rms / np.sqrt(3.0)
    tre2 = np.zeros(len(T))
    fre, tre0 = [], []
    for _ in range(trials):
        Q = F + rng.normal(0, s, F.shape)
        R, t = kabsch(F, Q)
        moved = apply(R, t, T)
        err = np.sum((moved - T) ** 2, 1)
        tre2 += err
        fre.append(rms(apply(R, t, F) - Q))
        tre0.append(np.sqrt(err[0]))
    return np.sqrt(tre2 / trials), np.array(fre), np.array(tre0)


def fiducial_layout(kind, n=6, radius=25.0):
    """Illustrative landmark layouts in mm: 'spread' around the atrium, 'clustered' on one side, or 'nearly
    collinear'."""
    k = np.arange(n)
    if kind == "spread":
        a = 2 * np.pi * k / n
        return np.c_[radius * np.cos(a), radius * np.sin(a), 8.0 * np.cos(3 * a)]
    if kind == "clustered":
        a = np.radians(-30 + 60 * k / max(n - 1, 1))
        return np.c_[radius * np.cos(a), radius * np.sin(a), 6.0 * np.sin(2 * a + 0.5)]
    if kind == "nearly collinear":
        x = np.linspace(-radius, radius, n)
        return np.c_[x, 2.0 * np.sin(1.3 * k), 2.0 * np.cos(0.7 * k)]
    raise ValueError(kind)


# ---------------------------------------------------------------- error budget (eq-m55-budget)


def budget(components):
    """eq-m55-budget: independent, zero-mean errors add in quadrature: sqrt(sum of squared RMS values)."""
    return float(np.sqrt(np.sum(np.square(list(components)))))


# ---------------------------------------------------------------- the phantom atrium and map points


def surface_points(mask, axis_mm):
    """Coordinates (mm) of the boundary voxels of a mask on a cubic grid with the given axis."""
    idx = np.argwhere(surface(mask))
    return axis_mm[idx]


def ellipsoid_points(semi_axes, n, rng):
    """n points uniform in angle on an ellipsoid surface (a stand-in for map points on the atrial wall)."""
    v = rng.normal(size=(n, 3))
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    return v * np.asarray(semi_axes, float)


def ellipsoid_wireframe(semi_axes, center=(0.0, 0.0, 0.0), n_lat=7, n_lon=8, m=73):
    """Latitude and longitude rings of an ellipsoid, as a list of (m, 3) polylines, for drawing an overlay."""
    a, b, c = semi_axes
    cx = np.asarray(center, float)
    t = np.linspace(0, 2 * np.pi, m)
    lines = []
    for phi in np.linspace(-np.pi / 2, np.pi / 2, n_lat + 2)[1:-1]:
        lines.append(np.c_[a * np.cos(phi) * np.cos(t), b * np.cos(phi) * np.sin(t), c * np.sin(phi) * np.ones_like(t)] + cx)
    for lam in np.linspace(0, np.pi, n_lon, endpoint=False):
        lines.append(np.c_[a * np.cos(t) * np.cos(lam), b * np.cos(t) * np.sin(lam), c * np.sin(t)] + cx)
    return lines


def kap(rate_gycm2_per_min, minutes, acquisitions_gycm2=0.0):
    """Kerma-area product of a procedure (m49): fluoroscopy rate times time plus acquisitions. Illustrative inputs."""
    return rate_gycm2_per_min * minutes + acquisitions_gycm2
