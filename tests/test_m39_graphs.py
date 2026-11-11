"""m39 equation tests: each numbered equation in modules/m39-ai-electrograms-maps.qmd is checked here."""

import numpy as np
import pytest
import sympy as sp

from epml import graphs as gr
from epml import mapping as mp


@pytest.fixture(scope="module")
def grid():
    verts, tris = mp.plane_mesh(9, 7, 2.0)
    A = gr.mesh_adjacency(tris, len(verts))
    return verts, tris, A


def test_normalized_adjacency_entries(grid):
    """eq-m39-gcn: A_hat_ij = (A + I)_ij / sqrt(d_i d_j), symmetric."""
    _, _, A = grid
    Ah = gr.normalized_adjacency(A).toarray()
    At = A.toarray() + np.eye(A.shape[0])
    d = At.sum(axis=1)
    assert np.allclose(Ah, At / np.sqrt(np.outer(d, d)))
    assert np.allclose(Ah, Ah.T)


def test_gcn_layer_matches_definition(grid):
    """eq-m39-gcn: one layer is ReLU(A_hat X W + b)."""
    _, _, A = grid
    rng = np.random.default_rng(1)
    X = rng.normal(size=(A.shape[0], 3))
    net = gr.GCN(3, 4, rng=rng)
    Ah = gr.normalized_adjacency(A)
    _, pre, H, _, _ = net.forward(Ah, X)
    assert np.allclose(H, np.maximum(Ah.toarray() @ X @ net.W1 + net.b1, 0))


def test_smoothing_eigen_structure(grid):
    """eq-m39-smoothing: A_hat has eigenvalues in (-1, 1], and sqrt(degree) is the eigenvector for 1."""
    _, _, A = grid
    Ah = gr.normalized_adjacency(A).toarray()
    ev = np.linalg.eigvalsh(Ah)
    assert ev.max() == pytest.approx(1.0) and ev.min() > -1.0
    v = gr.stationary_vector(A)
    assert np.allclose(Ah @ v, v)
    # repeated layers flatten any field towards that vector (low-pass on the mesh)
    rng = np.random.default_rng(2)
    f = rng.normal(size=A.shape[0])
    g = f.copy()
    for _ in range(400):
        g = Ah @ g
    assert np.allclose(g / np.linalg.norm(g), np.sign(g @ v) * v, atol=1e-3)


def test_hop_reach_grows_one_ring_per_layer(grid):
    verts, _, A = grid
    start = 31
    for L in range(4):
        reach = gr.hop_reach(A, start, L)
        # graph distance on this triangulated grid: every reached vertex is within L edges
        D = np.full(A.shape[0], np.inf)
        D[start] = 0
        frontier = [start]
        Ad = A.toarray()
        for step in range(1, L + 1):
            nxt = [j for i in frontier for j in np.flatnonzero(Ad[i]) if D[j] == np.inf]
            for j in nxt:
                D[j] = step
            frontier = list(set(nxt))
        assert np.array_equal(reach, D <= L)


def test_gcn_gradients_match_finite_differences(grid):
    """Hand-written backpropagation through eq-m39-gcn with the cross-entropy and with eq-m39-focal."""
    _, _, A = grid
    rng = np.random.default_rng(3)
    Ah = gr.normalized_adjacency(A)
    X = rng.normal(size=(A.shape[0], 3))
    y = (rng.random(A.shape[0]) < 0.2).astype(float)
    for kw in [{"loss": "bce", "weight": 3.0}, {"loss": "focal", "alpha": 0.75, "gamma": 2.0}]:
        net = gr.GCN(3, 5, rng=np.random.default_rng(4))
        net.b1 += 0.2
        _, g = net.loss_and_grads(Ah, X, y, **kw)
        for name in ["W1", "b1", "w2"]:
            arr = getattr(net, name).reshape(-1)
            for i in range(0, arr.size, max(1, arr.size // 5)):
                old = arr[i]
                arr[i] = old + 1e-6
                lp = net.loss_and_grads(Ah, X, y, **kw)[0]
                arr[i] = old - 1e-6
                lm = net.loss_and_grads(Ah, X, y, **kw)[0]
                arr[i] = old
                assert (lp - lm) / 2e-6 == pytest.approx(g[name].reshape(-1)[i], abs=1e-7)


def test_focal_loss_limits_and_gradient():
    """eq-m39-focal: gamma = 0 gives alpha-weighted cross-entropy; the gradient matches differentiation."""
    z = np.linspace(-4, 4, 17)
    for y in [0, 1]:
        yy = np.full(z.size, y)
        L0 = gr.focal_loss(z, yy, alpha=0.5, gamma=0.0)
        assert L0 == pytest.approx(0.5 * gr.weighted_bce(z, yy))
        _, g = gr.focal_loss(z, yy, alpha=0.75, gamma=2.0, grad=True)
        num = [(gr.focal_loss(z[i:i + 1] + 1e-6, yy[:1], 0.75, 2.0) - gr.focal_loss(z[i:i + 1] - 1e-6, yy[:1], 0.75, 2.0)) / 2e-6
               for i in range(z.size)]
        assert np.allclose(g, num, atol=1e-6)
    # well-classified examples are down-weighted: loss ratio focal/CE falls as p_t -> 1
    zz = sp.Symbol("z")
    p = 1 / (1 + sp.exp(-zz))
    ratio = ((1 - p) ** 2 * sp.log(p)) / sp.log(p)
    assert sp.limit(ratio, zz, sp.oo) == 0


def test_dice_closed_forms():
    """eq-m39-dice"""
    t = np.array([1, 1, 1, 1, 0, 0, 0, 0], bool)
    assert gr.dice(t, t) == 1.0
    assert gr.dice(~t, t) == 0.0
    p = np.array([1, 1, 0, 0, 1, 1, 0, 0], bool)
    assert gr.dice(p, t) == pytest.approx(2 * 2 / 8)
    w = np.array([1, 1, 1, 1, 3, 3, 3, 3], float)
    assert gr.dice(p, t, w) == pytest.approx(2 * 2 / (8 + 4))


@pytest.mark.parametrize("R,r,d", [(5, 5, 3), (8, 3, 6), (4, 6, 9), (5, 2, 1), (3, 3, 7)])
def test_lens_area_against_monte_carlo(R, r, d):
    """eq-m39-lens: sample uniformly inside the smaller disc and count points inside the other one."""
    rng = np.random.default_rng(5)
    n = 400_000
    small, big, c_small = (r, R, np.array([d, 0.0])) if r <= R else (R, r, np.array([0.0, 0.0]))
    c_big = np.array([0.0, 0.0]) if r <= R else np.array([d, 0.0])
    rad = small * np.sqrt(rng.random(n))
    ang = 2 * np.pi * rng.random(n)
    pts = c_small + np.c_[rad * np.cos(ang), rad * np.sin(ang)]
    frac = np.mean(np.hypot(*(pts - c_big).T) <= big)
    assert gr.lens_area(R, r, d) == pytest.approx(np.pi * small**2 * frac, rel=0.01, abs=0.02)


def test_disc_dice_small_offset_small_overlap():
    """Centroid distance and Dice measure different things: a small predicted disc 7 mm from the
    centre of a small true disc has low Dice."""
    assert gr.disc_dice(5, 5, 0) == pytest.approx(1.0)
    assert gr.disc_dice(5, 5, 10) == 0.0
    assert gr.disc_dice(4, 4, 7) < 0.15


def test_gmm_responsibilities_and_em_recovery():
    """eq-m39-gmm: responsibilities sum to one; EM recovers a two-component mixture (as scikit-learn does)."""
    from sklearn.mixture import GaussianMixture

    g = gr.gmm_responsibilities([0.0, 1.0, 5.0], [0.3, 0.7], [0.0, 5.0], [1.0, 1.0])
    assert np.allclose(g.sum(axis=1), 1)
    rng = np.random.default_rng(6)
    x = np.r_[rng.normal(1.0, 0.4, 3000), rng.normal(3.0, 0.6, 7000)]
    w, m, s = gr.gmm_em(x)
    assert w == pytest.approx([0.3, 0.7], abs=0.02)
    assert m == pytest.approx([1.0, 3.0], abs=0.05)
    assert s == pytest.approx([0.4, 0.6], abs=0.05)
    sk = GaussianMixture(2, tol=1e-10, max_iter=5000, random_state=0).fit(x[:, None])
    assert np.sort(sk.means_.ravel()) == pytest.approx(m, abs=0.02)


def test_vertex_areas_sum_to_mesh_area():
    verts, tris = mp.plane_mesh(5, 4, 1.5)
    assert gr.vertex_areas(verts, tris).sum() == pytest.approx(4 * 1.5 * 3 * 1.5)


def test_grid_fixed_point_is_a_checkerboard():
    """eq-m39-smoothing on the course grid: interior degrees 4 and 8, so v alternates in the ratio
    sqrt(5) : sqrt(9); the row-normalized operator keeps a constant map constant."""
    verts, tris = mp.plane_mesh(9, 9, 2.0)
    A = gr.mesh_adjacency(tris, len(verts))
    d = np.asarray(A.sum(axis=1)).ravel().reshape(9, 9)
    assert set(np.unique(d[1:-1, 1:-1])) == {4.0, 8.0}
    v = gr.stationary_vector(A).reshape(9, 9)
    assert v[1, 2] / v[1, 1] == pytest.approx(np.sqrt(5) / 3) or v[1, 1] / v[1, 2] == pytest.approx(np.sqrt(5) / 3)
    At = A + sp_eye(A.shape[0])
    rw = np.asarray(At.sum(axis=1)).ravel()
    ones = np.ones(A.shape[0])
    assert np.allclose((At @ ones) / rw, ones)


def sp_eye(n):
    import scipy.sparse as sps

    return sps.eye(n, format="csr")
