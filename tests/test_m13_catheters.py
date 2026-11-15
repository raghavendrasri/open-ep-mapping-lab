"""m13 equation tests: spreading resistance, bipole direction, spatial aliasing, basket geometry, contact force."""

import numpy as np
import pytest
import sympy as sp

from epml import catheters as K


def test_spreading():
    """eq-m13-spreading: disk 1/(4 sigma a), hemisphere 1/(2 pi sigma a)."""
    # The density 1/sqrt(a^2 - r^2) makes the disk an equipotential (pi^2 at every radius, numerically).
    for r in (0.0, 0.3, 0.7, 0.95):
        assert K.disk_density_potential(r, 1.0) == pytest.approx(np.pi ** 2, rel=1e-8)
    # On the axis the same density gives 2 pi atan(a/z), which tends to pi^2 at the disk (SymPy).
    from scipy import integrate
    for zv in (0.1, 0.5, 2.0):
        val, _ = integrate.quad(lambda q: 2 * np.pi * q / np.sqrt((1 + q) * (q * q + zv * zv)), 0, 1,
                                weight="alg", wvar=(0.0, -0.5))
        assert val == pytest.approx(2 * np.pi * np.arctan(1 / zv), rel=1e-9)
    a, z = sp.symbols("a z", positive=True)
    assert sp.limit(2 * sp.pi * sp.atan(a / z), z, 0, "+") == sp.pi ** 2
    # Resistance from that density and the half-space Green's function equals Newman's 1/(4 sigma a).
    for a_mm in (0.5, 1.0, 2.0):
        assert K.disk_resistance_numeric(a_mm, sigma=1.0) == pytest.approx(K.disk_resistance(a_mm), rel=1e-8)
    # Hemisphere: phi = I/(2 pi sigma r) is harmonic and carries current I through every hemisphere.
    x, y, zz, I, sig = sp.symbols("x y z I sigma", positive=True)
    r = sp.sqrt(x ** 2 + y ** 2 + zz ** 2)
    phi = I / (2 * sp.pi * sig * r)
    assert sp.simplify(sum(sp.diff(phi, v, 2) for v in (x, y, zz))) == 0
    R = sp.symbols("R", positive=True)
    flux = -sig * sp.diff(I / (2 * sp.pi * sig * R), R) * 2 * sp.pi * R ** 2
    assert sp.simplify(flux - I) == 0
    assert K.disk_resistance(1.0) / K.hemisphere_resistance(1.0) == pytest.approx(np.pi / 2)
    # Halving the radius doubles every one of them.
    for f in (K.disk_resistance, K.hemisphere_resistance, K.sphere_resistance):
        assert f(0.5) == pytest.approx(2 * f(1.0))


def test_orthogonal():
    """eq-m13-orthogonal: |cos| for one bipole, at least 1/sqrt(2) for the better of two, 1 for their RSS."""
    th = np.linspace(0, 2 * np.pi, 3601)
    best, rss = K.orthogonal_pair(th)
    assert np.min(best) == pytest.approx(1 / np.sqrt(2), abs=1e-6)
    assert th[np.argmin(best[:900])] == pytest.approx(np.pi / 4, abs=1e-3)
    assert np.allclose(rss, 1.0)
    assert K.bipole_amplitude(np.pi / 2) == pytest.approx(0.0, abs=1e-15)


def test_alias():
    """eq-m13-alias: the energy above Nyquist is exp(-2 pi h / spacing)."""
    k, h, D = sp.symbols("k h Delta", positive=True)
    frac = sp.integrate(sp.exp(-2 * k * h), (k, sp.pi / D, sp.oo)) / sp.integrate(sp.exp(-2 * k * h), (k, 0, sp.oo))
    assert sp.simplify(frac - sp.exp(-2 * sp.pi * h / D)) == 0
    # The Poisson kernel's transform is exp(-|k| h) (SymPy, cosine transform).
    x = sp.symbols("x", real=True)
    ft = sp.integrate(2 * (h / sp.pi) / (x ** 2 + h ** 2) * sp.cos(k * x), (x, 0, sp.oo))
    assert sp.simplify(ft - sp.exp(-k * h)) == 0
    for spacing, height in ((1.0, 1.0), (2.0, 1.0), (4.0, 1.0), (1.5, 0.5)):
        assert K.alias_fraction_fft(spacing, height) == pytest.approx(K.alias_fraction(spacing, height), rel=0.01)
    assert K.alias_fraction(K.max_spacing(1.0, 0.01), 1.0) == pytest.approx(0.01)
    assert K.alias_wavenumber(2 * np.pi / 1.0 * 0.8, 1.0) == pytest.approx(2 * np.pi * 0.2)


def test_basket():
    """eq-m13-basket: interspline arc 2 pi R sin(theta) / n; bunching enlarges the gaps."""
    R, n = 25.0, 8
    E = K.basket(n, 8, R).reshape(n, 8, 3)
    for i in range(8):
        a, b = E[0, i], E[1, i]
        rho = np.hypot(a[0], a[1])                      # radius of the latitude circle
        arc_on_circle = rho * np.arccos(np.dot(a[:2], b[:2]) / rho ** 2)
        theta = np.arccos(a[2] / R)
        assert arc_on_circle == pytest.approx(K.interspline_arc(theta, n, R), rel=1e-9)
    band = (25.0, 155.0)                                # the polar band the electrodes span
    even = K.fill_distance(K.basket(8, 8, R), R, polar_range_deg=band)
    more = K.fill_distance(K.basket(12, 8, R), R, polar_range_deg=band)
    bunched = K.fill_distance(K.basket(8, 8, R, azimuths_deg=np.linspace(0, 180, 8)), R, polar_range_deg=band)
    assert more < 0.8 * even and 3 * even < bunched


def test_force():
    """eq-m13-force and eq-m13-force-noise: least squares and its covariance."""
    a, b = sp.symbols("a b", positive=True)
    rows = [[b * sp.cos(p), b * sp.sin(p), a] for p in (0, 2 * sp.pi / 3, 4 * sp.pi / 3)]
    C = sp.Matrix(rows)
    assert sp.simplify(C.T * C - sp.diag(3 * b ** 2 / 2, 3 * b ** 2 / 2, 3 * a ** 2)) == sp.zeros(3)
    Cn = K.force_matrix([0, 120, 240], axial=2.0, lateral=0.5)
    F = np.array([3.0, -1.0, 20.0])
    assert K.estimate_force(Cn, Cn @ F) == pytest.approx(F)
    sd = np.sqrt(np.diag(K.force_covariance(Cn, 0.1)))
    assert sd == pytest.approx([0.1 * np.sqrt(2 / 3) / 0.5] * 2 + [0.1 / (np.sqrt(3) * 2.0)])
    est = K.force_trials(Cn, F, 0.1, 40000, np.random.default_rng(1))
    assert est.std(axis=0) == pytest.approx(sd, rel=0.03)
    # Sensors on one line cannot resolve the perpendicular force.
    assert np.linalg.matrix_rank(K.force_matrix([0, 180, 180])) < 3
    # The symmetric layout has the smallest condition number among 0, +beta, -beta layouts.
    conds = {g: np.linalg.cond(K.force_matrix([0, g, -g])) for g in range(30, 176)}
    assert min(conds, key=conds.get) == 120
