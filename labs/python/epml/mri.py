"""m52 · Cardiac MRI for EP: the Larmor relation, inversion recovery from the Bloch equations, gadolinium and T1,
extracellular volume, choosing the inversion time for late gadolinium enhancement (LGE), and how much "fibrosis"
an atrial wall shows under different thresholds. MIT License.

Sources for default values: the proton gyromagnetic ratio from CODATA 2022 (NIST); relaxivity 4.5 L/(mmol s), the
dose example and native myocardial T1 of 950 ms from Kellman and Arai 2012; native and 10-minute post-contrast T1
and extracellular volume of remote myocardium and chronic infarct at 1.5 T from Bauner et al. 2012. Native blood
T1 and hematocrit, and every value of the synthetic atrial wall, are illustrative."""
import numpy as np

GAMMA_BAR_MHZ_PER_T = 42.577478461     # proton gyromagnetic ratio / 2 pi, CODATA 2022
RELAXIVITY = 4.5                        # L/(mmol s), r1 of gadolinium agents as given by Kellman and Arai 2012

# Bauner et al. 2012, 26 patients with chronic infarction, 1.5 T, MOLLI before and 10 min after contrast (means).
BAUNER = {"myocardium": {"t1_pre": 1001.0, "t1_post": 379.0, "ecv": 0.28},
          "infarct": {"t1_pre": 1159.0, "t1_post": 238.0, "ecv": 0.53}}

# Illustrative values (not from a cited source): native blood T1 at 1.5 T and hematocrit.
BLOOD_T1_PRE_ILLUSTRATIVE = 1600.0      # ms
HCT_ILLUSTRATIVE = 0.42

# Published thresholds for left atrial "fibrosis" or scar, as image intensity ratios (IIR) or blood-pool SDs.
THRESHOLDS = {
    "IIR 0.97 (Boyle et al. 2022, upper burden)": ("iir", 0.97),
    "IIR 1.2 (Boyle et al. 2022, lower burden)": ("iir", 1.2),
    "IIR 1.21 (Gunturiz-Beltrán et al. 2022, upper normal, right atrium)": ("iir", 1.21),
    "IIR 1.61 (Kamali et al. 2020)": ("iir", 1.61),
    "blood pool + 3.3 SD (Kamali et al. 2020)": ("sd", 3.3),
    "Otsu on the wall (Kamali et al. 2020)": ("otsu", None),
}


# ---------------------------------------------------------------- Larmor relation (eq-m52-larmor)


def larmor_mhz(b0_tesla):
    """eq-m52-larmor: precession frequency f = (gamma / 2 pi) B0, in MHz."""
    return GAMMA_BAR_MHZ_PER_T * np.asarray(b0_tesla, float)


# ---------------------------------------------------------------- inversion recovery (eq-m52-ir)


def ir_mz(t_ms, t1_ms, m0=1.0):
    """eq-m52-ir: after an ideal inversion at t = 0, Mz(t) = M0 (1 - 2 exp(-t / T1))."""
    return m0 * (1.0 - 2.0 * np.exp(-np.asarray(t_ms, float) / t1_ms))


def null_time(t1_ms):
    """eq-m52-ir: Mz crosses zero at TI = T1 ln 2."""
    return t1_ms * np.log(2.0)


def bloch_inversion(t1_ms, t2_ms, b1_ut=11.7, t_end_ms=2000.0, n_out=401):
    """Integrate the Bloch equations in the rotating frame, on resonance: a rectangular RF pulse along x of
    amplitude b1 (microtesla), long enough to rotate M by 180 degrees, then free relaxation. Returns (t in ms after
    the pulse ends, Mx, My, Mz) with M0 = 1. The pulse amplitude is illustrative; the result does not depend on it
    once the pulse is short compared with T1 and T2."""
    from scipy.integrate import solve_ivp

    gamma = 2 * np.pi * GAMMA_BAR_MHZ_PER_T * 1e6           # rad/(s T)
    w1 = gamma * b1_ut * 1e-6                                # rad/s
    t_pulse = np.pi / w1                                     # s
    r1, r2 = 1e3 / t1_ms, 1e3 / t2_ms

    def rhs(_, m, on):
        mx, my, mz = m
        w = w1 if on else 0.0
        # dM/dt = gamma M x B with B = (B1, 0, 0) in the rotating frame, plus relaxation
        return [-r2 * mx, w * mz - r2 * my, -w * my - r1 * (mz - 1.0)]

    p = solve_ivp(rhs, (0, t_pulse), [0.0, 0.0, 1.0], args=(True,), rtol=1e-10, atol=1e-12)
    t_out = np.linspace(0, t_end_ms * 1e-3, n_out)
    f = solve_ivp(rhs, (0, t_out[-1]), p.y[:, -1], args=(False,), t_eval=t_out, rtol=1e-10, atol=1e-12)
    return f.t * 1e3, f.y[0], f.y[1], f.y[2]


# ---------------------------------------------------------------- gadolinium and T1 (eq-m52-relaxivity, eq-m52-ecv)


def t1_with_gd(t1_native_ms, conc_mmol_l, r1=RELAXIVITY):
    """eq-m52-relaxivity: 1/T1 = 1/T1,native + r1 [Gd] (concentration in mmol/L, r1 in L/(mmol s))."""
    return 1e3 / (1e3 / t1_native_ms + r1 * np.asarray(conc_mmol_l, float))


def blood_concentration(dose_mmol_kg, blood_fraction_by_weight, blood_density_kg_l):
    """Initial concentration (mmol per liter of blood) if the dose mixes into the blood volume only: Kellman and
    Arai's example uses 0.15 mmol/kg, 8% blood by weight and 1.06 kg/L."""
    return dose_mmol_kg / (blood_fraction_by_weight / blood_density_kg_l)


def delta_r1(t1_pre_ms, t1_post_ms):
    """Change in relaxation rate, 1/s."""
    return 1e3 / t1_post_ms - 1e3 / t1_pre_ms


def ecv(t1_myo_pre, t1_myo_post, t1_blood_pre, t1_blood_post, hct):
    """eq-m52-ecv: gadolinium stays outside cells, so at equilibrium the change in R1 is proportional to the
    volume it can reach: ECV = (1 - Hct) dR1(myocardium) / dR1(blood)."""
    return (1.0 - hct) * delta_r1(t1_myo_pre, t1_myo_post) / delta_r1(t1_blood_pre, t1_blood_post)


def t1_post_from_ecv(t1_pre_ms, ecv_value, plasma_dr1):
    """Post-contrast T1 of a tissue whose extracellular fraction is ecv_value, when the plasma's change in R1 is
    plasma_dr1 (1/s): 1/T1 = 1/T1,pre + ecv * plasma_dr1. Blood is the case ecv_value = 1 - Hct."""
    return 1e3 / (1e3 / t1_pre_ms + ecv_value * plasma_dr1)


def blood_t1_post_illustrative():
    """Post-contrast blood T1 consistent with Bauner et al.'s remote myocardium (dR1 / ECV gives the plasma's dR1)
    and the illustrative native blood T1 and hematocrit."""
    m = BAUNER["myocardium"]
    plasma = delta_r1(m["t1_pre"], m["t1_post"]) / m["ecv"]
    return float(t1_post_from_ecv(BLOOD_T1_PRE_ILLUSTRATIVE, 1.0 - HCT_ILLUSTRATIVE, plasma))


# ---------------------------------------------------------------- choosing the inversion time (eq-m52-lge)


def lge_signal(ti_ms, t1_ms, magnitude=True):
    """Signal after inversion, ignoring the readout: |1 - 2 exp(-TI/T1)| for magnitude images, or the signed value
    that phase-sensitive reconstruction keeps."""
    s = ir_mz(ti_ms, t1_ms)
    return np.abs(s) if magnitude else s


def best_ti_signed(t1_myo_ms, t1_scar_ms):
    """eq-m52-lge: the signed difference 2 (exp(-TI/T1m) - exp(-TI/T1s)) peaks at
    TI* = ln(T1m / T1s) / (1/T1s - 1/T1m)."""
    return np.log(t1_myo_ms / t1_scar_ms) / (1.0 / t1_scar_ms - 1.0 / t1_myo_ms)


def scar_signal_at_null(t1_myo_ms, t1_scar_ms):
    """Scar signal when myocardium is nulled: |1 - 2^(1 - T1m/T1s)|."""
    return abs(1.0 - 2.0 ** (1.0 - t1_myo_ms / t1_scar_ms))


# ---------------------------------------------------------------- image intensity ratio and thresholds (eq-m52-iir)


def iir(wall, blood):
    """eq-m52-iir: each wall intensity divided by the mean blood-pool intensity."""
    return np.asarray(wall, float) / float(np.mean(blood))


def burden(iir_values, threshold):
    """Fraction of wall samples above the threshold."""
    return float(np.mean(np.asarray(iir_values) > threshold))


def otsu_threshold(values, bins=256):
    """Otsu's threshold: the cut between histogram bins that maximizes the between-class variance."""
    v = np.asarray(values, float).ravel()
    hist, edges = np.histogram(v, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2
    w = hist.astype(float) / hist.sum()
    w0 = np.cumsum(w)
    m = np.cumsum(w * centers)
    mt = m[-1]
    w1 = 1.0 - w0
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mt * w0 - m) ** 2 / (w0 * w1)
    between[~np.isfinite(between)] = -1.0
    k = int(np.argmax(between))
    return float(edges[k + 1])


def threshold_for(method, kind_value, wall_iir, blood_norm):
    """The IIR threshold a method implies: a fixed IIR, the blood-pool mean plus k SD (in IIR units), or Otsu."""
    kind, value = kind_value
    if kind == "iir":
        return float(value)
    if kind == "sd":
        return float(1.0 + value * np.std(blood_norm))
    if kind == "otsu":
        return otsu_threshold(wall_iir)
    raise ValueError(method)


def _smooth_field(rng, shape, sigma):
    from scipy.ndimage import gaussian_filter

    f = gaussian_filter(rng.normal(size=shape), sigma, mode="wrap")
    return (f - f.mean()) / f.std()


def synthetic_wall(rng, shape=(60, 120), fibrosis_fraction=0.15, normal_mean=0.9, normal_sd=0.155,
                   fibrosis_mean=1.5, noise_sd=0.12, blood_sd=0.12, n_blood=4000, patch_sigma=4.0):
    """An unwrapped left atrial wall (rows: up the wall, columns: around it) with smooth fibrotic patches.
    Intensities are IIR-like: the blood pool has mean 1. Normal wall has mean 0.9 and SD 0.155 (so mean + 2 SD is
    1.21, the upper normal IIR of Gunturiz-Beltrán et al. 2022, measured in the right atrium at 3 T); every other
    value is illustrative. Returns a dict with the true fibrosis mask, the noiseless wall, and one scan."""
    field = _smooth_field(rng, shape, patch_sigma)
    truth = field > np.quantile(field, 1.0 - fibrosis_fraction)
    tissue = normal_mean + normal_sd * _smooth_field(rng, shape, 1.0)
    clean = np.where(truth, fibrosis_mean + 0.1 * _smooth_field(rng, shape, 1.0), tissue)
    return {"truth": truth, "clean": clean, **scan(rng, clean, noise_sd, blood_sd, n_blood)}


def scan(rng, clean, noise_sd=0.12, blood_sd=0.12, n_blood=4000, gain=1.0):
    """One acquisition of the same wall: independent noise on wall and blood, and an optional gain that scales both
    (normalization by the blood pool removes it)."""
    wall = gain * (clean + noise_sd * rng.normal(size=clean.shape))
    blood = gain * (1.0 + blood_sd * rng.normal(size=n_blood))
    return {"wall": wall, "blood": blood}


# ---------------------------------------------------------------- real images: blood-pool normalization


def shell_iir(img, label, spacing, shell_mm=(0.0, 3.0), erode_vox=1):
    """Blood-pool normalization on a real volume: the blood pool is the label eroded by erode_vox voxels; the
    'wall' is a shell of voxels between shell_mm[0] and shell_mm[1] mm outside the label (a stand-in for the wall,
    which the label does not contain). Returns (IIR of the shell voxels, blood-pool mean, number of blood voxels)."""
    from scipy.ndimage import binary_erosion, distance_transform_edt

    lab = np.asarray(label, bool)
    pool = binary_erosion(lab, iterations=erode_vox) if erode_vox else lab
    d = distance_transform_edt(~lab, sampling=spacing)
    shell = (d > shell_mm[0]) & (d <= shell_mm[1])
    img = np.asarray(img, float)
    mean_blood = float(img[pool].mean())
    return img[shell] / mean_blood, mean_blood, int(pool.sum())


def crop_to_label(img, label, spacing, margin_mm=10.0):
    """Crop a volume and its label to the label's bounding box plus a margin in mm (to speed up distance maps)."""
    idx = np.argwhere(np.asarray(label, bool))
    m = np.ceil(margin_mm / np.asarray(spacing, float)).astype(int)
    lo = np.maximum(idx.min(0) - m, 0)
    hi = np.minimum(idx.max(0) + m + 1, np.shape(label))
    box = tuple(slice(a, b) for a, b in zip(lo, hi))
    return np.asarray(img)[box], np.asarray(label)[box]

