"""m01 · Bioelectric sources: equation tests (numeric, and symbolic with SymPy where feasible)."""

import numpy as np
import pytest
import sympy as sp

from epml import sources as S


def test_point_source():
    """eq-m01-point: phi = I / (4 pi sigma r) satisfies Laplace's equation away from the source, and the current
    leaving any sphere around it is I."""
    x, y, z, I, sig = sp.symbols("x y z I sigma", positive=True)
    r = sp.sqrt(x ** 2 + y ** 2 + z ** 2)
    phi = I / (4 * sp.pi * sig * r)
    assert sp.simplify(sp.diff(phi, x, 2) + sp.diff(phi, y, 2) + sp.diff(phi, z, 2)) == 0
    rr = sp.symbols("r", positive=True)
    e_r = -sp.diff(I / (4 * sp.pi * sig * rr), rr)
    assert sp.simplify(sig * e_r * 4 * sp.pi * rr ** 2 - I) == 0
    assert S.flux_through_sphere(2.0, 0.5, 3.0) == pytest.approx(2.0, rel=1e-4)
    assert float(S.point_potential(1.0, 1.0, (0, 0, 2.0))) == pytest.approx(1 / (8 * np.pi))


def test_dipole_limit_and_falloff():
    """eq-m01-dipole: a source-sink pair +-I a distance d apart tends to the dipole p = I d as d -> 0 with I d fixed;
    near one pole the potential falls as 1/r, far away as 1/r^2."""
    x, z, d, p, sig = sp.symbols("x z d p sigma", positive=True)
    I = p / d
    pair = I / (4 * sp.pi * sig) * (1 / sp.sqrt(x ** 2 + (z - d / 2) ** 2) - 1 / sp.sqrt(x ** 2 + (z + d / 2) ** 2))
    dip = p * z / (4 * sp.pi * sig * (x ** 2 + z ** 2) ** sp.Rational(3, 2))
    assert sp.simplify(sp.limit(pair, d, 0) - dip) == 0
    obs = np.array([[0.3, 0.2, 5.0], [1.0, -2.0, 0.5], [4.0, 1.0, -3.0]])
    for sep in (0.1, 0.01):
        approx = S.pair_potential(1.0 / sep, sep, 1.0, obs)
        exact = S.dipole_potential((0, 0, 1.0), 1.0, obs)
        assert np.max(np.abs(approx / exact - 1)) < 30 * sep ** 2
    rho = np.logspace(-3, 3, 121)
    obs = np.stack([np.zeros_like(rho), np.zeros_like(rho), 0.5 + rho], -1)
    e = S.falloff_exponent(rho, S.pair_potential(1.0, 1.0, 1.0, obs))
    assert e[0] == pytest.approx(-1.0, abs=0.01) and e[-1] == pytest.approx(-2.0, abs=0.01)


def test_double_layer_solid_angle():
    """eq-m01-double-layer: a uniform double layer of strength tau gives tau Omega / (4 pi sigma). On the axis of a
    disk, Omega = 2 pi (1 - z / sqrt(z^2 + R^2)); the potential jumps by tau / sigma across the layer; a closed
    double layer gives zero outside."""
    z, R, rho = sp.symbols("z R rho", positive=True)
    omega = sp.integrate(2 * sp.pi * rho * z / (rho ** 2 + z ** 2) ** sp.Rational(3, 2), (rho, 0, R))
    assert sp.simplify(omega - 2 * sp.pi * (1 - z / sp.sqrt(z ** 2 + R ** 2))) == 0
    jump = sp.limit(omega, z, 0, "+") - sp.limit(-omega, z, 0, "+")
    assert sp.simplify(jump - 4 * sp.pi) == 0
    for x0, z0 in ((0.0, 1.0), (1.5, 0.5), (3.0, -2.0)):
        om = S.disk_solid_angle(2.0, x0, z0)
        assert S.double_layer_potential(1.0, 1.0, om) == pytest.approx(S.disk_dipole_sum(2.0, 1.0, 1.0, x0, z0), rel=1e-4)
    assert S.disk_solid_angle(2.0, 0.0, 1.0) == pytest.approx(float(S.disk_solid_angle_axis(2.0, 1.0)), rel=1e-8)
    # Closed surface: the solid angle of a closed surface seen from outside is zero, so a uniformly activated region
    # (a closed double layer) gives no potential. Check with the sphere: the flux of r/|r|^3 through a sphere of
    # radius 1 centered 3 away is zero.
    th, ph = sp.symbols("theta phi")
    pt = sp.Matrix([sp.sin(th) * sp.cos(ph), sp.sin(th) * sp.sin(ph), sp.cos(th)])
    d = pt + sp.Matrix([0, 0, 3])
    integrand = (d.dot(pt) / (d.dot(d)) ** sp.Rational(3, 2)) * sp.sin(th)
    f = sp.lambdify((th, ph), integrand)
    from scipy import integrate as si
    val = si.dblquad(lambda t, p_: f(t, p_), 0, 2 * np.pi, 0, np.pi)[0]
    assert abs(val) < 1e-8


def test_core_conductor_front():
    """eq-m01-core: along a strand, I_i = -beta dV_m/dx and i_m = -dI_i/dx = beta d2V_m/dx2. For the arctangent
    front the membrane current sums to zero and its dipole moment is beta dV, whatever the front width
    (eq-m01-moment)."""
    s, w, dv, beta = sp.symbols("s w DeltaV beta", positive=True)
    vm = dv * (sp.Rational(1, 2) - sp.atan(s / w) / sp.pi)
    ii = -beta * sp.diff(vm, s)
    im = -sp.diff(ii, s)
    assert sp.simplify(im - beta * sp.diff(vm, s, 2)) == 0
    assert sp.integrate(im, (s, -sp.oo, sp.oo)) == 0
    assert sp.simplify(sp.integrate(s * im, (s, -sp.oo, sp.oo)) - beta * dv) == 0
    x = np.linspace(-20000, 20000, 2000001)
    for width in (0.1, 0.5, 2.0):
        i_m = S.front_im(x, width)
        assert S.net_current(x, i_m) == pytest.approx(0.0, abs=1e-9)
        assert S.dipole_moment(x, i_m) == pytest.approx(1.0, abs=1e-3)
        assert np.allclose(S.front_im(x[::50000], width), np.gradient(-S.axial_current(x, width), x)[::50000], atol=1e-6)


def test_front_as_line_dipole():
    """eq-m01-front-dipole: a line of dipoles of moment p per unit length, seen from height h, gives
    p s / (2 pi sigma (s^2 + h^2)); with p = beta dV this is the m03 closed form with w + h replaced by h. Summing the
    2-D field of every membrane-current strip of the arctangent front reproduces the m03 closed form exactly."""
    s, h, p, sig = sp.symbols("s h p sigma", positive=True)
    # the 2-D dipole: -d/dx' of the line-source potential -ln(r)/(2 pi sigma), times p
    xp = sp.symbols("xp")
    g = -sp.log((s - xp) ** 2 + h ** 2) / (4 * sp.pi * sig)
    line = (p * sp.diff(g, xp)).subs(xp, 0)
    assert sp.simplify(line - p * s / (2 * sp.pi * sig * (s ** 2 + h ** 2))) == 0
    ss = np.linspace(-6, 6, 13)
    for w, hh in ((0.3, 1.0), (1.0, 0.5)):
        q = S.front_potential_quadrature(ss, w, hh)
        c = S.front_potential(ss, w, hh)
        assert np.max(np.abs(q - c)) < 1e-6 * np.max(np.abs(c))
        assert np.allclose(S.line_dipole_potential(1.0, 1.0, ss, w + hh), c)
    far = np.array([50.0, 200.0])
    assert np.allclose(S.front_potential(far, 0.3, 1.0), S.line_dipole_potential(1.0, 1.0, far, 0.0), rtol=1e-3)
