"""m12 demos: the JS sphere, lead and axis code matches epml.ecg."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import ecg as G

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m12-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m12-sphere, eq-m12-series, eq-m12-lead, eq-m12-einthoven, eq-m12-augmented and eq-m12-axis in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const p = [0.3, 0.8, 0.2];
console.log(JSON.stringify({{
  centric: m.leadsForDipole(p),
  ecc: m.leadsForDipole(p, [0.3, 0.1, 0.0]),
  lv: m.leadVector(m.LIMBS.L, m.LIMBS.R, [0.3, 0.0, 0.0]),
  axis: m.frontalAxis(0.4, 0.2),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    p = np.array([0.3, 0.8, 0.2])
    for key, r0 in (("centric", (0.0, 0.0, 0.0)), ("ecc", (0.3, 0.1, 0.0))):
        ref = G.leads_for_dipole(p, r0)
        for k in ("I", "II", "III", "aVR", "aVL", "aVF"):
            assert js[key][k] == pytest.approx(float(ref[k]), abs=1e-6)
    assert js["lv"] == pytest.approx(list(G.lead_vector(G.LIMBS["L"], G.LIMBS["R"], [0.3, 0.0, 0.0])), abs=1e-6)
    assert js["axis"] == pytest.approx(float(G.frontal_axis(0.4, 0.2)), abs=1e-12)
