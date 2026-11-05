"""m27 equation checks: current, heating, temperature, injury, impedance and lesion metrics.

Each test checks an equation in modules/m27-rf-ablation.qmd by a route that does not use the closed
form it is checking (SymPy, finite differences, ODE integration or brute-force sums). Parameter
values here are test inputs, not physiological claims.
"""

import numpy as np
import pytest
import sympy as sp

from epml import rf

r, r0, I, sigma, k, T_b, A, B = sp.symbols("r r_0 I sigma k T_b A B", positive=True)


def test_current_density_flux_is_the_current():
    """eq-m27-current-density: the flux of J = I/(4 pi r^2) through any sphere is I."""
    J = I / (4 * sp.pi * r**2)
    flux = sp.integrate(sp.integrate(J * r**2 * sp.sin(sp.Symbol("th")), (sp.Symbol("th"), 0, sp.pi)),
                        (sp.Symbol("ph"), 0, 2 * sp.pi))
    assert sp.simplify(flux - I) == 0
    # and it is divergence-free away from the electrode (charge conservation)
    assert sp.simplify(sp.diff(r**2 * J, r)) == 0


def test_power_density_integrates_to_joule_power():
    """eq-m27-power-density and eq-m27-spreading: integral of q over r > r0 equals I^2 R_s."""
    q = (I / (4 * sp.pi * r**2)) ** 2 / sigma
    total = sp.integrate(q * 4 * sp.pi * r**2, (r, r0, sp.oo))
    Rs = 1 / (4 * sp.pi * sigma * r0)
    assert sp.simplify(total - I**2 * Rs) == 0
    # numeric helpers agree with the closed forms
    assert rf.power_density(0.5, 0.4, 3e-3) == pytest.approx(0.25 / (16 * np.pi**2 * 0.4 * 3e-3**4))


def test_power_fraction_by_quadrature():
    """eq-m27-power-fraction: fraction of heating within r is 1 - r0/r; half within 2 r0."""
    r0_, sig = 1e-3, 0.5
    rr = np.geomspace(r0_, 1e3 * r0_, 200001)
    shell = rf.power_density(1.0, sig, rr) * 4 * np.pi * rr**2
    cum = np.concatenate([[0], np.cumsum(0.5 * (shell[1:] + shell[:-1]) * np.diff(rr))])
    total = 1.0 / (4 * np.pi * sig * r0_)  # I^2 R_s with I = 1 A
    for x in (1.5, 2.0, 5.0):
        i = np.searchsorted(rr, x * r0_)
        assert cum[i] / total == pytest.approx(rf.power_fraction_within(rr[i], r0_), abs=1e-4)
    assert rf.power_fraction_within(2 * r0_, r0_) == pytest.approx(0.5)


def test_spreading_resistance_from_shells():
    """eq-m27-spreading and eq-m27-impedance: summing thin shells dr/(4 pi r^2 sigma) gives
    1/(4 pi sigma r0) for a sphere; a hemisphere carries the same current through half the area, so
    its resistance is twice as large."""
    r0_, sig = 2e-3, 0.3
    rr = np.geomspace(r0_, 2.0, 400001)
    R = rf.shell_resistance(rr, np.full_like(rr, sig))
    assert R == pytest.approx(rf.spreading_resistance_sphere(sig, r0_), rel=1e-6)
    R_half = 2 * R  # same shells, half the cross-section each
    assert R_half == pytest.approx(rf.spreading_resistance_hemisphere(sig, r0_), rel=1e-6)


def test_steady_temperature_solves_the_radial_heat_equation():
    """eq-m27-steady-temperature and eq-m27-bioheat: T = T_b + A/r - B/r^2 with
    B = I^2/(32 pi^2 sigma k) solves k (1/r^2)(r^2 T')' + q = 0 with q from eq-m27-power-density,
    and tends to T_b far away."""
    Bsym = I**2 / (32 * sp.pi**2 * sigma * k)
    T = T_b + A / r - Bsym / r**2
    q = I**2 / (16 * sp.pi**2 * sigma * r**4)
    residual = k * sp.diff(r**2 * sp.diff(T, r), r) / r**2 + q
    assert sp.simplify(residual) == 0
    assert sp.limit(T, r, sp.oo) == T_b


def test_steady_temperature_matches_finite_differences():
    """eq-m27-steady-temperature: a finite-difference boundary-value solve with the same end values
    reproduces the closed form inside the domain."""
    r0_, r_out, Tb, Te = 1.0e-3, 30e-3, 37.0, 70.0
    Bv = rf.steady_source_coefficient(current=0.4, sigma=0.5, k=0.5)
    Av = rf.steady_A_for_interface(Te, Tb, r0_, Bv)
    exact_out = rf.steady_temperature(r_out, Tb, Av, Bv)
    rr, Tfd = rf.steady_profile_fd(r0_, r_out, Te, exact_out, Bv, n=20000)
    # both ends take the closed-form values, so the solve must reproduce the closed form inside
    assert np.max(np.abs(Tfd - rf.steady_temperature(rr, Tb, Av, Bv))) < 1e-3


def test_isotherm_radius_scales_with_electrode_radius():
    """eq-m27-isotherm: with the source term dropped, the isotherm T = T_L sits at
    r_L = r0 (T_e - T_b)/(T_L - T_b), proportional to r0 (the scaling reported by Haines 1990)."""
    Te, TL, Tb_, r0s = sp.symbols("T_e T_L T_b r_0", positive=True)
    Tprof = Tb_ + (Te - Tb_) * r0s / r
    rL = sp.solve(sp.Eq(Tprof, TL), r)[0]
    assert sp.simplify(rL - r0s * (Te - Tb_) / (TL - Tb_)) == 0
    a = rf.isotherm_radius_conduction(60.0, 37.0, 50.0, 1e-3)
    b = rf.isotherm_radius_conduction(60.0, 37.0, 50.0, 2e-3)
    assert b == pytest.approx(2 * a)


def test_transient_bioheat_settles_to_steady_state():
    """eq-m27-bioheat: the method-of-lines solution with no perfusion approaches the steady profile
    of eq-m27-steady-temperature (finite-domain version) at long times; perfusion lowers it."""
    r0_, r_out, Tb, Te = 1.0e-3, 10e-3, 37.0, 60.0
    sig, kk, rho_c, cur = 0.5, 0.5, 4.0e6, 0.05
    rr, t, T = rf.bioheat_spherical(r0_, r_out, Tb, Te, cur, sig, kk, rho_c, t_end=600.0, n=120)
    Bv = rf.steady_source_coefficient(cur, sig, kk)
    _, Tss = rf.steady_profile_fd(r0_, r_out, Te, Tb, Bv, n=rr.size)
    assert np.max(np.abs(T[-1] - Tss)) < 0.05
    _, _, Tp = rf.bioheat_spherical(r0_, r_out, Tb, Te, cur, sig, kk, rho_c, perfusion=4.0e4,
                                    t_end=600.0, n=120)
    assert np.all(Tp[-1][1:-1] <= T[-1][1:-1] + 1e-9)


def test_diffusion_length_from_a_heat_equation_run():
    """eq-m27-diffusion-length: a point of heat spreads as exp(-x^2 / (4 alpha t)); the 1/e
    half-width of an explicit finite-difference run is sqrt(4 alpha t)."""
    alpha, L, n = 1.4e-7, 0.02, 2001
    x = np.linspace(-L / 2, L / 2, n)
    dx = x[1] - x[0]
    dt = 0.4 * dx**2 / alpha
    u = np.zeros(n)
    u[n // 2] = 1.0 / dx
    t = 0.0
    while t < 30.0:
        u[1:-1] += alpha * dt / dx**2 * (u[2:] - 2 * u[1:-1] + u[:-2])
        t += dt
    above = x[n // 2:][u[n // 2:] >= u.max() / np.e]
    assert above.max() == pytest.approx(rf.diffusion_length(alpha, t), rel=0.02)


def test_arrhenius_constant_temperature_and_damage_fraction():
    """eq-m27-arrhenius: at constant temperature Omega = A exp(-Ea/(R T)) t, Omega grows
    monotonically with time and temperature, and Omega = 1 leaves 1/e undamaged."""
    Avals, Ea = 1e40, 2.5e5  # test inputs only
    t = np.linspace(0, 60, 601)
    om = rf.arrhenius_omega(t, np.full_like(t, 55.0), Avals, Ea)
    expected = Avals * np.exp(-Ea / (rf.R_GAS * (55.0 + 273.15))) * t
    assert om == pytest.approx(expected, rel=1e-9)
    hotter = rf.arrhenius_omega(t, np.full_like(t, 60.0), Avals, Ea)
    assert np.all(hotter[1:] > om[1:]) and np.all(np.diff(om) >= 0)
    # first-order kinetics dC/dt = -k C integrates to C/C0 = exp(-Omega)
    C, tt = sp.Function("C"), sp.symbols("t", positive=True)
    kk = sp.symbols("k", positive=True)
    sol = sp.dsolve(sp.Eq(C(tt).diff(tt), -kk * C(tt)), ics={C(0): 1})
    assert sp.simplify(sol.rhs - sp.exp(-kk * tt)) == 0
    assert 1 - rf.surviving_fraction(1.0) == pytest.approx(1 - np.exp(-1))


def test_impedance_falls_when_tissue_heats():
    """eq-m27-impedance: with sigma rising linearly with temperature, the shell integral over a heated
    profile gives a lower resistance than over tissue at body temperature."""
    r0_, Tb = 1e-3, 37.0
    rr = np.geomspace(r0_, 0.2, 20001)
    Bv = rf.steady_source_coefficient(0.4, 0.5, 0.5)
    Av = rf.steady_A_for_interface(70.0, Tb, r0_, Bv)
    T = rf.steady_temperature(rr, Tb, Av, Bv)
    cold = rf.shell_resistance(rr, rf.conductivity_linear(np.full_like(rr, Tb), 0.5, 0.02, Tb))
    hot = rf.shell_resistance(rr, rf.conductivity_linear(T, 0.5, 0.02, Tb))
    assert cold == pytest.approx(rf.spreading_resistance_sphere(0.5, r0_), rel=1e-4)
    assert hot < cold


def test_fti_energy_and_weighted_index():
    """eq-m27-fti and eq-m27-weighted-index: trapezoid integrals of sampled traces; the generic index
    is monotone in force, power and time, and two force traces with equal FTI can differ in index."""
    t = np.linspace(0, 20, 2001)
    steady = np.full_like(t, 20.0)
    assert rf.force_time_integral(t, steady) == pytest.approx(400.0)
    assert rf.energy(t, np.full_like(t, 30.0)) == pytest.approx(600.0)
    pulsing = 20.0 + 15.0 * np.sin(2 * np.pi * t)  # same mean force, same FTI over whole cycles
    assert rf.force_time_integral(t, pulsing) == pytest.approx(400.0, rel=1e-3)
    P = np.full_like(t, 30.0)
    base = rf.weighted_index(t, steady, P, a=0.7, b=1.4)
    assert rf.weighted_index(t, steady * 1.2, P, a=0.7, b=1.4) > base
    assert rf.weighted_index(t, steady, P * 1.2, a=0.7, b=1.4) > base
    assert rf.weighted_index(t[:1001], steady[:1001], P[:1001], a=0.7, b=1.4) < base
    # with a concave weight on force, the pulsing trace scores lower than the steady one
    assert rf.weighted_index(t, pulsing, P, a=0.7, b=1.4) < base
