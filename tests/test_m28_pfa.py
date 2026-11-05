"""m28 equation checks: induced membrane voltage, membrane charging, fields, lesion zones, heating.

Each test checks an equation in modules/m28-pulsed-field-ablation.qmd by SymPy or by a numerical
route that does not use the closed form. Parameter values are test inputs, not physiological claims.
"""

import numpy as np
import pytest
import sympy as sp
from scipy.integrate import solve_ivp

from epml import pfa

r, th, E, R, V, r0 = sp.symbols("r theta E R V r_0", positive=True)


def laplace_axisymmetric(phi):
    """Laplacian in spherical coordinates for a potential that does not depend on azimuth."""
    return sp.diff(r**2 * sp.diff(phi, r), r) / r**2 + sp.diff(sp.sin(th) * sp.diff(phi, th), th) / (
        r**2 * sp.sin(th))


def test_schwan_equation_from_laplace():
    """eq-m28-schwan: outside a non-conducting sphere in a uniform field E, the potential
    -E (r + R^3 / (2 r^2)) cos(theta) satisfies Laplace's equation, has no normal current at r = R
    and tends to the applied field far away. With the interior at the reference potential 0, the
    membrane voltage phi_in - phi_out at r = R is 3/2 E R cos(theta)."""
    phi_out = -E * (r + R**3 / (2 * r**2)) * sp.cos(th)
    assert sp.simplify(laplace_axisymmetric(phi_out)) == 0
    assert sp.simplify(sp.diff(phi_out, r).subs(r, R)) == 0
    assert sp.limit(phi_out / r, r, sp.oo) == -E * sp.cos(th)
    dpsi = 0 - phi_out.subs(r, R)
    assert sp.simplify(dpsi - sp.Rational(3, 2) * E * R * sp.cos(th)) == 0
    assert pfa.schwan_dpsi(1e5, 10e-6, 0.0) == pytest.approx(1.5)


def test_membrane_charging_time_constant():
    """eq-m28-charging: with conducting interior (sigma_i) and exterior (sigma_e), a thin membrane of
    capacitance C_m and the l = 1 solutions phi_i = a r cos, phi_e = (-E r + b / r^2) cos, current
    continuity and the capacitor law give dV/dt = -(V - 3/2 E R) / tau with
    tau = R C_m (rho_i + rho_e / 2)."""
    a, b, Vm, Cm, si, se = sp.symbols("a b V_m C_m sigma_i sigma_e", real=True)
    # membrane voltage coefficient (multiplies cos theta) at r = R
    V_expr = a * R - (-E * R + b / R**2)
    # radial current density out of the cell, from inside and from outside, must be equal
    j_in = -si * a
    j_out = -se * (-E - 2 * b / R**3)
    sol = sp.solve([sp.Eq(j_in, j_out), sp.Eq(V_expr, Vm)], [a, b], dict=True)[0]
    dVdt = (j_in / Cm).subs(sol)  # capacitor: C_m dV/dt = outward current density
    tau = R * Cm * (1 / si + 1 / (2 * se))
    assert sp.simplify(dVdt + (Vm - sp.Rational(3, 2) * E * R) / tau) == 0
    assert pfa.membrane_tau(10e-6, 1e-2, 1.0, 1.0) == pytest.approx(10e-6 * 1e-2 * 1.5)
    # the exponential approach follows from integrating that ODE numerically
    tau_n, Ev, Rv = 1e-6, 1e5, 10e-6
    s = solve_ivp(lambda t, y: -(y - 1.5 * Ev * Rv) / tau_n, (0, 5e-6), [0.0], rtol=1e-10,
                  atol=1e-12, t_eval=[1e-6, 3e-6])
    assert s.y[0] == pytest.approx(pfa.dpsi_step(Ev, Rv, 0.0, s.t, tau_n), rel=1e-6)


def test_sphere_field_solves_laplace_and_matches_finite_differences():
    """eq-m28-field-sphere: V r0 / r is the radial solution of Laplace's equation with phi(r0) = V and
    phi -> 0 far away; a finite-difference radial solve agrees."""
    phi = V * r0 / r
    assert sp.simplify(laplace_axisymmetric(phi)) == 0
    assert phi.subs(r, r0) == V and sp.limit(phi, r, sp.oo) == 0
    rr = np.linspace(1e-3, 0.05, 5001)
    h = rr[1] - rr[0]
    n = rr.size - 2
    rp, rm = (rr[1:-1] + h / 2) ** 2, (rr[1:-1] - h / 2) ** 2
    M = np.diag(-(rp + rm)) + np.diag(rp[:-1], 1) + np.diag(rm[1:], -1)
    rhs = np.zeros(n)
    rhs[0] -= rm[0] * 1000.0
    rhs[-1] -= rp[-1] * pfa.sphere_potential(1000.0, 1e-3, rr[-1])
    phi_fd = np.linalg.solve(M, rhs)
    assert np.max(np.abs(phi_fd - pfa.sphere_potential(1000.0, 1e-3, rr[1:-1]))) < 1e-5 * 1000.0


def test_lesion_radius_and_zones():
    """eq-m28-lesion-radius and eq-m28-zones: the iso-field radius found by root finding equals
    sqrt(V r0 / E_th); the reversible shell extends sqrt(E_irr / E_rev) times further."""
    from scipy.optimize import brentq

    Vv, r0v, Eth = 1500.0, 1.5e-3, 4e4
    root = brentq(lambda x: pfa.sphere_field(Vv, r0v, x) - Eth, r0v, 1.0)
    assert root == pytest.approx(pfa.lesion_radius(Vv, r0v, Eth), rel=1e-10)
    r_rev, r_irr = pfa.zone_radii(Vv, r0v, 2e4, 4e4)
    assert r_rev / r_irr == pytest.approx(np.sqrt(2.0))
    # unlike the RF isotherm at fixed interface temperature, the radius grows as sqrt(V)
    assert pfa.lesion_radius(4 * Vv, r0v, Eth) == pytest.approx(2 * pfa.lesion_radius(Vv, r0v, Eth))


@pytest.mark.parametrize("sep", [5.0, 10.0, 20.0, 40.0])
def test_bipolar_superposition_error_shrinks_with_separation(sep):
    """eq-m28-bipolar: superposing two isolated-sphere potentials violates the boundary condition on
    each sphere by about V_other r0 / d, so the approximation improves as separation d grows."""
    r0v = 1e-3
    d = sep * r0v
    x1, x2 = np.array([0, 0, 0.0]), np.array([d, 0, 0.0])
    angles = np.linspace(0, np.pi, 50)
    surf = np.column_stack([r0v * np.cos(angles), r0v * np.sin(angles), np.zeros_like(angles)])
    phi = pfa.bipolar_potential(surf, x1, 1000.0, x2, -1000.0, r0v)
    err = np.max(np.abs(phi - 1000.0))
    # the worst point faces the other sphere, at distance d - r0 from its centre
    assert err == pytest.approx(1000.0 * r0v / (d - r0v), rel=1e-9)


def test_joule_heating_bound():
    """eq-m28-joule: without conduction, heating sigma E^2 per unit volume over total on-time t_on
    raises temperature by sigma E^2 t_on / (rho c); conduction can only lower the peak."""
    sig, Ev, rho_c = 0.4, 5e4, 4e6
    pulse_on, n_pulses = 5e-6, 200
    # integrate dT/dt = sigma E^2 / (rho c) during pulses, 0 between them
    dT = sum(sig * Ev**2 / rho_c * pulse_on for _ in range(n_pulses))
    assert dT == pytest.approx(pfa.joule_bound(sig, Ev, pulse_on * n_pulses, rho_c))
    # 1D explicit heat equation with a heated slab and conduction: peak stays below the bound
    alpha, L, n = 1.4e-7, 4e-3, 401
    x = np.linspace(-L / 2, L / 2, n)
    dx = x[1] - x[0]
    heated = np.abs(x) < 0.2e-3
    T = np.zeros(n)
    t_total, dt = pulse_on * n_pulses * 50, 0.4 * dx**2 / alpha
    steps = int(t_total / dt)
    source = np.where(heated, sig * Ev**2 / rho_c / 50, 0.0)  # same energy spread over 50x time
    for _ in range(steps):
        T[1:-1] += dt * (alpha * (T[2:] - 2 * T[1:-1] + T[:-2]) / dx**2 + source[1:-1])
    assert T.max() <= pfa.joule_bound(sig, Ev, pulse_on * n_pulses, rho_c) + 1e-12
