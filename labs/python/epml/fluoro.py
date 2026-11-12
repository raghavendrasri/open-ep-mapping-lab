"""m49 · Fluoroscopy and radiation protection: attenuation, projection images of a phantom, quantum noise,
dose quantities, staff dose and reference levels. MIT License.

Attenuation data: NIST Standard Reference Database 126 (Hubbell and Seltzer), mass attenuation coefficients at
60 keV and the densities NIST lists, read from the NIST tables on 2026-11-11. A single photon energy is a
simplification chosen for teaching: real fluoroscopy beams are polyenergetic. Phantom sizes, photon counts,
pulse rates and staff positions are illustrative."""
import numpy as np

KEV = 60.0
# material: (mass attenuation coefficient mu/rho in cm^2/g at 60 keV, density in g/cm^3), NIST SRD 126.
MATERIALS = {
    "soft tissue": (0.2048, 1.06),     # Tissue, Soft (ICRU-44)
    "blood": (0.2057, 1.06),           # Blood, Whole (ICRU-44)
    "adipose": (0.1974, 0.95),         # Adipose Tissue (ICRU-44)
    "cortical bone": (0.3148, 1.92),   # Bone, Cortical (ICRU-44)
    "platinum": (4.339, 21.45),        # Pt, Z = 78
}


def mu_per_mm(material):
    """Linear attenuation coefficient in 1/mm: (mu/rho) * rho, converted from 1/cm."""
    mass, rho = MATERIALS[material]
    return mass * rho / 10.0


# ---------------------------------------------------------------- attenuation (eq-m49-beer)


def transmission(mu, length):
    """eq-m49-beer for a uniform path: I/I0 = exp(-mu L), mu in 1/mm and L in mm."""
    return np.exp(-np.asarray(mu, float) * np.asarray(length, float))


def half_value_layer(mu):
    """Thickness that halves a narrow monoenergetic beam: ln 2 / mu."""
    return np.log(2.0) / mu


def subject_contrast(mu_object, mu_background, thickness):
    """eq-m49-contrast: C = 1 - exp(-(mu_o - mu_b) t), the fractional drop in transmitted intensity behind an
    object of thickness t embedded in background material (negative if the object attenuates less)."""
    return 1.0 - np.exp(-(mu_object - mu_background) * thickness)


# ---------------------------------------------------------------- quantum noise (eq-m49-cnr)


def cnr(contrast, photons):
    """eq-m49-cnr: with Poisson counts N in the background, CNR = (N_b - N_o) / sqrt(N_b) = C sqrt(N)."""
    return np.asarray(contrast, float) * np.sqrt(photons)


def photons_for_cnr(contrast, target):
    """Background photons per pixel needed for a target CNR: (target / C)^2."""
    return (target / np.asarray(contrast, float)) ** 2


# ---------------------------------------------------------------- a projection phantom


class Ellipsoid:
    """An axis-aligned ellipsoid (centre and semi-axes in mm) filled with one material; `parent` is the
    material it displaces, so that nested objects add only their difference in attenuation."""

    def __init__(self, name, centre, axes, material, parent=None):
        self.name, self.centre, self.axes = name, np.asarray(centre, float), np.asarray(axes, float)
        self.material, self.parent = material, parent

    def delta_mu(self):
        return mu_per_mm(self.material) - (mu_per_mm(self.parent) if self.parent else 0.0)

    def chord(self, x, z):
        """Length of the ray parallel to y through (x, z): 2 b sqrt(1 - (dx/a)^2 - (dz/c)^2), or 0."""
        a, b, c = self.axes
        q = 1.0 - ((np.asarray(x, float) - self.centre[0]) / a) ** 2 - ((np.asarray(z, float) - self.centre[2]) / c) ** 2
        return 2.0 * b * np.sqrt(np.clip(q, 0.0, None))

    def inside(self, x, y, z):
        a, b, c = self.axes
        return (((x - self.centre[0]) / a) ** 2 + ((y - self.centre[1]) / b) ** 2 + ((z - self.centre[2]) / c) ** 2) <= 1.0


def chest_phantom(n_electrodes=4, spacing=5.0, electrode_length=2.0, electrode_radius=1.2):
    """A thorax-like phantom for an anterior-posterior view (all sizes illustrative): a soft-tissue body, a
    blood-filled heart, a cortical-bone spine behind it, and platinum ring electrodes of a catheter in the heart
    (each modelled as a short ellipsoid). x is left-right, y is the beam direction, z is head-foot (mm)."""
    parts = [
        Ellipsoid("body", (0, 0, 0), (160, 110, 200), "soft tissue"),
        Ellipsoid("heart", (15, -10, 10), (55, 45, 60), "blood", parent="soft tissue"),
        Ellipsoid("spine", (0, 75, 0), (18, 18, 190), "cortical bone", parent="soft tissue"),
    ]
    for k in range(n_electrodes):
        z = -10.0 + k * spacing
        parts.append(Ellipsoid(f"electrode {k + 1}", (20, -10, z), (electrode_radius, electrode_radius, electrode_length / 2),
                               "platinum", parent="blood"))
    return parts


def line_integral(phantom, x, z):
    """Exact line integral of mu along y for each (x, z): sum of (mu - mu_parent) * chord length."""
    x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
    total = np.zeros(x.shape)
    for part in phantom:
        total += part.delta_mu() * part.chord(x, z)
    return total


def line_integral_voxels(phantom, x, z, step=0.25, y_range=(-120.0, 120.0)):
    """The same integral by marching along y through the phantom on a grid (a numerical check)."""
    ys = np.arange(y_range[0] + step / 2, y_range[1], step)
    x, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(z, float))
    total = np.zeros(x.shape)
    for part in phantom:
        inside = part.inside(x[..., None], ys, z[..., None])
        total += part.delta_mu() * inside.sum(axis=-1) * step
    return total


def projection(phantom, x, z, photons, rng=None):
    """Detected counts per pixel: Poisson with mean photons * exp(-line integral). Without rng, the mean."""
    mean = photons * np.exp(-line_integral(phantom, x, z))
    return mean if rng is None else rng.poisson(mean).astype(float)


# ---------------------------------------------------------------- dose quantities (eq-m49-kap, eq-m49-staff)


def kerma_at(kerma_ref, d_ref, d):
    """Inverse-square law for air kerma along the beam: K(d) = K(d_ref) (d_ref / d)^2."""
    return kerma_ref * (d_ref / np.asarray(d, float)) ** 2


def field_area_at(area_ref, d_ref, d):
    """A diverging beam's cross-section grows as the square of distance from the focal spot."""
    return area_ref * (np.asarray(d, float) / d_ref) ** 2


def kerma_area_product(kerma, area):
    """eq-m49-kap: P_KA = K * A, the same at every distance along the beam."""
    return kerma * area


def shield_transmission(thickness_in_hvl):
    """Transmission through a shield of the given thickness in half-value layers: 2^(-n)."""
    return 2.0 ** (-np.asarray(thickness_in_hvl, float))


def relative_staff_dose(distance_m, minutes, shield_hvl=0.0, pulse_rate=15.0, dose_per_pulse=1.0,
                        reference=(1.0, 10.0, 0.0, 15.0, 1.0)):
    """eq-m49-staff: scattered dose to a person treated as a point source at the patient, relative to a
    reference setting (distance m, minutes, shield HVLs, pulses per second, relative dose per pulse). The
    reference values are illustrative."""
    def h(d, t, s, f, q):
        return f * q * t * shield_transmission(s) / np.asarray(d, float) ** 2
    return h(distance_m, minutes, shield_hvl, pulse_rate, dose_per_pulse) / h(*reference)


# ---------------------------------------------------------------- reference levels


def pooled_reference_level(values, q=75.0):
    """A reference level as the third quartile of all recorded values, as in the French survey (Greffier et
    al. 2026), which also reported medians."""
    return float(np.percentile(np.asarray(values, float), q))


def facility_median_reference_level(values_by_facility, q=75.0):
    """A national reference level as the 75th percentile of facility medians, as in the Swiss update (Samara
    et al. 2026)."""
    return float(np.percentile([np.median(v) for v in values_by_facility], q))


def synthetic_dose_logs(n_facilities, patients, median_kap, spread_between, spread_within, rng):
    """Kerma-area products (Gy cm^2) for n_facilities, each with `patients` procedures: log-normal within a
    facility around a facility median that is itself log-normal around median_kap. All values illustrative."""
    medians = median_kap * np.exp(spread_between * rng.normal(size=n_facilities))
    return [m * np.exp(spread_within * rng.normal(size=patients)) for m in medians]


# ---------------------------------------------------------------- pulse rate and motion


def sampled_position_error(amplitude_mm, heart_rate_hz, pulse_rate, duration_s=10.0, fine_hz=2000.0):
    """Largest distance between a catheter tip moving as amplitude * sin(2 pi f t) and the position shown on the
    last frame (each frame held until the next). An illustrative model of what a lower pulse rate costs."""
    t = np.arange(0.0, duration_s, 1.0 / fine_hz)
    x = amplitude_mm * np.sin(2 * np.pi * heart_rate_hz * t)
    held = x[(np.floor(t * pulse_rate) / pulse_rate * fine_hz).astype(int)]
    return float(np.max(np.abs(x - held)))
