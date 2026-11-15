"""m20 · Geometry from catheter positions: sampling a chamber, convex hulls, morphological closing, surface
smoothing, mesh volume and surface distances. MIT License.

Units: lengths in mm; voxel grids have spacing h (mm). The chamber is illustrative: a sphere with a concave notch and a
vein-like stub.
"""

import numpy as np
from scipy import ndimage
from scipy.spatial import ConvexHull, cKDTree


# ---- an illustrative chamber ------------------------------------------------------------------------------------

def chamber_inside(p, radius=25.0, notch_center=(34.0, 0.0, 0.0), notch_radius=12.0, vein=(-45.0, -20.0, 6.0)):
    """Inside test: a sphere, minus a notch sphere (a concavity), plus a cylindrical stub along -x."""
    p = np.asarray(p, float)
    r = np.linalg.norm(p, axis=-1)
    notch = np.linalg.norm(p - np.asarray(notch_center), axis=-1) < notch_radius
    x0, x1, rv = vein
    stub = (p[..., 0] >= x0) & (p[..., 0] <= x1) & (np.hypot(p[..., 1], p[..., 2]) <= rv)
    return ((r <= radius) & ~notch) | stub


def grid(h=1.0, half=50.0, dim=3):
    """Voxel centers on a cube [-half, half]^dim with spacing h; returns (axis, points with shape (n,)*dim + (dim,))."""
    ax = np.arange(-half, half + 1e-9, h)
    mesh = np.stack(np.meshgrid(*([ax] * dim), indexing="ij"), axis=-1)
    if dim == 2:
        mesh = np.concatenate([mesh, np.zeros(mesh.shape[:-1] + (1,))], axis=-1)
    return ax, mesh


def truth_mask(h=1.0, half=50.0, dim=3):
    ax, pts = grid(h, half, dim)
    return ax, chamber_inside(pts)


def wall_samples(mask, ax, n, depth, rng):
    """Catheter positions near the wall: random boundary voxels of the chamber, moved inward by up to `depth` mm."""
    dim = mask.ndim
    h = ax[1] - ax[0]
    inner = ndimage.distance_transform_edt(mask) * h
    shell = np.argwhere(mask & (inner <= depth + h))
    pick = shell[rng.integers(0, len(shell), n)]
    pts = ax[pick] + rng.uniform(-h / 2, h / 2, (n, dim))
    return pts


# ---- eq-m20-hull ----------------------------------------------------------------------------------------------------

def hull_volume(points):
    return float(ConvexHull(points).volume)


def hull_mask(points, ax):
    """Pixels (2D) or voxels (3D) inside the convex hull of the points, tested in chunks."""
    hull = ConvexHull(points)
    dim = points.shape[1]
    pts = np.stack(np.meshgrid(*([ax] * dim), indexing="ij"), axis=-1).reshape(-1, dim)
    inside = np.empty(len(pts), bool)
    for i in range(0, len(pts), 20000):
        q = pts[i:i + 20000]
        inside[i:i + 20000] = np.all(q @ hull.equations[:, :-1].T + hull.equations[:, -1] <= 1e-9, axis=1)
    return inside.reshape((len(ax),) * dim)


# ---- eq-m20-closing ---------------------------------------------------------------------------------------------

def ball(radius_vox, dim):
    r = int(np.ceil(radius_vox))
    ax = np.arange(-r, r + 1)
    g = np.stack(np.meshgrid(*([ax] * dim), indexing="ij"), axis=-1)
    return np.sum(g ** 2, axis=-1) <= radius_vox ** 2


def points_mask(points, ax):
    """Voxels that contain at least one point."""
    h = ax[1] - ax[0]
    idx = np.clip(np.round((points - ax[0]) / h).astype(int), 0, len(ax) - 1)
    m = np.zeros((len(ax),) * points.shape[1], bool)
    m[tuple(idx.T)] = True
    return m


def reconstruct(points, ax, radius, close=True):
    """Inflate the points by `radius` mm, fill enclosed holes, and (if close) shrink back by `radius`."""
    h = ax[1] - ax[0]
    dim = points.shape[1]
    b = ball(radius / h, dim)
    m = ndimage.binary_dilation(points_mask(points, ax), structure=b)
    m = ndimage.binary_fill_holes(m)
    if close:
        pad = int(np.ceil(radius / h)) + 1
        m = np.pad(m, pad)
        m = ndimage.binary_erosion(m, structure=b)
        m = m[tuple(slice(pad, -pad) for _ in range(dim))]
    return m


# ---- eq-m20-distance -------------------------------------------------------------------------------------------------

def boundary(mask):
    return mask & ~ndimage.binary_erosion(mask)


def surface_distances(a, b, ax):
    """Distances (mm) from boundary voxels of mask a to the boundary of b, and back."""
    h = ax[1] - ax[0]
    ba, bb = boundary(a), boundary(b)
    da = ndimage.distance_transform_edt(~bb) * h
    db = ndimage.distance_transform_edt(~ba) * h
    return da[ba], db[bb]


def hausdorff(a, b, ax):
    d1, d2 = surface_distances(a, b, ax)
    return float(max(d1.max(), d2.max()))


def mean_surface_distance(a, b, ax):
    d1, d2 = surface_distances(a, b, ax)
    return float((d1.sum() + d2.sum()) / (len(d1) + len(d2)))


def point_set_hausdorff(A, B):
    """Hausdorff distance between two point sets."""
    return float(max(cKDTree(B).query(A)[0].max(), cKDTree(A).query(B)[0].max()))


# ---- eq-m20-smoothing ------------------------------------------------------------------------------------------------

def umbrella_step(x, neighbors, lam):
    """x_i <- x_i + lam (mean of neighbors - x_i)."""
    mean = np.array([x[nb].mean(axis=0) for nb in neighbors])
    return x + lam * (mean - x)


def polygon(n, radius=1.0):
    t = 2.0 * np.pi * np.arange(n) / n
    return np.stack([radius * np.cos(t), radius * np.sin(t)], axis=1), [[(i - 1) % n, (i + 1) % n] for i in range(n)]


def polygon_factor(n, lam, mu=None):
    """Radius factor per smoothing step on a regular n-gon: 1 - lam a, or (1 - lam a)(1 - mu a) for Taubin; a = 1 - cos(2 pi / n)."""
    a = 1.0 - np.cos(2.0 * np.pi / n)
    f = 1.0 - lam * a
    return f if mu is None else f * (1.0 - mu * a)


def taubin(x, neighbors, lam, mu, steps):
    for _ in range(steps):
        x = umbrella_step(umbrella_step(x, neighbors, lam), neighbors, mu)
    return x


def laplacian(x, neighbors, lam, steps):
    for _ in range(steps):
        x = umbrella_step(x, neighbors, lam)
    return x


# ---- eq-m20-volume ---------------------------------------------------------------------------------------------------

def mesh_volume(V, F):
    """Volume of a closed, outward-oriented triangle mesh: (1/6) sum v_a . (v_b x v_c)."""
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    return float(np.sum(np.einsum("ij,ij->i", a, np.cross(b, c))) / 6.0)


def mesh_neighbors(F, n):
    nb = [set() for _ in range(n)]
    for f in F:
        for i in range(3):
            nb[f[i]].update((f[(i + 1) % 3], f[(i + 2) % 3]))
    return [sorted(s) for s in nb]
