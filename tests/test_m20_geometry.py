"""m20 equation tests: convex hull, morphological closing, smoothing, mesh volume, surface distances."""

import numpy as np
import pytest
import sympy as sp

from epml import geometry as G
from epml import meshes as MS


@pytest.fixture(scope="module")
def slice2d():
    ax, T = G.truth_mask(0.5, 50.0, 2)
    return ax, T


def test_hull(slice2d):
    """eq-m20-hull: the hull of points on a convex shape converges to it; on a concave one it misses the concavity."""
    rng = np.random.default_rng(20)
    t = rng.uniform(0, 2 * np.pi, 400)
    circle = 25.0 * np.stack([np.cos(t), np.sin(t)], axis=1)
    assert G.hull_volume(circle) == pytest.approx(np.pi * 25.0 ** 2, rel=0.01)
    ax, T = slice2d
    P = G.wall_samples(T, ax, 320, 2.0, rng)
    hm = G.hull_mask(P, ax)
    assert G.hausdorff(hm, T, ax) > 6.0                # the hull bridges the stub-body junction and the notch
    assert hm.sum() > T.sum()


def test_closing(slice2d):
    """eq-m20-closing: dilation grows a disk of radius R to R + r; erosion returns it; closing recovers the chamber."""
    ax = np.arange(-40, 40.001, 0.5)
    X, Y = np.meshgrid(ax, ax, indexing="ij")
    disk = np.hypot(X, Y) <= 20.0
    from scipy import ndimage
    b = G.ball(5.0 / 0.5, 2)
    dil = ndimage.binary_dilation(disk, structure=b)
    r_eff = np.sqrt(dil.sum() * 0.25 / np.pi)
    assert r_eff == pytest.approx(25.0, abs=0.5)
    assert np.array_equal(ndimage.binary_erosion(dil, structure=b), disk)
    ax2, T = slice2d
    rng = np.random.default_rng(20)
    P = G.wall_samples(T, ax2, 320, 2.0, rng)
    R = G.reconstruct(P, ax2, 5.0)
    D = G.reconstruct(P, ax2, 5.0, close=False)
    assert G.mean_surface_distance(R, T, ax2) < 1.0
    assert G.mean_surface_distance(D, T, ax2) > 3.0      # inflation without shrinking back
    sparse = G.reconstruct(G.wall_samples(T, ax2, 40, 2.0, rng), ax2, 3.0)
    assert sparse.sum() < 0.1 * T.sum()                 # a band with gaps cannot be filled


def test_smoothing():
    """eq-m20-smoothing: umbrella smoothing shrinks a regular n-gon by 1 - lam a; Taubin by (1 - lam a)(1 - mu a)."""
    lam, mu, n = sp.symbols("lambda mu n", positive=True)
    k = sp.symbols("k", integer=True)
    th = 2 * sp.pi / n
    x = sp.Matrix([sp.cos(k * th), sp.sin(k * th)])
    nbmean = (sp.Matrix([sp.cos((k - 1) * th), sp.sin((k - 1) * th)]) + sp.Matrix([sp.cos((k + 1) * th), sp.sin((k + 1) * th)])) / 2
    new = x + lam * (nbmean - x)
    assert sp.simplify(sp.expand_trig(new[0] - (1 - lam * (1 - sp.cos(th))) * x[0])) == 0
    V, nb = G.polygon(24, 10.0)
    r1 = np.linalg.norm(G.laplacian(V, nb, 0.5, 1), axis=1)
    assert r1 == pytest.approx(10.0 * G.polygon_factor(24, 0.5))
    rt = np.linalg.norm(G.taubin(V, nb, 0.5, -0.53, 1), axis=1)
    assert rt == pytest.approx(10.0 * G.polygon_factor(24, 0.5, -0.53))
    assert abs(G.polygon_factor(24, 0.5, -0.53) - 1) < 0.1 * (1 - G.polygon_factor(24, 0.5) ** 2)


def test_volume():
    """eq-m20-volume: (1/6) sum v_a . (v_b x v_c); exact for a tetrahedron, converging for an icosphere."""
    a, b, c = sp.symbols("a b c", positive=True)
    V = sp.Matrix([[0, 0, 0], [a, 0, 0], [0, b, 0], [0, 0, c]])
    F = [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]
    vol = sum(V.row(i).dot(V.row(j).cross(V.row(k))) for i, j, k in F) / 6
    assert sp.simplify(vol - a * b * c / 6) == 0
    Vs, Fs = MS.icosphere(level=4, radius=10.0)
    assert G.mesh_volume(Vs, Fs) == pytest.approx(4 / 3 * np.pi * 1000.0, rel=0.01)


def test_distance():
    """eq-m20-distance: Hausdorff distance between concentric circles is the radius difference."""
    t = np.linspace(0, 2 * np.pi, 2000, endpoint=False)
    A = 20.0 * np.stack([np.cos(t), np.sin(t)], axis=1)
    B = 23.0 * np.stack([np.cos(t), np.sin(t)], axis=1)
    assert G.point_set_hausdorff(A, B) == pytest.approx(3.0, abs=1e-3)
    ax = np.arange(-40, 40.001, 0.5)
    X, Y = np.meshgrid(ax, ax, indexing="ij")
    m1, m2 = np.hypot(X, Y) <= 20.0, np.hypot(X, Y) <= 23.0
    assert G.hausdorff(m1, m2, ax) == pytest.approx(3.0, abs=0.75)
