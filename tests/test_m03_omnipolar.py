"""m03 equation checks: electric field from a clique, and the omnipolar signal."""

import numpy as np
import pytest

from epml.electrograms import (
    clique_field,
    front_distance,
    omnipolar,
    peak_to_peak,
    unipolar,
)

a, c = 2.5, 1.0  # test inputs: a = w + h in mm; conduction velocity in mm/ms
T = np.linspace(-40, 40, 8001)  # ms


def square_clique(d):
    positions = np.array([[0, 0], [d, 0], [0, d], [d, d]], dtype=float) - d / 2
    pairs = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
    return positions, pairs


def triangle_clique(d):
    positions = np.array([[0, 0], [d, 0], [0, d]], dtype=float) - d / 3
    pairs = [(0, 1), (0, 2), (1, 2)]
    return positions, pairs


def wave_signals(positions, theta_deg):
    n = np.array([np.cos(np.deg2rad(theta_deg)), np.sin(np.deg2rad(theta_deg))])
    return unipolar(front_distance(positions, n, T, c), a), n


@pytest.mark.parametrize("clique", [square_clique, triangle_clique])
def test_clique_field_exact_for_linear_potential(clique):
    """eq-m03-clique-field: for phi = g . r + phi0, the estimate returns E = -g exactly."""
    positions, pairs = clique(2.0)
    rng = np.random.default_rng(1)
    for _ in range(20):
        g, phi0 = rng.normal(size=2), rng.normal()
        potentials = positions @ g + phi0
        E = clique_field(positions, potentials, pairs)
        np.testing.assert_allclose(E, -g, atol=1e-12)


def test_bipoles_are_projections_of_the_field():
    """eq-m03-clique-field: each bipole b = phi_j - phi_i equals -(r_j - r_i) . E for a linear field."""
    positions, pairs = square_clique(2.0)
    g = np.array([0.7, -1.3])
    potentials = positions @ g
    E = clique_field(positions, potentials, pairs)
    for i, j in pairs:
        assert potentials[j] - potentials[i] == pytest.approx(-(positions[j] - positions[i]) @ E)


@pytest.mark.parametrize("clique,tolerance", [(square_clique, 0.02), (triangle_clique, 0.02)])
def test_omnipolar_amplitude_independent_of_direction(clique, tolerance):
    """eq-m03-omnipole: with spacing small next to a = w + h, omnipolar peak-to-peak barely changes with direction,
    while a fixed bipole swings from full amplitude to zero."""
    d = 0.5
    positions, pairs = clique(d)
    omni, fixed = [], []
    for theta in range(0, 180, 10):
        u, _ = wave_signals(positions, theta)
        v, _ = omnipolar(clique_field(positions, u, pairs), d)
        omni.append(peak_to_peak(v))
        fixed.append(peak_to_peak(u[1] - u[0]))
    omni, fixed = np.array(omni), np.array(fixed)
    assert omni.max() / omni.min() - 1 < tolerance
    assert fixed.min() / fixed.max() < 1e-6


def test_omnipolar_matches_aligned_bipole():
    """eq-m03-omnipole: the omnipolar signal equals a bipole of the same spacing aligned with the wave (small d)."""
    d = 0.25
    positions, pairs = square_clique(d)
    s = np.linspace(-200, 200, 400001)
    aligned = peak_to_peak(unipolar(s + d / 2, a) - unipolar(s - d / 2, a))
    u, _ = wave_signals(positions, 37)
    v, _ = omnipolar(clique_field(positions, u, pairs), d)
    assert peak_to_peak(v) == pytest.approx(aligned, rel=0.01)


@pytest.mark.parametrize("clique", [square_clique, triangle_clique])
def test_loop_direction_recovers_propagation(clique):
    """The principal axis of the E-field loop lies along the propagation direction (small d)."""
    positions, pairs = clique(0.5)
    for theta in (0, 25, 60, 90, 135):
        u, n = wave_signals(positions, theta)
        _, omega = omnipolar(clique_field(positions, u, pairs), 0.5)
        angle_error = np.rad2deg(np.arccos(min(1.0, abs(omega @ n))))
        assert angle_error < 1.0


@pytest.mark.parametrize("clique", [square_clique, triangle_clique])
def test_direction_independence_degrades_with_spacing(clique):
    """Larger spacing relative to a = w + h breaks the plane-wave approximation inside the clique:
    the spread of omnipolar amplitude across directions grows with d (no time alignment)."""
    spreads = []
    for d in (0.5, 1.0, 2.0, 4.0):
        positions, pairs = clique(d)
        p2p = []
        for theta in range(0, 180, 10):
            u, _ = wave_signals(positions, theta)
            v, _ = omnipolar(clique_field(positions, u, pairs), d)
            p2p.append(peak_to_peak(v))
        spreads.append(max(p2p) / min(p2p) - 1)
    assert all(later > earlier for earlier, later in zip(spreads, spreads[1:]))
    assert spreads[-1] > 0.25


@pytest.mark.parametrize("speed", [0.5, 1.0, 1.5])
def test_clique_velocity_from_amplitude_ratio(speed):
    """eq-m03-clique-velocity: under a plane wave, peak-to-peak(dU/dt) / peak-to-peak(E . n) equals c."""
    positions, pairs = square_clique(0.25)
    n = np.array([np.cos(0.6), np.sin(0.6)])
    u = unipolar(front_distance(positions, n, T, speed), a)
    E = clique_field(positions, u, pairs)
    du_dt = np.gradient(u.mean(axis=0), T)
    ratio = peak_to_peak(du_dt) / peak_to_peak(n @ E)
    assert ratio == pytest.approx(speed, rel=0.01)


def test_collinear_clique_cannot_give_the_field():
    """Interview question: a 2D field needs two independent bipoles, so at least three electrodes
    that are not in a line. For collinear electrodes D D^T has rank 1 and the field is not determined."""
    line = np.array([[0, 0], [1, 0], [2, 0]], dtype=float)
    pairs = [(0, 1), (1, 2), (0, 2)]
    D = np.stack([line[j] - line[i] for i, j in pairs], axis=1)
    assert np.linalg.matrix_rank(D @ D.T) == 1
    positions, pairs = triangle_clique(1.0)
    D = np.stack([positions[j] - positions[i] for i, j in pairs], axis=1)
    assert np.linalg.matrix_rank(D @ D.T) == 2


def test_square_clique_spread_values_quoted_in_text():
    """Values quoted in the module: across 18 wave directions, without time alignment, the omnipolar
    amplitude spread for a square clique is under 1% at d/a = 0.2 and about 32% at d/a = 1.6."""
    spreads = {}
    for ratio in (0.2, 1.6):
        d = ratio * a
        positions, pairs = square_clique(d)
        p2p = []
        for theta in range(0, 180, 10):
            u, _ = wave_signals(positions, theta)
            v, _ = omnipolar(clique_field(positions, u, pairs), d)
            p2p.append(peak_to_peak(v))
        spreads[ratio] = max(p2p) / min(p2p) - 1
    assert spreads[0.2] < 0.01
    assert spreads[1.6] == pytest.approx(0.32, abs=0.01)
