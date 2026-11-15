"""m17 equation tests: pair potential, axis nonlinearity, linear map, metric field scaling, interfaces, precision."""

import numpy as np
import pytest
import sympy as sp

from epml import impedance as Z


def test_pair():
    """eq-m17-pair: k (1/|r-a| - 1/|r-b|) is harmonic away from the patches and odd about the midplane."""
    x, y, z = sp.symbols("x y z", real=True)
    d = sp.symbols("d", positive=True)
    phi = 1 / sp.sqrt((x - d) ** 2 + y ** 2 + z ** 2) - 1 / sp.sqrt((x + d) ** 2 + y ** 2 + z ** 2)
    assert sp.simplify(sum(sp.diff(phi, v, 2) for v in (x, y, z))) == 0
    assert sp.simplify(phi.subs(x, -x) + phi) == 0
    a, b = np.array([200.0, 0, 0]), np.array([-200.0, 0, 0])
    r = np.array([30.0, 40.0, -20.0])
    assert Z.pair_potential(r, a, b) == pytest.approx(1 / np.linalg.norm(r - a) - 1 / np.linalg.norm(r - b))


def test_axis():
    """eq-m17-axis: 2kx/(d^2 - x^2); the linear estimate overshoots by x^2/(d^2 - x^2)."""
    x, d, k = sp.symbols("x d k", positive=True)
    phi = k * (1 / (d - x) - 1 / (d + x))
    assert sp.simplify(phi - 2 * k * x / (d ** 2 - x ** 2)) == 0
    E0 = sp.diff(phi, x).subs(x, 0)
    assert sp.simplify(E0 - 2 * k / d ** 2) == 0
    rel = sp.simplify((phi / E0 - x) / x)
    assert sp.simplify(rel - x ** 2 / (d ** 2 - x ** 2)) == 0
    assert sp.series(rel, x, 0, 4).removeO() == x ** 2 / d ** 2
    assert Z.linear_estimate(Z.axis_potential(50.0, 200.0), 200.0) == pytest.approx(50.0 * (1 + 50 ** 2 / (200 ** 2 - 50 ** 2)))


def test_linear_map():
    """eq-m17-linear: three orthogonal pairs, phi_i / E0 recovers positions near the center, worse farther out."""
    P = Z.patch_pairs(200.0)
    near = np.array([2.0, -1.0, 3.0])
    far = np.array([60.0, -40.0, 50.0])
    est = lambda r: Z.linear_estimate(Z.potentials(r, P), 200.0)
    assert est(near) == pytest.approx(near, rel=1e-3)
    assert np.linalg.norm(est(far) - far) > 2.0


def test_metric():
    """eq-m17-metric: dphi^T M dphi = l^2 with M = (J J^T)^-1, recovered from >= 6 pairs of known spacing."""
    P = Z.patch_pairs(200.0)
    r0 = np.array([40.0, -30.0, 50.0])
    J = Z.local_jacobian(r0, P)
    rng = np.random.default_rng(17)
    dphis, ls = [], []
    for _ in range(12):
        u = rng.standard_normal(3); u /= np.linalg.norm(u)
        dphis.append(Z.potentials(r0 + 1.0 * u, P) - Z.potentials(r0 - 1.0 * u, P)); ls.append(2.0)
    M = Z.fit_metric(dphis, ls)
    Mt = np.linalg.inv(J @ J.T)
    assert M == pytest.approx(Mt, rel=1e-3)
    u = np.array([1.0, 2.0, -1.0]) / np.sqrt(6)
    dphi = Z.potentials(r0 + 2.5 * u, P) - Z.potentials(r0 - 2.5 * u, P)
    assert Z.metric_distance(dphi, M) == pytest.approx(5.0, rel=1e-3)
    # SymPy: the identity |J^-1 v|^2 = v^T (J J^T)^-1 v
    Js = sp.Matrix(3, 3, sp.symbols("j0:9")); v = sp.Matrix(sp.symbols("v0:3"))
    lhs = ((Js.inv() * v).T * (Js.inv() * v))[0]
    rhs = (v.T * (Js * Js.T).inv() * v)[0]
    assert sp.simplify(lhs - rhs) == 0


def test_interface():
    """eq-m17-interface: continuity of normal current stretches apparent distance by sigma_ref / sigma_local."""
    s1, s2, J = sp.symbols("sigma_1 sigma_2 J", positive=True)
    assert sp.simplify((J / s2) / (J / s1) - s1 / s2) == 0
    x = np.array([0.0, 10.0, 20.0, 30.0])
    app = Z.layered_positions(x, [0, 10, 20, 30], [1.0, 0.4, 1.0])
    assert app[2] - app[1] == pytest.approx(10.0 * Z.interface_stretch(1.0, 0.4))
    assert app[3] - app[2] == pytest.approx(10.0)


def test_precision():
    """eq-m17-precision: position noise = voltage noise / field."""
    assert Z.position_noise(1e-3, Z.center_field(200.0)) == pytest.approx(1e-3 * 200.0 ** 2 / 2)
    assert Z.position_noise(1e-3, Z.center_field(100.0)) == pytest.approx(Z.position_noise(1e-3, Z.center_field(200.0)) / 4)
