"""m07 · Inverse problems and regularization: equation tests."""

import numpy as np
import pytest
import sympy as sp

from epml import inverse as I

N, LENGTH, W = 256, 32.0, 0.3


def setup(h):
    s, k = I.grid(N, LENGTH)
    x = I.tissue_profile(s, W, LENGTH, n_harm=N // 2)
    A = I.continuation_matrix(N, LENGTH, h)
    return s, k, x, A


def test_model():
    """eq-m07-model: ||dx|| / ||x|| <= kappa ||db|| / ||b||, with equality for b along u_1 and db along u_n; for the
    continuation operator kappa = exp(pi h / dx)."""
    rng = np.random.default_rng(0)
    U, _ = np.linalg.qr(rng.standard_normal((12, 12)))
    V, _ = np.linalg.qr(rng.standard_normal((12, 12)))
    sv = np.logspace(0, -6, 12)
    A = U @ np.diag(sv) @ V.T
    kappa = sv[0] / sv[-1]
    for _ in range(200):
        x, dx = rng.standard_normal(12), rng.standard_normal(12) * 1e-3
        b, db = A @ x, A @ dx
        assert np.linalg.norm(dx) / np.linalg.norm(x) <= kappa * np.linalg.norm(db) / np.linalg.norm(b) * (1 + 1e-9)
    b, db = U[:, 0], 1e-3 * U[:, -1]
    x, dx = np.linalg.solve(A, b), np.linalg.solve(A, db)
    assert np.linalg.norm(dx) / np.linalg.norm(x) == pytest.approx(kappa * np.linalg.norm(db) / np.linalg.norm(b))
    for h in (0.25, 0.5):
        A = I.continuation_matrix(N, LENGTH, h)
        sv = np.linalg.svd(A, compute_uv=False)
        assert sv[0] / sv[-1] == pytest.approx(I.condition_number_continuation(h, LENGTH / N), rel=1e-6)


def test_continuation():
    """eq-m07-continuation: exp(-k z) cos(k x) solves Laplace's equation, so each harmonic is multiplied by
    exp(-|k| h) across a source-free layer; continuing the m03 front shape of width w by h gives width w + h; with the
    same amplitude in every harmonic and per-harmonic noise eps times that amplitude, the best truncation keeps
    |k| < ln(1/eps) / h."""
    x_, z, k = sp.symbols("x z k", positive=True)
    phi = sp.exp(-k * z) * sp.cos(k * x_)
    assert sp.simplify(sp.diff(phi, x_, 2) + sp.diff(phi, z, 2)) == 0
    s, kk, x, A = setup(1.0)
    assert np.allclose(I.front_profile(s - 5, 0.7, LENGTH), I.front_profile(s - 5, 0.7, LENGTH, n_harm=4000), atol=1e-10)
    near = np.abs(s - 16) < 2                                 # the periodic shape matches s / (s^2 + a^2) near a front
    assert np.allclose(I.front_profile(s[near] - 16, 0.7, LENGTH), (s[near] - 16) / ((s[near] - 16) ** 2 + 0.49), atol=0.02)
    for h in (0.5, 1.0, 3.0):
        up = I.continue_up(x, kk, h)
        assert np.allclose(up, I.tissue_profile(s, W + h, LENGTH, n_harm=N // 2), atol=1e-12)
        assert np.allclose(I.continuation_matrix(N, LENGTH, h) @ x, up, atol=1e-12)
    h, eps = 1.5, 1e-3
    gain = I.continuation_gain(kk, h)
    order = np.argsort(np.abs(kk), kind="stable")
    X = np.ones(N) * 10.0                                     # the same amplitude in every harmonic
    sigma = eps * 10.0 / np.sqrt(N)                           # white noise of this sigma: eps * 10 per harmonic
    best = min(range(1, N + 1), key=lambda m: I.fourier_expected_error(
        gain, X, sigma, np.isin(np.arange(N), order[:m]).astype(float))[2])
    kc = np.abs(kk[order[best - 1]])
    assert abs(kc - np.log(1 / eps) / h) < 2 * np.pi / LENGTH


def test_svd():
    """eq-m07-svd: the naive solution is the truth plus sum (u_i^T e / s_i) v_i; for clean continued data the
    coefficients |u^T b| decay faster than s (discrete Picard condition: their ratio is the tissue spectrum, which falls
    as exp(-|k| w)); with noise, the naive solution is useless."""
    rng = np.random.default_rng(1)
    s_, kk, x, A = setup(1.0)
    b0 = A @ x
    e = 1e-3 * np.max(np.abs(b0)) * rng.standard_normal(N)
    U, sv, Vt = np.linalg.svd(A)
    assert np.allclose(I.naive(A, b0 + e) - x, Vt.T @ ((U.T @ e) / sv), atol=1e-6 * np.linalg.norm(x))
    assert np.linalg.norm(I.naive(A, b0 + e) - x) > 1e4 * np.linalg.norm(x)
    B, X = np.fft.fft(b0), np.fft.fft(x)
    gain = I.continuation_gain(kk, 1.0)
    ok = gain > 1e-6                                          # below that, rounding in B dominates
    assert np.allclose(np.abs(B[ok]) / gain[ok], np.abs(X[ok]), rtol=1e-6)
    assert np.all(np.abs(X) <= 3 * (N * np.pi / LENGTH) * np.exp(-np.abs(kk) * W) * (1 + 1e-9) + 1e-9)


def test_filters():
    """eq-m07-filters: Tikhonov by normal equations equals the SVD filter form with f = s^2 / (s^2 + lam^2); TSVD
    equals the pseudo-inverse of the rank-k truncation; f = 1/2 at s = lam."""
    rng = np.random.default_rng(2)
    A = rng.standard_normal((30, 20)) @ np.diag(np.logspace(0, -5, 20))
    b = rng.standard_normal(30)
    for lam in (1e-4, 1e-2, 1.0):
        assert np.allclose(I.tikhonov(A, b, lam), I.filtered_solution(A, b, lambda s: I.tikhonov_factors(s, lam)))
    U, sv, Vt = np.linalg.svd(A, full_matrices=False)
    k = 7
    Ak = U[:, :k] @ np.diag(sv[:k]) @ Vt[:k]
    assert np.allclose(I.filtered_solution(A, b, I.tsvd_factors(sv, k)), np.linalg.pinv(Ak) @ b)
    lam = sp.symbols("lambda", positive=True)
    f = lambda s: s**2 / (s**2 + lam**2)
    assert f(lam) == sp.Rational(1, 2)
    assert sp.limit(f(sp.Symbol("s", positive=True)), sp.Symbol("s", positive=True), sp.oo) == 1


def test_expected_error():
    """eq-m07-error: the bias-plus-noise formula matches Monte Carlo; for one component the best factor is
    s^2 c^2 / (s^2 c^2 + sigma^2), Tikhonov's with lam = sigma / |c|; the DFT form equals the SVD form for the
    continuation operator."""
    rng = np.random.default_rng(3)
    A = rng.standard_normal((25, 25)) @ np.diag(np.logspace(0, -4, 25))
    x = rng.standard_normal(25)
    U, sv, Vt = np.linalg.svd(A)
    sigma, lam = 1e-3, 3e-3
    f = I.tikhonov_factors(sv, lam)
    bias, var, tot = I.expected_error(sv, Vt @ x, sigma, f)
    mc = np.mean([np.sum((I.filtered_solution(A, A @ x + sigma * rng.standard_normal(25), f) - x) ** 2)
                  for _ in range(4000)])
    assert mc == pytest.approx(tot, rel=0.04)
    s_, c_, sg_, ff = sp.symbols("s c sigma f", positive=True)
    J = (1 - ff) ** 2 * c_**2 + sg_**2 * ff**2 / s_**2
    assert sp.simplify(sp.solve(sp.diff(J, ff), ff)[0] - s_**2 * c_**2 / (s_**2 * c_**2 + sg_**2)) == 0
    assert I.best_single_factor(2.0, 3.0, 1.5) == pytest.approx(36 / (36 + 2.25))
    s, kk, x, A = setup(1.0)
    U, sv, Vt = np.linalg.svd(A)
    gain = I.continuation_gain(kk, 1.0)
    for lam in (1e-3, 1e-2):
        a = I.expected_error(sv, Vt @ x, 0.01, I.tikhonov_factors(sv, lam))
        bb = I.fourier_expected_error(gain, np.fft.fft(x), 0.01, I.tikhonov_factors(gain, lam))
        assert np.allclose(a, bb, rtol=1e-6)


def test_choice():
    """eq-m07-choice: the GCV function from the SVD equals the explicit trace form; the residual grows and the solution
    norm shrinks with lam; the discrepancy lam solves its equation. On the continuation problem (h = 1 mm) the
    discrepancy principle, the L-curve corner and GCV each give an error within 1.35 times the best possible; with
    h = 0.5 mm and 0.1% noise the L-curve corner is more than twice as bad (one known failure mode)."""
    rng = np.random.default_rng(4)
    A = rng.standard_normal((30, 20)) @ np.diag(np.logspace(0, -5, 20))
    b = A @ rng.standard_normal(20) + 1e-3 * rng.standard_normal(30)
    for lam in (1e-4, 1e-2):
        assert I.gcv(A, b, [lam])[0] == pytest.approx(I.gcv_explicit(A, b, lam), rel=1e-8)
    lams = np.logspace(-6, 0, 50)
    res, sol = I.residual_and_norm(A, b, lams)
    assert np.all(np.diff(res) > -1e-15) and np.all(np.diff(sol) < 1e-15)
    lam_d = I.discrepancy(A, b, 1e-3 * np.sqrt(30))
    assert I.residual_and_norm(A, b, lam_d)[0][0] == pytest.approx(1e-3 * np.sqrt(30), rel=1e-6)
    lams = np.logspace(-7, 0, 141)
    for h, eps, seed, limit in ((1.0, 1e-2, 0, 1.35), (1.0, 1e-1, 1, 1.35), (1.0, 1e-3, 2, 1.35)):
        s, kk, x, A = setup(h)
        b0 = A @ x
        sigma = eps * np.max(np.abs(b0))
        b = b0 + sigma * np.random.default_rng(seed).standard_normal(N)
        best = I.error_curve(A, b, x, lams).min()
        for lam in (I.discrepancy(A, b, sigma * np.sqrt(N)), I.lcurve_corner(A, b, lams),
                    lams[np.argmin(I.gcv(A, b, lams))]):
            assert I.error_curve(A, b, x, [lam])[0] < limit * best
    s, kk, x, A = setup(0.5)
    b0 = A @ x
    b = b0 + 1e-3 * np.max(np.abs(b0)) * np.random.default_rng(0).standard_normal(N)
    best = I.error_curve(A, b, x, lams).min()
    assert I.error_curve(A, b, x, [I.lcurve_corner(A, b, lams)])[0] > 2 * best


def test_bayes():
    """eq-m07-bayes: with Gaussian prior and noise, the posterior mean is the Tikhonov solution with
    lam = sigma_e / sigma_x and the covariance is sigma_e^2 (A^T A + lam^2 I)^-1 (equal to the conditioning formula);
    95% credible intervals contain the truth about 95% of the time when the prior is right."""
    a, b, sx, se = sp.symbols("a b sigma_x sigma_e", positive=True)
    mean_cond = sx**2 * a / (a**2 * sx**2 + se**2) * b
    lam = se / sx
    assert sp.simplify(mean_cond - a * b / (a**2 + lam**2)) == 0
    rng = np.random.default_rng(5)
    A = rng.standard_normal((15, 10)) @ np.diag(np.logspace(0, -3, 10))
    bb = rng.standard_normal(15)
    m1, C1 = I.posterior(A, bb, 0.05, 2.0)
    m2, C2 = I.posterior_by_conditioning(A, bb, 0.05, 2.0)
    assert np.allclose(m1, m2) and np.allclose(C1, C2)
    assert np.allclose(m1, I.tikhonov(A, bb, 0.05 / 2.0))
    A = I.continuation_matrix(20, 10.0, 0.5)
    hits = []
    for _ in range(600):
        x = 1.0 * rng.standard_normal(20)
        y = A @ x + 0.01 * rng.standard_normal(20)
        m, C = I.posterior(A, y, 0.01, 1.0)
        hits.append(np.abs(x - m) <= 1.96 * np.sqrt(np.diag(C)))
    assert 0.93 < np.mean(hits) < 0.97
