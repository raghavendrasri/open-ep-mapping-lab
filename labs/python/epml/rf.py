"""m27 helpers: RF ablation biophysics (current, heating, temperature, injury, impedance, metrics).

SI units throughout unless a name says otherwise: A, V, W, m, s, S/m, W/(m K), kg/m^3, J/(kg K).
Temperatures in degrees Celsius, except where an Arrhenius rate needs kelvin.
"""

import numpy as np

R_GAS = 8.314462618  # J/(mol K), CODATA 2018 exact value of the molar gas constant


def current_density(current, r):
    """eq-m27-current-density: J = I / (4 pi r^2) around a spherical electrode."""
    return current / (4.0 * np.pi * np.asarray(r, dtype=float) ** 2)


def power_density(current, sigma, r):
    """eq-m27-power-density: q = J^2 / sigma = I^2 / (16 pi^2 sigma r^4)."""
    return current_density(current, r) ** 2 / sigma


def power_fraction_within(r, r0):
    """eq-m27-power-fraction: share of tissue heating deposited between r0 and r."""
    return 1.0 - r0 / np.asarray(r, dtype=float)


def spreading_resistance_sphere(sigma, r0):
    """eq-m27-spreading: sphere of radius r0 in an infinite homogeneous medium."""
    return 1.0 / (4.0 * np.pi * sigma * r0)


def spreading_resistance_hemisphere(sigma, r0):
    """eq-m27-spreading: hemisphere on the flat, insulating face of a half-space."""
    return 1.0 / (2.0 * np.pi * sigma * r0)


def shell_resistance(r, sigma_r):
    """eq-m27-impedance: R = integral dr / (4 pi r^2 sigma(r)) for a radial conductivity profile.

    `r` is an increasing grid starting at the electrode surface; the integral is truncated at r[-1]
    and the far-field tail is added assuming sigma is constant beyond it.
    """
    r = np.asarray(r, dtype=float)
    sigma_r = np.asarray(sigma_r, dtype=float)
    integrand = 1.0 / (4.0 * np.pi * r**2 * sigma_r)
    near = np.trapezoid(integrand, r)
    tail = 1.0 / (4.0 * np.pi * sigma_r[-1] * r[-1])
    return near + tail


def conductivity_linear(T, sigma0, alpha, T0):
    """eq-m27-impedance: sigma(T) = sigma0 [1 + alpha (T - T0)], alpha per degree."""
    return sigma0 * (1.0 + alpha * (np.asarray(T, dtype=float) - T0))


def steady_source_coefficient(current, sigma, k):
    """B in eq-m27-steady-temperature: B = I^2 / (32 pi^2 sigma k), units K m^2."""
    return current**2 / (32.0 * np.pi**2 * sigma * k)


def steady_temperature(r, T_b, A, B):
    """eq-m27-steady-temperature: T(r) = T_b + A / r - B / r^2."""
    r = np.asarray(r, dtype=float)
    return T_b + A / r - B / r**2


def steady_A_for_interface(T_e, T_b, r0, B):
    """Choose A so that T(r0) = T_e in eq-m27-steady-temperature."""
    return (T_e - T_b + B / r0**2) * r0


def isotherm_radius_conduction(T_e, T_b, T_L, r0):
    """eq-m27-isotherm with the source term dropped: r_L = r0 (T_e - T_b) / (T_L - T_b)."""
    return r0 * (T_e - T_b) / (T_L - T_b)


def steady_profile_fd(r0, r_out, T_inner, T_outer, B, n=2000):
    """Finite-difference solution of (1/r^2) d/dr (r^2 dT/dr) = -2B / r^4 on [r0, r_out].

    This is eq-m27-bioheat at steady state with no perfusion, written with B = I^2/(32 pi^2 sigma k),
    so q/k = 2B / r^4. Dirichlet values at both ends. Returns (r, T).
    """
    r = np.linspace(r0, r_out, n)
    h = r[1] - r[0]
    rp = r[1:-1] + h / 2
    rm = r[1:-1] - h / 2
    m = n - 2
    main = -(rp**2 + rm**2) / (h**2 * r[1:-1] ** 2)
    upper = rp**2 / (h**2 * r[1:-1] ** 2)
    lower = rm**2 / (h**2 * r[1:-1] ** 2)
    rhs = -2.0 * B / r[1:-1] ** 4
    rhs[0] -= lower[0] * T_inner
    rhs[-1] -= upper[-1] * T_outer
    from scipy.linalg import solve_banded

    ab = np.zeros((3, m))
    ab[0, 1:] = upper[:-1]
    ab[1, :] = main
    ab[2, :-1] = lower[1:]
    inner = solve_banded((1, 1), ab, rhs)
    return r, np.concatenate([[T_inner], inner, [T_outer]])


def bioheat_spherical(r0, r_out, T_b, T_e, current, sigma, k, rho_c, perfusion=0.0, t_end=60.0,
                      n=200):
    """Method-of-lines solution of eq-m27-bioheat in spherical symmetry.

    rho_c is the volumetric heat capacity rho*c (J/(m^3 K)); perfusion is omega_b rho_b c_b
    (W/(m^3 K)). The interface is held at T_e (an idealized temperature-controlled electrode);
    the outer boundary at T_b. Returns (r, t, T[t, r]).
    """
    from scipy.integrate import solve_ivp

    r = np.linspace(r0, r_out, n)
    h = r[1] - r[0]
    q = power_density(current, sigma, r[1:-1])
    rp = (r[1:-1] + h / 2) ** 2
    rm = (r[1:-1] - h / 2) ** 2
    r2 = r[1:-1] ** 2

    def rhs(_t, u):
        T = np.concatenate([[T_e], u, [T_b]])
        lap = (rp * (T[2:] - T[1:-1]) - rm * (T[1:-1] - T[:-2])) / (h**2 * r2)
        return (k * lap + q - perfusion * (u - T_b)) / rho_c

    u0 = np.full(n - 2, float(T_b))
    sol = solve_ivp(rhs, (0.0, t_end), u0, method="BDF", t_eval=np.linspace(0, t_end, 61),
                    rtol=1e-6, atol=1e-8)
    T = np.column_stack([np.full(sol.t.size, T_e), sol.y.T, np.full(sol.t.size, T_b)])
    return r, sol.t, T


def diffusion_length(alpha, t):
    """eq-m27-diffusion-length: l = sqrt(4 alpha t), the 1/e half-width of the heat kernel."""
    return np.sqrt(4.0 * alpha * t)


def arrhenius_omega(t, T_celsius, A, Ea):
    """eq-m27-arrhenius: Omega(t) = integral A exp(-Ea / (R T)) dt, cumulative, T in Celsius."""
    T_k = np.asarray(T_celsius, dtype=float) + 273.15
    rate = A * np.exp(-Ea / (R_GAS * T_k))
    t = np.asarray(t, dtype=float)
    out = np.zeros_like(t)
    out[1:] = np.cumsum(0.5 * (rate[1:] + rate[:-1]) * np.diff(t))
    return out


def surviving_fraction(omega):
    """C/C0 = exp(-Omega): Omega = 1 leaves 1/e undamaged (63 % damaged)."""
    return np.exp(-np.asarray(omega, dtype=float))


def force_time_integral(t, force):
    """eq-m27-fti: FTI = integral F dt (same units as force times seconds, e.g. g s)."""
    return float(np.trapezoid(force, t))


def energy(t, power):
    """eq-m27-fti: E = integral P dt (J for W and s)."""
    return float(np.trapezoid(power, t))


def weighted_index(t, force, power, a=1.0, b=1.0, g=np.sqrt):
    """eq-m27-weighted-index: generic g(integral F^a P^b dt). Not any commercial formula."""
    return float(g(np.trapezoid(np.asarray(force, float) ** a * np.asarray(power, float) ** b, t)))
