"""m21 equation tests: Otsu threshold, Dice and Jaccard, Procrustes, ICP, and the sliding ambiguity."""

import numpy as np
import pytest
import sympy as sp

from epml import registration as RG


def test_threshold():
    """eq-m21-threshold: total variance = within + between; Otsu maximizes the between-class variance."""
    w0, m0, m1, v0, v1 = sp.symbols("w0 mu0 mu1 v0 v1", real=True)
    w1 = 1 - w0
    mt = w0 * m0 + w1 * m1
    total = w0 * (v0 + (m0 - mt) ** 2) + w1 * (v1 + (m1 - mt) ** 2)
    within = w0 * v0 + w1 * v1
    assert sp.simplify(total - within - w0 * w1 * (m0 - m1) ** 2) == 0
    rng = np.random.default_rng(21)
    v = np.concatenate([rng.normal(100, 40, 70000), rng.normal(350, 40, 30000)])
    t = RG.otsu_threshold(v)
    grid = np.linspace(150, 300, 301)
    sb = [np.mean(v <= g) * np.mean(v > g) * (v[v <= g].mean() - v[v > g].mean()) ** 2 for g in grid]
    assert t == pytest.approx(grid[int(np.argmax(sb))], abs=3.0)


def test_dice():
    """eq-m21-dice: D = 2|A&B|/(|A|+|B|) = 2J/(1+J); the Gaussian expected Dice matches simulation."""
    a, b, c = sp.symbols("a b c", positive=True)          # |A only|, |B only|, |A and B|
    D = 2 * c / ((a + c) + (b + c))
    J = c / (a + b + c)
    assert sp.simplify(D - 2 * J / (1 + J)) == 0
    A = np.zeros(100, bool); A[:60] = True
    B = np.zeros(100, bool); B[30:80] = True
    assert RG.dice(A, B) == pytest.approx(2 * 30 / 110)
    assert RG.dice(A, B) == pytest.approx(2 * RG.jaccard(A, B) / (1 + RG.jaccard(A, B)))
    rng = np.random.default_rng(2)
    n, p = 400000, 0.3
    truth = rng.random(n) < p
    val = np.where(truth, rng.normal(350, 60, n), rng.normal(100, 60, n))
    assert RG.dice(val > 225, truth) == pytest.approx(RG.gaussian_dice(225, 100, 350, 60, p), abs=0.003)


def test_procrustes():
    """eq-m21-procrustes: recovers rotation, translation and scale; never returns a reflection."""
    rng = np.random.default_rng(3)
    P = rng.normal(0, 30, (8, 3))
    R0 = RG.rotation(25, 2) @ RG.rotation(-10, 0)
    t0 = np.array([5.0, -3.0, 10.0])
    R, t, s = RG.procrustes(P, 1.1 * P @ R0.T + t0, scale=True)
    assert R == pytest.approx(R0, abs=1e-10) and t == pytest.approx(t0, abs=1e-9) and s == pytest.approx(1.1)
    R, t, s = RG.procrustes(P, P @ R0.T + t0)
    assert s == 1.0 and R == pytest.approx(R0, abs=1e-10)
    Pm = P * np.array([1, 1, -1])                         # a mirrored copy: the best proper rotation, not a reflection
    R, _, _ = RG.procrustes(P, Pm)
    assert np.linalg.det(R) == pytest.approx(1.0)
    # The least-squares rotation for 2D points is atan2(sum cross, sum dot).
    x = rng.normal(0, 10, (12, 2)); y = x @ RG.rotation(33, dim=2).T + rng.normal(0, 0.5, (12, 2))
    xc, yc = x - x.mean(0), y - y.mean(0)
    ang = np.degrees(np.arctan2(np.sum(xc[:, 0] * yc[:, 1] - xc[:, 1] * yc[:, 0]), np.sum(xc * yc)))
    R2, _, _ = RG.procrustes(x, y)
    assert np.degrees(np.arctan2(R2[1, 0], R2[0, 0])) == pytest.approx(ang)


def test_icp():
    """eq-m21-icp: the mean squared distance never increases; small starts converge, large ones can stall."""
    rng = np.random.default_rng(21)
    tgt = RG.ellipsoid_points((30, 22, 18), 3000, rng)
    src = tgt[rng.choice(3000, 400, replace=False)]
    for ang, ok in ((10, True), (170, False)):
        moved = src @ RG.rotation(ang, 2).T + np.array([3.0, -2.0, 1.0])
        R, t, hist = RG.icp(moved, tgt, iters=100)
        assert np.all(np.diff(hist) <= 1e-9)
        err = RG.rms(moved @ R.T + t - src)
        assert (err < 1e-6) if ok else (err > 20)


def test_sliding():
    """eq-m21-sliding: a sphere has three zero modes (rotations); an ellipsoid has none."""
    rng = np.random.default_rng(4)
    for axes, zeros in (((25, 25, 25), 3), ((30, 22, 18), 0)):
        p = RG.ellipsoid_points(axes, 3000, rng)
        ev = np.linalg.eigvalsh(RG.point_to_plane_hessian(p, RG.ellipsoid_normals(p, axes)))
        assert int(np.sum(ev < 1e-8 * ev.max())) == zeros
    # A sphere rotated about its center keeps every point on the surface: zero surface distance, nonzero target error.
    p = RG.ellipsoid_points((25, 25, 25), 200, rng)
    q = p @ RG.rotation(10, 2).T
    assert np.allclose(np.linalg.norm(q, axis=1), 25.0)
    assert RG.rms(q - p) > 3.0
