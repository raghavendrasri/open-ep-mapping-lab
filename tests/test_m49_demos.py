"""m49 demos: the JS attenuation, contrast and staff-dose code matches epml.fluoro."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import fluoro as fl

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m49-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m49-beer, eq-m49-contrast, eq-m49-cnr and eq-m49-staff in JS."""
    rng = np.random.default_rng(0)
    pts = [[float(a), float(b)] for a, b in zip(rng.uniform(-120, 120, 40), rng.uniform(-90, 90, 40))]
    pts += [[20.0, -10.0], [20.0, -5.0], [0.0, 0.0]]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const ph = m.chestPhantom();
const pts = {json.dumps(pts)};
console.log(JSON.stringify({{
  mu: Object.keys(m.MATERIALS).map((k) => [k, m.muPerMm(k)]),
  L: pts.map(([x, z]) => m.lineIntegral(ph, x, z)),
  c: m.subjectContrast(m.muPerMm("blood"), m.muPerMm("soft tissue"), 90),
  r: m.cnr(0.2, 400),
  s: [m.relativeStaffDose(2, 10), m.relativeStaffDose(1, 30, 1, 7.5), m.relativeStaffDose(0.7, 5, 2, 30, 0.5)],
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    for name, mu in js["mu"]:
        assert mu == pytest.approx(fl.mu_per_mm(name))
    P = np.array(pts)
    assert np.allclose(js["L"], fl.line_integral(fl.chest_phantom(), P[:, 0], P[:, 1]))
    assert js["c"] == pytest.approx(fl.subject_contrast(fl.mu_per_mm("blood"), fl.mu_per_mm("soft tissue"), 90))
    assert js["r"] == pytest.approx(fl.cnr(0.2, 400))
    want = [fl.relative_staff_dose(2, 10), fl.relative_staff_dose(1, 30, 1, 7.5), fl.relative_staff_dose(0.7, 5, 2, 30, 0.5)]
    assert np.allclose(js["s"], want)
