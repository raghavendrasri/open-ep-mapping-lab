"""m52 · Cardiac MRI for EP: equation tests (numeric, and symbolic with SymPy where feasible)."""

import numpy as np
import pytest
import sympy as sp

from epml import mri
from epml.imaging import dice


def test_larmor():
    """eq-m52-larmor: f = (gamma/2 pi) B0, about 63.9 MHz at 1.5 T and 127.7 MHz at 3 T."""
    assert mri.larmor_mhz(1.5) == pytest.approx(63.866, abs=1e-3)
    assert mri.larmor_mhz(3.0) == pytest.approx(2 * mri.larmor_mhz(1.5))
    assert mri.GAMMA_BAR_MHZ_PER_T == pytest.approx(42.577478461)


def test_inversion_recovery_from_bloch():
    """eq-m52-ir: solving dMz/dt = (M0 - Mz)/T1 from Mz(0) = -M0 gives M0 (1 - 2 e^(-t/T1)), null at T1 ln 2; the
    full Bloch equations with a finite RF pulse agree within the small loss during the pulse."""
    t, T1, M0 = sp.symbols("t T1 M0", positive=True)
    Mz = sp.Function("Mz")
    sol = sp.dsolve(sp.Eq(Mz(t).diff(t), (M0 - Mz(t)) / T1), Mz(t), ics={Mz(0): -M0}).rhs
    assert sp.simplify(sol - M0 * (1 - 2 * sp.exp(-t / T1))) == 0
    assert sp.simplify(sol.subs(t, T1 * sp.log(2))) == 0
    tt, mx, my, mz = mri.bloch_inversion(379.0, 50.0)
    dev = np.abs(mz - mri.ir_mz(tt, 379.0)).max()
    assert dev < 0.02
    tt2, _, _, mz2 = mri.bloch_inversion(379.0, 50.0, b1_ut=23.4)
    assert np.abs(mz2 - mri.ir_mz(tt2, 379.0)).max() < 0.6 * dev          # a shorter pulse is closer to ideal
    assert np.abs(mx).max() < 1e-6 and np.abs(my).max() < 0.01
    zero = tt[np.argmin(np.abs(mz))]
    assert zero == pytest.approx(mri.null_time(379.0), abs=6.0)


def test_relaxivity_and_kellman_example():
    """eq-m52-relaxivity: 1/T1 = 1/T1,0 + r1 [Gd]. Kellman and Arai's example: 0.15 mmol/kg into 8% blood by weight at
    1.06 kg/L gives about 2 mmol/L in blood, 0.5 mmol/L in tissue with ECV 25%, dR1 2.25/s, and T1 950 -> ~300 ms."""
    cb = mri.blood_concentration(0.15, 0.08, 1.06)
    assert cb == pytest.approx(1.9875)
    ct = 0.25 * cb
    assert ct == pytest.approx(0.5, abs=0.01)
    assert mri.RELAXIVITY * ct == pytest.approx(2.25, abs=0.02)
    assert mri.t1_with_gd(950.0, ct) == pytest.approx(300, abs=10)
    assert mri.t1_with_gd(950.0, 0.0) == pytest.approx(950.0)
    assert mri.t1_with_gd(950.0, 1.0) == pytest.approx(1e3 / (1e3 / 950.0 + 4.5))


def test_ecv():
    """eq-m52-ecv: with dR1 = r1 v Cp (v = ECV in tissue, 1 - Hct in blood), ECV = (1 - Hct) dR1_myo / dR1_blood
    recovers the ECV that generated the data; Bauner et al.'s infarct-to-myocardium dR1 ratio (2.04) is close to
    their ECV ratio (1.89)."""
    cp, r1, hct, e = 2.0, mri.RELAXIVITY, 0.42, 0.27
    t1m_pre, t1b_pre = 1000.0, 1600.0
    t1m_post = mri.t1_with_gd(t1m_pre, e * cp, r1)
    t1b_post = mri.t1_with_gd(t1b_pre, (1 - hct) * cp, r1)
    assert mri.ecv(t1m_pre, t1m_post, t1b_pre, t1b_post, hct) == pytest.approx(e)
    E, H, C, R = sp.symbols("E H C R", positive=True)
    assert sp.simplify((1 - H) * (R * E * C) / (R * (1 - H) * C) - E) == 0
    b = mri.BAUNER
    dm = mri.delta_r1(b["myocardium"]["t1_pre"], b["myocardium"]["t1_post"])
    di = mri.delta_r1(b["infarct"]["t1_pre"], b["infarct"]["t1_post"])
    assert di / dm == pytest.approx(2.04, abs=0.01)
    assert di / dm == pytest.approx(b["infarct"]["ecv"] / b["myocardium"]["ecv"], rel=0.1)
    assert mri.blood_t1_post_illustrative() == pytest.approx(248.7, abs=0.2)


def test_lge_inversion_time():
    """eq-m52-lge: the signed scar-myocardium difference peaks at TI* = ln(T1m/T1s)/(1/T1s - 1/T1m), just after the
    myocardial null; at the null the scar signal is |1 - 2^(1 - T1m/T1s)|."""
    TI, a, b = sp.symbols("TI T_m T_s", positive=True)
    diff = 2 * (sp.exp(-TI / a) - sp.exp(-TI / b))
    crit = sp.solve(sp.diff(diff, TI), TI)
    assert any(sp.simplify(c - sp.log(a / b) / (1 / b - 1 / a)) == 0 for c in crit)
    t1m, t1s = mri.BAUNER["myocardium"]["t1_post"], mri.BAUNER["infarct"]["t1_post"]
    ti = np.linspace(1, 800, 80000)
    d = mri.lge_signal(ti, t1s, magnitude=False) - mri.lge_signal(ti, t1m, magnitude=False)
    assert ti[np.argmax(d)] == pytest.approx(mri.best_ti_signed(t1m, t1s), abs=0.1)
    assert mri.best_ti_signed(t1m, t1s) > mri.null_time(t1m)
    assert mri.lge_signal(mri.null_time(t1m), t1s) == pytest.approx(mri.scar_signal_at_null(t1m, t1s))
    assert mri.lge_signal(mri.null_time(t1m), t1m) == pytest.approx(0.0, abs=1e-12)
    # magnitude images lose contrast when TI is too short: myocardium and scar both negative, myocardium "brighter"
    early = 120.0
    assert mri.lge_signal(early, t1m) > mri.lge_signal(early, t1s)


def test_iir_burden_and_otsu():
    """eq-m52-iir: IIR divides by the blood-pool mean, so a common gain cancels; burden falls as the threshold
    rises; Otsu's threshold maximizes the between-class variance."""
    rng = np.random.default_rng(1)
    w = mri.synthetic_wall(rng)
    a = mri.iir(w["wall"], w["blood"])
    b = mri.iir(3.7 * w["wall"], 3.7 * w["blood"])
    assert np.allclose(a, b)
    ths = np.linspace(0.8, 2.0, 25)
    bur = [mri.burden(a, t) for t in ths]
    assert all(x >= y for x, y in zip(bur[:-1], bur[1:]))
    v = np.concatenate([rng.normal(0, 1, 5000), rng.normal(6, 1, 5000)])
    t = mri.otsu_threshold(v)
    assert 2.0 < t < 4.0
    grid = np.linspace(v.min(), v.max(), 400)
    def between(th):
        lo, hi = v[v <= th], v[v > th]
        return lo.size * hi.size * (lo.mean() - hi.mean()) ** 2 if lo.size and hi.size else 0
    best = grid[np.argmax([between(g) for g in grid])]
    assert t == pytest.approx(best, abs=0.1)


def test_threshold_changes_burden_on_synthetic_wall():
    """The published thresholds give very different burdens on the same synthetic wall, bracketing the truth; a
    repeat scan with new noise agrees only partly."""
    rng = np.random.default_rng(52)
    w = mri.synthetic_wall(rng)
    rep = mri.scan(rng, w["clean"])
    wi, wi2 = mri.iir(w["wall"], w["blood"]), mri.iir(rep["wall"], rep["blood"])
    bn, bn2 = w["blood"] / w["blood"].mean(), rep["blood"] / rep["blood"].mean()
    res = {}
    for name, kv in mri.THRESHOLDS.items():
        t1, t2 = mri.threshold_for(name, kv, wi, bn), mri.threshold_for(name, kv, wi2, bn2)
        res[name] = (mri.burden(wi, t1), dice(wi > t1, w["truth"]), dice(wi > t1, wi2 > t2))
    burdens = [r[0] for r in res.values()]
    truth = w["truth"].mean()
    assert min(burdens) < truth < max(burdens)
    assert max(burdens) / min(burdens) > 5
    assert all(r[2] < 0.95 for r in res.values())
    assert np.mean(w["clean"][~w["truth"]]) + 2 * 0.155 == pytest.approx(1.21, abs=0.02)


def test_shell_iir_on_a_synthetic_volume():
    """Blood-pool normalization on a volume: a sphere of blood (value 300) inside tissue (value 150) gives a shell
    IIR of 0.5 and a blood-pool mean of 300, whatever the voxel size."""
    for spacing in ((1.0, 1.0, 1.0), (1.25, 1.25, 2.5)):
        n = 48
        z, y, x = np.mgrid[:n, :n, :n].astype(float)
        r = np.sqrt(((x - n / 2) * spacing[2]) ** 2 + ((y - n / 2) * spacing[1]) ** 2 + ((z - n / 2) * spacing[0]) ** 2)
        lab = r < 15
        img = np.where(lab, 300.0, 150.0)
        vals, mean_blood, n_blood = mri.shell_iir(img, lab, spacing, (0.0, 3.0))
        assert mean_blood == pytest.approx(300.0)
        assert np.allclose(vals, 0.5) and vals.size > 0 and n_blood > 0
        ci, cl = mri.crop_to_label(img, lab, spacing, 5.0)
        assert cl.sum() == lab.sum() and ci.size < img.size
        vals2, _, _ = mri.shell_iir(ci, cl, spacing, (0.0, 3.0))
        assert vals2.size == vals.size

