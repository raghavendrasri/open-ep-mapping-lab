"""m16 equation tests: dipole field, coil voltage, pose model and solver, precision, roll, distortion."""

import numpy as np
import pytest
import sympy as sp

from epml import magnetic as M


def test_dipole():
    """eq-m16-dipole: B = (3 (m.rhat) rhat - m)/r^3 is -grad(m.r/r^3), divergence- and curl-free."""
    x, y, z = sp.symbols("x y z", real=True)
    mx, my, mz = sp.symbols("m_x m_y m_z", real=True)
    r = sp.sqrt(x ** 2 + y ** 2 + z ** 2)
    psi = (mx * x + my * y + mz * z) / r ** 3
    B = [-sp.diff(psi, v) for v in (x, y, z)]
    m = sp.Matrix([mx, my, mz]); rv = sp.Matrix([x, y, z])
    target = (3 * (m.dot(rv)) * rv / r ** 2 - m) / r ** 3
    assert all(sp.simplify(B[i] - target[i]) == 0 for i in range(3))
    assert sp.simplify(sum(sp.diff(B[i], v) for i, v in enumerate((x, y, z)))) == 0
    assert sp.simplify(sp.diff(B[2], y) - sp.diff(B[1], z)) == 0
    mm, rr = np.array([0.3, -0.2, 1.0]), np.array([10.0, 20.0, 30.0])
    num = M.dipole_field(mm, rr)
    sub = {x: rr[0], y: rr[1], z: rr[2], mx: mm[0], my: mm[1], mz: mm[2]}
    assert num == pytest.approx([float(target[i].subs(sub)) for i in range(3)])


def test_emf():
    """eq-m16-emf: -d/dt of N A B sin(wt) has amplitude 2 pi f N A B."""
    t, f, N, A, B = sp.symbols("t f N A B", positive=True)
    v = -sp.diff(N * A * B * sp.sin(2 * sp.pi * f * t), t)
    assert sp.simplify(sp.Abs(v.subs(t, 0)) - 2 * sp.pi * f * N * A * B) == 0
    assert M.emf_amplitude(10e3, 100, 1e-6, 1e-6) == pytest.approx(2 * np.pi * 10e3 * 100 * 1e-6 * 1e-6)


def test_coupling_and_solver():
    """eq-m16-coupling: readings are G(p) n; least squares recovers the pose from noise-free readings."""
    gen = M.generator()
    true = np.array([10.0, -20.0, 150.0, 0.6, 1.1])
    v = M.readings(true, gen)
    assert v == pytest.approx(M.field_matrix(true[:3], gen) @ M.axis_from_angles(0.6, 1.1))
    est = M.solve_pose(v, gen, true + np.array([15.0, 10.0, -20.0, 0.2, -0.3]))
    assert est == pytest.approx(true, abs=1e-8)


def test_crlb():
    """eq-m16-crlb: Monte Carlo spread of the solver matches sigma^2 (J^T J)^-1."""
    gen = M.generator()
    true = np.array([10.0, -20.0, 150.0, 0.6, 1.1])
    v = M.readings(true, gen)
    rng = np.random.default_rng(16)
    sigma = 1e-3
    ests = np.array([M.solve_pose(v + sigma * rng.standard_normal(v.size), gen, true) for _ in range(800)])
    assert np.sqrt(np.sum(ests[:, :3].var(axis=0))) == pytest.approx(M.position_sd(true, gen, sigma), rel=0.08)


def test_sensitivity():
    """eq-m16-sensitivity: on a dipole's axis, dr = r dB / (3 B); range error grows as r^4 at fixed field noise."""
    r, m, dB = sp.symbols("r m dB", positive=True)
    Bax = 2 * m / r ** 3
    assert sp.simplify(-dB / sp.diff(Bax, r) - r * dB / (3 * Bax)) == 0
    errs = [M.axial_range_error(rv, 2e6 / rv ** 3, 1e-3) for rv in (100.0, 200.0)]
    assert errs[1] / errs[0] == pytest.approx(16.0)
    gen = M.generator()
    sd = [M.position_sd([0.0, 0.0, z, 0.6, 1.1], gen, 1e-3) for z in (300.0, 600.0)]
    assert np.log(sd[1] / sd[0]) / np.log(2.0) > 4.0          # the full pose degrades at least as fast as r^4


def test_5dof():
    """eq-m16-5dof: rotating one coil about its own axis changes nothing; the Jacobian has rank 5, not 6."""
    gen = M.generator()
    p, n = np.array([10.0, -20.0, 150.0]), M.axis_from_angles(0.6, 1.1)
    G = M.field_matrix(p, gen)
    assert G @ M.rotate(n, n, 0.7) == pytest.approx(G @ n)
    assert M.rotation_jacobian_rank(p, n, gen) == 5


def test_distortion():
    """eq-m16-distortion: an induced dipole biases the pose; the first-order bias matches the solver for small alpha."""
    gen = M.generator()
    true = np.array([10.0, -20.0, 150.0, 0.6, 1.1])
    v = M.readings(true, gen)
    q = np.array([0.0, 0.0, 250.0])
    dv = M.distorted_readings(true, gen, q, 2e3) - v
    est = M.solve_pose(v + dv, gen, true)
    assert M.linear_bias(true, gen, dv)[:3] == pytest.approx((est - true)[:3], rel=0.02, abs=1e-3)
    far = M.distorted_readings(true, gen, np.array([0.0, 0.0, 400.0]), 2e3) - v
    assert np.linalg.norm(M.linear_bias(true, gen, far)[:3]) < np.linalg.norm(M.linear_bias(true, gen, dv)[:3])
