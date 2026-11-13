"""m06 · Triangle meshes, Laplace-Beltrami operators and geodesics. MIT License.

Units: distances in mm (or relative), functions on vertices in relative units. Discretizations: per-face gradients of
piecewise-linear functions, the cotangent Laplacian (Pinkall and Polthier 1993) with barycentric vertex areas, graph
(Dijkstra) distance along edges, and the heat method for geodesic distance (Crane, Weischedel and Wardetzky 2012),
which the paper compares with fast marching on triangulated domains (Kimmel and Sethian 1998). Test surfaces: flat
triangulations and icospheres, whose exact answers are known.
"""

import numpy as np
from scipy import sparse
from scipy.sparse import csgraph
from scipy.sparse.linalg import eigsh, splu


# ---------------------------------------------------------------- meshes (eq-m06-euler)


def icosphere(level=2, radius=1.0):
    """An icosahedron subdivided `level` times and projected onto a sphere."""
    t = (1 + np.sqrt(5)) / 2
    V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                  [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
    F = np.array([[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2],
                  [10, 7, 6], [7, 1, 8], [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11],
                  [6, 2, 10], [8, 6, 7], [9, 8, 1]])
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    for _ in range(level):
        cache = {}
        verts = list(V)

        def mid(a, b):
            key = (min(a, b), max(a, b))
            if key not in cache:
                m = (verts[a] + verts[b]) / 2
                verts.append(m / np.linalg.norm(m))
                cache[key] = len(verts) - 1
            return cache[key]

        newF = []
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            newF += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        V, F = np.array(verts), np.array(newF)
    return V * radius, F


def lattice_mesh(n, spacing=1.0, jitter=0.0, seed=0):
    """A flat patch of equilateral triangles (n x n vertices), optionally with random vertex jitter (fraction of the
    spacing). Returns V (with z = 0) and F."""
    rng = np.random.default_rng(seed)
    ii, jj = np.meshgrid(np.arange(n), np.arange(n))
    x = (ii + 0.5 * (jj % 2)) * spacing
    y = jj * spacing * np.sqrt(3) / 2
    V = np.stack([x.ravel(), y.ravel(), np.zeros(n * n)], 1)
    if jitter:
        V[:, :2] += jitter * spacing * rng.uniform(-1, 1, (n * n, 2))
    F = []
    for j in range(n - 1):
        for i in range(n - 1):
            a, b, c, d = j * n + i, j * n + i + 1, (j + 1) * n + i, (j + 1) * n + i + 1
            if j % 2 == 0:
                F += [[a, b, c], [b, d, c]]
            else:
                F += [[a, b, d], [a, d, c]]
    return V, np.array(F)


def edges(F):
    """Unique undirected edges (E, 2)."""
    e = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), axis=1)
    return np.unique(e, axis=0)


def euler_characteristic(V, F):
    """eq-m06-euler: chi = V - E + F."""
    return len(V) - len(edges(F)) + len(F)


def face_areas(V, F):
    return 0.5 * np.linalg.norm(np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]]), axis=1)


def face_angles(V, F):
    """Interior angles (F, 3), angle k at vertex F[:, k]."""
    out = np.empty(F.shape)
    for k in range(3):
        a, b, c = V[F[:, k]], V[F[:, (k + 1) % 3]], V[F[:, (k + 2) % 3]]
        u, v = b - a, c - a
        out[:, k] = np.arctan2(np.linalg.norm(np.cross(u, v), axis=1), np.einsum("ij,ij->i", u, v))
    return out


# ---------------------------------------------------------------- gradient (eq-m06-gradient)


def face_gradients(V, F, u):
    """eq-m06-gradient: gradient of the piecewise-linear interpolant of u on each face,
    grad u = (1 / 2A) sum_i u_i (N x e_i), e_i the edge opposite vertex i, counterclockwise."""
    p0, p1, p2 = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    n = np.cross(p1 - p0, p2 - p0)
    A2 = np.linalg.norm(n, axis=1, keepdims=True)
    N = n / A2
    g = np.zeros_like(p0)
    for i, (a, b) in enumerate(((1, 2), (2, 0), (0, 1))):
        e = V[F[:, b]] - V[F[:, a]]
        g += u[F[:, i]][:, None] * np.cross(N, e)
    return g / A2


def conduction_velocity(V, F, lat):
    """Per-face conduction velocity vector from local activation times: v = grad T / |grad T|^2 (units mm / ms if
    V is in mm and lat in ms)."""
    g = face_gradients(V, F, lat)
    return g / np.sum(g * g, axis=1, keepdims=True)


# ---------------------------------------------------------------- cotangent Laplacian (eq-m06-cotan, eq-m06-spectrum)


def cotan_matrix(V, F):
    """eq-m06-cotan: the (negative semidefinite) cotangent matrix L_C with off-diagonal entries
    (cot alpha_ij + cot beta_ij) / 2 and rows summing to zero."""
    I, J, W = [], [], []
    for k in range(3):
        i, j, o = F[:, (k + 1) % 3], F[:, (k + 2) % 3], F[:, k]
        u, v = V[i] - V[o], V[j] - V[o]
        cot = np.einsum("ij,ij->i", u, v) / np.linalg.norm(np.cross(u, v), axis=1)
        I += [i, j]; J += [j, i]; W += [0.5 * cot, 0.5 * cot]
    n = len(V)
    L = sparse.csr_matrix((np.concatenate(W), (np.concatenate(I), np.concatenate(J))), shape=(n, n))
    return L - sparse.diags(np.asarray(L.sum(axis=1)).ravel())


def vertex_areas(V, F):
    """Barycentric vertex areas: one third of the area of each incident triangle."""
    a = face_areas(V, F) / 3
    return np.bincount(F.ravel(), weights=np.repeat(a, 3), minlength=len(V))


def laplace_beltrami(V, F, u):
    """Pointwise Laplace-Beltrami of u: (L_C u) / A_i."""
    return cotan_matrix(V, F) @ u / vertex_areas(V, F)


def edge_cotan_weight(alpha, beta):
    """The weight of one interior edge, (cot alpha + cot beta) / 2; negative when alpha + beta > pi (the edge is not
    locally Delaunay)."""
    return 0.5 * (1 / np.tan(alpha) + 1 / np.tan(beta))


def spectrum(V, F, k=16):
    """eq-m06-spectrum: the k smallest eigenvalues of -L_C phi = lambda A phi."""
    L = -cotan_matrix(V, F)
    M = sparse.diags(vertex_areas(V, F))
    vals = eigsh(L.tocsc(), k=k, M=M.tocsc(), sigma=-1e-8, which="LM", return_eigenvectors=False)
    return np.sort(vals)


# ---------------------------------------------------------------- distances (eq-m06-geodesic)


def edge_graph(V, F):
    e = edges(F)
    w = np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1)
    n = len(V)
    return sparse.csr_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n))


def graph_distance(V, F, source):
    """Shortest path along mesh edges (Dijkstra)."""
    return csgraph.dijkstra(edge_graph(V, F), indices=source)


def lattice_path_ratio(theta):
    """Exact ratio of the shortest edge path to the straight-line distance on an equilateral triangular lattice, for a
    direction theta (rad) measured from a lattice direction: (sin theta + sin(pi/3 - theta)) / sin(pi/3), periodic
    with period pi/3. Largest, 2/sqrt(3), at pi/6."""
    th = np.mod(np.asarray(theta, float), np.pi / 3)
    return (np.sin(th) + np.sin(np.pi / 3 - th)) / np.sin(np.pi / 3)


def divergence(V, F, X):
    """Integrated divergence at vertices of a per-face vector field X (Crane et al. 2012):
    (div X)_i = 1/2 sum over faces of cot(theta1) (e1 . X) + cot(theta2) (e2 . X)."""
    out = np.zeros(len(V))
    ang = face_angles(V, F)
    for k in range(3):
        i, j, l = F[:, k], F[:, (k + 1) % 3], F[:, (k + 2) % 3]
        e1, e2 = V[j] - V[i], V[l] - V[i]
        cot_l, cot_j = 1 / np.tan(ang[:, (k + 2) % 3]), 1 / np.tan(ang[:, (k + 1) % 3])
        val = 0.5 * (cot_l * np.einsum("ij,ij->i", e1, X) + cot_j * np.einsum("ij,ij->i", e2, X))
        out += np.bincount(i, weights=val, minlength=len(V))
    return out


def heat_geodesic(V, F, source, t=None):
    """eq-m06-geodesic: the heat method. (A - t L_C) u = delta; X = -grad u / |grad u|; L_C phi = div X; shift so the
    source is at zero. t defaults to the squared mean edge length."""
    e = edges(F)
    h = np.mean(np.linalg.norm(V[e[:, 0]] - V[e[:, 1]], axis=1))
    t = h * h if t is None else t
    LC = cotan_matrix(V, F)
    A = sparse.diags(vertex_areas(V, F))
    delta = np.zeros(len(V)); delta[source] = 1.0
    u = splu((A - t * LC).tocsc()).solve(delta)
    g = face_gradients(V, F, u)
    X = -g / np.linalg.norm(g, axis=1, keepdims=True)
    d = divergence(V, F, X)
    # L_C is singular (constants); pin the source vertex
    Lp = LC.tolil()
    Lp[source, :] = 0
    Lp[source, source] = 1
    d[source] = 0
    phi = splu(Lp.tocsc()).solve(d)
    phi = phi - phi[source]
    return np.abs(phi)


def sphere_distance(V, source, radius):
    """Exact great-circle distance on a sphere: R arccos(x . y / R^2)."""
    c = np.clip(V @ V[source] / radius ** 2, -1, 1)
    return radius * np.arccos(c)
