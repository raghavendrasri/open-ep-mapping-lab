"""m41 equation tests: forward model, QRS integrals, regression, geodesic error, pace-map similarity,
Gaussian process and expected improvement."""

import numpy as np
import pytest
import sympy as sp

from epml import origins as og
from epml.mapping import icosphere

E = np.array(list(og.ELECTRODES.values()))


@pytest.fixture(scope="module")
def heart():
    R = og.rotation((0, 0, 1), 40) @ og.rotation((0, 1, 0), 45)
    v, t = og.lv_mesh(R=R)
    n, a = og.normals_areas(v, t)
    return v, t, og.solid_angles(v, n, a, E), og.edge_distances(v, t)


def test_solid_angles_of_a_closed_surface(heart):
    """Outside a closed surface the solid angles cancel; from the centre they add up to 4 pi."""
    v, t, Om, _ = heart
    assert np.all(np.abs(Om.sum(1)) < 1e-3 * np.abs(Om).sum(1))
    n, a = og.normals_areas(v, t)
    assert og.solid_angles(v, n, a, [[0.0, 0.0, 0.0]]).sum() == pytest.approx(4 * np.pi, rel=0.01)


def test_qrs_integral_matches_numeric_integration(heart):
    """eq-m41-integral: integral over [0, T] of phi_e = sum_j Omega_ej (T - tau_j)_+ for a sharp step."""
    v, t, Om, D = heart
    tau = D[17] / 0.6
    tt = np.arange(0, 120.0001, 0.02)
    numeric = np.trapezoid(og.leads12(og.electrode_potentials(Om, tau, tt, rise=0.02)), dx=0.02, axis=1)
    closed = og.qrs_integral(Om, tau, 120.0)
    assert np.allclose(numeric, closed, rtol=0.01, atol=0.01 * np.abs(closed).max())


def test_qrs_integral_after_full_activation_is_linear_in_times(heart):
    """eq-m41-integral with T beyond the last activation: the T term cancels (closed surface)."""
    v, t, Om, D = heart
    tau = D[5] / 0.6
    T = tau.max() + 50
    lhs = og.qrs_integral(Om, tau, T)
    rhs = og.leads12(-(Om @ tau)) + og.leads12(Om.sum(1) * T)
    assert np.allclose(lhs, rhs)
    assert np.abs(og.leads12(Om.sum(1) * T)).max() < 1e-2 * np.abs(lhs).max()


def test_twelve_leads_obey_einthoven_and_goldberger():
    phi = np.random.default_rng(0).normal(size=(9, 50))
    L = og.leads12(phi)
    I, II, III, aVR, aVL, aVF = L[:6]
    assert np.allclose(I + III, II)
    assert np.allclose(aVR + aVL + aVF, 0)


def test_linear_fit_recovers_map_and_interpolates():
    """eq-m41-linear: noise-free data give W and b back; with p + 1 points the fit is exact at them."""
    rng = np.random.default_rng(1)
    W0, b0 = rng.normal(size=(3, 3)), rng.normal(size=3)
    X = rng.normal(size=(20, 3))
    W, b = og.fit_linear(X, X @ W0 + b0)
    assert np.allclose(W, W0) and np.allclose(b, b0)
    X4, Y4 = rng.normal(size=(4, 3)), rng.normal(size=(4, 3))
    W, b = og.fit_linear(X4, Y4)
    assert np.allclose(X4 @ W + b, Y4)
    A = np.c_[X, np.ones(20)]
    Y = rng.normal(size=(20, 3))
    assert np.allclose(np.r_[og.fit_linear(X, Y)[0], og.fit_linear(X, Y)[1][None]], np.linalg.lstsq(A, Y, rcond=None)[0])


def test_geodesic_error_on_sphere():
    """eq-m41-geodesic: d = R arccos(u.v) >= chord = 2 R sin(d / 2R); edge paths are 0-21% longer."""
    d, R = sp.symbols("d R", positive=True)
    chord = 2 * R * sp.sin(d / (2 * R))
    assert sp.simplify(chord.subs(d, R * sp.pi) - 2 * R) == 0
    assert sp.series(chord, d, 0, 4).removeO().equals(d - d**3 / (24 * R**2))
    v, t = icosphere(30.0, 3)
    g = og.sphere_geodesic(v[:, None, :], v[None, :, :], 30.0)
    De = og.edge_distances(v, t)
    m = g > 5
    ratio = De[m] / g[m]
    assert ratio.min() > 0.99 and 1.03 < ratio.mean() < 1.10 and ratio.max() < 1.25
    assert np.all(np.linalg.norm(v[:, None] - v[None], axis=-1) <= g + 1e-9)


def test_pacemap_correlation():
    """eq-m41-corr: 1 for identical signals, -1 for negated, unchanged by per-lead scale and offset."""
    rng = np.random.default_rng(2)
    a = rng.normal(size=(12, 100))
    assert og.pacemap_corr(a, a) == pytest.approx(1.0)
    assert og.pacemap_corr(a, -a) == pytest.approx(-1.0)
    b = a * rng.uniform(0.5, 2, (12, 1)) + rng.normal(size=(12, 1))
    assert og.pacemap_corr(a, b) == pytest.approx(1.0)


def test_gp_posterior_matches_formula_and_sklearn():
    """eq-m41-gp against the dense formula (Frazier 2018, eq. 3) and scikit-learn with fixed kernel."""
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF, ConstantKernel

    rng = np.random.default_rng(3)
    Xtr, ytr, Xte = rng.uniform(0, 50, (8, 2)), rng.normal(size=8), rng.uniform(0, 50, (30, 2))
    ell, sf, sn = 12.0, 0.8, 0.05
    mu, var = og.gp_posterior(Xtr, ytr, Xte, ell, sf, sn)
    K = og.rbf(Xtr, Xtr, ell, sf) + sn**2 * np.eye(8)
    Ks = og.rbf(Xte, Xtr, ell, sf)
    assert np.allclose(mu, Ks @ np.linalg.solve(K, ytr))
    assert np.allclose(var, sf**2 - np.einsum("ij,ji->i", Ks, np.linalg.solve(K, Ks.T)))
    gpr = GaussianProcessRegressor(ConstantKernel(sf**2, "fixed") * RBF(ell, "fixed"), alpha=sn**2, optimizer=None).fit(Xtr, ytr)
    m2, s2 = gpr.predict(Xte, return_std=True)
    assert np.allclose(mu, m2) and np.allclose(np.sqrt(var), s2, atol=1e-6)
    mu0, var0 = og.gp_posterior(Xtr, ytr, Xtr, ell, sf, 1e-6)
    assert np.allclose(mu0, ytr, atol=1e-4) and var0.max() < 1e-6


def test_expected_improvement_closed_form():
    """eq-m41-ei against Monte Carlo and symbolic integration; sigma = 0 limit."""
    rng = np.random.default_rng(4)
    for mu, s, best in [(0.2, 0.3, 0.5), (1.0, 0.5, 0.4), (0.0, 1.0, 0.0)]:
        f = rng.normal(mu, s, 2_000_000)
        assert og.expected_improvement(mu, s, best) == pytest.approx(np.maximum(f - best, 0).mean(), rel=0.01)
    assert og.expected_improvement(0.7, 0.0, 0.5) == pytest.approx(0.2)
    assert og.expected_improvement(0.3, 0.0, 0.5) == 0.0
    x, m, s, b = sp.symbols("x m s b", real=True)
    s_ = sp.Symbol("s", positive=True)
    dens = sp.exp(-((x - m) ** 2) / (2 * s_**2)) / (s_ * sp.sqrt(2 * sp.pi))
    integral = sp.integrate((x - b) * dens, (x, b, sp.oo))
    vals = {m: 0.3, s_: 0.7, b: 0.5}
    assert float(integral.subs(vals)) == pytest.approx(float(og.expected_improvement(0.3, 0.7, 0.5)), rel=1e-9)


def test_active_pacemap_beats_random_on_a_smooth_landscape():
    g = np.stack(np.meshgrid(np.arange(0, 60, 2.0), np.arange(0, 60, 2.0), indexing="ij"), -1).reshape(-1, 2)
    target = np.array([41.0, 17.0])
    sim = np.exp(-((g - target) ** 2).sum(1) / (2 * 12.0**2))
    err = {}
    for rule in ("ei", "random"):
        e = []
        for k in range(10):
            r = np.random.default_rng(k)
            paced = og.active_pacemap(sim, g, list(r.choice(len(g), 2, replace=False)), 10, ell=12.0, sf=0.5, sn=0.01, rule=rule, rng=r)
            assert len(set(paced)) == len(paced) == 10
            e.append(np.linalg.norm(g[paced[int(np.argmax(sim[paced]))]] - target))
        err[rule] = np.mean(e)
    assert err["ei"] < err["random"]
    allowed = g[:, 0] < 30
    paced = og.active_pacemap(sim, g, [0, 1], 8, ell=12.0, sf=0.5, sn=0.01, allowed=allowed, rng=np.random.default_rng(0))
    assert np.all(allowed[paced[2:]])


def test_sequential_patient_fit_returns_one_prediction_per_fit(heart):
    v, t, Om, D = heart
    X = np.array([og.qrs_integral(Om, D[s] / 0.6)[[2, 7, 11]] for s in range(len(v))])
    preds = og.sequential_patient_fit(X, v, D, 100, n_remote=4, n_total=9, radius=15.0, rng=np.random.default_rng(0))
    assert len(preds) == 6
    assert D[preds[-1], 100] < 10
