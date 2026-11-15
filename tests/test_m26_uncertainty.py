"""m26 equation tests: GP interpolation, leave-one-out, error budget, point density and adaptive sampling."""

import numpy as np
import pytest
import sympy as sp

from epml import uncertainty as UN


def test_gp():
    """eq-m26-gp: posterior mean and variance; calibrated 95% bands for functions drawn from the prior."""
    # One observation: mean k y / (s2 + n2), variance s2 - k^2 / (s2 + n2)
    k, s2, n2, y = sp.symbols("k s2 n2 y", positive=True)
    mu = k / (s2 + n2) * y
    var = s2 - k**2 / (s2 + n2)
    X = np.array([[0.0, 0.0]])
    m, v = UN.gp_posterior(X, [3.0], [[2.0, 1.0]], 4.0, 25.0, 1.5)
    kk = 25.0 * np.exp(-0.5 * 5.0 / 16.0)
    assert m[0] == pytest.approx(float(mu.subs({k: kk, s2: 25.0, n2: 2.25, y: 3.0})))
    assert v[0] == pytest.approx(float(var.subs({k: kk, s2: 25.0, n2: 2.25})))
    assert UN.single_point_variance(np.sqrt(5.0), 4.0, 25.0, 1.5) == pytest.approx(v[0])
    # Calibration: draw functions from the prior on a grid, observe 25 noisy points, check 95% coverage
    rng = np.random.default_rng(1)
    g = np.stack(np.meshgrid(np.linspace(0, 30, 16), np.linspace(0, 30, 16)), -1).reshape(-1, 2)
    K = UN.se_kernel(g, g, 6.0, 100.0) + 1e-8 * np.eye(len(g))
    Lc = np.linalg.cholesky(K)
    hits = []
    for _ in range(150):
        f = Lc @ rng.normal(size=len(g))
        idx = rng.choice(len(g), 25, replace=False)
        yobs = f[idx] + rng.normal(0, 1.0, 25)
        mu_, var_ = UN.gp_posterior(g[idx], yobs, g, 6.0, 100.0, 1.0)
        hits.append(np.mean(np.abs(f - mu_) <= 1.96 * np.sqrt(var_ + 1e-12)))
    assert np.mean(hits) == pytest.approx(0.95, abs=0.02)


def test_loo():
    """eq-m26-loo: closed-form leave-one-out residuals equal refitting without each point."""
    rng = np.random.default_rng(2)
    X = rng.uniform(0, 40, (30, 2))
    y = np.hypot(X[:, 0] - 12, X[:, 1] - 15) + rng.normal(0, 1, 30)
    r1, v1 = UN.loo_residuals(X, y, 8.0, 400.0, 1.0, y.mean())
    r2, v2 = UN.loo_bruteforce(X, y, 8.0, 400.0, 1.0, y.mean())
    assert np.allclose(r1, r2, atol=1e-9) and np.allclose(v1, v2, rtol=1e-9)


def test_budget():
    """eq-m26-budget: independent per-point errors add in variance; position error enters as sigma_x / c; the GP
    posterior SD at a mapped point approaches that per-point SD when the prior is broad."""
    rng = np.random.default_rng(3)
    n = 400_000
    sx, c = 2.0, 0.8
    # a position error moves the point along a plane wave of speed c: time error = displacement / c
    disp = rng.normal(0, sx, n)
    e = rng.normal(0, 1.0, n) + rng.normal(0, 2.0, n) + disp / c
    assert np.std(e) == pytest.approx(UN.error_budget(1.0, 2.0, sx, c), rel=0.005)
    a, r, p, cc = sp.symbols("sigma_a sigma_r sigma_x c", positive=True)
    from sympy.stats import Normal, variance
    tot = Normal("a", 0, a) + Normal("r", 0, r) + Normal("x", 0, p) / cc
    assert sp.simplify(variance(tot) - (a**2 + r**2 + p**2 / cc**2)) == 0
    sn = UN.error_budget(1.0, 2.0, sx, c)
    assert np.sqrt(UN.single_point_variance(0.0, 8.0, 1e6, sn)) == pytest.approx(sn, rel=1e-4)


def test_density():
    """eq-m26-density: distance from a random spot to the nearest Poisson point: mean 1/(2 sqrt(rho))."""
    r, rho = sp.symbols("r rho", positive=True)
    pdf = sp.diff(1 - sp.exp(-rho * sp.pi * r**2), r)
    assert sp.simplify(sp.integrate(r * pdf, (r, 0, sp.oo)) - 1 / (2 * sp.sqrt(rho))) == 0
    rng = np.random.default_rng(4)
    q = rng.uniform(30, 70, (800, 2))
    for dens in (0.01, 0.015):
        d = []
        for _ in range(60):
            P = rng.uniform(0, 100, (rng.poisson(dens * 1e4), 2))
            d.append(np.min(np.linalg.norm(q[:, None, :] - P[None, :, :], axis=2), axis=1))
        d = np.concatenate(d)
        assert np.mean(d) == pytest.approx(UN.nn_distance_mean(dens), rel=0.03)
        assert np.median(d) == pytest.approx(UN.nn_distance_median(dens), rel=0.03)


def test_adaptive():
    """eq-m26-adaptive: the posterior variance does not depend on the data, and greedy max-variance sampling lowers
    the largest remaining variance faster than random sampling."""
    rng = np.random.default_rng(5)
    G = np.stack(np.meshgrid(np.linspace(0, 40, 21), np.linspace(0, 40, 21)), -1).reshape(-1, 2)
    idx = rng.choice(len(G), 20, replace=False)
    _, v1 = UN.gp_posterior(G[idx], rng.normal(0, 30, 20), G, 8.0, 400.0, 1.0)
    _, v2 = UN.gp_posterior(G[idx], rng.normal(0, 30, 20), G, 8.0, 400.0, 1.0)
    assert np.allclose(v1, v2)
    ch = UN.greedy_max_variance(G, 20, 8.0, 400.0, 1.0)
    _, vg = UN.gp_posterior(G[ch], np.zeros(20), G, 8.0, 400.0, 1.0)
    worst_random = []
    for _ in range(20):
        ri = rng.choice(len(G), 20, replace=False)
        worst_random.append(UN.gp_posterior(G[ri], np.zeros(20), G, 8.0, 400.0, 1.0)[1].max())
    assert vg.max() < np.min(worst_random)
