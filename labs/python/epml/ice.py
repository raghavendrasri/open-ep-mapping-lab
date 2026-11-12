"""m50 · Intracardiac echocardiography: the ultrasound essentials an ICE catheter needs (pulse-echo ranging,
axial resolution, attenuation, phased-array steering, frame rate), a small delay-and-sum simulator, and a 3-D
shell from tracked 2-D contours. MIT License.

Sources for default values: the 1540 m/s speed of sound that scanners assume (Zhang et al. 2026); ICE imaging
frequencies of 7.5-10 MHz (Morton et al. 2003); myocardial attenuation slopes of 0.52 and 1.88 dB/(cm MHz)
across and along the fibers (Baldwin et al. 2007). Everything else (pulse length, element count, depth, number of
lines, phantom shapes) is illustrative."""
import numpy as np

C_ASSUMED = 1540.0                      # m/s, the value scanners assume when they turn time into depth
ICE_FREQ_MHZ = (7.5, 10.0)              # imaging frequencies reported for phased-array ICE (Morton et al. 2003)
MYOCARDIUM_DB_PER_CM_MHZ = {"across fibers": 0.52, "along fibers": 1.88}   # Baldwin et al. 2007, fresh tissue

# ---------------------------------------------------------------- ranging (eq-m50-range)


def depth_from_time(t_s, c=C_ASSUMED):
    """eq-m50-range: an echo that returns after t seconds came from depth z = c t / 2 (meters)."""
    return c * np.asarray(t_s, float) / 2.0


def displayed_depth(true_depth, c_true, c_assumed=C_ASSUMED):
    """Depth the scanner shows for a reflector at true_depth when sound actually travels at c_true:
    the echo time is 2 z / c_true, converted back with c_assumed, so z_shown = z c_assumed / c_true."""
    return np.asarray(true_depth, float) * c_assumed / c_true


# ---------------------------------------------------------------- axial resolution (eq-m50-axial)


def wavelength_mm(freq_mhz, c=C_ASSUMED):
    """lambda = c / f in millimeters (c in m/s, f in MHz)."""
    return c / (np.asarray(freq_mhz, float) * 1e6) * 1e3


def axial_resolution_mm(freq_mhz, cycles, c=C_ASSUMED):
    """eq-m50-axial: half the spatial pulse length, n lambda / 2."""
    return cycles * wavelength_mm(freq_mhz, c) / 2.0


def pulse(t, freq_hz, cycles):
    """A tone burst of exactly `cycles` periods with a Hann window, centered on t = 0 (zero outside
    |t| <= cycles / (2 f)). The burst shape is illustrative; its length is what sets axial resolution."""
    t = np.asarray(t, float)
    half = cycles / (2.0 * freq_hz)
    w = np.where(np.abs(t) <= half, 0.5 * (1 + np.cos(np.pi * t / half)), 0.0)
    return w * np.cos(2 * np.pi * freq_hz * t)


def a_line(depths_mm, amplitudes, freq_mhz, cycles, fs_hz=200e6, max_depth_mm=40.0, c=C_ASSUMED):
    """Radio-frequency echo signal of point reflectors at depths (mm): each echo is the burst centered on its
    round-trip time 2 z / c. Returns (depth axis in mm, signal)."""
    t = np.arange(0, 2 * max_depth_mm * 1e-3 / c, 1 / fs_hz)
    s = np.zeros_like(t)
    for z, a in zip(depths_mm, amplitudes):
        s += a * pulse(t - 2 * z * 1e-3 / c, freq_mhz * 1e6, cycles)
    return depth_from_time(t, c) * 1e3, s


def envelope(signal):
    """Magnitude of the analytic signal (Hilbert transform)."""
    from scipy.signal import hilbert

    return np.abs(hilbert(signal))


def echo_extent_mm(depth_mm, signal):
    """First and last depth (mm) where an echo signal is non-zero."""
    nz = np.flatnonzero(np.abs(signal) > 0)
    return float(depth_mm[nz[0]]), float(depth_mm[nz[-1]])


def echoes_overlap(z1_mm, z2_mm, freq_mhz, cycles, fs_hz=500e6, c=C_ASSUMED):
    """Simulate the two echoes separately and report whether their non-zero stretches overlap in depth."""
    zmax = max(z1_mm, z2_mm) + 5.0
    d, s1 = a_line([z1_mm], [1.0], freq_mhz, cycles, fs_hz, zmax, c)
    _, s2 = a_line([z2_mm], [1.0], freq_mhz, cycles, fs_hz, zmax, c)
    a1, b1 = echo_extent_mm(d, s1)
    a2, b2 = echo_extent_mm(d, s2)
    return bool(min(b1, b2) >= max(a1, a2))


# ---------------------------------------------------------------- attenuation (eq-m50-attenuation)


def round_trip_loss_db(alpha_db_cm_mhz, freq_mhz, depth_cm):
    """eq-m50-attenuation: a linear-in-frequency attenuation alpha (dB per cm per MHz) costs
    2 alpha f z decibels on the way out and back."""
    return 2.0 * alpha_db_cm_mhz * np.asarray(freq_mhz, float) * np.asarray(depth_cm, float)


def max_depth_cm(budget_db, alpha_db_cm_mhz, freq_mhz):
    """Depth at which the round-trip loss uses up a signal budget of budget_db decibels."""
    return budget_db / (2.0 * alpha_db_cm_mhz * freq_mhz)


# ---------------------------------------------------------------- steering (eq-m50-steer)


def element_positions(n, pitch):
    """x positions of n elements with spacing `pitch`, centered on 0."""
    return (np.arange(n) - (n - 1) / 2.0) * pitch


def steering_delays(n, pitch, theta_rad, c=C_ASSUMED):
    """eq-m50-steer: transmit delays tau_k = x_k sin(theta) / c, shifted so the earliest is 0 (seconds)."""
    tau = element_positions(n, pitch) * np.sin(theta_rad) / c
    return tau - tau.min()


def array_factor(theta_rad, n, pitch_over_lambda, steer_rad):
    """Normalized far-field array factor of n equal elements spaced pitch_over_lambda wavelengths apart and
    steered to steer_rad: |sum_k exp(i 2 pi k d (sin theta - sin theta0) / lambda)| / n."""
    u = np.sin(np.asarray(theta_rad, float)) - np.sin(steer_rad)
    k = np.arange(n)[:, None]
    return np.abs(np.exp(2j * np.pi * k * pitch_over_lambda * u[None, :]).sum(axis=0)) / n


def grating_lobes_deg(pitch_over_lambda, steer_rad):
    """Angles (degrees) of grating lobes: sin(theta) = sin(theta0) + m lambda / d for integers m != 0 with
    |sin(theta)| <= 1."""
    out = []
    m_max = int(np.ceil(2 * pitch_over_lambda)) + 1
    for m in range(-m_max, m_max + 1):
        if m == 0:
            continue
        s = np.sin(steer_rad) + m / pitch_over_lambda
        if abs(s) <= 1:
            out.append(float(np.degrees(np.arcsin(s))))
    return sorted(out)


def first_null_offset(n, pitch_over_lambda):
    """Distance in sin(theta) from the main lobe to its first null: lambda / (n d)."""
    return 1.0 / (n * pitch_over_lambda)


# ---------------------------------------------------------------- frame rate (eq-m50-frame-rate)


def frame_rate(depth_m, n_lines, c=C_ASSUMED):
    """eq-m50-frame-rate: each line waits for echoes from depth D (time 2 D / c), so a frame of N lines takes
    2 D N / c and the frame rate is c / (2 D N)."""
    return c / (2.0 * depth_m * n_lines)


# ---------------------------------------------------------------- delay-and-sum imaging


def simulate_channels(scatterers, amplitudes, n, pitch, freq_mhz, cycles, fs_hz=60e6, max_depth_m=0.06,
                      c=C_ASSUMED):
    """Received radio-frequency signals on each of n elements for point scatterers (x, z in meters) after a
    single unfocused transmit from the array center (a simplification: real systems focus each transmit).
    Returns (time axis, channels of shape (n, len(t)))."""
    t = np.arange(0, 2 * max_depth_m / c, 1 / fs_hz)
    xs = element_positions(n, pitch)
    ch = np.zeros((n, t.size))
    for (x, z), a in zip(scatterers, amplitudes):
        d_tx = np.hypot(x, z)
        for k, xe in enumerate(xs):
            d_rx = np.hypot(x - xe, z)
            ch[k] += a * pulse(t - (d_tx + d_rx) / c, freq_mhz * 1e6, cycles) / max(d_rx, 1e-3)
    return t, ch


def das_sector(t, ch, n, pitch, angles_rad, radii_m, c=C_ASSUMED):
    """Delay-and-sum beamforming onto a polar grid: for each pixel, sum each channel at the transmit-plus-receive
    travel time. Returns the envelope image (len(angles), len(radii))."""
    from scipy.signal import hilbert

    xs = element_positions(n, pitch)
    analytic = hilbert(ch, axis=1)
    fs = 1.0 / (t[1] - t[0])
    img = np.zeros((len(angles_rad), len(radii_m)), complex)
    for i, th in enumerate(angles_rad):
        px, pz = radii_m * np.sin(th), radii_m * np.cos(th)
        d_tx = np.hypot(px, pz)
        for k, xe in enumerate(xs):
            idx = (d_tx + np.hypot(px - xe, pz)) / c * fs
            i0 = np.clip(idx.astype(int), 0, t.size - 2)
            w = idx - i0
            img[i] += (1 - w) * analytic[k, i0] + w * analytic[k, i0 + 1]
    return np.abs(img)


def septum_scatterers(tent_mm=0.0, fossa_halfwidth_mm=6.0, depth_mm=25.0, half_length_mm=15.0, spacing_mm=0.4,
                      tent_width_mm=4.0):
    """Point scatterers along a synthetic interatrial septum seen face-on at depth_mm: a straight line whose
    central part (the fossa) is pushed away from the probe by a Gaussian tent of height tent_mm (a sheath tip
    pressing on it). All sizes are illustrative. Returns (points in meters, amplitudes)."""
    x = np.arange(-half_length_mm, half_length_mm + 1e-9, spacing_mm)
    z = depth_mm + tent_mm * np.exp(-(x**2) / (2 * tent_width_mm**2))
    amp = np.where(np.abs(x) < fossa_halfwidth_mm, 0.5, 1.0)     # a thinner fossa reflects less (illustrative)
    return np.c_[x, z] * 1e-3, amp


def peak_depth_on_axis(img, radii_m, angles_rad):
    """Depth (mm) of the brightest echo on the line closest to straight ahead."""
    i = int(np.argmin(np.abs(angles_rad)))
    return float(radii_m[int(np.argmax(img[i]))] * 1e3)


# ---------------------------------------------------------------- shell from tracked planes


def ellipsoid_contours(n_planes, semi_axes_mm=(25.0, 20.0, 30.0), points_per_contour=60, noise_mm=0.0, rng=None):
    """Contours of an ellipsoidal chamber cut by n_planes imaging planes that rotate about the z axis (the
    catheter axis), as a tracked ICE catheter turned in steps would see them. Returns an (N, 3) point cloud."""
    rng = np.random.default_rng() if rng is None else rng
    a, b, c = semi_axes_mm
    pts = []
    for phi in np.linspace(0, np.pi, n_planes, endpoint=False):
        u = np.array([np.cos(phi), np.sin(phi), 0.0])
        r_in_plane = 1.0 / np.sqrt((u[0] / a) ** 2 + (u[1] / b) ** 2)       # semi-axis along u
        s = np.linspace(0, 2 * np.pi, points_per_contour, endpoint=False)
        for si in s:
            p = r_in_plane * np.cos(si) * u + np.array([0, 0, c * np.sin(si)])
            pts.append(p + noise_mm * rng.normal(size=3))
    return np.array(pts)


def distance_to_ellipsoid(points, semi_axes_mm=(25.0, 20.0, 30.0)):
    """First-order distance from each point to the ellipsoid surface: |F(p)| / |grad F(p)| with
    F(p) = sum (p_i / a_i)^2 - 1. Accurate for points close to the surface."""
    a = np.asarray(semi_axes_mm, float)
    p = np.asarray(points, float)
    f = ((p / a) ** 2).sum(axis=1) - 1.0
    g = np.linalg.norm(2 * p / a**2, axis=1)
    return np.abs(f) / g


def largest_gap_mm(n_planes, semi_axes_mm=(25.0, 20.0, 30.0)):
    """Planes rotating about the catheter axis by pi / n_planes leave, at the widest part of the chamber, an
    unsampled arc of at most pi * max(a, b) / n_planes between neighboring planes."""
    a, b, _ = semi_axes_mm
    return np.pi * max(a, b) / n_planes
