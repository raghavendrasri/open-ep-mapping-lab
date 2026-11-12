"""m51 · Cardiac CT for EP: Hounsfield units from tabulated attenuation, the Radon transform and filtered
back-projection, quantum noise, the gating window and motion blur, how thin walls look, and wall thickness and
esophagus distance on a synthetic left atrium. MIT License.

Attenuation data: NIST Standard Reference Database 126 (Hubbell and Seltzer) at one photon energy, 60 keV, the
same energy as m49 (epml.fluoro). Water (liquid, density 1.000 g/cm^3) 0.2059 cm^2/g and iodine 7.579 cm^2/g were
read from the NIST tables on 2026-11-11; the tissues come from epml.fluoro. Real CT beams are polyenergetic, so
clinical Hounsfield values differ from these monoenergetic ones. Phantom shapes, the iodine concentration in the
blood, rotation times other than the cited ones, wall thicknesses other than the cited range, and photon counts
are illustrative."""
import numpy as np
from scipy.special import erf

from .fluoro import MATERIALS as _TISSUES

WATER_MASS_ATT = 0.2059      # cm^2/g at 60 keV, NIST SRD 126, Water, Liquid (density 1.000 g/cm^3)
IODINE_MASS_ATT = 7.579      # cm^2/g at 60 keV, NIST SRD 126, Iodine (Z = 53)

# Gating sources (PubMed): single-source 125 ms and dual-source 66 ms at 0.25 s rotation (Mergen et al. 2023);
# dual-source 83 ms at 0.33 s, "a quarter of the gantry rotation time" (Petersilka et al. 2008).
GATING_REPORTED = [(0.25, 1, 0.125), (0.25, 2, 0.066), (0.33, 2, 0.083)]
# In-plane coronary artery speed, mm/s, by electron-beam CT in 25 patients (Achenbach et al. 2000).
CORONARY_SPEED = {"left anterior descending": 22.4, "slowest phase (48% of the cycle)": 27.9,
                  "all three arteries": 46.6, "left circumflex": 48.4, "right coronary": 69.5}
# Left atrial wall thickness on CT: mean 1.89 mm, range 0.5 to 3.5 mm (Beinart et al. 2011).
LA_WALL_MM = {"mean": 1.89, "min": 0.5, "max": 3.5}


def mu_per_mm(material):
    """Linear attenuation coefficient (1/mm) at 60 keV: water, air (taken as 0) or an epml.fluoro tissue."""
    if material == "water":
        return WATER_MASS_ATT * 1.0 / 10.0
    if material == "air":
        return 0.0
    mass, rho = _TISSUES[material]
    return mass * rho / 10.0


# ---------------------------------------------------------------- Hounsfield units (eq-m51-hu, eq-m51-iodine)


def hounsfield(mu, mu_water=None, mu_air=0.0):
    """eq-m51-hu: HU = 1000 (mu - mu_water) / (mu_water - mu_air). Air's attenuation is about a thousandth of
    water's and is taken as 0 here, so air maps to -1000."""
    mw = mu_per_mm("water") if mu_water is None else mu_water
    return 1000.0 * (np.asarray(mu, float) - mw) / (mw - mu_air)


def mu_from_hu(hu, mu_water=None):
    mw = mu_per_mm("water") if mu_water is None else mu_water
    return mw * (1.0 + np.asarray(hu, float) / 1000.0)


def iodine_hu_per_mg_ml(mu_water=None):
    """eq-m51-iodine: attenuation adds by mass, so c mg/mL of iodine adds c * 1e-3 g/cm^3 * 7.579 cm^2/g per cm,
    which is 1000 * c * 1e-3 * 7.579 / mu_water(1/cm) Hounsfield units. Returns the HU per mg/mL."""
    mw_cm = (mu_per_mm("water") if mu_water is None else mu_water) * 10.0
    return 1000.0 * 1e-3 * IODINE_MASS_ATT / mw_cm


def blood_with_iodine_mu(conc_mg_ml):
    """Blood plus dissolved iodine (1/mm), assuming the iodine does not change the blood's own density."""
    return mu_per_mm("blood") + conc_mg_ml * 1e-3 * IODINE_MASS_ATT / 10.0


# ---------------------------------------------------------------- phantom and Radon transform (eq-m51-radon)


def thorax_phantom(contrast_mg_ml=10.0):
    """An axial slice through a synthetic thorax as ellipses (x0, y0, a, b, phi in degrees, delta-mu in 1/mm).
    Each ellipse adds its delta to whatever lies under it, so nested structures carry the difference from their
    parent and no two siblings overlap. Coordinates in mm: x toward the patient's left (shown on the right, as in
    radiology), y toward the front. The lungs are drawn as air (-1000 HU); inflated lung is denser. Shapes and the
    iodine concentration are illustrative."""
    tissue, fat, bone = mu_per_mm("soft tissue"), mu_per_mm("adipose"), mu_per_mm("cortical bone")
    blood = blood_with_iodine_mu(contrast_mg_ml)
    return [
        (0.0, 0.0, 150.0, 110.0, 0.0, tissue),               # body
        (-88.0, 10.0, 46.0, 72.0, 0.0, -tissue),             # right lung (air)
        (92.0, 10.0, 46.0, 72.0, 0.0, -tissue),              # left lung (air)
        (5.0, -5.0, 40.0, 72.0, 0.0, fat - tissue),          # mediastinal fat
        (10.0, 20.0, 34.0, 26.0, 30.0, tissue - fat),        # heart (myocardium)
        (14.0, 24.0, 21.0, 14.0, 30.0, blood - tissue),      # ventricular cavity, contrast-filled
        (0.0, -32.0, 24.5, 14.5, 0.0, tissue - fat),         # left atrial wall (2.5 mm here)
        (0.0, -32.0, 22.0, 12.0, 0.0, blood - tissue),       # left atrium, contrast-filled
        (-22.0, -58.0, 10.0, 10.0, 0.0, blood - fat),        # descending aorta
        (10.0, -56.0, 7.0, 6.0, 0.0, tissue - fat),          # esophagus
        (0.0, -92.0, 16.0, 13.0, 0.0, bone - tissue),        # vertebral body
    ]


def raster(phantom, n=256, fov=320.0, oversample=1):
    """Sample the phantom on an n x n grid covering fov mm (pixel centers; oversample > 1 averages
    oversample^2 points per pixel). Returns (image in 1/mm, x axis in mm). Rows run along y."""
    x = (np.arange(n) - (n - 1) / 2.0) * fov / n
    off = (np.arange(oversample) - (oversample - 1) / 2.0) * fov / n / oversample
    img = np.zeros((n, n))
    for dy in off:
        for dx in off:
            X, Y = np.meshgrid(x + dx, x + dy)
            for x0, y0, a, b, phi, v in phantom:
                c, s = np.cos(np.radians(phi)), np.sin(np.radians(phi))
                u = (X - x0) * c + (Y - y0) * s
                w = -(X - x0) * s + (Y - y0) * c
                img += v * ((u / a) ** 2 + (w / b) ** 2 <= 1.0)
    return img / oversample**2, x


def radon_ellipses(phantom, thetas_rad, s):
    """eq-m51-radon, exactly: along the line x cos(theta) + y sin(theta) = s an ellipse contributes its value times
    its chord, 2 a b sqrt(r^2 - (s - s0)^2) / r^2, with r^2 = a^2 cos^2(theta - phi) + b^2 sin^2(theta - phi) and
    s0 = x0 cos(theta) + y0 sin(theta). Returns a sinogram of shape (len(thetas), len(s))."""
    s = np.asarray(s, float)
    out = np.zeros((len(thetas_rad), s.size))
    for i, th in enumerate(thetas_rad):
        for x0, y0, a, b, phi, v in phantom:
            d = th - np.radians(phi)
            r2 = (a * np.cos(d)) ** 2 + (b * np.sin(d)) ** 2
            s0 = x0 * np.cos(th) + y0 * np.sin(th)
            q = r2 - (s - s0) ** 2
            out[i] += v * np.where(q > 0, 2 * a * b * np.sqrt(np.clip(q, 0, None)) / r2, 0.0)
    return out


def radon_image(img, x, thetas_rad, s):
    """A discrete check of eq-m51-radon: integrate the image along each line by sampling it every half pixel
    (bilinear interpolation). Independent of the analytic formula."""
    from scipy.ndimage import map_coordinates

    dx = x[1] - x[0]
    t = np.arange(x[0], x[-1] + dx / 2, dx / 2)
    out = np.zeros((len(thetas_rad), len(s)))
    for i, th in enumerate(thetas_rad):
        c, sn = np.cos(th), np.sin(th)
        for j, sj in enumerate(s):
            px, py = sj * c - t * sn, sj * sn + t * c
            vals = map_coordinates(img, [(py - x[0]) / dx, (px - x[0]) / dx], order=1, cval=0.0)
            out[i, j] = vals.sum() * (dx / 2)
    return out


def disk_projection_ft(k, radius):
    """eq-m51-slice for a unit disk: the 1-D Fourier transform of its projection 2 sqrt(R^2 - s^2) equals the 2-D
    transform of the disk on any radial line, R J1(2 pi R k) / k (value pi R^2 at k = 0)."""
    from scipy.special import j1

    k = np.asarray(k, float)
    safe = np.where(k == 0, 1.0, k)
    return np.where(k == 0, np.pi * radius**2, radius * j1(2 * np.pi * radius * safe) / safe)


def detector_axis(fov=320.0, n=256):
    """Detector bins one pixel wide that cover the image diagonal (an odd count, centered on 0)."""
    ds = fov / n
    half = int(np.ceil(fov * np.sqrt(2) / 2 / ds))
    return np.arange(-half, half + 1) * ds


# ---------------------------------------------------------------- filtered back-projection (eq-m51-fbp)


def ramlak_kernel(n_half, ds):
    """eq-m51-ramlak: the ramp |k| band-limited to the detector's Nyquist frequency 1/(2 ds), sampled at n ds:
    h[0] = 1/(4 ds^2), h[n] = -1/(pi^2 n^2 ds^2) for odd n, 0 for even n != 0. Returns h for n = -n_half..n_half."""
    n = np.arange(-n_half, n_half + 1)
    h = np.zeros(n.size)
    h[n == 0] = 1.0 / (4.0 * ds**2)
    odd = n % 2 != 0
    h[odd] = -1.0 / (np.pi**2 * n[odd].astype(float) ** 2 * ds**2)
    return h


def ramp_filter(sinogram, ds):
    """Convolve every projection with the Ram-Lak kernel (times ds, the discrete integral). The kernel is as long
    as the projection, so the result equals a linear convolution with no wrap-around."""
    n = sinogram.shape[1]
    h = ramlak_kernel(n - 1, ds)
    return np.array([np.convolve(p, h, mode="full")[n - 1:2 * n - 1] * ds for p in sinogram])


def backproject(sinogram, thetas_rad, s, x):
    """Smear each projection back along its lines and sum over the angles, times pi / (number of angles)."""
    X, Y = np.meshgrid(x, x)
    img = np.zeros_like(X)
    for i, th in enumerate(thetas_rad):
        img += np.interp(X * np.cos(th) + Y * np.sin(th), s, sinogram[i], left=0.0, right=0.0)
    return img * (np.pi / len(thetas_rad))


def fbp(sinogram, thetas_rad, s, x, filtered=True):
    """eq-m51-fbp: back-project ramp-filtered projections (filtered=False gives plain back-projection)."""
    sino = ramp_filter(sinogram, s[1] - s[0]) if filtered else sinogram
    return backproject(sino, thetas_rad, s, x)


def angles(n):
    """n projection angles spread evenly over 180 degrees (parallel beam)."""
    return np.arange(n) * np.pi / n


# ---------------------------------------------------------------- quantum noise (eq-m51-noise)


def noisy_sinogram(sinogram, photons, rng):
    """Poisson counts behind each ray from `photons` incident photons (m49), turned back into line integrals."""
    counts = rng.poisson(photons * np.exp(-sinogram))
    return -np.log(np.maximum(counts, 1) / photons)


def line_integral_variance(p, photons):
    """eq-m51-noise: Var(-ln(N / N0)) is about 1 / mean(N) = exp(p) / N0 (first-order, for large counts)."""
    return np.exp(np.asarray(p, float)) / photons


# ---------------------------------------------------------------- gating and motion (eq-m51-gating, eq-m51-smear)


def temporal_window(rotation_s, sources=1):
    """eq-m51-gating: a half-scan needs about half a rotation of data; with two tube-detector pairs 90 degrees
    apart, about a quarter. Window = rotation time / (2 x number of sources)."""
    return rotation_s / (2.0 * sources)


def motion_blur_mm(speed_mm_s, window_s):
    """A structure moving at constant in-plane speed smears over speed x window."""
    return speed_mm_s * window_s


def smeared_disk(x, y, diameter, blur):
    """eq-m51-smear: a disk of the given diameter moving along x by `blur` during the window, averaged over the
    window: the fraction of the window that the point (x, y) spends inside the disk."""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    c = np.sqrt(np.clip((diameter / 2) ** 2 - y**2, 0, None))
    if blur <= 0:
        return ((np.abs(x) <= c) & (c > 0)).astype(float)
    lo = np.maximum(x - blur / 2, -c)
    hi = np.minimum(x + blur / 2, c)
    return np.clip(hi - lo, 0, None) / blur


# ---------------------------------------------------------------- thin walls (eq-m51-wall)


def fwhm_to_sigma(fwhm):
    return fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))


def slab_profile(x, width, sigma):
    """eq-m51-wall: a wall of thickness `width` and unit contrast seen through a Gaussian blur of standard
    deviation sigma: 0.5 [erf((x + w/2) / (sqrt(2) sigma)) - erf((x - w/2) / (sqrt(2) sigma))]."""
    x = np.asarray(x, float)
    r = np.sqrt(2.0) * sigma
    return 0.5 * (erf((x + width / 2) / r) - erf((x - width / 2) / r))


def slab_peak(width, sigma):
    """Peak of the blurred wall: erf(w / (2 sqrt(2) sigma))."""
    return float(erf(width / (2.0 * np.sqrt(2.0) * sigma)))


def _half_width_at(level, width, sigma):
    lo, hi = 0.0, width / 2 + 10 * sigma
    for _ in range(80):
        mid = (lo + hi) / 2
        if slab_profile(mid, width, sigma) >= level:
            lo = mid
        else:
            hi = mid
    return lo


def threshold_thickness(width, sigma, level=0.5):
    """Thickness read from the blurred profile with a fixed threshold at `level` of the full contrast (0 if the
    peak never reaches it)."""
    if slab_peak(width, sigma) < level:
        return 0.0
    return 2 * _half_width_at(level, width, sigma)


def fwhm_thickness(width, sigma):
    """Thickness read as the full width at half of the profile's own peak: never below the blur's FWHM."""
    return 2 * _half_width_at(0.5 * slab_peak(width, sigma), width, sigma)


def step_window_width(sigma, lo, hi, left, right):
    """Width (mm) over which a blurred step from `left` to `right` (for example blood to fat, with no wall between)
    lies inside the window (lo, hi): the step is left + (right - left) (1 + erf(x / (sqrt 2 sigma))) / 2, so each
    crossing sits at sqrt(2) sigma erfinv(2 (v - left) / (right - left) - 1)."""
    from scipy.special import erfinv

    def cross(v):
        return np.sqrt(2.0) * sigma * erfinv(2.0 * (v - left) / (right - left) - 1.0)

    return float(abs(cross(hi) - cross(lo)))


# ---------------------------------------------------------------- a synthetic left atrium in 3-D


def atrium_volume(voxel=0.5, semi_axes=(25.0, 20.0, 22.0), wall=(1.0, 3.0), esophagus_gap=3.0,
                  blood_hu=400.0, wall_hu=None, fat_hu=None):
    """A contrast-filled ellipsoidal left atrium in fat. Its wall thickness, measured along rays from the center,
    varies smoothly from wall[0] mm at the back (-y) to wall[1] mm at the front (+y). An esophagus (a tube of
    radius 8 mm along z) runs behind the back wall, `esophagus_gap` mm from it. Values in HU; wall and fat from
    the 60 keV NIST values unless given. Shapes and the blood value are illustrative.
    Returns (volume indexed [x, y, z], axis in mm, dict of masks and the true thickness field)."""
    wall_hu = float(hounsfield(mu_per_mm("soft tissue"))) if wall_hu is None else wall_hu
    fat_hu = float(hounsfield(mu_per_mm("adipose"))) if fat_hu is None else fat_hu
    a, b, c = semi_axes
    ext = max(a, b, c) + wall[1] + esophagus_gap + 20.0
    x = np.arange(-ext, ext + voxel / 2, voxel)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")
    r = np.sqrt((X / a) ** 2 + (Y / b) ** 2 + (Z / c) ** 2)
    rho = np.sqrt(X**2 + Y**2 + Z**2)
    ang = np.arctan2(Y, X)
    thick = wall[0] + (wall[1] - wall[0]) * 0.5 * (1 + np.sin(ang))
    to_surface = rho / np.maximum(r, 1e-9)              # distance from the center to the blood surface on this ray
    blood = r <= 1.0
    outer = rho <= to_surface + thick
    wall_mask = outer & ~blood
    eso_y = -(b + wall[0] + esophagus_gap + 8.0)
    esophagus = ((X**2 + (Y - eso_y) ** 2) <= 8.0**2) & ~outer
    vol = np.full(X.shape, fat_hu)
    vol[wall_mask] = wall_hu
    vol[blood] = blood_hu
    vol[esophagus] = wall_hu
    return vol, x, {"blood": blood, "wall": wall_mask, "outer": outer, "esophagus": esophagus, "thickness": thick}


def blur_volume(vol, voxel, fwhm_mm):
    """Gaussian blur with the given full width at half maximum (the scanner's resolution, illustrative)."""
    from scipy.ndimage import gaussian_filter

    return gaussian_filter(vol, fwhm_to_sigma(fwhm_mm) / voxel, mode="nearest")


def downsample(vol, x, factor):
    """Average factor^3 blocks (partial volume): a coarser voxel of factor x the size."""
    n = (vol.shape[0] // factor) * factor
    v = vol[:n, :n, :n].reshape(n // factor, factor, n // factor, factor, n // factor, factor).mean(axis=(1, 3, 5))
    return v, x[:n].reshape(-1, factor).mean(axis=1)


def ray_thickness(mask, x, directions):
    """Wall thickness along rays from the center: the length of the first run of the ray inside the mask (mm),
    sampled every quarter voxel with nearest-voxel lookup. Later runs (for example the esophagus) are ignored."""
    dx = x[1] - x[0]
    t = np.arange(0, x[-1], dx / 4)
    out = []
    for d in directions:
        d = np.asarray(d, float) / np.linalg.norm(d)
        idx = np.rint((np.outer(t, d) - x[0]) / dx).astype(int)
        ok = np.all((idx >= 0) & (idx < mask.shape[0]), axis=1)
        hits = np.zeros(t.size, bool)
        hits[ok] = mask[idx[ok, 0], idx[ok, 1], idx[ok, 2]]
        first = np.flatnonzero(hits)
        if first.size == 0:
            out.append(0.0)
            continue
        after = np.flatnonzero(~hits[first[0]:])
        run = after[0] if after.size else hits.size - first[0]
        out.append(run * dx / 4)
    return np.array(out)


def sphere_directions(n, rng):
    """n random unit vectors, uniform on the sphere."""
    v = rng.normal(size=(n, 3))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def true_ray_thickness(directions, wall=(1.0, 3.0)):
    """The thickness atrium_volume builds along each ray (depends only on the in-plane angle)."""
    d = np.asarray(directions, float)
    ang = np.arctan2(d[:, 1], d[:, 0])
    return wall[0] + (wall[1] - wall[0]) * 0.5 * (1 + np.sin(ang))


def min_distance_mm(mask_a, mask_b, x):
    """Smallest distance (mm) from any voxel of mask_b to the region mask_a, by a Euclidean distance transform
    (voxel centers)."""
    from scipy.ndimage import distance_transform_edt

    d = distance_transform_edt(~mask_a, sampling=x[1] - x[0])
    return float(d[mask_b].min())
