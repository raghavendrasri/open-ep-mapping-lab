"""m45 demos: the JS CUSUM and sample-size functions match epml.evidence."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import evidence as ev

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m45-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m45-cusum and eq-m45-n-sens in JS."""
    x = [float(v) for v in np.random.default_rng(0).normal(0.3, 1, 80)]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const r = m.cusum({json.dumps(x)}, 0, 0.5, 4);
const z = m.normals(1000, 7);
const mean = z.reduce((a, b) => a + b, 0) / z.length;
const sd = Math.sqrt(z.reduce((a, b) => a + (b - mean) ** 2, 0) / z.length);
console.log(JSON.stringify({{S: r.S, alarm: r.alarm, n1: m.nForSensitivity(0.9, 0.05, 0.2), n2: m.nForSpecificity(0.85, 0.03, 0.1), mean, sd}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    S, alarm = ev.cusum(x, 0, 0.5, 4)
    assert np.allclose(js["S"], S) and js["alarm"] == alarm
    assert js["n1"] == ev.n_for_sensitivity(0.9, 0.05, 0.2) and js["n2"] == ev.n_for_specificity(0.85, 0.03, 0.1)
    assert abs(js["mean"]) < 0.1 and abs(js["sd"] - 1) < 0.08
