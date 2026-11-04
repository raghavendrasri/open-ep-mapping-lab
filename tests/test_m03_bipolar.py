"""m03 equation checks: bipolar electrograms and spatial filters."""

import numpy as np
import pytest
from scipy.special import j1

from epml.electrograms import bipolar_planar, unipolar, unipolar_ds

a, A = 2.5, 1.0  # test inputs: a = w + h in mm, amplitude in arbitrary units


def test_bipole_geometry_reduces_to_shifted_unipoles():
    """eq-m03-bipolar and eq-m03-bipolar-planar: placing two electrodes at r0 +/- (d/2) u in 2D and
    subtracting their unipolar signals equals U(s + delta) - U(s - delta), delta = (d/2) cos(theta)."""
    from epml.electrograms import front_distance

    rng = np.random.default_rng(2)
    t = np.linspace(-30, 30, 601)
    for _ in range(20):
        d, phi_n, phi_u, c = rng.uniform(0.5, 6), rng.uniform(0, 2 * np.pi), rng.uniform(0, 2 * np.pi), rng.uniform(0.3, 1.5)
        n = np.array([np.cos(phi_n), np.sin(phi_n)])
        u = np.array([np.cos(phi_u), np.sin(phi_u)])
        r0 = rng.uniform(-10, 10, size=2)
        electrodes = np.stack([r0 + d / 2 * u, r0 - d / 2 * u])
        s = front_distance(electrodes, n, t, c)
        v_geometry = unipolar(s[0], a, A) - unipolar(s[1], a, A)
        theta = np.arccos(np.clip(u @ n, -1, 1))
        v_formula = bipolar_planar(front_distance(r0[None, :], n, t, c)[0], d, theta, a, A)
        np.testing.assert_allclose(v_geometry, v_formula, atol=1e-12)


def test_bipolar_transfer_function_on_harmonics():
    """eq-m03-bipolar-transfer: a bipole maps exp(i k n.r) to amplitude 2|sin(k d cos(theta) / 2)|."""
    rng = np.random.default_rng(0)
    for _ in range(50):
        k, d, theta = rng.uniform(0.05, 3.0), rng.uniform(0.5, 6.0), rng.uniform(0, np.pi)
        u = np.array([np.cos(theta), np.sin(theta)])  # bipole axis; propagation along x
        centers = rng.uniform(-50, 50, size=(400, 2))
        field = lambda r: np.cos(k * r[:, 0])
        v = field(centers + 0.5 * d * u) - field(centers - 0.5 * d * u)
        expected = 2 * abs(np.sin(0.5 * k * d * np.cos(theta)))
        assert np.max(np.abs(v)) == pytest.approx(expected, abs=0.02 * max(expected, 0.05))


def test_bipole_nulls():
    """eq-m03-bipolar-transfer: zero output when k d cos(theta) is a multiple of 2 pi."""
    d = 2.0
    k_null = 2 * np.pi / d
    x = np.linspace(-20, 20, 2001)
    v = np.cos(k_null * (x + d / 2)) - np.cos(k_null * (x - d / 2))
    assert np.max(np.abs(v)) < 1e-12


def test_close_bipole_is_directional_derivative():
    """eq-m03-bipolar-gradient: V_bip ~ d cos(theta) dU/ds, with relative error falling as d^2."""
    s = np.linspace(-15, 15, 3001)
    theta = np.deg2rad(30)
    errors = []
    for d in (1.0, 0.5, 0.25):
        exact = bipolar_planar(s, d, theta, a, A)
        approx = d * np.cos(theta) * unipolar_ds(s, a, A)
        errors.append(np.max(np.abs(exact - approx)) / np.max(np.abs(exact)))
    assert errors[0] / errors[1] == pytest.approx(4.0, rel=0.05)
    assert errors[1] / errors[2] == pytest.approx(4.0, rel=0.05)


def test_bipolar_amplitude_follows_cos_theta():
    """eq-m03-bipolar-gradient: for a close bipole, peak-to-peak scales with |cos(theta)|."""
    s = np.linspace(-30, 30, 6001)
    d = 0.2
    ref = np.ptp(bipolar_planar(s, d, 0.0, a, A))
    for deg in (0, 30, 60, 80, 90, 120, 150):
        theta = np.deg2rad(deg)
        ratio = np.ptp(bipolar_planar(s, d, theta, a, A)) / ref
        assert ratio == pytest.approx(abs(np.cos(theta)), abs=2e-3)


def test_bipolar_peak_to_peak_small_spacing():
    """eq-m03-bipolar-gradient: peak-to-peak -> d |cos(theta)| * 9 A / (8 a^2) as d -> 0."""
    s = np.linspace(-30, 30, 60001)
    d = 0.05
    assert np.ptp(bipolar_planar(s, d, 0.0, a, A)) == pytest.approx(d * 9 * A / (8 * a**2), rel=1e-3)


def test_bipole_more_local_than_unipole():
    """Unipolar peak-to-peak scales as 1/(w+h); a close bipole's scales as 1/(w+h)^2."""
    s = np.linspace(-200, 200, 200001)
    heights = np.array([2.0, 4.0, 8.0])  # values of a = w + h
    uni = [np.ptp(unipolar(s, aa, A)) for aa in heights]
    bip = [np.ptp(bipolar_planar(s, 0.05, 0.0, aa, A)) for aa in heights]
    slope_uni = np.polyfit(np.log(heights), np.log(uni), 1)[0]
    slope_bip = np.polyfit(np.log(heights), np.log(bip), 1)[0]
    assert slope_uni == pytest.approx(-1.0, abs=1e-3)
    assert slope_bip == pytest.approx(-2.0, abs=1e-2)


@pytest.mark.parametrize("k_radius", [0.3, 1.0, 2.5, 3.8317, 5.0])
def test_disk_average_transfer(k_radius):
    """eq-m03-disk-average: averaging cos(k x) over a disk of radius r scales it by 2 J1(kr)/(kr)."""
    radius = 1.0
    k = k_radius / radius
    n = 801
    g = np.linspace(-radius, radius, n)
    xx, yy = np.meshgrid(g, g)
    inside = xx**2 + yy**2 <= radius**2
    average = np.mean(np.cos(k * xx[inside]))
    expected = 2 * j1(k * radius) / (k * radius)
    assert average == pytest.approx(expected, abs=2e-3)


def test_far_field_decay_exponents():
    """eq-m03-farfield: unipole vs bipole decay for a distant monopole (1/R vs 1/R^2) and dipole (1/R^2 vs 1/R^3)."""
    d = 2.0
    distances = np.array([50.0, 100.0, 200.0, 400.0])

    def monopole(r):
        return 1.0 / np.linalg.norm(r, axis=-1)

    def dipole(r):
        p = np.array([1.0, 0.0, 0.0])
        return (r @ p) / np.linalg.norm(r, axis=-1) ** 3

    slopes = {}
    for name, field in [("monopole", monopole), ("dipole", dipole)]:
        uni, bip = [], []
        for R in distances:
            electrode = np.array([R, 0.0, 0.0])
            axis = np.array([1.0, 0.0, 0.0])
            uni.append(abs(field(electrode)))
            bip.append(abs(field(electrode + d / 2 * axis) - field(electrode - d / 2 * axis)))
        slopes[name] = (
            np.polyfit(np.log(distances), np.log(uni), 1)[0],
            np.polyfit(np.log(distances), np.log(bip), 1)[0],
        )
    assert slopes["monopole"][0] == pytest.approx(-1.0, abs=1e-6)
    assert slopes["monopole"][1] == pytest.approx(-2.0, abs=1e-2)
    assert slopes["dipole"][0] == pytest.approx(-2.0, abs=1e-6)
    assert slopes["dipole"][1] == pytest.approx(-3.0, abs=1e-2)


def test_close_bipole_is_scaled_time_derivative():
    """Cheat sheet: eq-m03-bipolar-gradient with eq-m03-unipolar-slope gives
    V_bip ~ -(d cos(theta) / c) dU/dt at the bipole's center, so its largest value falls when the
    front passes the center."""
    t = np.linspace(-30, 30, 600_001)
    for c, theta in [(0.5, 0.0), (1.0, 0.6), (1.5, -1.0)]:
        d = 0.05 * a
        s_center = -c * t  # bipole center at x = 0, front passes it at t = 0
        v = bipolar_planar(s_center, d, theta, a, A)
        du_dt = np.gradient(unipolar(s_center, a, A), t)
        approx = -(d * np.cos(theta) / c) * du_dt
        assert np.max(np.abs(v - approx)) < 5e-3 * np.max(np.abs(v))
        assert abs(t[np.argmax(np.abs(v))]) < 2 * (t[1] - t[0])


def test_disk_transfer_first_null():
    """Cheat sheet: the disk factor 2 J1(k r) / (k r) first reaches zero at k r = 3.8317 (first zero of J1)."""
    from scipy.special import jn_zeros

    from epml.electrograms import disk_transfer

    x0 = jn_zeros(1, 1)[0]
    assert x0 == pytest.approx(3.8317, abs=1e-4)
    x = np.linspace(1e-6, x0 - 1e-6, 10_001)
    assert np.all(disk_transfer(x, 1.0) > 0)
    assert disk_transfer(np.array([x0]), 1.0)[0] == pytest.approx(0.0, abs=1e-12)


def test_far_field_share_grows_with_spacing():
    """Interview question: for d << a both the local and the far-field bipolar signals scale with d,
    so their ratio barely changes; once d is comparable to a = w + h the local signal saturates
    (towards the unipolar peak-to-peak A / a) while the far-field term keeps growing.
    Far source: a unit monopole on the bipole axis at R = 200 a."""
    s = np.linspace(-150 * a, 150 * a, 600_001)
    R = 200 * a

    def share(d):
        far = 1 / (R - d / 2) - 1 / (R + d / 2)
        return far / np.ptp(bipolar_planar(s, d, 0.0, a, A))

    ratios = {k: share(k * a) / share(0.05 * a) for k in (0.1, 0.2, 0.5, 1, 2, 3)}
    assert ratios[0.2] == pytest.approx(1.0, abs=0.01)
    assert ratios[1] == pytest.approx(1.22, abs=0.01)
    assert ratios[2] == pytest.approx(1.86, abs=0.01)
    values = [ratios[k] for k in (0.1, 0.2, 0.5, 1, 2, 3)]
    assert all(x < y for x, y in zip(values, values[1:]))
    assert np.ptp(bipolar_planar(s, 40 * a, 0.0, a, A)) == pytest.approx(A / a, rel=5e-3)
