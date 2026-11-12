"""m48 · Imaging across the EP workflow: one vocabulary for every modality (blur, contrast, noise) and the
accuracy of imaging tests. MIT License.

Sources for default values: CT section-sensitivity FWHM of 0.34 and 0.64 mm on a photon-counting system
(Rajendran et al. 2022); LGE resolution of 1.5-2 mm routinely and about 1 mm for thin walls (Kellman and Arai 2012);
clinical PET resolution of 4-7 mm FWHM (Kinahan and Fletcher 2010); left atrial wall thickness (Beinart et al. 2011,
through epml.ct); accuracy of CT for left atrial appendage thrombus against TEE (Romero et al. 2013). Contrasts,
noise levels, the phantom's geometry and the simulated meta-analysis are illustrative."""
import numpy as np
from scipy import ndimage as ndi
from scipy.special import erf, erfinv

from .ct import LA_WALL_MM, fwhm_thickness, slab_peak, slab_profile, threshold_thickness  # noqa: F401
from .ml import predictive_values

FWHM_PER_SIGMA = 2.0 * np.sqrt(2.0 * np.log(2.0))

# Published resolutions, in mm, read as the FWHM of a Gaussian blur (a simplification: real point-spread functions
# are not Gaussian, and MRI voxel size is not exactly a FWHM).
RESOLUTION_MM = {
    "CT, photon-counting, thinnest section, high-resolution mode": 0.34,   # Rajendran et al. 2022
    "CT, photon-counting, thinnest section, standard mode": 0.64,         # Rajendran et al. 2022
    "MRI LGE, thin-wall protocol": 1.0,                                   # Kellman and Arai 2012
    "MRI LGE, routine (finer end)": 1.5,                                  # Kellman and Arai 2012
    "MRI LGE, routine (coarser end)": 2.0,                                # Kellman and Arai 2012
    "PET, clinical (best case)": 4.0,                                     # Kinahan and Fletcher 2010
    "PET, clinical (coarser end)": 7.0,                                   # Kinahan and Fletcher 2010
}

# CT against TEE for left atrial appendage thrombus: 19 studies, 2,955 patients, thrombus in 8.9% (Romero et al.
# 2013). Each accuracy measure was pooled across studies separately.
ROMERO2013 = {
    "studies": 19,
    "patients": 2955,
    "prevalence": 0.089,
    "standard": {"se": 0.96, "sp": 0.92, "ppv": 0.41, "npv": 0.99},
    "delayed imaging": {"se": 1.00, "sp": 0.99, "ppv": 0.92, "npv": 1.00},
}


# ---------------------------------------------------------------- blur (eq-m48-psf)


def sigma_from_fwhm(fwhm):
    """sigma = FWHM / (2 sqrt(2 ln 2))."""
    return np.asarray(fwhm, float) / FWHM_PER_SIGMA


def fwhm_from_sigma(sigma):
    return np.asarray(sigma, float) * FWHM_PER_SIGMA


def gaussian_psf(x, sigma):
    """eq-m48-psf: h(x) = exp(-x^2 / (2 sigma^2)) / (sqrt(2 pi) sigma), unit area."""
    x = np.asarray(x, float)
    return np.exp(-x ** 2 / (2 * sigma ** 2)) / (np.sqrt(2 * np.pi) * sigma)


def measured_fwhm(x, y):
    """Full width at half maximum of a sampled single-peaked profile, with linear interpolation at both edges."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    half = y.max() / 2
    above = np.nonzero(y >= half)[0]
    i0, i1 = above[0], above[-1]
    left = np.interp(half, [y[i0 - 1], y[i0]], [x[i0 - 1], x[i0]])
    right = np.interp(half, [y[i1 + 1], y[i1]], [x[i1 + 1], x[i1]])
    return right - left


def two_point_profile(x, d, sigma):
    """Two equal point sources a distance d apart, each blurred by the PSF."""
    x = np.asarray(x, float)
    return gaussian_psf(x - d / 2, sigma) + gaussian_psf(x + d / 2, sigma)


def critical_separation(sigma):
    """eq-m48-psf: the blurred pair shows a dip between the peaks only if d > 2 sigma (= FWHM / sqrt(2 ln 2))."""
    return 2.0 * np.asarray(sigma, float)


def dip_depth(d, sigma):
    """Depth of the dip between two blurred points, 1 - f(0) / max f (0 when there is no dip)."""
    x = np.linspace(-d / 2 - 4 * sigma, d / 2 + 4 * sigma, 4001)
    f = two_point_profile(x, d, sigma)
    return float(max(0.0, 1.0 - two_point_profile(0.0, d, sigma) / f.max()))


# ---------------------------------------------------------------- contrast and noise (eq-m48-cnr)


def cnr(signal_a, signal_b, noise):
    """eq-m48-cnr: |S_A - S_B| / sigma_n."""
    return np.abs(np.asarray(signal_a, float) - np.asarray(signal_b, float)) / np.asarray(noise, float)


def cnr_averaged(cnr_single, n):
    """eq-m48-cnr: averaging n independent samples divides the noise by sqrt(n)."""
    return np.asarray(cnr_single, float) * np.sqrt(n)


def measured_cnr(region_a, region_b):
    """CNR of two image regions: difference of means over the pooled standard deviation."""
    a, b = np.ravel(region_a), np.ravel(region_b)
    pooled = np.sqrt(0.5 * (a.var(ddof=1) + b.var(ddof=1)))
    return abs(a.mean() - b.mean()) / pooled


def smoothed_noise(noise, pixel, sigma_s):
    """eq-m48-smooth: white noise of standard deviation `noise` on a 2-D grid of spacing `pixel`, smoothed by a unit
    -area Gaussian of standard deviation sigma_s, keeps sigma_n pixel / (2 sqrt(pi) sigma_s) (sigma_s >> pixel)."""
    return np.asarray(noise, float) * pixel / (2.0 * np.sqrt(np.pi) * np.asarray(sigma_s, float))


def smoothed_noise_exact(noise, pixel, sigma_s, half=None):
    """The same quantity from the discrete kernel: sigma_n sqrt(sum h_ij^2), with the sampled kernel normalized."""
    s = sigma_s / pixel
    half = half or int(np.ceil(6 * s))
    k = np.arange(-half, half + 1)
    g = np.exp(-k ** 2 / (2 * s ** 2))
    g /= g.sum()
    return noise * np.sqrt(np.sum(np.outer(g, g) ** 2))


def wall_cnr(contrast, noise, width, sigma):
    """eq-m48-visibility: CNR at the center of a blurred wall, (C / sigma_n) erf(w / (2 sqrt 2 sigma))."""
    return np.asarray(contrast, float) / noise * erf(np.asarray(width, float) / (2 * np.sqrt(2) * sigma))


def min_visible_wall(contrast, noise, sigma, k):
    """eq-m48-visibility: thinnest wall reaching CNR k, 2 sqrt(2) sigma erfinv(k sigma_n / C); infinite if even a
    thick wall (CNR C / sigma_n) falls short."""
    r = k * noise / contrast
    return np.inf if r >= 1 else float(2 * np.sqrt(2) * sigma * erfinv(r))


def smoothed_wall_cnr(contrast, noise, width, sigma, pixel, sigma_s):
    """eq-m48-smooth with eq-m48-visibility: smoothing by sigma_s widens the blur to sqrt(sigma^2 + sigma_s^2) and
    divides the white noise by 2 sqrt(pi) sigma_s / pixel."""
    sigma_s = np.asarray(sigma_s, float)
    total = np.sqrt(sigma ** 2 + sigma_s ** 2)
    return contrast * erf(width / (2 * np.sqrt(2) * total)) / smoothed_noise(noise, pixel, sigma_s)


# ---------------------------------------------------------------- accuracy of an imaging test (eq-m48-lr)


def likelihood_ratios(se, sp):
    """eq-m48-lr: LR+ = Se / (1 - Sp), LR- = (1 - Se) / Sp."""
    se, sp = np.asarray(se, float), np.asarray(sp, float)
    with np.errstate(divide="ignore"):
        return se / (1 - sp), (1 - se) / sp


def post_test_probability(pretest, lr):
    """eq-m48-lr: post-test odds = pre-test odds x LR."""
    odds = np.asarray(pretest, float) / (1 - np.asarray(pretest, float)) * lr
    return odds / (1 + odds)


def ppv_npv(se, sp, prevalence):
    """eq-m35-ppv, from epml.ml."""
    return predictive_values(se, sp, prevalence)


def simulate_pooled_ppv(se, sp, prevalences, patients, rng):
    """Illustrative meta-analysis: studies with the same Se and Sp but different prevalence, each with `patients`
    patients. Returns the per-study PPVs, their mean, and the PPV the formula gives at the mean prevalence."""
    ppvs = []
    for pi in prevalences:
        disease = rng.random(patients) < pi
        positive = np.where(disease, rng.random(patients) < se, rng.random(patients) > sp)
        if positive.sum():
            ppvs.append(np.sum(positive & disease) / positive.sum())
    ppvs = np.array(ppvs)
    return ppvs, float(ppvs.mean()), float(predictive_values(se, sp, float(np.mean(prevalences)))[0])


# ---------------------------------------------------------------- a cross-section through the posterior wall


def wall_phantom(pixel=0.05, width=1.89, gap=2.0, esophagus_wall=3.0, size=(16.0, 24.0)):
    """A 2-D label map across the posterior left atrial wall: blood (1) above, the atrial wall (2), a fat gap (0),
    the esophageal wall (3) and its lumen (0) below. The wall runs along x; y is depth in mm, with the atrial wall
    centered at y = 0. Wall thickness defaults to the mean in Beinart et al. 2011; the gap and the esophageal wall
    are illustrative. Returns (labels, y coordinates of the rows)."""
    ny, nx = int(round(size[1] / pixel)), int(round(size[0] / pixel))
    y = (np.arange(ny) - (ny - 1) / 2) * pixel
    rows = np.zeros(ny, int)
    rows[y >= width / 2] = 1
    rows[np.abs(y) < width / 2] = 2
    lo = -width / 2 - gap
    rows[(y < lo) & (y >= lo - esophagus_wall)] = 3
    return np.repeat(rows[:, None], nx, axis=1), y


def image(labels, values, fwhm, noise, pixel, rng):
    """Image a label map: assign a signal to each label, blur by a Gaussian of the given FWHM (mm), then add white
    noise of standard deviation `noise` per pixel."""
    obj = np.zeros(labels.shape)
    for lab, v in values.items():
        obj[labels == lab] = v
    blurred = ndi.gaussian_filter(obj, float(sigma_from_fwhm(fwhm)) / pixel, mode="nearest")
    return blurred + rng.normal(0.0, noise, labels.shape)


def depth_profile(img):
    """Average the image along the wall (x) to get a profile in depth."""
    return img.mean(axis=1)


def separated(profile, y, width, gap, esophagus_wall=3.0, tol=0.01):
    """True if the depth profile has a dip between the atrial wall and the esophageal wall: a local minimum strictly
    inside the gap, at least `tol` below the lower of the two walls' peaks."""
    wall = np.abs(y) < width / 2
    top = -width / 2 - gap
    esoph = (y < top) & (y >= top - esophagus_wall)
    idx = np.nonzero((y >= top - esophagus_wall) & (y < width / 2))[0]
    i_min = idx[int(np.argmin(profile[idx]))]
    in_gap = (y[i_min] < -width / 2) and (y[i_min] > top)
    depth = min(profile[wall].max(), profile[esoph].max()) - profile[i_min]
    return bool(in_gap and depth > tol)


def wall_above_blood(profile, y, width, blood_level):
    """How far the blurred wall's peak rises above the blood signal next to it (0 or less: the wall is lost in the
    blood)."""
    return float(profile[np.abs(y) < width / 2].max() - blood_level)
