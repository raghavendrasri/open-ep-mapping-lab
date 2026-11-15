"""m22 demos: the JS annotation and window code matches epml.annotation."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import annotation as AN

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m22-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m22-intrinsic, eq-m22-onset and eq-m22-woi in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const t = []; for (let x = -15; x <= 15.0001; x += 0.01) t.push(x);
const u = t.map((x) => m.unipolarTrace(x, 1.0, 1.3, 1.0));
const b = t.map((x) => m.bipolarTrace(x, 1.0, 2.3, 2.0));
console.log(JSON.stringify({{ sd: m.steepestDownstroke(t, u), pk: m.peakTime(t, b), on: m.onsetTime(t, b, 0.2),
  r: m.onsetLeadRatio(0.1), w: [m.windowLat(-130, -150, 250, 250), m.windowLat(130, -150, 250, 250),
  m.windowLat(90, -150, 200, 250)] }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    t = np.arange(-1500, 1501) * 0.01
    assert js["sd"] == pytest.approx(AN.steepest_downstroke(t, AN.unipolar_trace(t, 1.0, 1.3, 1.0)), abs=1e-6)
    b = AN.bipolar_trace(t, 1.0, 2.3, 2.0)
    assert js["pk"] == pytest.approx(AN.peak_time(t, b), abs=1e-6)
    assert js["on"] == pytest.approx(AN.onset_time(t, b, 0.2), abs=1e-6)
    assert js["r"] == pytest.approx(AN.onset_lead_ratio(0.1))
    w = AN.window_lat(np.array([-130.0, 130.0, 90.0]), -150.0, np.array([250.0, 250.0, 200.0]), 250.0)
    assert js["w"][0] == pytest.approx(w[0]) and js["w"][1] == pytest.approx(w[1])
    assert js["w"][2] is None and np.isnan(w[2])
