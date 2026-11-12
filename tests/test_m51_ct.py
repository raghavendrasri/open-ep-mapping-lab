"""m51 · Cardiac CT for EP: equation tests (numeric, and symbolic with SymPy where feasible)."""

import numpy as np
import pytest
import sympy as sp
from scipy.special import erf

from epml import ct
from epml.fluoro import MATERIALS


def test_hounsfield_units():
    """eq-m51-hu: water is 0 and air -1000 by construction; tissues from the NIST 60 keV table."""
    mu, mw = sp.symbols("mu mu_w", positive=True)
    hu = 1000 * (mu - mw) / (mw - 0)
    assert sp.simplify(hu.subs(mu, mw)) == 0
    assert sp.simplify(hu.subs(mu, 0)) == -1000
    h = sp.symbols("h", real=True)
    assert sp.simplify(hu.subs(mu, mw * (1 + h / 1000)) - h) == 0          # mu_from_hu is the inverse
    assert ct.hounsfield(ct.mu_per_mm("water")) == pytest.approx(0.0)
    assert ct.hounsfield(ct.mu_per_mm("air")) == pytest.approx(-1000.0)
    for name, (mass, rho) in MATERIALS.items():
        expected = 1000 * (mass * rho - ct.WATER_MASS_ATT) / ct.WATER_MASS_ATT
        assert ct.hounsfield(ct.mu_per_mm(name)) == pytest.approx(expected)
    assert ct.hounsfield(ct.mu_per_mm("soft tissue")) == pytest.approx(54.3, abs=0.1)
    assert ct.hounsfield(ct.mu_per_mm("adipose")) == pytest.approx(-89.2, abs=0.1)
    assert ct.mu_from_hu(ct.hounsfield(0.0137)) == pytest.approx(0.0137)


def test_iodine_mixture_rule():
    """eq-m51-iodine: c mg/mL of iodine adds 1000 c 1e-3 (mu/rho)_I / mu_w Hounsfield units, linearly."""
    per = ct.iodine_hu_per_mg_ml()
    assert per == pytest.approx(ct.IODINE_MASS_ATT / ct.WATER_MASS_ATT, rel=1e-12)
    assert per == pytest.approx(36.81, abs=0.01)
    base = ct.hounsfield(ct.mu_per_mm("blood"))
    for c in (0.0, 2.5, 10.0):
        assert ct.hounsfield(ct.blood_with_iodine_mu(c)) - base == pytest.approx(c * per)


def test_radon_transform_of_ellipses():
    """eq-m51-radon: the analytic chord formula matches line sums through a rasterized image, a disk gives
    2 sqrt(R^2 - s^2), and every projection carries the same total (the image integral)."""
    ph = ct.thorax_phantom()
    img, x = ct.raster(ph, n=256, oversample=3)
    s = ct.detector_axis(320.0, 256)
    th = ct.angles(12)
    analytic = ct.radon_ellipses(ph, th, s[::4])
    discrete = ct.radon_image(img, x, th, s[::4])
    assert np.linalg.norm(discrete - analytic) / np.linalg.norm(analytic) < 0.02
    total = sum(v * np.pi * a * b for _, _, a, b, _, v in ph)
    sino = ct.radon_ellipses(ph, ct.angles(30), s)
    assert np.allclose(sino.sum(axis=1) * (s[1] - s[0]), total, rtol=2e-3)
    disk = [(3.0, -4.0, 20.0, 20.0, 0.0, 1.0)]
    ss = np.linspace(-30, 30, 121)
    for t in (0.0, 0.7, 2.0):
        s0 = 3.0 * np.cos(t) - 4.0 * np.sin(t)
        assert np.allclose(ct.radon_ellipses(disk, [t], ss)[0], 2 * np.sqrt(np.clip(400 - (ss - s0) ** 2, 0, None)))


def test_central_slice_theorem():
    """eq-m51-slice: the 1-D Fourier transform of a projection is the 2-D transform of the image along the radial
    line at the same angle. Checked for a disk in closed form and for a rotated, off-center ellipse numerically."""
    R = 10.0
    s = np.linspace(-R, R, 40001)
    p = 2 * np.sqrt(np.clip(R**2 - s**2, 0, None))
    for k in (0.0, 0.03, 0.08, 0.15):
        ft = np.trapezoid(p * np.exp(-2j * np.pi * k * s), s)
        assert ft.real == pytest.approx(float(ct.disk_projection_ft(k, R)), abs=1e-3 * np.pi * R**2)
    ell = [(6.0, -3.0, 12.0, 6.0, 25.0, 1.0)]
    img, x = ct.raster(ell, n=400, fov=40.0, oversample=2)
    X, Y = np.meshgrid(x, x)
    dA = (x[1] - x[0]) ** 2
    ss = np.linspace(-25, 25, 5001)
    for th in (0.3, 1.2, 2.5):
        proj = ct.radon_ellipses(ell, [th], ss)[0]
        for k in (0.02, 0.05, 0.1):
            P = np.trapezoid(proj * np.exp(-2j * np.pi * k * ss), ss)
            F = np.sum(img * np.exp(-2j * np.pi * k * (X * np.cos(th) + Y * np.sin(th)))) * dA
            assert abs(P - F) < 0.01 * np.pi * 12 * 6


def test_ramlak_kernel_symbolic():
    """eq-m51-ramlak: the band-limited ramp integral 2 int_0^W k cos(2 pi k n d) dk with W = 1/(2d) equals
    1/(4 d^2) at n = 0, -1/(pi^2 n^2 d^2) for odd n and 0 for even n."""
    k, d = sp.symbols("k d", positive=True)
    W = 1 / (2 * d)
    h = ct.ramlak_kernel(6, 1.0)
    for n in range(0, 7):
        val = sp.simplify(2 * sp.integrate(k * sp.cos(2 * sp.pi * k * n * d), (k, 0, W)))
        if n == 0:
            expected = 1 / (4 * d**2)
        elif n % 2:
            expected = -1 / (sp.pi**2 * n**2 * d**2)
        else:
            expected = sp.Integer(0)
        assert sp.simplify(val - expected) == 0
        assert h[6 + n] == pytest.approx(float(expected.subs(d, 1)))
        assert h[6 - n] == pytest.approx(h[6 + n])


def test_filtered_back_projection():
    """eq-m51-fbp: filtered back-projection recovers a disk's value and the phantom's Hounsfield units; plain
    back-projection does not."""
    disk = [(0.0, 0.0, 40.0, 40.0, 0.0, 0.02)]
    x = (np.arange(128) - 63.5) * 1.0
    s = np.arange(-91, 92) * 1.0
    th = ct.angles(360)
    sino = ct.radon_ellipses(disk, th, s)
    rec = ct.fbp(sino, th, s, x)
    X, Y = np.meshgrid(x, x)
    inner = np.hypot(X, Y) < 30
    assert np.mean(rec[inner]) == pytest.approx(0.02, rel=0.01)
    assert np.abs(rec[np.hypot(X, Y) > 50]).max() < 0.002
    plain = ct.fbp(sino, th, s, x, filtered=False)
    outside = np.hypot(X, Y) > 50
    assert np.mean(plain[outside]) > 0.2 * np.mean(plain[inner])               # plain back-projection leaks out
    ph = ct.thorax_phantom()
    img, x = ct.raster(ph, n=256, oversample=3)
    s = ct.detector_axis(320.0, 256)
    th = ct.angles(180)
    rec = ct.fbp(ct.radon_ellipses(ph, th, s), th, s, x)
    body = img > 0.5 * ct.mu_per_mm("soft tissue")
    err = ct.hounsfield(rec) - ct.hounsfield(img)
    assert np.median(np.abs(err[body])) < 25
    err_few = ct.hounsfield(ct.fbp(ct.radon_ellipses(ph, ct.angles(30), s), ct.angles(30), s, x)) - ct.hounsfield(img)
    assert np.median(np.abs(err_few[body])) > 3 * np.median(np.abs(err[body]))     # streaks with few angles


def test_quantum_noise():
    """eq-m51-noise: Var(-ln(N/N0)) is about exp(p)/N0, so image noise falls as one over the square root of the
    photon count (dose)."""
    rng = np.random.default_rng(51)
    N0 = 1e5
    for p in (1.0, 3.0, 5.0):
        sim = ct.noisy_sinogram(np.full((1, 200000), p), N0, rng)[0]
        assert np.var(sim) == pytest.approx(float(ct.line_integral_variance(p, N0)), rel=0.03)
    disk = [(0.0, 0.0, 40.0, 40.0, 0.0, 0.02)]
    x = (np.arange(96) - 47.5) * 1.0
    s = np.arange(-69, 70) * 1.0
    th = ct.angles(120)
    clean = ct.radon_ellipses(disk, th, s)
    X, Y = np.meshgrid(x, x)
    inner = np.hypot(X, Y) < 25
    sd = []
    for n0 in (1e4, 4e4, 1.6e5):
        sd.append(np.std(ct.fbp(ct.noisy_sinogram(clean, n0, rng), th, s, x)[inner]))
    assert sd[1] / sd[0] == pytest.approx(0.5, rel=0.1)
    assert sd[2] / sd[1] == pytest.approx(0.5, rel=0.1)


def test_gating_window_and_blur():
    """eq-m51-gating: the window is about the rotation time over 2 (one source) or 4 (two sources), against the
    published values; blur is speed times window."""
    for rot, src, reported in ct.GATING_REPORTED:
        assert ct.temporal_window(rot, src) == pytest.approx(reported, rel=0.06)
    assert ct.temporal_window(0.25, 1) == pytest.approx(0.125)
    assert ct.motion_blur_mm(ct.CORONARY_SPEED["all three arteries"], 0.125) == pytest.approx(5.825)
    assert ct.motion_blur_mm(46.6, ct.temporal_window(0.25, 2)) < ct.motion_blur_mm(27.9, ct.temporal_window(0.25, 1))


def test_smeared_disk():
    """eq-m51-smear: the closed form equals the time average of a moving disk; it keeps the disk's area; on the
    center line its peak is min(1, D / b)."""
    D, b = 3.0, 2.5
    xs = np.linspace(-4, 4, 161)
    ys = np.linspace(-2, 2, 81)
    X, Y = np.meshgrid(xs, ys)
    times = np.linspace(-b / 2, b / 2, 2001)
    avg = np.mean([(np.hypot(X - t, Y) <= D / 2) for t in times], axis=0)
    assert np.abs(ct.smeared_disk(X, Y, D, b) - avg).max() < 0.01
    fine = np.linspace(-6, 6, 1201)
    Xf, Yf = np.meshgrid(fine, fine)
    area = ct.smeared_disk(Xf, Yf, D, b).sum() * (fine[1] - fine[0]) ** 2
    assert area == pytest.approx(np.pi * (D / 2) ** 2, rel=0.01)
    for blur in (0.0, 1.0, 3.0, 6.0, 12.0):
        assert ct.smeared_disk(0.0, 0.0, D, blur) == pytest.approx(min(1.0, D / blur) if blur else 1.0)


def test_thin_wall_profile():
    """eq-m51-wall: the erf profile is a box convolved with a Gaussian; its area is the wall thickness; its peak is
    erf(w / (2 sqrt 2 sigma)); a fixed threshold loses thin walls; the FWHM never drops below the blur's FWHM; a
    blurred step with no wall still spans a wall window over a width set by sigma."""
    xx, w, sg = sp.symbols("x w sigma", positive=True)
    prof = sp.Rational(1, 2) * (sp.erf((xx + w / 2) / (sp.sqrt(2) * sg)) - sp.erf((xx - w / 2) / (sp.sqrt(2) * sg)))
    assert sp.simplify(sp.diff(prof, xx).subs(xx, 0)) == 0
    assert sp.simplify(prof.subs(xx, 0) - sp.erf(w / (2 * sp.sqrt(2) * sg))) == 0
    sigma = ct.fwhm_to_sigma(1.0)
    x = np.linspace(-8, 8, 16001)
    dx = x[1] - x[0]
    for width in (0.3, 1.0, 2.5):
        box = (np.abs(x) <= width / 2).astype(float)
        g = np.exp(-x**2 / (2 * sigma**2)) / (np.sqrt(2 * np.pi) * sigma)
        conv = np.convolve(box, g, mode="same") * dx
        assert np.abs(conv - ct.slab_profile(x, width, sigma)).max() < 2e-3
        assert np.trapezoid(ct.slab_profile(x, width, sigma), x) == pytest.approx(width, rel=1e-6)
        assert ct.slab_profile(0.0, width, sigma) == pytest.approx(ct.slab_peak(width, sigma))
    assert ct.threshold_thickness(0.5, sigma) == 0.0                     # peak below half the contrast
    assert ct.threshold_thickness(4.0, sigma) == pytest.approx(4.0, abs=1e-3)
    assert ct.fwhm_thickness(0.01, sigma) == pytest.approx(1.0, rel=1e-3)
    assert ct.fwhm_thickness(0.5, sigma) > 1.0
    assert ct.fwhm_to_sigma(2 * np.sqrt(2 * np.log(2))) == pytest.approx(1.0)
    # a blurred blood-to-fat step with no wall still crosses a wall window over a finite width
    sg2 = ct.fwhm_to_sigma(2.0)
    step = 400.0 + (-89.0 - 400.0) * 0.5 * (1 + erf(x / (np.sqrt(2) * sg2)))
    inside = (step > 0.0) & (step < 200.0)
    assert ct.step_window_width(sg2, 0.0, 200.0, 400.0, -89.0) == pytest.approx(inside.sum() * dx, abs=2 * dx)


def test_atrium_wall_thickness_and_esophagus():
    """The 3-D phantom: wall thickness along rays matches what was built (within 1.5 voxels), the esophagus sits at
    the built distance, a threshold window between the blood and fat midpoints measures blurred walls of 1 mm and
    more to within 0.3 mm, and coarser voxels overestimate the thinnest walls."""
    rng = np.random.default_rng(5)
    vol, x, m = ct.atrium_volume(voxel=0.5, wall=(0.5, 3.5))
    dirs = ct.sphere_directions(200, rng)
    truth = ct.true_ray_thickness(dirs, wall=(0.5, 3.5))
    exact = ct.ray_thickness(m["wall"], x, dirs)
    assert np.abs(exact - truth).max() <= 0.75 and np.mean(np.abs(exact - truth)) < 0.25
    assert ct.min_distance_mm(m["outer"], m["esophagus"], x) == pytest.approx(3.0, abs=0.5)
    wall_hu = float(ct.hounsfield(ct.mu_per_mm("soft tissue")))
    fat_hu = float(ct.hounsfield(ct.mu_per_mm("adipose")))
    lo, hi = (wall_hu + fat_hu) / 2, (wall_hu + 400.0) / 2
    blurred = ct.blur_volume(vol, 0.5, 1.0)
    meas = ct.ray_thickness((blurred > lo) & (blurred < hi), x, dirs)
    ok = truth >= 1.0
    assert np.abs(np.mean(meas[ok] - truth[ok])) < 0.3
    coarse, xc = ct.downsample(vol, x, 4)
    thin = truth < 1.0
    meas_c = ct.ray_thickness((coarse > lo) & (coarse < hi), xc, dirs)
    assert np.mean(meas_c[thin] - truth[thin]) > 0.3
