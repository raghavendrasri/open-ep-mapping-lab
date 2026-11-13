"""m04 demos: the JS aliasing, Butterworth, filtering and downstroke code matches epml.recording."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import recording as R

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m04-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m04-sampling, eq-m04-butterworth, eq-m04-highpass and eq-m04-delay in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const fs = 20000;
const t = Array.from({{ length: 4000 }}, (_, i) => -100 + (i * 1000) / fs);
const x = t.map((v) => m.unipolarEgm(v));
const res = {{}};
res.alias = [10, 600, 950, 1050, 1490].map((f) => m.aliasFrequency(f, 1000));
res.coef = [[1, "low"], [1, "high"], [2, "low"], [2, "high"]].map(([o, k]) => m.butterDigital(30, 1000, o, k));
for (const [name, opts] of [["causal", {{ hp: 30, lp: 500 }}], ["zero", {{ hp: 100, lp: 500, zeroPhase: true }}]]) {{
  const y = m.chain(x, fs, opts);
  res[name] = {{ y: Array.from(y).filter((_, i) => i % 97 === 0), lat: m.steepestDownstroke(t, Array.from(y)) }};
}}
res.lat0 = m.steepestDownstroke(t, x);
console.log(JSON.stringify(res));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["alias"] == list(R.alias_frequency([10, 600, 950, 1050, 1490], 1000))
    for got, (o, k) in zip(js["coef"], [(1, "low"), (1, "high"), (2, "low"), (2, "high")]):
        b, a = R.butter_digital(30.0, 1000.0, o, k)
        assert got["b"] == pytest.approx(list(b), abs=1e-12) and got["a"] == pytest.approx(list(a), abs=1e-12)
    fs = 20000.0
    t = -100 + np.arange(4000) * 1000 / fs
    x = R.unipolar_egm(t)
    for name, kw in (("causal", dict(hp=30.0, lp=500.0)), ("zero", dict(hp=100.0, lp=500.0, zero_phase=True))):
        y = R.chain(x, fs, **kw)
        assert js[name]["y"] == pytest.approx(list(y[::97]), abs=1e-9)
        assert js[name]["lat"] == pytest.approx(R.steepest_downstroke(t, y), abs=1e-9)
    assert js["lat0"] == pytest.approx(R.steepest_downstroke(t, x), abs=1e-9)
