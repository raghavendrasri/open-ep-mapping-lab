"""m02 · Volume conduction and Poisson's equation. MIT License.

Units: distance mm, currents and potentials in relative units, conductivities relative (sigma = 1 unless stated).
Models: the quasi-static current-conservation (Poisson) equation for a volume conductor (Plonsey and Barr 2007;
Plonsey and Heppner 1967), its 2-D finite-difference solution with a flux-conserving variable-conductivity stencil,
the method of images for a planar interface between two conductivities, and Helmholtz reciprocity (lead fields).
Conductivity ratios are parameters; no tissue value is asserted here.
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.special import exp1


# ---------------------------------------------------------------- a Gaussian source (eq-m02-poisson)


def gaussian_source_2d(x, y, current=1.0, width=1.0):
    """Current source density (per unit area) of a 2-D Gaussian blob carrying total current I."""
    r2 = np.asarray(x, float) ** 2 + np.asarray(y, float) ** 2
    return current / (2 * np.pi * width ** 2) * np.exp(-r2 / (2 * width ** 2))


def gaussian_potential_2d(r, current=1.0, width=1.0, sigma=1.0):
    """Exact 2-D potential of the Gaussian source, phi = -(I / 2 pi sigma) (ln r + E1(r^2 / 2 s^2) / 2), up to a
    constant (finite at r = 0, where it equals -(I / 4 pi sigma)(ln(2 s^2) - gamma))."""
    r = np.asarray(r, float)
    out = np.empty_like(r)
    small = r < 1e-12
    rr = r[~small]
    out[~small] = -(current / (2 * np.pi * sigma)) * (np.log(rr) + 0.5 * exp1(rr ** 2 / (2 * width ** 2)))
    out[small] = -(current / (4 * np.pi * sigma)) * (np.log(2 * width ** 2) - np.euler_gamma)
    return out


# ---------------------------------------------------------------- finite differences (eq-m02-fd)


def poisson_matrix(sig, h):
    """Flux-conserving 5-point operator for div(sigma grad phi) on a grid of spacing h (all nodes unknown, Dirichlet
    rows added by solve_poisson). sig: node conductivities (ny, nx); face conductivities are harmonic means."""
    ny, nx = sig.shape
    idx = np.arange(nx * ny).reshape(ny, nx)
    rows, cols, vals = [], [], []
    diag = np.zeros((ny, nx))
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        a = sig[max(0, -dy):ny - max(0, dy), max(0, -dx):nx - max(0, dx)]
        b = sig[max(0, dy):ny - max(0, -dy) or None, max(0, dx):nx - max(0, -dx) or None]
        face = 2 * a * b / (a + b)
        i = idx[max(0, -dy):ny - max(0, dy), max(0, -dx):nx - max(0, dx)]
        j = idx[max(0, dy):ny - max(0, -dy) or None, max(0, dx):nx - max(0, -dx) or None]
        rows.append(i.ravel()); cols.append(j.ravel()); vals.append(face.ravel() / h ** 2)
        diag[max(0, -dy):ny - max(0, dy), max(0, -dx):nx - max(0, dx)] -= face / h ** 2
    rows.append(idx.ravel()); cols.append(idx.ravel()); vals.append(diag.ravel())
    return sparse.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(nx * ny,) * 2)


def solve_poisson(sig, source, h, boundary):
    """eq-m02-fd: solve div(sigma grad phi) = -source on a grid, with phi fixed to `boundary` on the outer ring.
    sig, source, boundary: arrays (ny, nx). Returns phi (ny, nx)."""
    ny, nx = sig.shape
    A = poisson_matrix(sig, h).tolil()
    rhs = -np.asarray(source, float).ravel().copy()
    edge = np.zeros((ny, nx), bool)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    for k in np.flatnonzero(edge.ravel()):
        A.rows[k] = [k]; A.data[k] = [1.0]
        rhs[k] = boundary.ravel()[k]
    return spsolve(A.tocsr(), rhs).reshape(ny, nx)


def grid(n, half):
    """Square grid of n x n nodes spanning [-half, half] mm. Returns x, y (2-D) and spacing h. With n even, y = 0
    falls halfway between two rows of nodes, so an interface at y = 0 lies on cell faces (second-order accurate)."""
    v = np.linspace(-half, half, n)
    X, Y = np.meshgrid(v, v)
    return X, Y, v[1] - v[0]


# ---------------------------------------------------------------- interfaces (eq-m02-interface, eq-m02-images)


def reflection_coefficient(sigma1, sigma2):
    """eq-m02-images: k = (sigma1 - sigma2) / (sigma1 + sigma2) for a source in medium 1."""
    return (sigma1 - sigma2) / (sigma1 + sigma2)


def image_potential_3d(current, sigma1, sigma2, depth, obs, src_xy=(0.0, 0.0)):
    """eq-m02-images: point source I in medium 1 (z < 0) at (x0, y0, -depth), planar interface z = 0, medium 2 above.
    Medium 1: phi = I / (4 pi sigma1) (1 / r + k / r'), image at (x0, y0, +depth); medium 2: phi = I / (2 pi
    (sigma1 + sigma2) r)."""
    obs = np.atleast_2d(np.asarray(obs, float))
    k = reflection_coefficient(sigma1, sigma2)
    x0, y0 = src_xy
    r = np.linalg.norm(obs - np.array([x0, y0, -depth]), axis=-1)
    ri = np.linalg.norm(obs - np.array([x0, y0, depth]), axis=-1)
    with np.errstate(divide="ignore"):
        below = current / (4 * np.pi * sigma1) * (1 / r + k / ri)
        above = current / (2 * np.pi * (sigma1 + sigma2) * r)
    return np.where(obs[:, 2] <= 0, below, above)


def image_potential_2d(current, sigma1, sigma2, depth, x, y):
    """The 2-D (line-source) version: source at (0, -depth) in medium 1 (y < 0); phi = -(I / 2 pi sigma1)(ln r +
    k ln r') below, -(I / pi (sigma1 + sigma2)) ln r above (up to the same constant)."""
    k = reflection_coefficient(sigma1, sigma2)
    x, y = np.asarray(x, float), np.asarray(y, float)
    r = np.hypot(x, y + depth)
    ri = np.hypot(x, y - depth)
    with np.errstate(divide="ignore", invalid="ignore"):
        below = -(current / (2 * np.pi * sigma1)) * (np.log(r) + k * np.log(ri))
        above = -(current / (np.pi * (sigma1 + sigma2))) * np.log(r)
    return np.where(y <= 0, below, above)


def image_dipole_potential_3d(p, sigma1, sigma2, depth, obs, eps=1e-5):
    """Potential of a current dipole p (3-vector) at (0, 0, -depth) in medium 1: a source of current |p| / eps at
    +eps/2 along p and a sink at -eps/2, each with its own image."""
    p = np.asarray(p, float)
    n = np.linalg.norm(p)
    u = p / n * eps / 2
    plus = image_potential_3d(1.0, sigma1, sigma2, depth - u[2], obs, (u[0], u[1]))
    minus = image_potential_3d(1.0, sigma1, sigma2, depth + u[2], obs, (-u[0], -u[1]))
    return n * (plus - minus) / eps


# ---------------------------------------------------------------- reciprocity (eq-m02-reciprocity)


def lead_vector_homogeneous(electrode, src, sigma=1.0):
    """eq-m02-reciprocity in an infinite homogeneous medium: grad of psi = 1 / (4 pi sigma |r - r_e|) at the source,
    so a dipole p at the source gives V = p . grad psi."""
    d = np.asarray(src, float) - np.asarray(electrode, float)
    r = np.linalg.norm(d, axis=-1, keepdims=True)
    return -d / (4 * np.pi * sigma * r ** 3)


def reciprocity_two_media(p, sigma1, sigma2, depth, electrode, eps=1e-5):
    """eq-m02-reciprocity across the interface: inject unit current at the electrode (in medium 2, z > 0), compute the
    potential psi it makes in medium 1 by images (roles of the media swapped), and return p . grad psi at the source
    (0, 0, -depth)."""
    e = np.asarray(electrode, float)
    # reflect the geometry so the injected current sits in "medium 1" of image_potential_3d (z < 0)
    def psi(point):
        q = np.array([point[0] - e[0], point[1] - e[1], -point[2]])      # mirror z
        return float(image_potential_3d(1.0, sigma2, sigma1, e[2], [q])[0])
    src = np.array([0.0, 0.0, -depth])
    grad = np.array([(psi(src + eps * v) - psi(src - eps * v)) / (2 * eps) for v in np.eye(3)])
    return float(np.dot(p, grad))


def bipole_lead_magnitude(points, d, h, sigma=1.0):
    """|grad psi| of a bipole (two electrodes at (+-d/2, 0, h), unit current in and out) at tissue points (n, 3):
    the bipole's sensitivity to a dipole at each point, compared with one electrode at (d/2, 0, h)."""
    pts = np.atleast_2d(np.asarray(points, float))
    e1, e2 = np.array([d / 2, 0, h]), np.array([-d / 2, 0, h])
    uni = lead_vector_homogeneous(e1, pts, sigma)
    bi = uni - lead_vector_homogeneous(e2, pts, sigma)
    return np.linalg.norm(uni, axis=-1), np.linalg.norm(bi, axis=-1)
