"""m17 demos: the JS potential and linear-map code matches epml.impedance."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import impedance as Z

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m17-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m17-pair, eq-m17-axis and eq-m17-linear in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const P = m.patchPairs(180);
console.log(JSON.stringify({{
  pot: m.potentials([30, -40, 20], P), ax: m.axisPotential(45, 180), e0: m.centerField(180),
  lin: m.linearEstimate(m.axisPotential(45, 180), 180),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["pot"] == pytest.approx(Z.potentials(np.array([30.0, -40.0, 20.0]), Z.patch_pairs(180.0)))
    assert js["ax"] == pytest.approx(Z.axis_potential(45.0, 180.0))
    assert js["e0"] == pytest.approx(Z.center_field(180.0))
    assert js["lin"] == pytest.approx(Z.linear_estimate(Z.axis_potential(45.0, 180.0), 180.0))
