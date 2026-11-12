"""Equation tests for m49 (fluoroscopy and radiation protection)."""
import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "labs" / "python"))
from epml import fluoro as fl  # noqa: E402


def test_beer_lambert_and_half_value_layer():
    """eq-m49-beer: dI/dx = -mu I gives I = I0 exp(-mu x); the half-value layer is ln 2 / mu."""
    x, mu, I0 = sp.symbols("x mu I_0", positive=True)
    intensity = I0 * sp.exp(-mu * x)
    assert sp.simplify(sp.diff(intensity, x) + mu * intensity) == 0
    assert sp.simplify(intensity.subs(x, sp.log(2) / mu) - I0 / 2) == 0
    for material in fl.MATERIALS:
        m = fl.mu_per_mm(material)
        assert fl.transmission(m, fl.half_value_layer(m)) == pytest.approx(0.5)
    # NIST SRD 126 values at 60 keV: soft tissue 0.2048 cm^2/g at 1.06 g/cm^3
    assert fl.mu_per_mm("soft tissue") == pytest.approx(0.2048 * 1.06 / 10)
    assert fl.half_value_layer(fl.mu_per_mm("cortical bone")) < fl.half_value_layer(fl.mu_per_mm("soft tissue"))


def test_exact_line_integrals_match_ray_marching():
    """eq-m49-beer along a ray: the analytic chord sum equals a numerical march through the phantom."""
    phantom = fl.chest_phantom()
    rng = np.random.default_rng(0)
    x = np.r_[20.0, 0.0, -100.0, rng.uniform(-150, 150, 20)]
    z = np.r_[-10.0, 0.0, 0.0, rng.uniform(-150, 150, 20)]
    exact = fl.line_integral(phantom, x, z)
    marched = fl.line_integral_voxels(phantom, x, z, step=0.02)
    assert np.allclose(exact, marched, atol=0.02)
    # the body alone, through its centre: 2 * 110 mm of soft tissue
    assert fl.line_integral([phantom[0]], 0.0, 0.0) == pytest.approx(220 * fl.mu_per_mm("soft tissue"))


def test_subject_contrast():
    """eq-m49-contrast: C = 1 - exp(-dmu t); for small dmu t, C is close to dmu t."""
    dmu, t = sp.symbols("dmu t", positive=True)
    C = 1 - sp.exp(-dmu * t)
    assert sp.series(C, dmu, 0, 2).removeO() == dmu * t
    blood, tissue, pt = fl.mu_per_mm("blood"), fl.mu_per_mm("soft tissue"), fl.mu_per_mm("platinum")
    heart = fl.subject_contrast(blood, tissue, 90.0)
    assert 0 < heart < 0.01                                  # blood against soft tissue: under 1%
    assert fl.subject_contrast(pt, blood, 2.4) > 0.999       # a platinum electrode: nearly opaque
    assert fl.subject_contrast(tissue, blood, 10.0) < 0      # less attenuating object: negative contrast


def test_quantum_noise_cnr():
    """eq-m49-cnr: with Poisson counts, CNR = C sqrt(N); doubling the dose raises CNR by sqrt 2."""
    rng = np.random.default_rng(1)
    for N, C in [(400.0, 0.2), (10_000.0, 0.05)]:
        bg = rng.poisson(N, 200_000)
        obj = rng.poisson(N * (1 - C), 200_000)
        measured = (bg.mean() - obj.mean()) / bg.std()
        assert measured == pytest.approx(fl.cnr(C, N), rel=0.02)
    assert fl.cnr(0.1, 2 * 900) / fl.cnr(0.1, 900) == pytest.approx(np.sqrt(2))
    assert fl.photons_for_cnr(0.1, 3) == pytest.approx(900)


def test_kerma_area_product_is_independent_of_distance():
    """eq-m49-kap: K falls as 1/d^2 and A grows as d^2, so K * A is constant along the beam."""
    d, d0, K0, A0 = sp.symbols("d d_0 K_0 A_0", positive=True)
    assert sp.simplify(K0 * (d0 / d) ** 2 * A0 * (d / d0) ** 2 - K0 * A0) == 0
    ds = np.array([0.5, 0.7, 1.0, 1.2])
    kap = fl.kerma_area_product(fl.kerma_at(2.0, 0.7, ds), fl.field_area_at(100.0, 0.7, ds))
    assert np.allclose(kap, 200.0)


def test_staff_dose_scaling():
    """eq-m49-staff: twice the distance quarters the dose; one half-value layer halves it; dose scales with
    pulse rate, time and dose per pulse."""
    ref = fl.relative_staff_dose(1.0, 10.0)
    assert ref == pytest.approx(1.0)
    assert fl.relative_staff_dose(2.0, 10.0) == pytest.approx(0.25)
    assert fl.relative_staff_dose(1.0, 10.0, shield_hvl=1.0) == pytest.approx(0.5)
    assert fl.relative_staff_dose(1.0, 10.0, pulse_rate=7.5) == pytest.approx(0.5)
    assert fl.relative_staff_dose(1.0, 20.0, dose_per_pulse=0.5) == pytest.approx(1.0)
    assert fl.shield_transmission(3.0) == pytest.approx(0.125)


def test_reference_levels_and_motion_sampling():
    values = [np.array([1.0, 2.0, 3.0, 4.0]), np.array([10.0, 10.0, 10.0]), np.array([5.0])]
    assert fl.facility_median_reference_level(values) == pytest.approx(np.percentile([2.5, 10.0, 5.0], 75))
    assert fl.pooled_reference_level(np.concatenate(values)) == pytest.approx(np.percentile(np.concatenate(values), 75))
    # a lower pulse rate leaves the catheter further from where the last frame showed it
    errs = [fl.sampled_position_error(5.0, 1.2, p) for p in (30.0, 15.0, 7.5)]
    assert errs[0] < errs[1] < errs[2] <= 10.0
