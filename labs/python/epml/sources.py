"""m01 · Bioelectric sources: transmembrane current, dipoles and double layers. MIT License.

Units: distance mm, potentials and currents in relative units (conductivity sigma = 1 unless stated), as in m03.
The models: point current sources in an infinite homogeneous volume conductor (Plonsey and Barr 2007), the current
dipole as the limit of a source-sink pair, a uniform double layer whose potential is proportional to the solid angle
it subtends (Holland and Arnsdorf 1977), and the arctangent wavefront of m03 (epml.electrograms) as a moving line of
dipoles. All values are illustrative unless a docstring says otherwise.
"""

import numpy as np
from scipy import integrate

from .electrograms import unipolar


# ---------------------------------------------------------------- point sources (eq-m01-point)


def point_potential(current, sigma, r_obs, r_src=(0.0, 0.0, 0.0)):
    """eq-m01-point: phi = I / (4 pi sigma |r - r'|) for a point current source I in an infinite conductor."""
    d = np.asarray(r_obs, float) - np.asarray(r_src, float)
    return current / (4 * np.pi * sigma * np.linalg.norm(d, axis=-1))


def sources_potential(currents, positions, sigma, r_obs):
    """Superposition of point sources (currents in relative units, positions (n, 3) in mm)."""
    r_obs = np.asarray(r_obs, float)
    return sum(point_potential(i, sigma, r_obs, p) for i, p in zip(currents, np.asarray(positions, float)))


def flux_through_sphere(current, sigma, radius, n=200):
    """Total current sigma * (outward E) integrated over a sphere around the source, by quadrature (should be I)."""
    th = (np.arange(n) + 0.5) * np.pi / n
    ph = (np.arange(2 * n) + 0.5) * np.pi / n
    T, P = np.meshgrid(th, ph, indexing="ij")
    # radial field of a point source: E = I / (4 pi sigma r^2)
    e_r = current / (4 * np.pi * sigma * radius ** 2)
    dA = radius ** 2 * np.sin(T) * (np.pi / n) * (np.pi / n)
    return float(np.sum(sigma * e_r * dA))


# ---------------------------------------------------------------- dipoles (eq-m01-dipole)


def dipole_potential(p, sigma, r_obs, r0=(0.0, 0.0, 0.0)):
    """eq-m01-dipole: phi = p . (r - r0) / (4 pi sigma |r - r0|^3) for a current dipole moment p (current x length)."""
    d = np.asarray(r_obs, float) - np.asarray(r0, float)
    r = np.linalg.norm(d, axis=-1)
    return np.sum(np.asarray(p, float) * d, axis=-1) / (4 * np.pi * sigma * r ** 3)


def pair_potential(current, sep, sigma, r_obs):
    """A source +I at (0, 0, sep/2) and a sink -I at (0, 0, -sep/2): the dipole p = I sep along z, before the limit."""
    return sources_potential([current, -current], [(0, 0, sep / 2), (0, 0, -sep / 2)], sigma, r_obs)


def falloff_exponent(r, phi):
    """Local slope of log|phi| against log r: -1 for a monopole, -2 for a dipole."""
    return np.gradient(np.log(np.abs(phi)), np.log(r))


# ---------------------------------------------------------------- double layers (eq-m01-double-layer)


def disk_solid_angle_axis(radius, z):
    """Solid angle of a disk of the given radius seen from height z on its axis: 2 pi (1 - |z| / sqrt(z^2 + R^2)),
    signed by the side (positive on the side the layer's positive face points to, +z)."""
    z = np.asarray(z, float)
    return np.sign(z) * 2 * np.pi * (1 - np.abs(z) / np.sqrt(z ** 2 + radius ** 2))


def disk_solid_angle(radius, x, z):
    """Signed solid angle of a disk (radius R, in the plane z = 0, centered at the origin) seen from (x, 0, z), by
    quadrature of the exact integral z / |r - r'|^3 over the disk (polar coordinates)."""
    if z == 0:
        return 0.0 if abs(x) > radius else np.nan

    def inner(rho):
        f = lambda t: z / ((x - rho * np.cos(t)) ** 2 + (rho * np.sin(t)) ** 2 + z ** 2) ** 1.5
        return integrate.quad(f, 0, 2 * np.pi, limit=200)[0] * rho

    return integrate.quad(inner, 0, radius, limit=200)[0]


def double_layer_potential(tau, sigma, solid_angle):
    """eq-m01-double-layer: phi = tau Omega / (4 pi sigma) for a uniform double layer of strength tau (dipole moment
    per unit area)."""
    return tau * np.asarray(solid_angle, float) / (4 * np.pi * sigma)


def disk_dipole_sum(radius, tau, sigma, x, z, n=400):
    """The same potential computed directly as a sum of small dipoles tau dA (pointing +z) over the disk."""
    rho = (np.arange(n) + 0.5) * radius / n
    th = (np.arange(2 * n) + 0.5) * np.pi / n
    R, T = np.meshgrid(rho, th, indexing="ij")
    pts = np.stack([R * np.cos(T), R * np.sin(T), np.zeros_like(R)], -1)
    dA = R * (radius / n) * (np.pi / n)
    obs = np.array([x, 0.0, z])
    d = obs - pts
    r = np.linalg.norm(d, axis=-1)
    return float(np.sum(tau * dA * d[..., 2] / (4 * np.pi * sigma * r ** 3)))


# ---------------------------------------------------------------- the wavefront (eq-m01-core, eq-m01-front-dipole)


def front_vm(s, w, delta_v=1.0):
    """The m03 arctangent front: V_m(s) = dV (1/2 - arctan(s / w) / pi); s > 0 is tissue not yet reached."""
    return delta_v * (0.5 - np.arctan(np.asarray(s, float) / w) / np.pi)


def front_im(s, w, delta_v=1.0, beta=1.0):
    """eq-m01-core: i_m = beta d2V_m/ds2 = (2 beta dV / pi) w s / (s^2 + w^2)^2; outward (source) ahead, inward
    (sink) behind."""
    s = np.asarray(s, float)
    return beta * delta_v * 2 * w * s / (np.pi * (s ** 2 + w ** 2) ** 2)


def axial_current(s, w, delta_v=1.0, beta=1.0):
    """eq-m01-core: I_i = -beta dV_m/ds, the intracellular current along the strand (positive toward +s)."""
    s = np.asarray(s, float)
    return beta * delta_v * w / (np.pi * (s ** 2 + w ** 2))


def net_current(s, i_m):
    """Total membrane current of a profile (zero for a front: every source has its sink)."""
    return float(np.trapezoid(i_m, s))


def dipole_moment(s, i_m):
    """First moment of the membrane current, p = integral s i_m ds (equals beta dV for any front shape)."""
    return float(np.trapezoid(np.asarray(s) * i_m, s))


def line_dipole_potential(p, sigma, s, h):
    """eq-m01-front-dipole: a line of dipoles (moment p per unit length, along +s, in the plane z = 0) seen from height
    h: phi = p s / (2 pi sigma (s^2 + h^2))."""
    s = np.asarray(s, float)
    return p * s / (2 * np.pi * sigma * (s ** 2 + h ** 2))


def front_potential(s, w, h, delta_v=1.0, beta=1.0, sigma=1.0):
    """The m03 unipolar closed form, U = A s / (s^2 + (w + h)^2) with A = beta dV / (2 pi sigma)."""
    return unipolar(s, w + h, beta * delta_v / (2 * np.pi * sigma))


def front_potential_quadrature(s_obs, w, h, delta_v=1.0, beta=1.0, sigma=1.0, half=4000.0, n=800001):
    """Direct check: sum the field of every line source i_m(x) dx at height h (2-D Green's function
    -ln(r) / (2 pi sigma)). Returns the potential at each s_obs (relative to the far field)."""
    x = np.linspace(-half, half, n)
    dx = x[1] - x[0]
    im = front_im(x, w, delta_v, beta)
    out = []
    for s0 in np.atleast_1d(s_obs):
        r2 = (s0 - x) ** 2 + h ** 2
        out.append(-np.sum(im * np.log(r2) / 2) * dx / (2 * np.pi * sigma))
    return np.array(out)
