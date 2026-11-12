"""m51 demos: the JS CT code matches epml.ct."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import ct

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m51-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m51-hu, eq-m51-iodine, eq-m51-radon, eq-m51-ramlak, eq-m51-fbp, eq-m51-gating and eq-m51-smear in JS."""
    pts = [[-4.0, 0.0], [0.0, 1.2], [1.0, -0.5], [2.6, 0.3], [0.0, 1.6]]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const ph = m.thoraxPhantom();
const th = m.angles(24);
const s = m.detectorAxis(320, 64);
const rows = m.radonEllipses(ph, th, s);
const r = m.raster(ph, 64, 320);
const rec = m.fbp(rows, th, s, r.x);
const pts = {json.dumps(pts)};
console.log(JSON.stringify({{
  hu: ["water", "air", "soft tissue", "blood", "adipose", "cortical bone"].map((k) => m.hounsfield(m.muPerMm(k))),
  iod: m.hounsfield(m.bloodWithIodineMu(10)),
  ph, s, sino: rows.map((row) => Array.from(row)), img: Array.from(r.img), x: r.x,
  h: Array.from(m.ramlakKernel(5, 2.5)), rec: Array.from(rec),
  plain: Array.from(m.fbp(rows, th, s, r.x, false)),
  win: [m.temporalWindow(0.25, 1), m.temporalWindow(0.33, 2)],
  smear: pts.map(([x, y]) => [m.smearedDisk(x, y, 3, 2.5), m.smearedDisk(x, y, 3, 0)]),
  speed: m.CORONARY_SPEED,
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    names = ["water", "air", "soft tissue", "blood", "adipose", "cortical bone"]
    assert js["hu"] == pytest.approx([float(ct.hounsfield(ct.mu_per_mm(k))) for k in names])
    assert js["iod"] == pytest.approx(float(ct.hounsfield(ct.blood_with_iodine_mu(10))))
    assert np.allclose(np.array(js["ph"]), np.array(ct.thorax_phantom()))
    s = ct.detector_axis(320, 64)
    assert np.allclose(js["s"], s)
    th = ct.angles(24)
    sino = ct.radon_ellipses(ct.thorax_phantom(), th, s)
    assert np.allclose(js["sino"], sino, atol=1e-9)
    img, x = ct.raster(ct.thorax_phantom(), n=64)
    assert np.allclose(js["x"], x)
    assert np.allclose(np.array(js["img"]).reshape(64, 64), img)
    assert np.allclose(js["h"], ct.ramlak_kernel(5, 2.5))
    assert np.allclose(np.array(js["rec"]).reshape(64, 64), ct.fbp(sino, th, s, x), atol=1e-9)
    assert np.allclose(np.array(js["plain"]).reshape(64, 64), ct.fbp(sino, th, s, x, filtered=False), atol=1e-9)
    assert js["win"] == pytest.approx([ct.temporal_window(0.25, 1), ct.temporal_window(0.33, 2)])
    for (x0, y0), (moving, still) in zip(pts, js["smear"]):
        assert moving == pytest.approx(float(ct.smeared_disk(x0, y0, 3, 2.5)))
        assert still == pytest.approx(float(ct.smeared_disk(x0, y0, 3, 0)))
    assert js["speed"] == ct.CORONARY_SPEED
