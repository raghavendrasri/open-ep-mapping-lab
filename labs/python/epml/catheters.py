"""m13 · Catheter design: electrode size and spacing, grids, baskets and contact-force sensing. MIT License.

Units: lengths in mm, conductivity relative (sigma = 1 unless stated), so resistances are in units of
1/(sigma mm). Forces and sensor readings are relative unless stated. Angles in radians unless named _deg.
"""

import numpy as np
from scipy import integrate


# ---- eq-m13-spreading: electrode spreading resistance -------------------------------------------------------

def disk_resistance(a, sigma=1.0):
    """Equipotential disk of radius a flush with an insulating plane, return electrode far away: 1/(4 sigma a)."""
    return 1.0 / (4.0 * sigma * a)


def hemisphere_resistance(a, sigma=1.0):
    """Hemisphere of radius a on an insulating plane: 1/(2 pi sigma a)."""
    return 1.0 / (2.0 * np.pi * sigma * a)


def sphere_resistance(a, sigma=1.0):
    """Sphere of radius a in an infinite medium (the m27 tip model): 1/(4 pi sigma a)."""
    return 1.0 / (4.0 * np.pi * sigma * a)


def disk_density_potential(r, a=1.0):
    """Integral over the disk of 1/sqrt(a^2 - |x'|^2) / |x - x'| dA', at a point x on the disk at radius r < a.

    Computed numerically in polar coordinates centered on x (the 1/|x - x'| cancels the Jacobian), with the
    inverse-square-root edge singularity handled by an algebraic quadrature weight. It equals pi^2 for every r,
    so this current density makes the disk an equipotential.
    """
    def ray(psi):
        s = np.sqrt(a * a - (r * np.sin(psi)) ** 2)
        far, back = s - r * np.cos(psi), s + r * np.cos(psi)    # a^2 - |x'|^2 = (far - rho)(rho + back)
        val, _ = integrate.quad(lambda rho: 1.0 / np.sqrt(rho + back), 0.0, far, weight="alg", wvar=(0.0, -0.5))
        return val
    val, _ = integrate.quad(ray, 0.0, 2.0 * np.pi, limit=200)
    return val


def disk_resistance_numeric(a=1.0, sigma=1.0, r=0.5):
    """Resistance from the numerically integrated equipotential density j = 1/sqrt(a^2 - r^2) (one face).

    Half-space Green's function with an insulating plane: phi = (1/(2 pi sigma)) integral j dA / distance.
    Total current: integral j dA = 2 pi a.
    """
    v = disk_density_potential(r * a, a) / (2.0 * np.pi * sigma)
    return v / (2.0 * np.pi * a)


# ---- eq-m13-orthogonal: bipole direction ----------------------------------------------------------------------

def bipole_amplitude(theta, a0=1.0):
    """Amplitude of a closely spaced bipole at angle theta to the wavefront's direction of travel (planar front)."""
    return a0 * np.abs(np.cos(theta))


def orthogonal_pair(theta, a0=1.0):
    """Two perpendicular bipoles: (best single amplitude, root-sum-square amplitude)."""
    ax, ay = bipole_amplitude(theta, a0), bipole_amplitude(theta - np.pi / 2, a0)
    return np.maximum(ax, ay), np.hypot(ax, ay)


# ---- eq-m13-alias: spatial sampling and electrode height ------------------------------------------------------

def poisson_kernel(x, h):
    """Bipolar-type profile across a planar front seen from height h: (h/pi)/(x^2 + h^2). Fourier transform exp(-|k| h)."""
    return (h / np.pi) / (x * x + h * h)


def alias_fraction(spacing, h):
    """Fraction of the profile's energy above the spatial Nyquist wavenumber pi/spacing: exp(-2 pi h / spacing)."""
    return np.exp(-2.0 * np.pi * h / spacing)


def max_spacing(h, fraction):
    """Largest spacing that keeps the energy above Nyquist below `fraction`: 2 pi h / ln(1/fraction)."""
    return 2.0 * np.pi * h / np.log(1.0 / fraction)


def alias_fraction_fft(spacing, h, dx=0.01, length=4000.0):
    """The same fraction from an FFT of the finely sampled profile (a check on alias_fraction)."""
    x = np.arange(-length / 2, length / 2, dx)
    g = poisson_kernel(x, h)
    power = np.abs(np.fft.rfft(g)) ** 2
    k = 2.0 * np.pi * np.fft.rfftfreq(x.size, dx)
    w = np.ones_like(power)
    w[1:] = 2.0                        # one-sided spectrum: count negative wavenumbers too
    above = k > np.pi / spacing
    return float(np.sum((w * power)[above]) / np.sum(w * power))


def alias_wavenumber(k, spacing):
    """Wavenumber that a pattern of wavenumber k appears at after sampling at `spacing` (folded into [0, pi/spacing])."""
    ks = 2.0 * np.pi / spacing
    r = np.mod(k, ks)
    return np.minimum(r, ks - r)


# ---- eq-m13-basket: basket geometry ----------------------------------------------------------------------------

def basket(n_splines, n_electrodes, radius, theta_min_deg=25.0, theta_max_deg=155.0, azimuths_deg=None):
    """Electrode positions on a spherical basket: splines from pole to pole, electrodes evenly spaced in polar angle."""
    theta = np.radians(np.linspace(theta_min_deg, theta_max_deg, n_electrodes))
    if azimuths_deg is None:
        azimuths_deg = 360.0 * np.arange(n_splines) / n_splines
    phi = np.radians(np.asarray(azimuths_deg, float))
    T, P = np.meshgrid(theta, phi)
    pts = radius * np.stack([np.sin(T) * np.cos(P), np.sin(T) * np.sin(P), np.cos(T)], axis=-1)
    return pts.reshape(-1, 3)


def interspline_arc(theta, n_splines, radius):
    """Arc length between neighboring, evenly spaced splines at polar angle theta: 2 pi R sin(theta) / n."""
    return 2.0 * np.pi * radius * np.sin(theta) / n_splines


def sphere_points(n, radius=1.0):
    """Near-uniform points on a sphere (Fibonacci lattice)."""
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    phi = np.pi * (1.0 + 5.0 ** 0.5) * i
    r = np.sqrt(1.0 - z * z)
    return radius * np.stack([r * np.cos(phi), r * np.sin(phi), z], axis=1)


def fill_distance(electrodes, radius, n=20000, polar_range_deg=(0.0, 180.0)):
    """Largest great-circle distance (mm) from a surface point to its nearest electrode.

    Only surface points whose polar angle lies in polar_range_deg are used (default: the whole sphere).
    """
    s = sphere_points(n, radius)
    polar = np.degrees(np.arccos(np.clip(s[:, 2] / radius, -1.0, 1.0)))
    s = s[(polar >= polar_range_deg[0]) & (polar <= polar_range_deg[1])]
    cos = np.clip(s @ electrodes.T / radius ** 2, -1.0, 1.0)
    return float(radius * np.max(np.min(np.arccos(cos), axis=1)))


# ---- eq-m13-force, eq-m13-force-noise: contact-force sensing ---------------------------------------------------

def force_matrix(angles_deg, axial=1.0, lateral=1.0):
    """Sensor model s_i = axial * Fz + lateral * (Fx cos phi_i + Fy sin phi_i); columns ordered (Fx, Fy, Fz)."""
    p = np.radians(np.asarray(angles_deg, float))
    return np.stack([lateral * np.cos(p), lateral * np.sin(p), axial * np.ones_like(p)], axis=1)


def estimate_force(C, s):
    """Least-squares force (Fx, Fy, Fz) from sensor readings s (rows: sensors)."""
    return np.linalg.lstsq(C, s, rcond=None)[0]


def force_covariance(C, sigma):
    """Covariance of the least-squares estimate for independent sensor noise of SD sigma: sigma^2 (C^T C)^-1."""
    return sigma ** 2 * np.linalg.inv(C.T @ C)


def force_trials(C, force, sigma, n, rng):
    """Monte Carlo: estimates from n noisy readings of the same force."""
    s = (C @ force)[None, :] + sigma * rng.standard_normal((n, C.shape[0]))
    return np.linalg.lstsq(C, s.T, rcond=None)[0].T


GRAM_FORCE_N = 9.80665e-3   # 1 gram-force in newtons (standard acceleration of gravity, a defined value; CODATA 2018)
