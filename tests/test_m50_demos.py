"""m50 demos: the JS ultrasound formulas match epml.ice."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import ice

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m50-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m50-axial, eq-m50-attenuation, eq-m50-steer and eq-m50-frame-rate in JS."""
    theta = [float(v) for v in np.radians(np.linspace(-90, 90, 361))]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const th = {json.dumps(theta)};
const cases = [[16, 0.5, 0.2], [64, 1.0, 0.5], [32, 0.75, -0.3]];
console.log(JSON.stringify({{
  lam: [5, 7.5, 10].map((f) => m.wavelengthMm(f)),
  ax: [[7.5, 2], [10, 3]].map(([f, n]) => m.axialResolutionMm(f, n)),
  loss: m.roundTripLossDb(0.52, 7.5, 4), zmax: m.maxDepthCm(60, 1.88, 10),
  af: cases.map(([n, d, s]) => m.arrayFactor(th, n, d, s)),
  gl: cases.map(([n, d, s]) => m.gratingLobesDeg(d, s)),
  nul: m.firstNullOffset(32, 0.5), fr: m.frameRate(0.08, 96),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["lam"] == pytest.approx([ice.wavelength_mm(f) for f in (5, 7.5, 10)])
    assert js["ax"] == pytest.approx([ice.axial_resolution_mm(7.5, 2), ice.axial_resolution_mm(10, 3)])
    assert js["loss"] == pytest.approx(ice.round_trip_loss_db(0.52, 7.5, 4))
    assert js["zmax"] == pytest.approx(ice.max_depth_cm(60, 1.88, 10))
    for got, (n, d, s) in zip(js["af"], [(16, 0.5, 0.2), (64, 1.0, 0.5), (32, 0.75, -0.3)]):
        assert np.allclose(got, ice.array_factor(np.array(theta), n, d, s), atol=1e-9)
    for got, (n, d, s) in zip(js["gl"], [(16, 0.5, 0.2), (64, 1.0, 0.5), (32, 0.75, -0.3)]):
        assert got == pytest.approx(ice.grating_lobes_deg(d, s))
    assert js["nul"] == pytest.approx(ice.first_null_offset(32, 0.5))
    assert js["fr"] == pytest.approx(ice.frame_rate(0.08, 96))
