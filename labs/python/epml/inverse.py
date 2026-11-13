"""m07 · Inverse problems and regularization (Tikhonov, L-curve). MIT License.

Units: distance mm, potentials in relative units. The worked example is harmonic continuation: a potential that is
harmonic in a source-free layer (blood) of thickness h is smoothed on its way from the tissue surface to the electrode,
each spatial harmonic of wavenumber k by exp(-|k| h). The tissue-level profile is a sum of activation fronts with the
closed-form shape of m03 (eq-m03-unipolar-closed), made periodic. Generic tools work on any matrix through its SVD:
naive inversion, truncated SVD and Tikhonov filters (Hansen 1990), the expected error split into bias and noise,
the discrepancy principle, the L-curve corner (Hansen 1992; Hansen and O'Leary 1993), generalized cross-validation
(Golub, Heath and Wahba 1979), and the Gaussian (Bayesian) reading of Tikhonov regularization.
"""

import numpy as np


# ---------------------------------------------------------------- the forward problem (eq-m07-model, eq-m07-continuation)


def grid(n=256, length=32.0):
    """Periodic grid of n points over `length` mm: positions s (mm) and wavenumbers k (rad/mm), numpy FFT order."""
    s = np.arange(n) * length / n
    k = 2 * np.pi * np.fft.fftfreq(n, d=length / n)
    return s, k


def continuation_gain(k, h):
    """eq-m07-continuation: the factor exp(-|k| h) applied to each harmonic across a source-free layer of
    thickness h."""
    return np.exp(-np.abs(k) * h)


def continue_up(x, k, h):
    """Apply the continuation operator to samples x on the periodic grid with wavenumbers k."""
    return np.real(np.fft.ifft(np.fft.fft(x) * continuation_gain(k, h)))


def continuation_matrix(n, length, h):
    """The same operator as a dense, symmetric circulant matrix A (A @ x == continue_up(x))."""
    _, k = grid(n, length)
    col = np.real(np.fft.ifft(continuation_gain(k, h)))
    idx = (np.arange(n)[:, None] - np.arange(n)[None, :]) % n
    return col[idx]


def condition_number_continuation(h, dx):
    """eq-m07-model for the continuation operator: kappa = s_max / s_min = exp(pi h / dx), the gain at k = 0 over the
    gain at the Nyquist wavenumber pi / dx."""
    return np.exp(np.pi * h / dx)


def front_profile(s, a, length, n_harm=None):
    """The periodic version of the m03 unipolar front shape s / (s^2 + a^2):
    p(s; a) = (pi / L) sin(2 pi s / L) / (cosh(2 pi a / L) - cos(2 pi s / L)) = (2 pi / L) sum_m exp(-k_m a) sin(k_m s),
    k_m = 2 pi m / L. With n_harm set, the sum is truncated to m < n_harm (band-limited, exact on a grid)."""
    s = np.asarray(s, float)
    if n_harm is None:
        t = 2 * np.pi / length
        return (np.pi / length) * np.sin(t * s) / (np.cosh(t * a) - np.cos(t * s))
    m = np.arange(1, n_harm)
    km = 2 * np.pi * m / length
    return (2 * np.pi / length) * np.sin(np.outer(s, km)) @ np.exp(-km * a)


FRONTS = ((8.0, 1.0), (18.0, 1.0), (21.0, -1.0))   # (position mm, sign): one front, then two fronts 3 mm apart
                                                   # moving toward each other (illustrative)


def tissue_profile(s, width, length, fronts=FRONTS, n_harm=None):
    """Sum of fronts of width `width` (mm) on the tissue surface, in relative units (peak about 1 / (2 width))."""
    return sum(sign * front_profile(s - pos, width, length, n_harm) for pos, sign in fronts)


# ---------------------------------------------------------------- SVD tools (eq-m07-svd, eq-m07-filters)


def svd(A):
    return np.linalg.svd(A, full_matrices=False)


def picard(A, b):
    """Singular values s_i, coefficients |u_i^T b| and the ratios |u_i^T b| / s_i (eq-m07-svd)."""
    U, s, Vt = svd(A)
    beta = np.abs(U.T @ b)
    return s, beta, beta / s


def tikhonov_factors(s, lam):
    """eq-m07-filters: f_i = s_i^2 / (s_i^2 + lam^2)."""
    return s**2 / (s**2 + lam**2)


def tsvd_factors(s, k):
    """eq-m07-filters: f_i = 1 for the k largest singular values, else 0."""
    f = np.zeros_like(s)
    f[:k] = 1.0
    return f


def filtered_solution(A, b, factors):
    """x = sum_i f_i (u_i^T b / s_i) v_i, with f given as an array or as a function of s."""
    U, s, Vt = svd(A)
    f = factors(s) if callable(factors) else factors
    return Vt.T @ (f * (U.T @ b) / s)


def tikhonov(A, b, lam):
    """argmin ||A x - b||^2 + lam^2 ||x||^2 via the normal equations."""
    n = A.shape[1]
    return np.linalg.solve(A.T @ A + lam**2 * np.eye(n), A.T @ b)


def naive(A, b):
    """The unregularized least-squares solution (all filter factors 1)."""
    return filtered_solution(A, b, np.ones(min(A.shape)))


# ---------------------------------------------------------------- error (eq-m07-error)


def expected_error(s, coef, sigma, f):
    """eq-m07-error: E ||x_filt - x||^2 = sum (1 - f_i)^2 c_i^2 + sigma^2 sum f_i^2 / s_i^2, with c_i = v_i^T x and
    white noise of standard deviation sigma per sample. Returns (bias^2, noise variance, total)."""
    bias = np.sum((1 - f) ** 2 * coef**2)
    var = sigma**2 * np.sum(f**2 / s**2)
    return bias, var, bias + var


def best_single_factor(s, c, sigma):
    """The filter factor that minimizes (1 - f)^2 c^2 + sigma^2 f^2 / s^2 for one component: s^2 c^2 / (s^2 c^2 +
    sigma^2), Tikhonov's factor with lam = sigma / |c|."""
    return s**2 * c**2 / (s**2 * c**2 + sigma**2)


def fourier_expected_error(gain, X, sigma, f):
    """eq-m07-error for a circulant operator in the DFT basis: X = fft(x) (unnormalized), gain = the operator's
    eigenvalues. E ||x_filt - x||^2 = (1/n) sum (1 - f)^2 |X|^2 + sigma^2 sum f^2 / gain^2."""
    n = len(X)
    bias = np.sum((1 - f) ** 2 * np.abs(X) ** 2) / n
    var = sigma**2 * np.sum(f**2 / gain**2)
    return bias, var, bias + var


def fourier_tikhonov(b, gain, lam):
    """Tikhonov for a circulant operator: each harmonic multiplied by gain / (gain^2 + lam^2)."""
    return np.real(np.fft.ifft(np.fft.fft(b) * gain / (gain**2 + lam**2)))


# ---------------------------------------------------------------- choosing lambda (eq-m07-choice)


def residual_and_norm(A, b, lams):
    """Residual norms ||A x_lam - b|| and solution norms ||x_lam|| for Tikhonov (any m >= n)."""
    U, s, Vt = svd(A)
    beta = U.T @ b
    outside = np.linalg.norm(b - U @ beta) ** 2
    res, sol = [], []
    for lam in np.atleast_1d(lams):
        f = tikhonov_factors(s, lam)
        res.append(np.sqrt(np.sum(((1 - f) * beta) ** 2) + outside))
        sol.append(np.linalg.norm(f * beta / s))
    return np.array(res), np.array(sol)


def discrepancy(A, b, noise_norm, tau=1.0, lo=1e-12, hi=1e3, iters=200):
    """eq-m07-choice: the lam with ||A x_lam - b|| = tau ||e||, by bisection in log lam (the residual grows with lam)."""
    a, c = np.log(lo), np.log(hi)
    for _ in range(iters):
        mid = (a + c) / 2
        if residual_and_norm(A, b, np.exp(mid))[0][0] < tau * noise_norm:
            a = mid
        else:
            c = mid
    return float(np.exp((a + c) / 2))


def gcv(A, b, lams):
    """eq-m07-choice: G(lam) = ||A x_lam - b||^2 / [trace(I - A A_lam^#)]^2, with trace(A A_lam^#) = sum f_i."""
    m = A.shape[0]
    _, s, _ = svd(A)
    res, _ = residual_and_norm(A, b, lams)
    return np.array([r**2 / (m - np.sum(tikhonov_factors(s, lam))) ** 2 for r, lam in zip(res, np.atleast_1d(lams))])


def gcv_explicit(A, b, lam):
    """The same G(lam) from the explicit influence matrix, for checking."""
    m, n = A.shape
    Asharp = np.linalg.solve(A.T @ A + lam**2 * np.eye(n), A.T)
    r = A @ (Asharp @ b) - b
    return r @ r / np.trace(np.eye(m) - A @ Asharp) ** 2


def lcurve_corner(A, b, lams):
    """The lam of largest curvature of (log ||A x - b||, log ||x||) (Hansen 1992); `lams` increasing and evenly
    spaced in log. Curvature by finite differences in log lam."""
    res, sol = residual_and_norm(A, b, lams)
    x, y, t = np.log(res), np.log(sol), np.log(lams)
    dx, dy = np.gradient(x, t), np.gradient(y, t)
    ddx, ddy = np.gradient(dx, t), np.gradient(dy, t)
    kappa = (dx * ddy - dy * ddx) / (dx**2 + dy**2) ** 1.5
    inner = slice(2, -2)
    return float(lams[inner][np.argmax(kappa[inner])])


def error_curve(A, b, x_true, lams):
    """Actual ||x_lam - x|| for each lam (only possible when the truth is known)."""
    U, s, Vt = svd(A)
    beta = U.T @ b
    return np.array([np.linalg.norm(Vt.T @ (tikhonov_factors(s, lam) * beta / s) - x_true) for lam in lams])


# ---------------------------------------------------------------- Bayesian reading (eq-m07-bayes)


def posterior(A, b, sigma_e, sigma_x):
    """eq-m07-bayes: with x ~ N(0, sigma_x^2 I) and e ~ N(0, sigma_e^2 I), the posterior of x given b is Gaussian with
    mean (A^T A + lam^2 I)^-1 A^T b and covariance sigma_e^2 (A^T A + lam^2 I)^-1, lam = sigma_e / sigma_x."""
    n = A.shape[1]
    lam = sigma_e / sigma_x
    M = A.T @ A + lam**2 * np.eye(n)
    return np.linalg.solve(M, A.T @ b), sigma_e**2 * np.linalg.inv(M)


def posterior_by_conditioning(A, b, sigma_e, sigma_x):
    """The same posterior from the joint Gaussian of (x, b): mean Sx A^T (A Sx A^T + Se)^-1 b and covariance
    Sx - Sx A^T (A Sx A^T + Se)^-1 A Sx."""
    m, n = A.shape
    Sx = sigma_x**2 * np.eye(n)
    G = A @ Sx @ A.T + sigma_e**2 * np.eye(m)
    K = Sx @ A.T @ np.linalg.inv(G)
    return K @ b, Sx - K @ A @ Sx
