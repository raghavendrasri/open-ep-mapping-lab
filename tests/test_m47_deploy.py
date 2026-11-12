"""Equation tests for m47 (data and deployment engineering)."""
import sys
from pathlib import Path

import numpy as np
import pytest
import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "labs" / "python"))
from epml import deploy as dp  # noqa: E402


def test_adu_conversion_round_trip_and_gain_error():
    """eq-m47-adu: v = (d - b) / g; rounding to integers costs at most 1 / (2 g)."""
    d, b, g = sp.symbols("d b g", positive=True)
    v = (d - b) / g
    assert sp.simplify(v * g + b - d) == 0
    x = np.random.default_rng(0).normal(0, 1, 5000)
    for gain, base in [(200, 0), (1000, 37)]:
        back = dp.adu_to_physical(dp.physical_to_adu(x, gain, base), gain, base)
        assert np.max(np.abs(back - x)) <= 1 / (2 * gain) + 1e-12
    # a header that claims gain 1000 for data stored at gain 200 shrinks every value by 5
    q = dp.physical_to_adu(x, 200)
    assert np.allclose(dp.adu_to_physical(q, 1000), dp.adu_to_physical(q, 200) / 5)


def test_wfdb_round_trip_and_header_edit(tmp_path):
    pytest.importorskip("wfdb")
    x = np.sin(np.linspace(0, 20, 1000))
    hea = dp.write_wfdb(x, 250, 200, tmp_path)
    y, fs, gain, units = dp.read_wfdb(hea)
    assert (fs, gain, units) == (250.0, 200.0, "mV")
    assert np.max(np.abs(y - x)) <= 1 / 400 + 1e-9
    dp.edit_header(hea, gain=1000, fs=500)
    y2, fs2, gain2, _ = dp.read_wfdb(hea)
    assert (fs2, gain2) == (500.0, 1000.0) and np.allclose(y2, y / 5)


def test_majority_vote_formula_symbolic_and_simulated():
    """eq-m47-majority for m = 3 is 3p^2 - 2p^3; simulation matches for m = 5."""
    p = sp.symbols("p")
    three = sum(sp.binomial(3, j) * p**j * (1 - p) ** (3 - j) for j in range(2, 4))
    assert sp.expand(three - (3 * p**2 - 2 * p**3)) == 0
    assert dp.majority_accuracy(0.5, 7) == pytest.approx(0.5)
    assert dp.majority_accuracy(0.8, 1) == pytest.approx(0.8)
    assert dp.majority_accuracy(0.8, 3) < dp.majority_accuracy(0.8, 5) < dp.majority_accuracy(0.8, 7)
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 200_000)
    L, _ = dp.simulate_labels(y, 5, 0.8, rng)
    assert np.mean(dp.majority_vote(L) == y) == pytest.approx(dp.majority_accuracy(0.8, 5), abs=0.004)
    # shared hard cases: majority accuracy is the mixture of the two formulas
    L, hard = dp.simulate_labels(y, 5, 0.9, rng, hard_share=0.2, p_hard=0.5)
    want = 0.8 * dp.majority_accuracy(0.9, 5) + 0.2 * 0.5
    assert np.mean(dp.majority_vote(L) == y) == pytest.approx(want, abs=0.004)
    with pytest.raises(ValueError):
        dp.majority_accuracy(0.8, 4)


def test_reidentification_risk_identities():
    """eq-m47-risk: average of 1/f_i equals classes / records; generalizing never raises the risk."""
    table = {"a": np.array([1, 1, 2, 2, 2, 3]), "b": np.array([0, 0, 0, 0, 1, 1])}
    f = dp.class_sizes(table, ["a", "b"])
    assert list(f) == [2, 2, 2, 2, 1, 1]
    risk = dp.reid_risk(f)
    assert risk["max"] == 1.0 and risk["k"] == 1 and risk["unique"] == pytest.approx(2 / 6)
    assert risk["average"] == pytest.approx(4 / 6)    # four classes, six records
    reg = dp.synthetic_registry(3000, np.random.default_rng(2))
    cols = ["age", "sex", "device", "region", "date"]
    fine = dp.reid_risk(dp.class_sizes(dp.generalize(reg), cols))
    coarse_t = dp.generalize(reg, age_width=10, date="none", keep_region=False)
    coarse = dp.reid_risk(dp.class_sizes(coarse_t, ["age", "sex", "device"]))
    n_classes = len(set(zip(*(coarse_t[c] for c in ["age", "sex", "device"]))))
    assert coarse["average"] == pytest.approx(n_classes / 3000)
    assert coarse["average"] < fine["average"] and coarse["unique"] <= fine["unique"]


def test_affine_quantization_scale_zero_point():
    """eq-m47-affine: r = S (q - Z); zero is exact; in-range error is at most S/2."""
    S, Z, qmin, qmax = dp.qparams(-1.0, 3.0, bits=8)
    assert S == pytest.approx(4 / 255) and Z == 64 and (qmin, qmax) == (0, 255)
    assert dp.dequantize(dp.quantize(0.0, S, Z, qmin, qmax), S, Z) == 0.0
    r = np.linspace(-1, 3, 10_001)
    err = dp.dequantize(dp.quantize(r, S, Z, qmin, qmax), S, Z) - r
    assert np.max(np.abs(err)) <= S / 2 + 1e-12
    # a range that excludes zero is widened to include it
    S2, Z2, _, _ = dp.qparams(0.5, 2.0, bits=8)
    assert S2 == pytest.approx(2.0 / 255) and Z2 == 0


def test_quantization_noise_and_sqnr():
    """eq-m47-qnoise: uniform error on [-S/2, S/2] has variance S^2/12; a full-scale sine gives
    SQNR = 20 b log10(2) + 10 log10(3/2), about 6.02 b + 1.76 dB."""
    e, S, A, b = sp.symbols("e S A b", positive=True)
    var = sp.integrate(e**2 / S, (e, -S / 2, S / 2))
    assert sp.simplify(var - S**2 / 12) == 0
    sqnr = 10 * sp.log((A**2 / 2) / ((2 * A / 2**b) ** 2 / 12), 10)
    target = 20 * b * sp.log(2, 10) + 10 * sp.log(sp.Rational(3, 2), 10)
    assert sp.N((sqnr - target).subs({A: 1.3, b: 9})) == pytest.approx(0, abs=1e-12)
    assert float(20 * np.log10(2)) == pytest.approx(6.02, abs=0.005)
    assert float(10 * np.log10(1.5)) == pytest.approx(1.76, abs=0.005)
    t = np.arange(200_000)
    x = np.sin(2 * np.pi * t / 1000.37)
    for bits in (8, 12):
        xq, S = dp.fake_quant(x, bits, rmin=-1, rmax=1)
        assert dp.sqnr_db(x, xq) == pytest.approx(6.02 * bits + 1.76, abs=0.3)
        assert dp.sqnr_db(x, xq) == pytest.approx(dp.predicted_sqnr_db(x, S), abs=0.3)


def test_manifest_detects_a_silent_change(tmp_path):
    (tmp_path / "a.csv").write_text("1,2\n")
    (tmp_path / "b.csv").write_text("3,4\n")
    m1 = dp.manifest(tmp_path)
    (tmp_path / "b.csv").write_text("3,5\n")
    (tmp_path / "c.csv").write_text("new\n")
    m2 = dp.manifest(tmp_path)
    assert dp.diff_manifest(m1, m2) == {"changed": ["b.csv"], "added": ["c.csv"], "removed": []}
    assert dp.manifest_id(m1) != dp.manifest_id(m2) and dp.manifest_id(m1) == dp.manifest_id(dict(m1))


def test_per_channel_quantization_and_model_card():
    from epml import trust as tr

    rng = np.random.default_rng(3)
    mlp = tr.TinyMLP(20, 8, seed=0)
    mlp.W *= np.r_[np.ones(4) * 0.05, np.ones(4) * 3.0][:, None]   # rows with very different ranges
    X = rng.normal(0, 1, (500, 20))
    e_tensor = np.abs(dp.quantize_mlp(mlp, 4).prob(X) - mlp.prob(X)).mean()
    e_channel = np.abs(dp.quantize_mlp(mlp, 4, per_channel=True).prob(X) - mlp.prob(X)).mean()
    assert e_channel < e_tensor
    assert dp.model_bytes(mlp, 8) < dp.model_bytes(mlp, 32)
    fields = {s: "text" for s in dp.CARD_SECTIONS}
    card = dp.model_card(fields)
    assert dp.missing_sections(card) == []
    fields["Limitations"] = " "
    with pytest.raises(ValueError, match="Limitations"):
        dp.model_card(fields)
