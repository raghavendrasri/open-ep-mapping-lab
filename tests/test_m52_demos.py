"""m52 demos: the JS MRI code matches epml.mri, and the demo's wall data are up to date."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from epml import mri
from epml.imaging import dice

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m52-common.js").as_posix()
WALL = ROOT / "demos" / "m52-d2-wall.json"
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def test_wall_data_is_current():
    """demos/m52-d2-wall.json is what tools/make_m52_d2.py writes now."""
    sys.path.insert(0, str(ROOT / "tools"))
    import make_m52_d2

    assert json.loads(WALL.read_text()) == json.loads(json.dumps(make_m52_d2.compute()))
    assert WALL.stat().st_size < 2_000_000


@node
def test_js_matches_python():
    """eq-m52-larmor, eq-m52-ir, eq-m52-lge and eq-m52-iir in JS."""
    data = json.loads(WALL.read_text())
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
import {{ readFileSync }} from "node:fs";
const d = JSON.parse(readFileSync({json.dumps(WALL.as_posix())}, "utf8"));
const tis = [50, 150, 262.7, 300, 500];
console.log(JSON.stringify({{
  f: [m.larmorMhz(1.5), m.larmorMhz(3)],
  mz: tis.map((t) => m.irMz(t, 379)),
  mag: tis.map((t) => [m.lgeSignal(t, 238), m.lgeSignal(t, 238, false)]),
  nul: m.nullTime(379), best: m.bestTiSigned(379, 238),
  t1: [m.T1_POST.myocardium, m.T1_POST.infarct, m.T1_BLOOD_ILLUSTRATIVE],
  burden: [0.97, 1.2, 1.61].map((t) => m.burden(d.wall, t)),
  otsu: m.otsuThreshold(d.wall),
  th: d.methods.map((x) => m.thresholdFor(x, d.wall, d.bloodSd)),
  dice: m.dice(d.wall.map((v) => v > 1.2), d.truth.map(Boolean)),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["f"] == pytest.approx([float(mri.larmor_mhz(1.5)), float(mri.larmor_mhz(3.0))])
    tis = np.array([50, 150, 262.7, 300, 500])
    assert js["mz"] == pytest.approx(list(mri.ir_mz(tis, 379.0)))
    assert np.allclose(js["mag"], np.c_[mri.lge_signal(tis, 238.0), mri.lge_signal(tis, 238.0, magnitude=False)])
    assert js["nul"] == pytest.approx(float(mri.null_time(379.0)))
    assert js["best"] == pytest.approx(float(mri.best_ti_signed(379.0, 238.0)))
    b = mri.BAUNER
    assert js["t1"] == pytest.approx([b["myocardium"]["t1_post"], b["infarct"]["t1_post"],
                                       mri.blood_t1_post_illustrative()], abs=0.01)
    wall = np.array(data["wall"])
    assert js["burden"] == pytest.approx([mri.burden(wall, t) for t in (0.97, 1.2, 1.61)])
    width = (wall.max() - wall.min()) / 256
    assert js["otsu"] == pytest.approx(mri.otsu_threshold(wall), abs=1.01 * width)
    blood_sd = data["bloodSd"]
    for got, (name, kv) in zip(js["th"], mri.THRESHOLDS.items()):
        assert got == pytest.approx(mri.threshold_for(name, kv, wall, 1 + blood_sd * np.array([-1, 1])), abs=1.01 * width)
    assert js["dice"] == pytest.approx(dice(wall > 1.2, np.array(data["truth"], bool)))
