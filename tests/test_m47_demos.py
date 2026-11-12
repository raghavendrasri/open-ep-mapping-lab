"""m47 demos: the JS quantizer and re-identification risk match epml.deploy."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import deploy as dp

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m47-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m47-affine, eq-m47-qnoise and eq-m47-risk in JS."""
    rng = np.random.default_rng(0)
    x = [float(v) for v in rng.normal(0.2, 0.5, 300)]
    a = [int(v) for v in rng.integers(0, 4, 300)]
    b = [int(v) for v in rng.integers(0, 3, 300)]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const x = {json.dumps(x)};
const out = {{}};
for (const [lo, hi, bits] of [[-1, 3, 8], [0.5, 2, 8], [-5, 5, 4], [-0.4, 1.1, 6]]) {{
  const p = m.qparams(lo, hi, bits);
  const xq = m.fakeQuant(x, p);
  out[`${{lo}},${{hi}},${{bits}}`] = {{S: p.S, Z: p.Z, xq, sqnr: m.sqnrDb(x, xq), pred: m.predictedSqnrDb(x, p.S)}};
}}
const f = m.classSizes([{json.dumps(a)}, {json.dumps(b)}]);
console.log(JSON.stringify({{q: out, f, risk: m.reidRisk(f), half: [0.5, 1.5, 2.5, -0.5].map(m.rint)}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    X = np.array(x)
    for key, v in js["q"].items():
        lo, hi, bits = (float(s) for s in key.split(","))
        S, Z, qmin, qmax = dp.qparams(lo, hi, int(bits))
        xq = dp.dequantize(dp.quantize(X, S, Z, qmin, qmax), S, Z)
        assert v["S"] == pytest.approx(S) and v["Z"] == Z
        assert np.allclose(v["xq"], xq)
        assert v["sqnr"] == pytest.approx(dp.sqnr_db(X, xq)) and v["pred"] == pytest.approx(dp.predicted_sqnr_db(X, S))
    f = dp.class_sizes({"a": np.array(a), "b": np.array(b)}, ["a", "b"])
    assert js["f"] == list(f)
    r = dp.reid_risk(f)
    assert js["risk"]["average"] == pytest.approx(r["average"]) and js["risk"]["k"] == r["k"]
    assert js["risk"]["unique"] == pytest.approx(r["unique"])
    assert js["half"] == [float(round(v)) for v in (0.5, 1.5, 2.5, -0.5)]
