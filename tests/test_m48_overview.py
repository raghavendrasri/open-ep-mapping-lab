"""m48 · Imaging across the EP workflow: equation tests (numeric, and symbolic with SymPy where feasible)."""

import numpy as np
import pytest
import sympy as sp
from scipy import ndimage as ndi

from epml import overview as O


def test_psf_fwhm():
    """eq-m48-psf: a Gaussian of standard deviation sigma falls to half its peak at sigma sqrt(2 ln 2), so
    FWHM = 2 sqrt(2 ln 2) sigma (about 2.355 sigma); the sampled PSF has unit area and the measured FWHM agrees."""
    x, s = sp.symbols("x sigma", positive=True)
    half = sp.solve(sp.Eq(sp.exp(-x ** 2 / (2 * s ** 2)), sp.Rational(1, 2)), x)
    assert len(half) == 1 and sp.simplify(2 * half[0] - 2 * sp.sqrt(2 * sp.log(2)) * s) == 0
    assert sp.integrate(sp.exp(-x ** 2 / (2 * s ** 2)) / (sp.sqrt(2 * sp.pi) * s), (x, -sp.oo, sp.oo)) == 1
    assert O.FWHM_PER_SIGMA == pytest.approx(2.35482, abs=1e-5)
    xs = np.linspace(-20, 20, 40001)
    for sigma in (0.3, 1.0, 2.7):
        assert np.trapezoid(O.gaussian_psf(xs, sigma), xs) == pytest.approx(1.0, abs=1e-9)
        assert O.measured_fwhm(xs, O.gaussian_psf(xs, sigma)) == pytest.approx(O.fwhm_from_sigma(sigma), rel=1e-5)
    assert O.sigma_from_fwhm(O.fwhm_from_sigma(1.7)) == pytest.approx(1.7)


def test_two_point_dip():
    """eq-m48-psf: two equal blurred points a distance d apart show a dip between them only if d > 2 sigma.
    Symbolically, the second derivative of the sum at the midpoint is proportional to d^2/4 - sigma^2; numerically
    the dip is zero at d <= 2 sigma, about 7% at one FWHM and about 36% at 3 sigma."""
    x, s, d = sp.symbols("x sigma d", positive=True)
    f = sp.exp(-(x - d / 2) ** 2 / (2 * s ** 2)) + sp.exp(-(x + d / 2) ** 2 / (2 * s ** 2))
    curv = sp.simplify(sp.diff(f, x, 2).subs(x, 0) * s ** 4 * sp.exp(d ** 2 / (8 * s ** 2)) / 2)
    assert sp.simplify(curv - (d ** 2 / 4 - s ** 2)) == 0
    assert sp.diff(f, x).subs(x, 0) == 0
    for sigma in (0.5, 1.0, 3.0):
        assert O.critical_separation(sigma) == pytest.approx(2 * sigma)
        assert O.dip_depth(1.98 * sigma, sigma) == 0.0
        assert O.dip_depth(2.0 * sigma, sigma) == 0.0
        assert O.dip_depth(2.1 * sigma, sigma) > 0.0
    assert O.dip_depth(float(O.fwhm_from_sigma(1.0)), 1.0) == pytest.approx(0.0728, abs=5e-4)
    assert O.dip_depth(3.0, 1.0) == pytest.approx(0.358, abs=1e-3)


def test_cnr_and_averaging():
    """eq-m48-cnr: CNR = |S_A - S_B| / sigma_n; averaging n independent samples multiplies it by sqrt(n)."""
    rng = np.random.default_rng(48)
    assert O.cnr(3.0, 1.0, 0.5) == pytest.approx(4.0)
    assert O.cnr(1.0, 3.0, 0.5) == pytest.approx(4.0)
    a = rng.normal(1.0, 1.0, (40000, 16))
    b = rng.normal(0.0, 1.0, (40000, 16))
    single = O.measured_cnr(a[:, 0], b[:, 0])
    assert single == pytest.approx(1.0, rel=0.05)
    for n in (4, 16):
        avg = O.measured_cnr(a[:, :n].mean(axis=1), b[:, :n].mean(axis=1))
        assert avg == pytest.approx(float(O.cnr_averaged(1.0, n)), rel=0.05)


def test_smoothing_noise():
    """eq-m48-smooth: a unit-area 2-D Gaussian of standard deviation sigma_s has integral of h^2 equal to
    1 / (4 pi sigma_s^2), so white noise on a grid of spacing Delta keeps sigma_n Delta / (2 sqrt(pi) sigma_s);
    blurs add in quadrature."""
    x, y, s = sp.symbols("x y sigma_s", positive=True)
    h = sp.exp(-(x ** 2 + y ** 2) / (2 * s ** 2)) / (2 * sp.pi * s ** 2)
    assert sp.simplify(sp.integrate(h ** 2, (x, -sp.oo, sp.oo), (y, -sp.oo, sp.oo)) - 1 / (4 * sp.pi * s ** 2)) == 0
    rng = np.random.default_rng(1)
    pixel = 0.25
    noise = rng.normal(0.0, 1.0, (900, 900))
    for sigma_s in (0.5, 1.0, 2.0):
        sm = ndi.gaussian_filter(noise, sigma_s / pixel)[60:-60, 60:-60]
        assert O.smoothed_noise_exact(1.0, pixel, sigma_s) == pytest.approx(O.smoothed_noise(1.0, pixel, sigma_s), rel=1e-3)
        assert sm.std() == pytest.approx(O.smoothed_noise(1.0, pixel, sigma_s), rel=0.05)
    # Two Gaussian blurs in a row are one Gaussian blur with variances added.
    xs = np.arange(-400, 401) * 0.05
    imp = np.zeros_like(xs)
    imp[400] = 1.0
    both = ndi.gaussian_filter1d(ndi.gaussian_filter1d(imp, 0.6 / 0.05), 0.8 / 0.05)
    assert O.measured_fwhm(xs, both) == pytest.approx(O.fwhm_from_sigma(1.0), rel=2e-3)


def test_wall_visibility():
    """eq-m48-visibility: a wall of contrast C and thickness w between equal backgrounds, blurred by sigma and with
    white noise sigma_n, has CNR (C / sigma_n) erf(w / (2 sqrt 2 sigma)) at its center; w_min inverts it."""
    rng = np.random.default_rng(3)
    pixel, w, fwhm, c, n = 0.05, 0.8, 1.5, 1.0, 0.25
    labels, yy = O.wall_phantom(pixel=pixel, width=w, gap=6.0, esophagus_wall=0.0)
    img = O.image(labels, {2: c}, fwhm, n, pixel, rng)
    center = img[np.argmin(np.abs(yy))]
    far = img[np.abs(yy) > 6]
    measured = (center.mean() - far.mean()) / far.std()
    sigma = float(O.sigma_from_fwhm(fwhm))
    assert measured == pytest.approx(float(O.wall_cnr(c, n, w, sigma)), rel=0.05)
    for k in (2.0, 3.0):
        wm = O.min_visible_wall(1.0, 0.2, sigma, k)
        assert float(O.wall_cnr(1.0, 0.2, wm, sigma)) == pytest.approx(k)
    assert O.min_visible_wall(1.0, 0.5, sigma, 3.0) == np.inf
    # Smoothing: a thick region gains sqrt-area CNR; the wall gains less because its contrast falls.
    s_small, s_big = O.smoothed_wall_cnr(1.0, 1.0, 1.89, sigma, 0.25, np.array([0.5, 2.0]))
    assert s_big > s_small
    assert s_big / s_small < 4.0


def test_likelihood_ratios():
    """eq-m48-lr: post-test odds = pre-test odds x LR+ gives the same PPV as eq-m35-ppv, and post-test odds with
    LR- gives 1 - NPV. With the pooled accuracy of CT for appendage thrombus (Se 96%, Sp 92%) at 8.9%
    prevalence, the formula gives a PPV of 54% (the meta-analysis reported a pooled 41%); with delayed imaging
    (Se 100%, Sp 99%) 91% (reported 92%) [Romero et al. 2013]."""
    se, spc, pi = sp.symbols("Se Sp pi", positive=True)
    odds = pi / (1 - pi) * se / (1 - spc)
    ppv = se * pi / (se * pi + (1 - spc) * (1 - pi))
    assert sp.simplify(odds / (1 + odds) - ppv) == 0
    odds_neg = pi / (1 - pi) * (1 - se) / spc
    npv = spc * (1 - pi) / (spc * (1 - pi) + (1 - se) * pi)
    assert sp.simplify(odds_neg / (1 + odds_neg) - (1 - npv)) == 0
    r = O.ROMERO2013
    lp, ln = O.likelihood_ratios(r["standard"]["se"], r["standard"]["sp"])
    assert lp == pytest.approx(12.0) and ln == pytest.approx(0.04 / 0.92)
    p, n = O.ppv_npv(r["standard"]["se"], r["standard"]["sp"], r["prevalence"])
    assert p == pytest.approx(0.540, abs=1e-3) and n == pytest.approx(0.996, abs=1e-3)
    assert float(O.post_test_probability(r["prevalence"], lp)) == pytest.approx(p)
    p_d, _ = O.ppv_npv(r["delayed imaging"]["se"], r["delayed imaging"]["sp"], r["prevalence"])
    assert p_d == pytest.approx(0.907, abs=1e-3)
    assert r["standard"]["ppv"] < p


def test_ppv_concave_in_prevalence():
    """eq-m35-ppv as a function of prevalence is concave whenever Se > 1 - Sp, so the mean of per-study PPVs from
    studies of different prevalence is below the PPV at the mean prevalence (Jensen's inequality); the illustrative
    simulated meta-analysis shows the same."""
    a, b, pi = sp.symbols("a b pi", positive=True)   # a = Se, b = 1 - Sp
    f = a * pi / (a * pi + b * (1 - pi))
    second = sp.simplify(sp.diff(f, pi, 2))
    assert sp.simplify(second - (-2 * a * b * (a - b) / (b + (a - b) * pi) ** 3)) == 0
    rng = np.random.default_rng(13)
    prev = rng.uniform(0.02, 0.25, 19)
    ppvs, mean, formula = O.simulate_pooled_ppv(0.96, 0.92, prev, 150, rng)
    exact_mean = np.mean([O.ppv_npv(0.96, 0.92, q)[0] for q in prev])
    assert exact_mean < formula
    assert mean == pytest.approx(exact_mean, abs=0.06)


def test_phantom_four_ways():
    """Lab part F: with the cited resolutions, the mean 1.89-mm atrial wall [Beinart et al. 2011] stays separate
    from an illustrative esophageal wall 2 mm away at CT and MRI resolutions but merges with it at PET
    resolution (4-7 mm FWHM); a 0.5-mm wall rises above the blood only at the finest resolutions."""
    rng = np.random.default_rng(48)
    vals = {0: 0.0, 1: 0.4, 2: 1.0, 3: 1.0}
    labels, y = O.wall_phantom(width=O.LA_WALL_MM["mean"], gap=2.0)
    for name, fwhm in O.RESOLUTION_MM.items():
        prof = O.depth_profile(O.image(labels, vals, fwhm, 0.0, 0.05, rng))
        assert O.separated(prof, y, O.LA_WALL_MM["mean"], 2.0) == (fwhm <= 2.0), name
    labels, y = O.wall_phantom(width=O.LA_WALL_MM["min"], gap=2.0)
    above = {f: O.wall_above_blood(O.depth_profile(O.image(labels, vals, f, 0.0, 0.05, rng)), y, 0.5, 0.4)
             for f in O.RESOLUTION_MM.values()}
    assert above[0.34] > 0.5 and above[2.0] < 0.05
    assert O.RESOLUTION_MM["PET, clinical (best case)"] == 4.0 and O.LA_WALL_MM["min"] == 0.5
