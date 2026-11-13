"""m06 · Triangle meshes, Laplace-Beltrami operators and geodesics: equation tests."""

import numpy as np
import pytest
import sympy as sp

from epml import meshes as M


def test_euler_characteristic():
    """eq-m06-euler: V - E + F = 2 - 2g; every icosphere (g = 0) gives 2, and on a closed triangle mesh E = 3F/2."""
    for level in (0, 1, 2, 3):
        V, F = M.icosphere(level)
        assert M.euler_characteristic(V, F) == 2
        assert len(M.edges(F)) * 2 == 3 * len(F)
        assert len(V) == 10 * 4 ** level + 2
    V, F = M.lattice_mesh(6)
    assert M.euler_characteristic(V, F) == 1               # a disk


def test_gradient_and_velocity():
    """eq-m06-gradient: the per-face gradient reproduces any linear function exactly, on any triangulation; the
    conduction velocity grad T / |grad T|^2 of a planar activation recovers speed and direction exactly."""
    a, b, c, x0, y0, x1, y1, x2, y2 = sp.symbols("a b c x0 y0 x1 y1 x2 y2", real=True)
    P = [sp.Matrix([x0, y0, 0]), sp.Matrix([x1, y1, 0]), sp.Matrix([x2, y2, 0])]
    u = [a * p[0] + b * p[1] + c for p in P]
    n = (P[1] - P[0]).cross(P[2] - P[0])
    A2 = sp.sqrt(n.dot(n))
    N = n / A2
    g = sp.zeros(3, 1)
    for i, (j, k) in enumerate(((1, 2), (2, 0), (0, 1))):
        g += u[i] * N.cross(P[k] - P[j])
    g = g / A2
    assume = {x0: 0, y0: 0, x1: 1, y1: 0}                 # fix one edge; any third vertex above it
    gg = sp.simplify(g.subs(assume).subs(y2, sp.Abs(y2) + 1))
    assert sp.simplify(gg[0] - a) == 0 and sp.simplify(gg[1] - b) == 0
    V, F = M.lattice_mesh(15, 1.0, jitter=0.25, seed=3)
    lin = 2 * V[:, 0] - 3 * V[:, 1] + 1
    assert np.allclose(M.face_gradients(V, F, lin), [2, -3, 0], atol=1e-12)
    direction = np.array([np.cos(0.7), np.sin(0.7), 0.0])
    lat = (V @ direction) / 0.8                              # 0.8 mm/ms planar wave
    v = M.conduction_velocity(V, F, lat)
    assert np.allclose(np.linalg.norm(v, axis=1), 0.8) and np.allclose(v / 0.8, direction, atol=1e-12)


def test_cotan_laplacian():
    """eq-m06-cotan: the cotangent Laplacian annihilates linear functions at interior vertices of any flat mesh, gives
    exactly 4 for x^2 + y^2 on the equilateral lattice, and on the unit sphere maps z to -2 z as the mesh is refined:
    the typical (median) and integrated errors fall about fourfold per refinement, while the worst error, at the 12
    vertices with five neighbors, does not fall with barycentric areas."""
    V, F = M.lattice_mesh(15, 1.0, jitter=0.2, seed=1)
    interior = (V[:, 0] > 2) & (V[:, 0] < 10) & (V[:, 1] > 2) & (V[:, 1] < 10)
    assert np.max(np.abs(M.laplace_beltrami(V, F, 2 * V[:, 0] - 3 * V[:, 1] + 1)[interior])) < 1e-10
    V, F = M.lattice_mesh(15, 1.0)
    interior = (V[:, 0] > 2) & (V[:, 0] < 10) & (V[:, 1] > 2) & (V[:, 1] < 10)
    assert np.allclose(M.laplace_beltrami(V, F, V[:, 0] ** 2 + V[:, 1] ** 2)[interior], 4.0)
    med, weak, worst = [], [], []
    for level in (2, 3, 4):
        V, F = M.icosphere(level)
        e = np.abs(M.laplace_beltrami(V, F, V[:, 2]) + 2 * V[:, 2])
        med.append(np.median(e)); worst.append(e.max())
        weak.append(np.abs(M.cotan_matrix(V, F) @ V[:, 2] + 2 * M.vertex_areas(V, F) * V[:, 2]).sum())
    assert med[0] / med[1] > 3 and med[1] / med[2] > 3 and med[2] < 1e-3
    assert weak[0] / weak[1] > 2.5 and weak[1] / weak[2] > 2.5
    assert worst[2] > 0.2
    rows = np.asarray(M.cotan_matrix(V, F).sum(axis=1)).ravel()
    assert np.max(np.abs(rows)) < 1e-12
    assert M.edge_cotan_weight(np.pi / 3, np.pi / 3) > 0
    assert M.edge_cotan_weight(1.9, 1.5) < 0                                   # alpha + beta > pi
    assert M.edge_cotan_weight(1.5, np.pi - 1.5) == pytest.approx(0.0, abs=1e-12)


def test_spectrum():
    """eq-m06-spectrum: on a sphere of radius R the Laplace-Beltrami eigenvalues are l(l + 1)/R^2 with multiplicity
    2l + 1; the cotangent discretization converges to them."""
    th, ph = sp.symbols("theta phi")
    Y = sp.sin(th) * sp.cos(ph)                             # an l = 1 harmonic (x on the unit sphere)
    lb = 1 / sp.sin(th) * sp.diff(sp.sin(th) * sp.diff(Y, th), th) + sp.diff(Y, ph, 2) / sp.sin(th) ** 2
    assert sp.simplify(lb + 2 * Y) == 0
    R = 2.0
    V, F = M.icosphere(4, R)
    vals = M.spectrum(V, F, k=16) * R ** 2
    assert vals[0] == pytest.approx(0.0, abs=1e-6)
    assert np.allclose(vals[1:4], 2.0, rtol=0.01)
    assert np.allclose(vals[4:9], 6.0, rtol=0.01)
    assert np.allclose(vals[9:16], 12.0, rtol=0.02)


def test_geodesics():
    """eq-m06-geodesic: on a flat mesh, graph (Dijkstra) distance along edges never underestimates the geodesic; on a
    sphere it does not converge to it under refinement; on the equilateral lattice its excess is exactly (sin theta + sin(pi/3 - theta)) /
    sin(pi/3), up to 2/sqrt(3). The heat method converges: its error falls as the mesh is refined."""
    th = sp.symbols("theta")
    r = (sp.sin(th) + sp.sin(sp.pi / 3 - th)) / sp.sin(sp.pi / 3)
    assert sp.simplify(r.subs(th, sp.pi / 6) - 2 / sp.sqrt(3)) == 0
    assert sp.solve(sp.diff(r, th), th) == [sp.pi / 6]
    V, F = M.lattice_mesh(41, 1.0)
    src = 20 * 41 + 20
    d = np.linalg.norm(V - V[src], axis=1)
    gd = M.graph_distance(V, F, src)
    far = d > 5
    ang = np.arctan2(V[:, 1] - V[src, 1], V[:, 0] - V[src, 0])
    assert np.allclose(gd[far] / d[far], M.lattice_path_ratio(ang[far]), atol=1e-12)
    graph_err, heat_err = [], []
    for level in (2, 3, 4):
        V, F = M.icosphere(level)
        exact = M.sphere_distance(V, 0, 1.0)
        g = M.graph_distance(V, F, 0)
        graph_err.append(np.max(g - exact))
        heat_err.append(np.mean(np.abs(M.heat_geodesic(V, F, 0) - exact)))
    assert graph_err[2] > 0.9 * graph_err[0]                 # no convergence along edges
    assert heat_err[1] < 0.6 * heat_err[0] and heat_err[2] < 0.6 * heat_err[1] and heat_err[2] < 0.02
    assert np.all(gd[far] >= d[far] - 1e-12)                 # on a flat mesh, edge paths are never shorter
