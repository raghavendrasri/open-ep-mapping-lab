"""m40 equation tests: segmentation metrics, closed forms, the concordance index and the MSD loader."""

import hashlib
import io
import itertools
import tarfile

import numpy as np
import pytest
import sympy as sp

from epml import data
from epml import imaging as im


ball = im.ball


def test_dice_jaccard_relation():
    """eq-m40-jaccard on random masks, and its inverse J = D / (2 - D) symbolically."""
    rng = np.random.default_rng(0)
    for _ in range(20):
        a, b = rng.random((10, 10, 10)) < 0.4, rng.random((10, 10, 10)) < 0.6
        assert im.dice(a, b) == pytest.approx(im.dice_from_jaccard(im.jaccard(a, b)))
    J, D = sp.symbols("J D", positive=True)
    assert sp.simplify(sp.solve(sp.Eq(D, 2 * J / (1 + J)), J)[0] - D / (2 - D)) == 0
    assert im.dice(np.zeros(3, bool), np.zeros(3, bool)) == 1.0


def test_hausdorff_of_shifted_boxes_is_the_shift():
    """eq-m40-hausdorff: two boxes shifted by k voxels along x (anisotropic voxels) are k * dx apart."""
    spacing = (0.7, 1.0, 1.3)
    a = np.zeros((40, 30, 30), bool)
    a[5:25, 5:25, 5:25] = True
    for k in (1, 2, 4):
        b = np.roll(a, k, axis=0)
        assert im.hausdorff(a, b, spacing) == pytest.approx(k * spacing[0])
        assert im.hausdorff(a, b, spacing, 95) <= im.hausdorff(a, b, spacing)


def test_island_moves_hausdorff_not_dice():
    """A one-voxel island 20 voxels away: the Hausdorff distance jumps, Dice barely changes."""
    a = ball((60, 40, 40), (20, 20, 20), 10)
    b = a.copy()
    b[51, 20, 20] = True          # 31 voxels from the centre, 21 beyond the surface
    assert im.dice(a, b) > 0.999
    assert im.hausdorff(a, b) == pytest.approx(31 - 10, abs=1.0)
    assert im.hausdorff(a, b, percentile=95) < 1.0
    assert im.assd(a, b) < 0.1


@pytest.mark.parametrize("delta", [-3.0, -1.5, 2.0, 3.0])
def test_concentric_spheres_distances_equal_offset(delta):
    """eq-m40-hausdorff, eq-m40-assd and eq-m40-nsd for concentric voxel spheres (spacing 0.5 mm)."""
    sp_ = (0.5, 0.5, 0.5)
    a = ball((80, 80, 80), (20, 20, 20), 12, sp_)
    b = ball((80, 80, 80), (20, 20, 20), 12 + delta, sp_)
    assert im.assd(a, b, sp_) == pytest.approx(abs(delta), abs=0.4)
    assert im.hausdorff(a, b, sp_) == pytest.approx(abs(delta), abs=0.6)
    assert im.nsd(a, b, abs(delta) + 1.0, sp_) == 1.0
    assert im.nsd(a, b, abs(delta) - 1.0, sp_) < 0.05


@pytest.mark.parametrize("R,delta", [(10, 1), (10, -1), (20, 2), (15, -3)])
def test_sphere_dice_matches_voxels(R, delta):
    """eq-m40-sphere against voxelized spheres at 0.25 mm."""
    s = (0.25,) * 3
    n = int(2 * (R + abs(delta) + 2) / 0.25)
    c = (n * 0.25 / 2,) * 3
    a, b = ball((n,) * 3, c, R, s), ball((n,) * 3, c, R + delta, s)
    assert im.dice(a, b) == pytest.approx(im.sphere_dice(R, delta), abs=0.004)


def test_offset_first_order_symbolic():
    """eq-m40-offset: the first-order term of the exact Dice equals |delta| S / (2 V) for a sphere, a
    cube and a closed cylinder grown uniformly by delta."""
    d, R, a, r, h = sp.symbols("delta R a r h", positive=True)
    cases = [
        (2 * R**3 / (R**3 + (R + d) ** 3), 4 * sp.pi * R**2, sp.Rational(4, 3) * sp.pi * R**3),
        (2 * a**3 / (a**3 + (a + 2 * d) ** 3), 6 * a**2, a**3),
        (2 * r**2 * h / (r**2 * h + (r + d) ** 2 * (h + 2 * d)), 2 * sp.pi * r**2 + 2 * sp.pi * r * h, sp.pi * r**2 * h),
    ]
    for exact, S, V in cases:
        slope = sp.diff(exact, d).subs(d, 0)
        assert sp.simplify(slope + S / (2 * V)) == 0
    # sphere, shrinking: same slope magnitude
    shrink = 2 * (R - d) ** 3 / (R**3 + (R - d) ** 3)
    assert sp.simplify(sp.diff(shrink, d).subs(d, 0) + 3 / (2 * R)) == 0


def test_slab_shift_exact_on_voxels():
    """eq-m40-slab: a wall 8 voxels thick shifted by k voxels keeps Dice 1 - k/8."""
    a = np.zeros((40, 20, 20), bool)
    a[10:18] = True
    for k in range(0, 10):
        assert im.dice(a, np.roll(a, k, axis=0)) == pytest.approx(float(im.slab_dice(8, k)))


def test_wall_loses_more_than_blood_pool():
    """The same 1 mm error: a 1.89 mm wall (Beinart et al. 2011, mean) against a 25 mm sphere
    (illustrative)."""
    assert im.slab_dice(1.89, 1.0) < 0.5 < 0.9 < im.sphere_dice(25, 1.0)


def brute_cindex(time, event, risk):
    num = den = 0.0
    for i, j in itertools.permutations(range(len(time)), 2):
        if event[i] and time[i] < time[j]:
            den += 1
            num += 1.0 if risk[i] > risk[j] else 0.5 if risk[i] == risk[j] else 0.0
    return num / den


def test_cindex_against_brute_force_and_limits():
    """eq-m40-cindex."""
    rng = np.random.default_rng(3)
    for _ in range(10):
        n = 40
        t = rng.exponential(5, n)
        e = rng.random(n) < 0.6
        risk = rng.integers(0, 6, n).astype(float)        # with ties
        assert im.cindex(t, e, risk) == pytest.approx(brute_cindex(t, e, risk))
    t = np.arange(1.0, 21.0)
    e = np.ones(20, bool)
    assert im.cindex(t, e, -t) == 1.0          # earlier event, higher risk
    assert im.cindex(t, e, t) == 0.0
    assert im.cindex(t, e, np.zeros(20)) == 0.5


def test_surface_area_of_voxel_sphere_overestimates_by_half():
    R = 20.0
    a = ball((50, 50, 50), (25, 25, 25), R)
    assert im.surface_area_voxels(a, (1, 1, 1)) / (4 * np.pi * R**2) == pytest.approx(1.5, rel=0.04)


def test_offset_mask_quantizes_to_voxel_layers():
    """Shrinking by less than one voxel still removes the boundary layer (half-voxel convention)."""
    s = (1.25, 1.25, 1.25)
    a = im.ball((40, 40, 40), (25, 25, 25), 15, s)
    shrunk = im.offset_mask(a, -1.0, s)
    removed = a & ~shrunk
    assert np.array_equal(removed, im.surface(a))           # exactly the boundary layer
    assert np.array_equal(im.offset_mask(a, 0.0, s), a)


def test_offset_mask_matches_the_offset_ball():
    """Growing or shrinking a voxel ball by 2 mm gives the ball of radius R +/- 2 mm to within one voxel."""
    s = (0.5, 0.5, 0.5)
    a = ball((80, 80, 80), (20, 20, 20), 10, s)
    for delta in (2.0, -2.0):
        o, b = im.offset_mask(a, delta, s), ball((80, 80, 80), (20, 20, 20), 10 + delta, s)
        assert im.hausdorff(o, b, s) <= 0.5
        assert im.dice(o, b) > 0.96


def test_circle_island_metrics_against_raster():
    """The closed forms behind m40-d1 against masks rasterized at 0.05 mm."""
    R, delta, rho, gap, tau = 6.0, 1.0, 1.5, 3.0, 1.5
    m = im.circle_island_metrics(R, delta, rho, gap, tau)
    h = 0.05
    x = np.arange(-9, 18, h)
    X, Y = np.meshgrid(x, np.arange(-9, 9, h), indexing="ij")
    c = R + delta + gap + rho
    truth = X**2 + Y**2 <= R**2
    pred = (X**2 + Y**2 <= (R + delta) ** 2) | ((X - c) ** 2 + Y**2 <= rho**2)
    assert im.dice(pred, truth) == pytest.approx(m["dice"], abs=0.002)
    assert im.hausdorff(pred, truth, (h, h)) == pytest.approx(m["hd"], abs=0.1)
    assert im.assd(pred, truth, (h, h)) == pytest.approx(m["assd"], rel=0.05)
    assert im.nsd(pred, truth, tau, (h, h)) == pytest.approx(m["nsd"], abs=0.03)
    assert m["hd"] == pytest.approx(c + rho - R)
    no_island = im.circle_island_metrics(R, delta, 0, gap, tau)
    assert no_island["hd"] == no_island["assd"] == pytest.approx(abs(delta))
    assert no_island["dice"] == pytest.approx(float(im.disc_dice(R, delta)))


def test_synthetic_atrium_structure():
    img, lab, info = im.synth_atrium(np.random.default_rng(1))
    assert img.shape == lab.shape == (64, 64, 48)
    assert 0.02 < lab.mean() < 0.10
    assert info["veins"].any() and info["appendage"].any()
    assert not (info["distractor"] & lab).any()
    img2, lab2, _ = im.synth_atrium(np.random.default_rng(1))
    assert np.array_equal(lab, lab2) and np.allclose(img, img2)
    assert im.largest_component(lab).sum() >= 0.9 * lab.sum()


def _fake_msd_tar():
    """A tar with the Task02_Heart layout, 20 cases, and the macOS '._' files the real one may hold."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        for i in range(1, 21):
            for sub in ("imagesTr", "labelsTr"):
                for name in (f"la_{i:03d}.nii.gz", f"._la_{i:03d}.nii.gz"):
                    payload = f"{sub}/{name}".encode()
                    info = tarfile.TarInfo(f"Task02_Heart/{sub}/{name}")
                    info.size = len(payload)
                    t.addfile(info, io.BytesIO(payload))
        info = tarfile.TarInfo("Task02_Heart/dataset.json")
        info.size = 2
        t.addfile(info, io.BytesIO(b"{}"))
    return buf.getvalue()


def test_fetch_msd_heart_verifies_and_unpacks(tmp_path, monkeypatch):
    payload = _fake_msd_tar()

    class Response(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.delenv("EPML_SKIP_REAL_DATA", raising=False)
    monkeypatch.setattr(data.urllib.request, "urlopen", lambda url, timeout=0: Response(payload))
    with pytest.raises(ValueError, match="MD5"):
        data.fetch_msd_heart(cache=tmp_path / "a")
    monkeypatch.setattr(data, "MSD_HEART_MD5", hashlib.md5(payload).hexdigest())
    with pytest.raises(ValueError, match="changed"):                   # the registry pins the real archive
        data.fetch_msd_heart(cache=tmp_path / "c")
    fake_sha = hashlib.sha256(payload).hexdigest()
    monkeypatch.setattr(data, "pinned_checksums", lambda prefix="": {"Task02_Heart.tar": fake_sha})
    pairs = data.fetch_msd_heart(cache=tmp_path / "b")
    assert len(pairs) == 20 and all(p.exists() and q.exists() for p, q in pairs)
    assert not any(p.name.startswith("._") for p, _ in pairs)
    assert not (tmp_path / "b" / "Task02_Heart.tar").exists()
    assert data.fetch_msd_heart(cache=tmp_path / "b") == pairs          # cached: no second download
