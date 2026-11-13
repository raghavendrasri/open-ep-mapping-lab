"""m02 · Volume conduction and Poisson's equation: equation tests (numeric, and symbolic with SymPy where feasible)."""

import numpy as np
import pytest
import sympy as sp

from epml import sources as S
from epml import volume as V


def test_poisson_gaussian():
    """eq-m02-poisson: div(sigma grad phi) = -I_v. The 2-D Gaussian source of total current I has the exact potential
    -(I / 2 pi sigma)(ln r + E1(r^2 / 2 s^2) / 2), whose Laplacian is -I_v / sigma."""
    r, s, I, sig = sp.symbols("r s I sigma", positive=True)
    phi = -(I / (2 * sp.pi * sig)) * (sp.log(r) + sp.expint(1, r ** 2 / (2 * s ** 2)) / 2)
    lap = sp.diff(r * sp.diff(phi, r), r) / r                      # radial 2-D Laplacian
    q = I / (2 * sp.pi * s ** 2) * sp.exp(-r ** 2 / (2 * s ** 2))
    assert sp.simplify(lap + q / sig) == 0
    # the total current of the source is I
    assert sp.simplify(sp.integrate(q * 2 * sp.pi * r, (r, 0, sp.oo)) - I) == 0
    rr = np.array([0.0, 0.5, 1.0, 3.0])
    assert np.all(np.isfinite(V.gaussian_potential_2d(rr)))
    assert float(V.gaussian_potential_2d(np.array([1e-7]))[0]) == pytest.approx(float(V.gaussian_potential_2d(np.array([0.0]))[0]), abs=1e-6)


def test_finite_differences_converge():
    """eq-m02-fd: the flux-conserving 5-point scheme converges at second order, for a homogeneous medium and for an
    interface lying on cell faces."""
    errs = []
    for n in (40, 80, 160):
        X, Y, h = V.grid(n, 10.0)
        exact = V.gaussian_potential_2d(np.hypot(X, Y))
        phi = V.solve_poisson(np.ones_like(X), V.gaussian_source_2d(X, Y), h, exact)
        errs.append(np.max(np.abs(phi - exact)))
    assert errs[0] / errs[1] == pytest.approx(4.0, rel=0.15) and errs[1] / errs[2] == pytest.approx(4.0, rel=0.15)
    errs = []
    for n in (80, 160, 320):
        X, Y, h = V.grid(n, 10.0)
        sig = np.where(Y <= 0, 1.0, 3.0)
        exact = V.image_potential_2d(1.0, 1.0, 3.0, 2.0, X, Y)
        phi = V.solve_poisson(sig, V.gaussian_source_2d(X, Y + 2.0, 1.0, 0.3), h, exact)
        far = np.hypot(X, Y + 2.0) > 2.0
        errs.append(np.max(np.abs(phi - exact)[far]))
    assert errs[0] / errs[1] > 3.5 and errs[1] / errs[2] > 3.5


def test_interface_and_images():
    """eq-m02-interface and eq-m02-images: with k = (sigma1 - sigma2) / (sigma1 + sigma2), the image solution satisfies
    Laplace's equation on each side, continuity of potential and of normal current at z = 0. An insulating medium 2
    (k = 1) doubles the potential at the boundary; equal media (k = 0) give the m01 point source."""
    x, y, z, d, I, s1, s2 = sp.symbols("x y z d I sigma1 sigma2", positive=True)
    zz = sp.symbols("zz", real=True)
    k = (s1 - s2) / (s1 + s2)
    r = sp.sqrt(x ** 2 + y ** 2 + (zz + d) ** 2)
    ri = sp.sqrt(x ** 2 + y ** 2 + (zz - d) ** 2)
    phi1 = I / (4 * sp.pi * s1) * (1 / r + k / ri)
    phi2 = I / (2 * sp.pi * (s1 + s2) * r)
    lap = lambda f: sp.diff(f, x, 2) + sp.diff(f, y, 2) + sp.diff(f, zz, 2)
    assert sp.simplify(lap(phi1)) == 0 and sp.simplify(lap(phi2)) == 0
    assert sp.simplify((phi1 - phi2).subs(zz, 0)) == 0
    assert sp.simplify((s1 * sp.diff(phi1, zz) - s2 * sp.diff(phi2, zz)).subs(zz, 0)) == 0
    assert sp.simplify(phi2.subs(s2, 0) * (4 * sp.pi * s1 * r) / I) == 2
    obs = np.array([[0.7, 0.3, -1e-9], [0.7, 0.3, 1e-9]])
    a, b = V.image_potential_3d(1.0, 1.0, 4.0, 2.0, obs)
    assert a == pytest.approx(b, rel=1e-6)
    assert V.reflection_coefficient(1.0, 0.0) == 1.0 and V.reflection_coefficient(1.0, 1.0) == 0.0
    pts = np.array([[0.4, -0.2, -0.5], [1.0, 1.0, 2.0]])
    assert np.allclose(V.image_potential_3d(1.0, 1.0, 1.0, 2.0, pts), S.point_potential(1.0, 1.0, pts, (0, 0, -2.0)))


def test_reciprocity():
    """eq-m02-reciprocity: the potential a dipole p at r0 produces at an electrode equals p . grad psi(r0), where psi
    is the potential made by unit current injected at the electrode. Checked across the interface and, in a
    homogeneous medium, against the m01 dipole."""
    p = np.array([0.3, -0.5, 1.0])
    for e in ([1.0, 0.5, 1.5], [0.2, -0.3, 0.4], [-2.0, 1.0, 3.0]):
        for s2 in (0.25, 4.0):
            direct = float(V.image_dipole_potential_3d(p, 1.0, s2, 2.0, [e])[0])
            assert V.reciprocity_two_media(p, 1.0, s2, 2.0, e) == pytest.approx(direct, rel=1e-5)
    e = np.array([1.0, 0.5, 1.5])
    src = np.array([0.0, 0.0, -2.0])
    lead = V.lead_vector_homogeneous(e, src)
    assert float(np.dot(p, lead)) == pytest.approx(float(S.dipole_potential(p, 1.0, e, src)), rel=1e-12)
    # a bipole's lead field falls off faster with depth than a single electrode's
    depths = np.array([[0, 0, -1.0], [0, 0, -4.0]])
    uni, bi = V.bipole_lead_magnitude(depths, 2.0, 1.0)
    assert bi[1] / bi[0] < uni[1] / uni[0]
