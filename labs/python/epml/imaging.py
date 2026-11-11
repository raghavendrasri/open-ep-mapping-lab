"""Segmentation metrics, closed-form checks and synthetic atria for m40 (AI for cardiac imaging).

Equations (module m40):
  eq-m40-jaccard    Dice = 2J / (1 + J)
  eq-m40-hausdorff  Hausdorff distance between two surfaces (and its percentile form)
  eq-m40-assd       average symmetric surface distance
  eq-m40-nsd        normalized surface Dice at tolerance tau
  eq-m40-offset     Dice after a uniform boundary offset: 1 - |delta| S / (2 V) to first order
  eq-m40-sphere     exact Dice of concentric spheres
  eq-m40-slab       exact Dice of a shifted wall
  eq-m40-cindex     Harrell's concordance index

Surface distances are computed on voxel surfaces (boundary voxels, 6-connectivity) with Euclidean
distance transforms that respect the voxel spacing. Conventions differ between toolkits (surface
voxels or mesh faces, percentile per direction or pooled); the choices here are stated in each
function. Units: mm for lengths, mm^3 for volumes.
"""

import numpy as np
from scipy import ndimage as ndi

# --------------------------------------------------------------------------------------------
# Overlap


def dice(a, b):
    """Dice coefficient of two boolean masks; 1.0 when both are empty."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    s = a.sum() + b.sum()
    return 1.0 if s == 0 else 2.0 * np.logical_and(a, b).sum() / s


def jaccard(a, b):
    """Jaccard index (intersection over union) of two boolean masks; 1.0 when both are empty."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    u = np.logical_or(a, b).sum()
    return 1.0 if u == 0 else np.logical_and(a, b).sum() / u


def dice_from_jaccard(j):
    """eq-m40-jaccard: Dice = 2J / (1 + J)."""
    j = np.asarray(j, float)
    return 2 * j / (1 + j)


# --------------------------------------------------------------------------------------------
# Surfaces and surface distances

_FACE = ndi.generate_binary_structure(3, 1)


def surface(mask):
    """Boundary voxels: voxels of the mask with at least one face neighbour outside it.
    The volume edge counts as outside."""
    mask = np.asarray(mask, bool)
    if mask.ndim == 2:
        st = ndi.generate_binary_structure(2, 1)
    else:
        st = ndi.generate_binary_structure(mask.ndim, 1)
    inner = ndi.binary_erosion(mask, structure=st, border_value=0)
    return mask & ~inner


def surface_distances(a, b, spacing=None):
    """Directed distances (mm) from each surface voxel of a to the nearest surface voxel of b,
    and from b to a. Returns (d_ab, d_ba). Both masks must be non-empty."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if spacing is None:
        spacing = (1.0,) * a.ndim
    sa, sb = surface(a), surface(b)
    if not sa.any() or not sb.any():
        raise ValueError("surface distances need two non-empty masks")
    dt_b = ndi.distance_transform_edt(~sb, sampling=spacing)
    dt_a = ndi.distance_transform_edt(~sa, sampling=spacing)
    return dt_b[sa], dt_a[sb]


def hausdorff(a, b, spacing=None, percentile=100.0):
    """eq-m40-hausdorff. percentile=100 gives the Hausdorff distance; 95 gives HD95, here the larger
    of the two directed 95th percentiles (one common convention; others pool both directions)."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    return float(max(np.percentile(d_ab, percentile), np.percentile(d_ba, percentile)))


def assd(a, b, spacing=None):
    """eq-m40-assd: average symmetric surface distance, every surface voxel weighted equally."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    return float((d_ab.sum() + d_ba.sum()) / (d_ab.size + d_ba.size))


def nsd(a, b, tau, spacing=None):
    """eq-m40-nsd: share of both surfaces lying within tau (mm) of the other surface. This counts
    surface voxels; the definition used by challenges weights mesh surface elements by area."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    return float(((d_ab <= tau).sum() + (d_ba <= tau).sum()) / (d_ab.size + d_ba.size))


def offset_mask(mask, delta, spacing=None):
    """Grow (delta > 0) or shrink (delta < 0) a mask by |delta| mm.

    Uses a signed distance to the voxel boundary: centre-to-centre distance transforms minus half the
    smallest voxel size, so that a voxel layer counts as lying half a voxel inside the surface. On a
    grid the offset is quantized to whole voxel layers."""
    mask = np.asarray(mask, bool)
    if spacing is None:
        spacing = (1.0,) * mask.ndim
    half = 0.5 * min(spacing)
    if delta >= 0:
        return mask | (ndi.distance_transform_edt(~mask, sampling=spacing) - half <= delta)
    return ndi.distance_transform_edt(mask, sampling=spacing) - half > -delta


# --------------------------------------------------------------------------------------------
# Closed forms


def sphere_dice(R, delta):
    """eq-m40-sphere: Dice of concentric spheres of radii R and R + delta (delta > -R)."""
    R, delta = np.asarray(R, float), np.asarray(delta, float)
    r2 = R + delta
    return 2 * np.minimum(R, r2) ** 3 / (R**3 + r2**3)


def disc_dice(R, delta):
    """Two-dimensional counterpart of eq-m40-sphere: concentric discs of radii R and R + delta."""
    R, delta = np.asarray(R, float), np.asarray(delta, float)
    r2 = R + delta
    return 2 * np.minimum(R, r2) ** 2 / (R**2 + r2**2)


def cylinder_dice(r, delta):
    """Concentric cylinders of equal length (a vein seen along its axis): the disc formula."""
    return disc_dice(r, delta)


def slab_dice(t, delta):
    """eq-m40-slab: a wall of thickness t shifted by delta along its normal: max(0, 1 - |delta|/t)."""
    t, delta = np.asarray(t, float), np.asarray(delta, float)
    return np.clip(1 - np.abs(delta) / t, 0, 1)


def offset_dice_first_order(delta, area, volume):
    """eq-m40-offset: Dice ~ 1 - |delta| S / (2 V) for a uniform offset delta of a smooth body with
    surface area S and volume V."""
    return 1 - np.abs(delta) * area / (2 * volume)


# --------------------------------------------------------------------------------------------
# Survival models: Harrell's concordance index


def cindex(time, event, risk):
    """eq-m40-cindex: share of comparable pairs ordered correctly by the risk score.

    A pair (i, j) is comparable when time_i < time_j and patient i had the event. It is concordant
    when risk_i > risk_j; ties in risk count one half. Pairs with equal times are not compared."""
    time, event, risk = (np.asarray(x, float) for x in (time, event, risk))
    event = event.astype(bool)
    num = den = 0.0
    for i in np.flatnonzero(event):
        later = time > time[i]
        n = later.sum()
        if n == 0:
            continue
        den += n
        num += (risk[i] > risk[later]).sum() + 0.5 * (risk[i] == risk[later]).sum()
    if den == 0:
        raise ValueError("no comparable pairs")
    return num / den


# --------------------------------------------------------------------------------------------
# Synthetic atria (illustrative shapes and intensities, not anatomy from any data set)


def _capsule(X, Y, Z, p0, p1, r):
    """Points within r of the segment p0-p1."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    v = p1 - p0
    w = np.stack([X - p0[0], Y - p0[1], Z - p0[2]], -1)
    t = np.clip((w @ v) / (v @ v), 0, 1)
    d = w - t[..., None] * v
    return (d**2).sum(-1) <= r**2


def synth_atrium(rng, shape=(64, 64, 48), spacing=(1.5, 1.5, 1.5), noise=0.25, bias=0.3):
    """One synthetic case: an ellipsoidal body, four veins and an appendage (label), a bright
    neighbour that is not atrium (a distractor), a smooth intensity bias and noise.

    Returns (image, label, info). Every size and intensity is illustrative."""
    nx, ny, nz = shape
    X, Y, Z = np.meshgrid(*(np.arange(n) * s for n, s in zip(shape, spacing)), indexing="ij")
    c = np.array([nx * spacing[0] / 2, ny * spacing[1] / 2, nz * spacing[2] / 2])
    c = c + rng.normal(0, 2.0, 3)
    a = rng.uniform(18, 24), rng.uniform(15, 20), rng.uniform(13, 17)   # semi-axes, mm (illustrative)
    body = ((X - c[0]) / a[0]) ** 2 + ((Y - c[1]) / a[1]) ** 2 + ((Z - c[2]) / a[2]) ** 2 <= 1
    label = body.copy()
    veins = np.zeros_like(body)
    for sx in (-1, 1):            # left and right veins
        for sz in (-1, 1):        # superior and inferior
            start = c + np.array([sx * 0.55 * a[0], 0.55 * a[1], sz * 0.45 * a[2]])
            end = start + np.array([sx * rng.uniform(8, 14), rng.uniform(10, 16), sz * rng.uniform(2, 6)])
            veins |= _capsule(X, Y, Z, start, end, rng.uniform(4.0, 6.0))
    app = _capsule(X, Y, Z, c + np.array([0.8 * a[0], -0.4 * a[1], 0.3 * a[2]]),
                   c + np.array([1.15 * a[0], -0.75 * a[1], 0.45 * a[2]]), rng.uniform(4.0, 5.5))
    label |= veins | app
    distractor = _capsule(X, Y, Z, c + np.array([-0.2 * a[0], -1.6 * a[1], -0.9 * a[2]]),
                          c + np.array([0.3 * a[0], -1.6 * a[1], 1.2 * a[2]]), rng.uniform(7, 9)) & ~label
    img = np.where(label, 1.0, 0.25) + np.where(distractor, 0.75, 0.0)
    img = ndi.gaussian_filter(img, 0.8)                                     # partial volume
    g = np.linspace(-1, 1, nx)[:, None, None] * rng.uniform(-1, 1) + np.linspace(-1, 1, nz)[None, None, :] * rng.uniform(-1, 1)
    img = img * (1 + bias * g / 2) + rng.normal(0, noise, shape)
    info = {"centre": c, "semi_axes": a, "veins": veins & ~body, "appendage": app & ~body,
            "body": body, "distractor": distractor, "spacing": spacing}
    return img.astype(np.float32), label, info


def local_features(img, sigmas=(1.0, 2.0)):
    """Per-voxel features: intensity, Gaussian-smoothed intensity and gradient magnitude at each
    scale (in voxels), Laplacian of Gaussian at the largest scale. Shape (n_voxels, n_features)."""
    feats = [img]
    for s in sigmas:
        feats.append(ndi.gaussian_filter(img, s))
        feats.append(ndi.gaussian_gradient_magnitude(img, s))
    feats.append(ndi.gaussian_laplace(img, max(sigmas)))
    return np.stack([f.ravel() for f in feats], axis=1)


def largest_component(mask):
    """Keep the largest face-connected component of a boolean mask."""
    lab, n = ndi.label(mask, structure=_FACE if np.asarray(mask).ndim == 3 else None)
    if n == 0:
        return np.zeros_like(mask, bool)
    sizes = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def surface_area_voxels(mask, spacing):
    """Surface area (mm^2) of a voxelized object counted as exposed voxel faces. On curved surfaces
    this overestimates the true area (about 1.5 times for a sphere), so use it for comparisons."""
    mask = np.asarray(mask, bool)
    area = 0.0
    for ax in range(mask.ndim):
        face = np.prod([s for i, s in enumerate(spacing) if i != ax])
        pad = np.pad(mask, [(1, 1) if i == ax else (0, 0) for i in range(mask.ndim)])
        area += face * np.count_nonzero(np.diff(pad.astype(np.int8), axis=ax))
    return area


def circle_island_metrics(R, delta, rho, gap, tau, n=3600):
    """Metrics for the two-dimensional picture of m40-d1, from closed forms and the midpoint rule.

    True region: disc of radius R. Prediction: a concentric disc of radius R + delta, plus (if rho > 0)
    a separate island disc of radius rho whose nearest edge lies `gap` beyond the outer of the two main
    contours. Surface distances are taken between the contours (circles), weighted by arc length.
    Returns dict with dice, hd, assd and nsd (at tolerance tau)."""
    R, delta, rho, gap = float(R), float(delta), float(rho), float(gap)
    Rp = R + delta
    if Rp <= 0:
        raise ValueError("R + delta must be positive")
    phi = (np.arange(n) + 0.5) * 2 * np.pi / n
    dice_v = 2 * min(R, Rp) ** 2 / (R**2 + Rp**2 + rho**2)
    ad = abs(delta)
    len_main, len_T = 2 * np.pi * Rp, 2 * np.pi * R
    if rho > 0:
        c = R + max(delta, 0.0) + gap + rho
        d_isl = np.hypot(c + rho * np.cos(phi), rho * np.sin(phi)) - R          # island -> true contour
        d_T = np.minimum(ad, np.hypot(R * np.cos(phi) - c, R * np.sin(phi)) - rho)  # true -> prediction
        len_isl = 2 * np.pi * rho
    else:
        d_isl = np.zeros(0)
        d_T = np.full(n, ad)
        len_isl = 0.0
    total = len_main + len_isl + len_T
    hd = max(ad, d_isl.max() if d_isl.size else 0.0, d_T.max())
    s = len_main * ad + (len_isl * d_isl.mean() if d_isl.size else 0.0) + len_T * d_T.mean()
    within = len_main * (ad <= tau) + (len_isl * np.mean(d_isl <= tau) if d_isl.size else 0.0) + len_T * np.mean(d_T <= tau)
    return {"dice": float(dice_v), "hd": float(hd), "assd": float(s / total), "nsd": float(within / total)}


def ball(shape, centre, radius, spacing=None):
    """Boolean mask of voxels whose centres lie within radius (mm) of centre (mm)."""
    if spacing is None:
        spacing = (1.0,) * len(shape)
    grids = np.meshgrid(*(np.arange(n) * s for n, s in zip(shape, spacing)), indexing="ij")
    return sum((g - c) ** 2 for g, c in zip(grids, centre)) <= radius**2
