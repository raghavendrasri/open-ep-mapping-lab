"""m21 demos: the JS threshold, Dice, Procrustes and ICP code matches epml.registration."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import registration as RG

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m21-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m21-threshold, eq-m21-dice, eq-m21-procrustes and eq-m21-icp in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const h = m.mixtureHistogram(100, 300, 60, 0.25);
const tgt = m.outline(200), src = m.outline(40);
const a = 0.3, R = [[Math.cos(a), -Math.sin(a)], [Math.sin(a), Math.cos(a)]];
const moved = m.applyRt(R, [4, -3], src);
const fit = m.procrustes2(src, moved), icp = m.icp2(moved, tgt, 25);
console.log(JSON.stringify({{ h, t: m.otsuFromHistogram(h.hist, h.centers), gd: m.gaussianDice(210, 100, 300, 60, 0.25),
  nd: m.ndtr(0.7), fit, tgt, moved, icp }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    hist, centers = np.array(js["h"]["hist"]), np.array(js["h"]["centers"])
    sb = RG.between_class_variance(hist, centers)
    k = int(np.argmax(sb))
    assert js["t"] == pytest.approx(0.5 * (centers[k] + centers[k + 1]))
    assert js["gd"] == pytest.approx(RG.gaussian_dice(210, 100, 300, 60, 0.25), abs=1e-6)
    assert js["nd"] == pytest.approx(0.758036, abs=1e-6)
    assert js["fit"]["angle"] == pytest.approx(0.3, abs=1e-12)
    tgt, moved = np.array(js["tgt"]), np.array(js["moved"])
    R, t, hist_py = RG.icp(moved, tgt, iters=25, tol=-1.0)
    assert np.array(js["icp"]["R"]) == pytest.approx(R, abs=1e-9)
    assert js["icp"]["hist"] == pytest.approx(hist_py, rel=1e-9, abs=1e-12)
