"""m12 · The surface ECG and the forward problem: equation tests."""

import numpy as np
import pytest
import sympy as sp

from epml import ecg as G


def test_sphere():
    """eq-m12-sphere: (p cos theta / 4 pi sigma)(1 / r^2 + 2 r / R^3) is harmonic, has zero normal current at r = R,
    and equals 3 p cos theta / (4 pi sigma R^2) there: three times the infinite-medium value."""
    r, th, R, p, s = sp.symbols("r theta R p sigma", positive=True)
    phi = p * sp.cos(th) / (4 * sp.pi * s) * (1 / r**2 + 2 * r / R**3)
    lap = sp.diff(r**2 * sp.diff(phi, r), r) / r**2 + sp.diff(sp.sin(th) * sp.diff(phi, th), th) / (r**2 * sp.sin(th))
    assert sp.simplify(lap) == 0
    assert sp.simplify(sp.diff(phi, r).subs(r, R)) == 0
    assert sp.simplify(phi.subs(r, R) / (p * sp.cos(th) / (4 * sp.pi * s * R**2))) == 3
    pv = np.array([0.3, 0.8, 0.2])
    x = np.array([0.0, 0.0, 0.5])
    assert G.centric_interior(pv, x) == pytest.approx(np.dot(pv, x / 0.5) / (4 * np.pi) * (1 / 0.25 + 1.0))


def test_series():
    """eq-m12-series: each term r0^l / r^(l+1) P_l + A_l r^l P_l with A_l = (l+1) r0^l / (l R^(2l+1)) has zero radial
    derivative at R and surface value ((2l+1)/l) r0^l / R^(l+1) P_l; a dipole near the center reproduces the closed
    form."""
    r, R, r0, l = sp.symbols("r R r_0 l", positive=True)
    A = (l + 1) * r0**l / (l * R ** (2 * l + 1))
    f = r0**l / r ** (l + 1) + A * r**l
    assert sp.simplify(sp.diff(f, r).subs(r, R)) == 0
    assert sp.simplify(f.subs(r, R) - (2 * l + 1) / l * r0**l / R ** (l + 1)) == 0
    p = np.array([0.3, 0.8, 0.2])
    for v in G.LIMBS.values():
        assert G.dipole_surface(p, [0.0, 0.0, 1e-3], v) == pytest.approx(G.centric_surface(p, v), abs=2e-4)


def test_lead():
    """eq-m12-lead: lead voltage = L . p (superposition), with L = 3 (a_hat - b_hat) / (4 pi sigma R^2) for a centric
    dipole; an eccentric heart distorts the limb-lead vectors away from Einthoven's equilateral triangle."""
    a, b = G.LIMBS["L"], G.LIMBS["R"]
    assert np.allclose(G.lead_vector(a, b), 3 * (a - b) / (4 * np.pi))
    r0 = np.array([0.3, 0.1, 0.2])
    L = G.lead_vector(a, b, r0)
    p = np.array([0.5, -0.4, 0.7])
    direct = G.dipole_surface(p, r0, a) - G.dipole_surface(p, r0, b)
    assert np.dot(L, p) == pytest.approx(direct, rel=1e-6)
    li = G.lead_vector(G.LIMBS["L"], G.LIMBS["R"], [0.3, 0.0, 0.0])
    assert abs(np.degrees(np.arctan2(li[1], li[0]))) > 10


def test_einthoven_and_augmented():
    """eq-m12-einthoven and eq-m12-augmented: I + III = II; aVR + aVL + aVF = 0; aVR = -(I + II)/2,
    aVL = (I - III)/2, aVF = (II + III)/2."""
    R_, L_, F_ = sp.symbols("phi_R phi_L phi_F")
    d = G.limb_leads(R_, L_, F_)
    assert sp.simplify(d["I"] + d["III"] - d["II"]) == 0
    assert sp.simplify(d["aVR"] + d["aVL"] + d["aVF"]) == 0
    assert sp.simplify(d["aVR"] + (d["I"] + d["II"]) / 2) == 0
    assert sp.simplify(d["aVL"] - (d["I"] - d["III"]) / 2) == 0
    assert sp.simplify(d["aVF"] - (d["II"] + d["III"]) / 2) == 0
    p = np.array([1.0, 0.5, 0.0])
    assert abs(G.leads_for_dipole(p)["WCT"]) < 1e-12                       # zero for a centric dipole
    assert abs(G.leads_for_dipole(p, r0=[0.3, 0.0, 0.0])["WCT"]) > 1e-3     # not with the heart off center


def test_axis():
    """eq-m12-axis: in the centric, equilateral model the axis from I and aVF equals the heart vector's frontal angle
    for any vector; with the heart displaced 0.3 R to the left it is off by more than 5 degrees for some vectors."""
    rng = np.random.default_rng(0)
    for _ in range(20):
        p = rng.standard_normal(3)
        L = G.leads_for_dipole(p)
        assert G.frontal_axis(L["I"], L["aVF"]) == pytest.approx(np.degrees(np.arctan2(p[1], p[0])), abs=1e-9)
    errs = []
    for ang in np.radians([0, 30, 60, 90]):
        p = np.array([np.cos(ang), np.sin(ang), 0.0])
        L = G.leads_for_dipole(p, r0=[0.3, 0.0, 0.0])
        errs.append(abs(G.frontal_axis(L["I"], L["aVF"]) - np.degrees(ang)))
    assert max(errs) > 5


def test_forward():
    """eq-m12-forward: a planar front crossing a ball gives a heart vector along its direction with magnitude
    proportional to the front area; the QRS lasts 2a / CV and the axis of its area is the front's frontal angle."""
    t = np.linspace(0, 120, 1201)
    u = np.array([np.cos(np.radians(50)), np.sin(np.radians(50)), 0.2])
    pt = G.front_heart_vector(t, u, radius=30.0, cv=0.6)
    on = np.where(np.linalg.norm(pt, axis=1) > 0)[0]
    assert (t[on[-1]] - t[on[0]]) == pytest.approx(2 * 30.0 / 0.6, abs=0.2)
    lv = {k: G.lead_vector(G.LIMBS[a], G.LIMBS[b]) for k, (a, b) in {"I": ("L", "R"), "II": ("F", "R"), "III": ("F", "L")}.items()}
    sig = G.lead_signals(pt, lv)
    area_i = np.trapezoid(sig["I"], t)
    area_avf = np.trapezoid((sig["II"] + sig["III"]) / 2, t)
    assert G.frontal_axis(area_i, area_avf) == pytest.approx(50.0, abs=1e-6)
    peak = np.max(np.linalg.norm(pt, axis=1))
    assert peak == pytest.approx(np.pi * 30.0**2 * np.linalg.norm(u / np.linalg.norm(u)), rel=1e-3)
