"""m01 demos: the JS source, dipole, double-layer and wavefront code matches epml.sources."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import sources as S

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m01-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m01-point, eq-m01-dipole, eq-m01-double-layer, eq-m01-core and eq-m01-front-dipole in JS."""
    rs = [0.1, 0.7, 3.0, 40.0]
    ss = [-4.0, -0.2, 0.0, 0.5, 6.0]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const rs = {json.dumps(rs)}, ss = {json.dumps(ss)};
console.log(JSON.stringify({{
  point: rs.map((r) => m.pointPotential(2, 0.5, r)),
  dip: rs.map((r) => m.dipoleAxis(1.5, 1, r)),
  disk: rs.map((r) => m.doubleLayerPotential(1, 1, m.diskSolidAngleAxis(3, r))),
  slope: rs.map((r) => m.falloffSlope((x) => m.dipoleAxis(1, 1, x), r)),
  vm: ss.map((s) => m.frontVm(s, 0.3)),
  im: ss.map((s) => m.frontIm(s, 0.3)),
  front: ss.map((s) => m.frontPotential(s, 0.3, 1.0)),
  line: ss.map((s) => m.lineDipole(1, 1, s, 1.3)),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    obs = np.stack([np.zeros(len(rs)), np.zeros(len(rs)), rs], -1)
    assert js["point"] == pytest.approx(list(S.point_potential(2.0, 0.5, obs)))
    assert js["dip"] == pytest.approx(list(S.dipole_potential((0, 0, 1.5), 1.0, obs)))
    assert js["disk"] == pytest.approx(list(S.double_layer_potential(1.0, 1.0, S.disk_solid_angle_axis(3.0, np.array(rs)))))
    assert js["slope"] == pytest.approx([-2.0] * len(rs), abs=1e-6)
    assert js["vm"] == pytest.approx(list(S.front_vm(np.array(ss), 0.3)))
    assert js["im"] == pytest.approx(list(S.front_im(np.array(ss), 0.3)))
    assert js["front"] == pytest.approx(list(S.front_potential(np.array(ss), 0.3, 1.0)))
    assert js["front"] == pytest.approx(js["line"])
