"""m55 · Capstone: equation tests for projection, target registration error and the error budget."""

import numpy as np
import pytest
import sympy as sp

from epml import capstone as C


def test_pinhole_projection():
    """eq-m55-projection: by similar triangles a point at depth y beyond the isocenter lands at SID/(SOD + y) times
    its lateral position; magnification at the isocenter is SID/SOD; rotating the C-arm moves the beam."""
    x, y, sod, sid = sp.symbols("x y SOD SID", positive=True)
    u = sid * x / (sod + y)
    assert sp.simplify(u.subs(y, 0) - x * sid / sod) == 0
    assert sp.simplify(sp.diff(u, x) - sid / (sod + y)) == 0
    uv, m = C.project(np.array([[10.0, 0.0, 5.0], [10.0, 100.0, 5.0]]), sod=750.0, sid=1100.0)
    assert m[0] == pytest.approx(1100 / 750)
    assert uv[0] == pytest.approx([10 * 1100 / 750, 5 * 1100 / 750])
    assert uv[1][0] == pytest.approx(10 * 1100 / 850)
    p = np.array([[0.0, 30.0, 0.0]])
    uv90, _ = C.project(p, angle_deg=90.0)
    assert abs(uv90[0, 0]) > 30.0                        # a point along the beam becomes lateral after 90 degrees
    seen, hidden = C.visible_error([0.0, 5.0, 0.0], 0.0)
    assert seen == pytest.approx(0.0, abs=1e-12) and hidden == pytest.approx(5.0)
    seen, hidden = C.visible_error([3.0, 4.0, 0.0], 0.0)
    assert seen == pytest.approx(3.0) and hidden == pytest.approx(4.0)


def test_kabsch_and_icp():
    """Rigid registration (derived in m21) recovers a known transform exactly from noise-free points, and ICP from a
    rough start on a noise-free surface."""
    rng = np.random.default_rng(0)
    P = C.ellipsoid_points((25, 20, 22), 400, rng)
    R = C.random_rotation(rng, 20)
    t = np.array([5.0, -3.0, 7.0])
    Q = C.apply(R, t, P)
    R1, t1 = C.kabsch(P, Q)
    assert np.allclose(R1, R) and np.allclose(t1, t)
    assert np.linalg.det(R1) == pytest.approx(1.0)
    R0 = R @ C.random_rotation(rng, 5)
    R2, t2, d = C.icp(P[::2], Q, R0, t + 2.0)
    assert d < 0.5
    assert np.linalg.norm(C.apply(R2, t2, P) - Q, axis=1).max() < 1.5


def test_predicted_tre_matches_simulation():
    """eq-m55-tre: the first-order prediction <TRE^2> = FLE^2/N (1 + 1/3 sum d_k^2/f_k^2) agrees with Monte Carlo
    landmark registration within 8% for three layouts; <FRE^2> = (1 - 2/N) FLE^2 does not depend on the layout; FRE
    and TRE are nearly uncorrelated."""
    rng = np.random.default_rng(55)
    targets = np.array([[0, 0, 0], [30, 0, 0], [-30, 10, 5], [0, 0, 30]], float)
    for kind in ("spread", "clustered", "nearly collinear"):
        F = C.fiducial_layout(kind, 6)
        pred = C.predicted_tre(F, targets, 2.0)
        sim, fre, tre0 = C.simulate_tre(F, targets, 2.0, rng, 3000)
        assert np.allclose(sim, pred, rtol=0.08)
        assert np.sqrt(np.mean(fre**2)) == pytest.approx(C.predicted_fre(6, 2.0), rel=0.03)
        assert abs(np.corrcoef(fre, tre0)[0, 1]) < 0.1
    F = C.fiducial_layout("spread", 6)
    at_centroid = C.predicted_tre(F, F.mean(0), 2.0)[0]
    assert at_centroid == pytest.approx(2.0 / np.sqrt(6))       # at the centroid TRE = FLE / sqrt(N)
    N, fle, d, f = sp.symbols("N FLE d f", positive=True)
    tre2 = fle**2 / N * (1 + sp.Rational(1, 3) * (d**2 / f**2) * 3)
    assert sp.limit(tre2.subs(d, 0), N, sp.oo) == 0


def test_error_budget():
    """eq-m55-budget: independent zero-mean errors add in quadrature (checked by simulation)."""
    assert C.budget([3.0, 4.0]) == pytest.approx(5.0)
    rng = np.random.default_rng(1)
    parts = [1.0, 2.0, 1.5]
    total = sum(rng.normal(0, s, (200000, 3)) / np.sqrt(3) for s in parts)
    assert C.rms(total) == pytest.approx(C.budget(parts), rel=0.01)
    assert C.kap(0.5, 10.0, 2.0) == pytest.approx(7.0)
