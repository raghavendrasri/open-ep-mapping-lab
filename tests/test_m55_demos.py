"""m55 demos: the JS registration-error and projection code matches epml.capstone."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import capstone as C

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m55-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m55-tre and eq-m55-projection in JS."""
    targets = [[0, 0, 0], [30, 0, 0], [-30, 10, 5], [0, 0, 30], [45, -40, 0]]
    pts = [[0, 0, 0], [10, 0, 5], [10, 100, 5], [-20, -30, 10]]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const targets = {json.dumps(targets)};
const pts = {json.dumps(pts)};
const out = {{}};
for (const kind of ["spread", "clustered", "nearly collinear"]) {{
  for (const n of [3, 6, 10]) {{
    out[kind + n] = {{ F: m.fiducialLayout(kind, n), tre: m.predictedTre(m.fiducialLayout(kind, n), targets, 2.5) }};
  }}
}}
out.fre = [3, 6, 12].map((n) => m.predictedFre(n, 2));
out.proj = [-40, 0, 25].map((a) => pts.map((p) => {{ const q = m.project(p, 750, 1100, a); return [q.u, q.v, q.m]; }}));
out.vis = [[0, 5, 0, 0], [3, 4, 0, 30], [0, 5, 0, 90]].map(([x, y, z, a]) => {{ const r = m.visibleError([x, y, z], a); return [r.seen, r.hidden]; }});
out.wire = m.ellipsoidWireframe([25, 20, 22]).map((l) => l[5]);
console.log(JSON.stringify(out));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    for kind in ("spread", "clustered", "nearly collinear"):
        for n in (3, 6, 10):
            F = C.fiducial_layout(kind, n)
            assert np.allclose(js[kind + str(n)]["F"], F)
            assert np.allclose(js[kind + str(n)]["tre"], C.predicted_tre(F, np.array(targets, float), 2.5), rtol=1e-6)
    assert js["fre"] == pytest.approx([C.predicted_fre(n, 2.0) for n in (3, 6, 12)])
    for got, a in zip(js["proj"], (-40, 0, 25)):
        uv, mag = C.project(np.array(pts, float), angle_deg=a)
        assert np.allclose(np.array(got)[:, :2], uv) and np.allclose(np.array(got)[:, 2], mag)
    for got, (x, y, z, a) in zip(js["vis"], [(0, 5, 0, 0), (3, 4, 0, 30), (0, 5, 0, 90)]):
        assert got == pytest.approx(list(C.visible_error([x, y, z], a)), abs=1e-9)
    py = [line[5] for line in C.ellipsoid_wireframe((25, 20, 22))]
    assert np.allclose(js["wire"], py)
