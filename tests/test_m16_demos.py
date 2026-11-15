"""m16 demos: the JS field, Jacobian, CRLB and bias code matches epml.magnetic."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import magnetic as M

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m16-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m16-dipole, eq-m16-coupling, eq-m16-crlb and eq-m16-distortion in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const gen = m.generator();
const q = [10, -20, 150, 0.6, 1.1];
const v = m.readings(q, gen), d = m.distortedReadings(q, gen, [60, 0, 250], 2000);
console.log(JSON.stringify({{
  b: m.dipoleField([0.3, -0.2, 1.0], [10, 20, 30]), v, sd: m.positionSd(q, gen, 1e-4),
  bias: m.linearBias(q, gen, d.map((x, k) => x - v[k])),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    gen = M.generator()
    q = np.array([10.0, -20.0, 150.0, 0.6, 1.1])
    assert js["b"] == pytest.approx(M.dipole_field(np.array([0.3, -0.2, 1.0]), np.array([10.0, 20.0, 30.0])))
    assert js["v"] == pytest.approx(M.readings(q, gen), rel=1e-12)
    assert js["sd"] == pytest.approx(M.position_sd(q, gen, 1e-4), rel=1e-6)
    dv = M.distorted_readings(q, gen, np.array([60.0, 0.0, 250.0]), 2000.0) - M.readings(q, gen)
    assert js["bias"] == pytest.approx(M.linear_bias(q, gen, dv), rel=1e-5, abs=1e-9)
