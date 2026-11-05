"""m30 equation checks: eikonal ground truth, localization model, projection, interpolation,
conduction velocity and map errors.

Each test checks an equation in modules/m30-capstone-mini-mapping-system.qmd against a known
answer. Geometry and parameter values are test inputs (mm, ms), not physiological claims.
"""

import numpy as np
import pytest

from epml import mapping as mp


def plane_errors(n, spacing):
    V, F = mp.plane_mesh(n, n, spacing)
    c = (n // 2) * n + n // 2
    T = mp.eikonal(V, F, c, 1.0)
    d = np.linalg.norm(V - V[c], axis=1)
    far = d > 5.0
    return np.abs(T[far] - d[far]) / d[far]


def test_eikonal_on_a_plane_converges():
    """eq-m30-eikonal: on a flat sheet with speed v, T = distance / v; the mesh solution is within a
    few percent and improves as the mesh is refined."""
    coarse, fine = plane_errors(21, 2.0), plane_errors(81, 0.5)
    assert coarse.max() < 0.05 and fine.max() < 0.03
    assert fine.mean() < coarse.mean()
    V, F = mp.plane_mesh(21, 21, 1.0)
    T2 = mp.eikonal(V, F, 0, 2.0)
    T1 = mp.eikonal(V, F, 0, 1.0)
    assert T2 == pytest.approx(T1 / 2.0)  # doubling the speed halves every time


def test_eikonal_on_a_sphere_matches_great_circles():
    """eq-m30-eikonal: on a sphere of radius R, T = R * angle / v (geodesic distance / speed)."""
    errs = []
    for sub in (3, 4):
        V, F = mp.icosphere(20.0, sub)
        T = mp.eikonal(V, F, 0, 1.0)
        g = 20.0 * np.arccos(np.clip(V @ V[0] / 400.0, -1, 1))
        far = g > 5.0
        errs.append(np.mean(np.abs(T[far] - g[far]) / g[far]))
    assert errs[1] < 0.02 and errs[1] < errs[0]


def test_eikonal_goes_around_scar():
    """eq-m30-eikonal: triangles with zero speed do not conduct; the wave reaches the far side of a
    line of block only through the gap, so it arrives later than the straight-line time."""
    n, s = 41, 1.0
    V, F = mp.plane_mesh(n, n, s)
    cent = V[F].mean(axis=1)
    speed = np.ones(len(F))
    wall = (np.abs(cent[:, 0] - 20.0) < 1.0) & (cent[:, 1] < 30.0)  # wall at x = 20, gap above y = 30
    speed[wall] = 0.0
    src = 10 * n + 5  # (5, 10)
    T = mp.eikonal(V, F, src, speed)
    tgt = 10 * n + 35  # (35, 10), directly behind the wall
    straight = np.linalg.norm(V[tgt] - V[src])
    detour = np.linalg.norm(np.array([20.0, 31.0]) - V[src, :2]) + np.linalg.norm(
        V[tgt, :2] - np.array([20.0, 31.0]))
    assert T[tgt] > 1.5 * straight
    assert T[tgt] == pytest.approx(detour, rel=0.06)


def test_localization_model_statistics():
    """eq-m30-localization: measured = true + Gaussian error + respiratory sinusoid; over whole
    breathing cycles the error has the chosen spread and the respiratory part averages out."""
    rng = np.random.default_rng(0)
    n = 20000
    true = np.zeros((n, 3))
    t = np.linspace(0, 4000.0, n, endpoint=False)  # four 1000-ms cycles
    m = mp.measured_positions(true, t, sigma=1.0, resp_amp=3.0, resp_period=1000.0,
                              resp_dir=[0, 0, 1], rng=rng)
    assert np.std(m[:, 0]) == pytest.approx(1.0, rel=0.03)
    assert np.mean(m[:, 2]) == pytest.approx(0.0, abs=0.05)
    # z also carries the sinusoid: variance = sigma^2 + A^2 / 2
    assert np.var(m[:, 2]) == pytest.approx(1.0 + 4.5, rel=0.05)


def test_projection_onto_a_mesh():
    """eq-m30-projection: points on the surface project to themselves; off-surface points project to
    the nearest surface point (checked against a dense sampling of the triangles)."""
    V, F = mp.icosphere(10.0, 2)
    on = V[:20]
    proj, _ = mp.project_to_mesh(on, V, F)
    assert proj == pytest.approx(on, abs=1e-9)
    rng = np.random.default_rng(2)
    pts = rng.normal(0, 8.0, (15, 3))
    proj, idx = mp.project_to_mesh(pts, V, F)
    # dense barycentric sampling of every triangle
    u, w = np.meshgrid(np.linspace(0, 1, 30), np.linspace(0, 1, 30))
    keep = (u + w) <= 1
    u, w = u[keep], w[keep]
    A, B, C = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    samples = (A[:, None] + u[None, :, None] * (B - A)[:, None] + w[None, :, None] * (C - A)[:, None]
               ).reshape(-1, 3)
    for p, q in zip(pts, proj):
        dmin = np.min(np.linalg.norm(samples - p, axis=1))
        assert np.linalg.norm(q - p) <= dmin + 1e-9
        assert np.linalg.norm(q - p) >= dmin - 0.2  # samples are a fine grid on each triangle


def test_idw_reproduces_data_and_constants():
    """eq-m30-idw: the interpolant equals the data at data points and keeps a constant field
    constant."""
    rng = np.random.default_rng(3)
    data = rng.uniform(0, 50, (12, 2))
    query = np.vstack([data, rng.uniform(0, 50, (30, 2))])
    dist = np.linalg.norm(query[:, None] - data[None], axis=2)
    vals = rng.uniform(0, 100, 12)
    out = mp.idw(dist, vals)
    assert out[:12] == pytest.approx(vals)
    assert mp.idw(dist, np.full(12, 7.0)) == pytest.approx(np.full(len(query), 7.0))
    assert np.all((out >= vals.min() - 1e-9) & (out <= vals.max() + 1e-9))


def test_plane_fit_velocity_recovers_a_plane_wave():
    """eq-m30-cv-plane: for T = t0 + (x . n) / v, the fitted gradient gives speed v along n."""
    rng = np.random.default_rng(4)
    pts = rng.uniform(-3, 3, (8, 2))
    n = np.array([np.cos(0.7), np.sin(0.7)])
    T = 12.0 + pts @ n / 0.8
    vel = mp.plane_fit_velocity(pts, T)
    assert np.linalg.norm(vel) == pytest.approx(0.8)
    assert vel / np.linalg.norm(vel) == pytest.approx(n)


def test_map_errors():
    """eq-m30-errors: a perfect map has RMSE 0; fill distance shrinks as points are added."""
    V, F = mp.icosphere(15.0, 3)
    T = mp.eikonal(V, F, 0, 1.0)
    assert mp.rmse(T, T) == 0.0
    assert mp.rmse(T + 2.0, T) == pytest.approx(2.0)
    rng = np.random.default_rng(5)
    order = rng.permutation(len(V))
    D = mp.geodesic_distances(V, F, order[:40])
    h10, h40 = mp.fill_distance(D[:10]), mp.fill_distance(D)
    assert h40 < h10
