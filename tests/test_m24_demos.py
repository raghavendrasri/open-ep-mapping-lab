"""m24 demos: the JS interpolation, isoline and coverage code matches epml.interpolation."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import interpolation as IP

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m24-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m24-linear, eq-m24-idw, eq-m24-isochrone and eq-m24-block (with coverage) in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const pts = [[1, 2], [5, 1], [3, 7], [8, 6]], vals = [3, 7, 2, 9];
const T = []; for (let j = 0; j < 11; j++) {{ const r = []; for (let i = 0; i < 11; i++) r.push(i * 2 / 0.8); T.push(r); }}
const segs = m.isolines(T, 0, 0, 2, 2, 10);
console.log(JSON.stringify({{ lin: m.linear1d([0, 2, 5], [1, 3, 9], 3.5), idw: m.idw(pts, vals, [4, 4], 2.5),
  xs: segs.flatMap((s) => [s[0][0], s[1][0]]), av: m.apparentVelocity(4, 100), cov: m.coverageFraction(0.005, 5),
  eb: m.linearErrorBound(5, 0.2) }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["lin"] == pytest.approx(IP.linear_1d([0, 2, 5], [1, 3, 9], 3.5))
    pts = np.array([[1, 2], [5, 1], [3, 7], [8, 6]], float)
    assert js["idw"] == pytest.approx(IP.idw_points(pts, [3, 7, 2, 9], [[4, 4]], 2.5)[0])
    assert len(js["xs"]) > 0 and np.allclose(js["xs"], 0.8 * 10)
    assert js["av"] == pytest.approx(IP.apparent_velocity_across_block(4, 100))
    assert js["cov"] == pytest.approx(IP.coverage_fraction(0.005, 5))
    assert js["eb"] == pytest.approx(IP.linear_error_bound(5, 0.2))
