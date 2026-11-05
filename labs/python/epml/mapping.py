"""m30 helpers: a mini mapping system on triangle meshes (also used by m33).

Lengths in mm, times in ms, speeds in mm/ms (= m/s). Meshes are (verts [n, 3], tris [m, 3]).
"""

import numpy as np


# ---------------------------------------------------------------------------- meshes

def plane_mesh(nx, ny, spacing):
    """Flat triangulated grid in the z = 0 plane, with alternating diagonals."""
    x, y = np.meshgrid(np.arange(nx) * spacing, np.arange(ny) * spacing)
    verts = np.column_stack([x.ravel(), y.ravel(), np.zeros(nx * ny)])
    tris = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a, b, c, d = j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i
            if (i + j) % 2 == 0:
                tris += [(a, b, c), (a, c, d)]
            else:
                tris += [(a, b, d), (b, c, d)]
    return verts, np.array(tris)


def icosphere(radius, subdivisions):
    """Sphere mesh by repeated subdivision of an icosahedron."""
    t = (1 + 5**0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t),
         (0, 1, -t), (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4),
         (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
         (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    verts = [np.array(p, float) / np.linalg.norm(p) for p in v]
    faces = f
    for _ in range(subdivisions):
        cache, new = {}, []

        def mid(i, j):
            key = (min(i, j), max(i, j))
            if key not in cache:
                m = verts[i] + verts[j]
                verts.append(m / np.linalg.norm(m))
                cache[key] = len(verts) - 1
            return cache[key]

        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            new += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = new
    return radius * np.array(verts), np.array(faces)


# ---------------------------------------------------------------------------- eikonal

def _triangle_update(Xa, Xb, Xc, Ta, Tb, v):
    """Smallest arrival time at C from a front crossing edge AB with linear T on AB, speed v."""
    e = Xb - Xa
    L = np.linalg.norm(e, axis=1)
    eh = e / L[:, None]
    u = Xc - Xa
    along = np.einsum("ij,ij->i", u, eh)
    h = np.linalg.norm(u - along[:, None] * eh, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        cand_a = Ta + np.linalg.norm(u, axis=1) / v
        cand_b = Tb + np.linalg.norm(Xc - Xb, axis=1) / v
        best = np.minimum(cand_a, cand_b)
        k = v * (Tb - Ta) / L
        ok = np.isfinite(Ta) & np.isfinite(Tb) & (np.abs(k) < 1)
        w = np.where(ok, k * h / np.sqrt(np.where(ok, 1 - k**2, 1.0)), 0.0)
        s = (along - w) / L
        inside = ok & (s >= 0) & (s <= 1)
        interior = Ta + s * (Tb - Ta) + np.sqrt(w**2 + h**2) / v
    return np.where(inside, np.minimum(best, interior), best)


def eikonal(verts, tris, sources, speed, t0=0.0, tol=1e-10, max_iter=10000):
    """eq-m30-eikonal: activation times on a triangle mesh, v |grad T| = 1.

    `speed` is a scalar or one value per triangle; triangles with speed 0 do not conduct (scar).
    `sources` are vertex indices activated at t0 (scalar or one per source).
    """
    n = verts.shape[0]
    speed = np.broadcast_to(np.asarray(speed, float), (tris.shape[0],))
    live = speed > 0
    tr, sp = tris[live], speed[live]
    T = np.full(n, np.inf)
    T[np.atleast_1d(sources)] = t0
    X = verts
    orders = [(0, 1, 2), (1, 2, 0), (2, 0, 1)]
    for _ in range(max_iter):
        old = T.copy()
        for ia, ib, ic in orders:
            a, b, c = tr[:, ia], tr[:, ib], tr[:, ic]
            cand = _triangle_update(X[a], X[b], X[c], T[a], T[b], sp)
            np.minimum.at(T, c, cand)
        finite = np.isfinite(T)
        if np.all(np.abs(T[finite] - old[finite]) <= tol) and np.array_equal(finite, np.isfinite(old)):
            break
    return T


def geodesic_distances(verts, tris, sources):
    """Geodesic distance from each source vertex to all vertices (eikonal with speed 1)."""
    return np.array([eikonal(verts, tris, s, 1.0) for s in np.atleast_1d(sources)])


# ---------------------------------------------------------------------------- acquisition

def measured_positions(true_pos, times, sigma, resp_amp, resp_period, resp_dir, rng):
    """eq-m30-localization: true position + Gaussian error + sinusoidal respiratory displacement."""
    d = np.asarray(resp_dir, float) / np.linalg.norm(resp_dir)
    resp = resp_amp * np.sin(2 * np.pi * np.asarray(times, float) / resp_period)[:, None] * d
    return true_pos + rng.normal(0.0, sigma, true_pos.shape) + resp


def _closest_on_triangles(p, A, B, C):
    """Closest points on many triangles to one point p (Ericson, Real-Time Collision Detection)."""
    ab, ac, ap = B - A, C - A, p - A
    d1, d2 = np.einsum("ij,ij->i", ab, ap), np.einsum("ij,ij->i", ac, ap)
    bp = p - B
    d3, d4 = np.einsum("ij,ij->i", ab, bp), np.einsum("ij,ij->i", ac, bp)
    cp = p - C
    d5, d6 = np.einsum("ij,ij->i", ab, cp), np.einsum("ij,ij->i", ac, cp)
    va = d3 * d6 - d5 * d4
    vb = d5 * d2 - d1 * d6
    vc = d1 * d4 - d3 * d2
    out = np.empty_like(A)
    done = np.zeros(A.shape[0], bool)

    def put(mask, val):
        m = mask & ~done
        out[m] = val[m] if np.ndim(val) == 2 else val
        done[m] = True

    put((d1 <= 0) & (d2 <= 0), A)
    put((d3 >= 0) & (d4 <= d3), B)
    with np.errstate(invalid="ignore", divide="ignore"):
        v_ab = d1 / (d1 - d3)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), A + v_ab[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), C)
        w_ac = d2 / (d2 - d6)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), A + w_ac[:, None] * ac)
        w_bc = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), B + w_bc[:, None] * (C - B))
        denom = 1.0 / (va + vb + vc)
        v_in, w_in = vb * denom, vc * denom
        put(np.ones_like(done), A + v_in[:, None] * ab + w_in[:, None] * ac)
    return out


def project_to_mesh(points, verts, tris):
    """eq-m30-projection: closest point on the mesh to each point. Returns (projected, tri index)."""
    A, B, C = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    proj = np.empty_like(np.atleast_2d(points), dtype=float)
    idx = np.empty(proj.shape[0], int)
    for i, p in enumerate(np.atleast_2d(points)):
        q = _closest_on_triangles(p, A, B, C)
        d = np.linalg.norm(q - p, axis=1)
        idx[i] = np.argmin(d)
        proj[i] = q[idx[i]]
    return proj, idx


# ---------------------------------------------------------------------------- maps

def idw(dist, values, p=2.0):
    """eq-m30-idw: inverse-distance weights from a [n_query, n_data] distance matrix."""
    dist = np.asarray(dist, float)
    values = np.asarray(values, float)
    out = np.empty(dist.shape[0])
    exact = dist <= 1e-12
    for i in range(dist.shape[0]):
        if exact[i].any():
            out[i] = values[exact[i]].mean()
        else:
            w = dist[i] ** -p
            out[i] = np.sum(w * values) / np.sum(w)
    return out


def plane_fit_velocity(points, times):
    """eq-m30-cv-plane: fit T = a + g . x by least squares; velocity vector g / |g|^2."""
    X = np.column_stack([np.ones(len(points)), np.asarray(points, float)])
    coef, *_ = np.linalg.lstsq(X, np.asarray(times, float), rcond=None)
    g = coef[1:]
    return g / np.dot(g, g)


def rmse(estimate, truth):
    """eq-m30-errors: root-mean-square error over mesh vertices."""
    return float(np.sqrt(np.mean((np.asarray(estimate) - np.asarray(truth)) ** 2)))


def fill_distance(dist_to_points):
    """eq-m30-errors: largest distance from any vertex to its nearest acquired point.

    `dist_to_points` is [n_points, n_vertices], for example from geodesic_distances.
    """
    return float(np.max(np.min(np.asarray(dist_to_points), axis=0)))
