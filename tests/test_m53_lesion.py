"""m53 · Imaging ablation lesions and real-time MRI-guided EP: equation tests."""

import numpy as np
import pytest
import sympy as sp
from scipy.ndimage import gaussian_filter

from epml import lesion as L


def test_gap_in_a_blurred_band():
    """eq-m53-gap: a band with a gap, blurred by a Gaussian, equals B(y)(1 - G(x)); it matches a numerical blur;
    the gap center is peak (1 - erf(g/(2 sqrt 2 sigma))); the smallest visible gap solves gap_center = threshold."""
    pixel, sigma, w, g = 0.05, L.fwhm_to_sigma(1.5), 3.0, 1.2
    x = np.arange(-12, 12 + pixel / 2, pixel)
    X, Y = np.meshgrid(x, x)
    img = ((np.abs(Y) <= w / 2) & ~(np.abs(X) <= g / 2)).astype(float)
    num = gaussian_filter(img, sigma / pixel, mode="constant", truncate=6.0)
    ana = L.band_gap_image(X, Y, w, g, sigma)
    inner = (np.abs(X) < 6) & (np.abs(Y) < 6)
    assert np.abs(num - ana)[inner].max() < 0.02
    assert L.band_gap_image(0.0, 0.0, w, g, sigma) == pytest.approx(L.gap_center(w, g, sigma))
    assert L.band_gap_image(50.0, 0.0, w, g, sigma) == pytest.approx(L.band_peak(w, sigma))
    gmin = L.min_visible_gap(w, sigma, 0.5)
    assert L.gap_center(w, gmin, sigma) == pytest.approx(0.5, abs=1e-9)
    assert L.gap_center(w, 1.1 * gmin, sigma) < 0.5 < L.gap_center(w, 0.9 * gmin, sigma)
    assert L.min_visible_gap(0.5, L.fwhm_to_sigma(3.0)) == float("inf")      # band itself below threshold
    gs, ss, th, P = sp.symbols("g sigma theta P", positive=True)
    expr = P * (1 - sp.erf(gs / (2 * sp.sqrt(2) * ss)))
    sol = 2 * sp.sqrt(2) * ss * sp.erfinv(1 - th / P)
    assert sp.simplify(expr.subs(gs, sol) - th) == 0
    assert L.apparent_gap(3.0, 1.0) == 1.0 and L.apparent_gap(1.5, 1.0) == 0.0


def test_ring_lesion_gap_detection():
    """On a ring lesion, gaps wider than the minimum visible gap are found where they are, narrower ones are
    missed, and the first is the one predicted by eq-m53-gap."""
    gaps = [(30.0, 0.6), (120.0, 2.5), (250.0, 5.0)]
    img, x = L.ring_lesion(gaps)
    for fwhm in (1.0, 2.0, 3.0):
        b = L.blur(img, x[1] - x[0], fwhm)
        found = L.detect_gaps(*L.ring_profile(b, x))
        hit = L.matched(gaps, found)
        gmin = L.min_visible_gap(4.0, L.fwhm_to_sigma(fwhm))
        for (c, arc), h in zip(gaps, hit):
            if arc > 1.25 * gmin:
                assert h
            if arc < 0.8 * gmin:
                assert not h
    a = np.arange(8) * 45.0
    assert L.detect_gaps(a, np.ones(8)) == []
    runs = L.detect_gaps(a, np.array([0, 1, 1, 1, 1, 1, 1, 0.0]))      # one run wrapping through 0
    assert len(runs) == 1 and runs[0][1] == pytest.approx(90.0)


def test_kappa_between_image_and_reconnection():
    """Cohen's kappa (m35) is 1 for identical labels and about 0 for independent ones."""
    rng = np.random.default_rng(0)
    a = rng.random(5000) < 0.4
    assert L.kappa(a, a) == pytest.approx(1.0)
    assert abs(L.kappa(a, rng.random(5000) < 0.4)) < 0.05
    w, rec = L.simulate_veins(np.random.default_rng(53))
    det = L.image_detects(w, 4.0, 2.0)
    assert -1 <= L.kappa(det, rec) <= 1
    assert det.sum() <= (w > 0).sum()


def test_frame_time():
    """eq-m53-frame: T = N TR / R; 64 lines at 3 ms give 192 ms, about 5 frames/s, inside the 4-8 frames/s reported
    for passive visualization; halving lines or doubling acceleration doubles the rate."""
    N, TR, R = sp.symbols("N TR R", positive=True)
    T = N * TR / R
    assert sp.simplify(T.subs(N, N / 2) - T / 2) == 0
    assert L.frame_time_ms(64, 3.0) == pytest.approx(192.0)
    assert L.FPS_PASSIVE[0] < L.fps(64, 3.0) < L.FPS_PASSIVE[1]
    assert L.fps(128, 3.0, 2.0) == pytest.approx(L.fps(64, 3.0))
    assert 1e3 / L.FPS_ACTIVE == pytest.approx(20.0)
    assert L.motion_per_frame_mm(46.6, 192.0) == pytest.approx(8.947, abs=1e-3)


def test_egm_filter_chain():
    """The filter chain removes most of the illustrative scanner interference; a 120 Hz low-pass leaves less noise
    and a smaller electrogram than 300 Hz, as reported."""
    t, s, on = L.synthetic_egm()
    art = L.gradient_artifact(t)
    res = {}
    for lp in (300.0, 120.0):
        y = L.filter_chain(s + art, 2000.0, low_pass=lp)
        clean = L.filter_chain(s, 2000.0, low_pass=lp)
        res[lp] = (np.sqrt(np.mean((y - clean) ** 2)), L.peak_to_peak_at(clean, t, on))
    raw_rms = np.sqrt(np.mean(art**2))
    assert res[300.0][0] < 0.3 * raw_rms
    assert res[120.0][0] < res[300.0][0]
    assert res[120.0][1] < res[300.0][1]
