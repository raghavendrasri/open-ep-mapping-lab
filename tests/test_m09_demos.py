"""m09 demos: the JS cable and anisotropy code matches epml.propagation."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import propagation as G

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m09-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m09-cv and eq-m09-anisotropy in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const run = m.msCable(300, 0.1, 0.2, 80);
console.log(JSON.stringify({{
  cv: m.cableCV(run.act, 0.1),
  t: m.pointActivation(3, 4, 1.0, 0.4, 0.5),
  ray: [0, 0.3, 1.2].map((a) => m.raySpeed(a, 1.0, 0.4)),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["cv"] == pytest.approx(G.cable_cv(0.2, dx=0.1, length=30.0), rel=0.01)
    assert js["t"] == pytest.approx(G.point_activation(3, 4, 1.0, 0.4, 0.5), abs=1e-12)
    assert js["ray"] == pytest.approx(list(G.ray_speed(np.array([0, 0.3, 1.2]), 1.0, 0.4)), abs=1e-12)
