"""m54 · Nuclear imaging in EP: radioactive decay and timing, the standardized uptake value (SUV), partial volume in
thin myocardium, partial-volume correction on a synthetic left ventricle with inflamed regions, and how test-retest
noise affects a serial-scan response rule. MIT License.

Sources for default values: the fluorine-18 half-life, 109.73 min (TUNL Nuclear Data Evaluation, recommended value
2019); the SUV definition, clinical PET resolution of 4-7 mm FWHM, about 10% test-retest variability and the effect
of clock errors (Kinahan and Fletcher 2010); the response rule, a decrease in lesion metabolic activity of at least
25% (Muser et al. 2018). Wall thickness, uptake values, lesion shapes and noise of the synthetic heart are
illustrative."""
import numpy as np
from scipy.special import erf
from scipy.stats import norm

F18_HALF_LIFE_MIN = 109.73          # TUNL recommended value (2019): 109.732 +/- 0.011 min
PET_FWHM_MM = (4.0, 7.0)            # best-case reconstructed resolution of clinical scanners (Kinahan and Fletcher 2010)
TEST_RETEST_CV = 0.10               # approximate test-retest variability of SUV (Kinahan and Fletcher 2010)
RESPONSE_DROP = 0.25                # response: LMA decrease of at least 25% (Muser et al. 2018)


# ---------------------------------------------------------------- decay (eq-m54-decay)


def decay_constant(half_life):
    return np.log(2.0) / half_life


def activity(a0, t, half_life=F18_HALF_LIFE_MIN):
    """eq-m54-decay: A(t) = A0 exp(-lambda t), lambda = ln 2 / T_half (t and T_half in the same unit)."""
    return a0 * np.exp(-decay_constant(half_life) * np.asarray(t, float))


def clock_error_bias(dt, half_life=F18_HALF_LIFE_MIN):
    """Relative SUV error when the decay correction uses a time that is off by dt: 2^(dt / T_half) - 1."""
    return 2.0 ** (np.asarray(dt, float) / half_life) - 1.0


# ---------------------------------------------------------------- standardized uptake value (eq-m54-suv)


def suv(conc_kbq_ml, injected_mbq, weight_kg, minutes_since_injection=0.0, residual_mbq=0.0,
        half_life=F18_HALF_LIFE_MIN):
    """eq-m54-suv: SUV = C / (A' / W), with C in kBq/mL, A' the net injected activity decay-corrected to the scan
    time, and W the body weight. MBq/kg equals kBq/g, and 1 mL of tissue is taken as 1 g, so SUV is dimensionless."""
    a = activity(injected_mbq - residual_mbq, minutes_since_injection, half_life)
    return np.asarray(conc_kbq_ml, float) / (a / weight_kg)


# ---------------------------------------------------------------- partial volume (eq-m54-recovery)


def fwhm_to_sigma(fwhm):
    return fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))


def slab_profile(x, width, sigma):
    """A slab of thickness w and unit uptake, blurred by a Gaussian of standard deviation sigma (as in m51)."""
    x = np.asarray(x, float)
    r = np.sqrt(2.0) * sigma
    return 0.5 * (erf((x + width / 2) / r) - erf((x - width / 2) / r))


def rc_peak(width, sigma):
    """eq-m54-recovery: recovery of the maximum, erf(w / (2 sqrt 2 sigma))."""
    return float(erf(width / (2.0 * np.sqrt(2.0) * sigma)))


def rc_mean(width, sigma):
    """eq-m54-recovery: recovery of the mean over the true slab, erf(b) - (1 - exp(-b^2)) / (b sqrt(pi)),
    with b = w / (sqrt 2 sigma)."""
    b = width / (np.sqrt(2.0) * sigma)
    return float(erf(b) - (1.0 - np.exp(-b * b)) / (b * np.sqrt(np.pi)))


# ---------------------------------------------------------------- a synthetic left ventricle


def lv_phantom(pixel=1.0, radius=25.0, wall=10.0, background=1.0, myocardium=2.0, lesions=((40.0, 30.0, 6.0),),
               half=50.0):
    """A short-axis slice of the left ventricle: a ring of myocardium (inner radius `radius`, thickness `wall`) in a
    uniform background, with inflamed arcs [(center angle deg, arc width deg, uptake)] across the full wall. Values
    are SUV-like and all illustrative. Returns (image, x axis, masks dict)."""
    x = np.arange(-half, half + pixel / 2, pixel)
    X, Y = np.meshgrid(x, x)
    r = np.hypot(X, Y)
    ang = np.degrees(np.arctan2(Y, X)) % 360
    ring = (r >= radius) & (r <= radius + wall)
    img = np.full(X.shape, background, float)
    img[ring] = myocardium
    lesion = np.zeros_like(ring)
    for center, width, value in lesions:
        d = np.abs((ang - center + 180) % 360 - 180)
        m = ring & (d <= width / 2)
        img[m] = value
        lesion |= m
    return img, x, {"ring": ring, "lesion": lesion}


def blur(img, pixel, fwhm):
    from scipy.ndimage import gaussian_filter

    return gaussian_filter(img, fwhm_to_sigma(fwhm) / pixel, mode="nearest")


def add_noise(img, cv, rng):
    """Multiplicative Gaussian noise with coefficient of variation cv (a stand-in for PET image noise)."""
    return img * (1.0 + cv * rng.normal(size=img.shape))


def lesion_stats(img, mask, rc=None, pixel=1.0):
    """SUVmax, SUVmean, partial-volume-corrected SUVmean (mean / rc) and lesion metabolic activity (corrected mean
    times area, in SUV mm^2 for this 2-D slice)."""
    vals = img[mask]
    mean = float(vals.mean())
    pvc = mean / rc if rc else mean
    return {"max": float(vals.max()), "mean": mean, "pvc_mean": pvc, "lma": pvc * mask.sum() * pixel**2}


# ---------------------------------------------------------------- serial scans and response (eq-m54-change)


def lognormal_sigma(cv):
    """Standard deviation of log(X) for a log-normal X with coefficient of variation cv."""
    return float(np.sqrt(np.log(1.0 + cv * cv)))


def p_called_responder(true_ratio, cv=TEST_RETEST_CV, drop=RESPONSE_DROP):
    """eq-m54-change: with independent log-normal noise of coefficient of variation cv on each scan, the measured
    log ratio is normal with mean log(true_ratio) and variance 2 sigma^2; the scan pair is called a response when the
    measured ratio is at most 1 - drop."""
    s = np.sqrt(2.0) * lognormal_sigma(cv)
    return norm.cdf((np.log(1.0 - drop) - np.log(np.asarray(true_ratio, float))) / s)


def simulate_called_responder(true_ratio, cv, rng, n=200000, drop=RESPONSE_DROP):
    s = lognormal_sigma(cv)
    m1 = np.exp(rng.normal(-s * s / 2, s, n))
    m2 = true_ratio * np.exp(rng.normal(-s * s / 2, s, n))
    return float(np.mean(m2 / m1 <= 1.0 - drop))
