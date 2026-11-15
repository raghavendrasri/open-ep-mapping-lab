"""m13 demos: the JS sampling and force code matches epml.catheters."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import catheters as K

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m13-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m13-alias, eq-m13-orthogonal, eq-m13-force and eq-m13-force-noise in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const C = m.forceMatrix([0, 100, -100], 1.7, 0.6);
console.log(JSON.stringify({{
  pk: m.poissonKernel(0.7, 1.3), af: m.aliasFraction(2.0, 1.0), ms: m.maxSpacing(0.8, 0.02),
  op: m.orthogonalPair(0.4), C, cov: m.forceCovariance(C, 0.3),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["pk"] == pytest.approx(K.poisson_kernel(0.7, 1.3))
    assert js["af"] == pytest.approx(K.alias_fraction(2.0, 1.0))
    assert js["ms"] == pytest.approx(K.max_spacing(0.8, 0.02))
    best, rss = K.orthogonal_pair(0.4)
    assert js["op"]["best"] == pytest.approx(best) and js["op"]["rss"] == pytest.approx(rss)
    C = K.force_matrix([0, 100, -100], axial=1.7, lateral=0.6)
    assert np.array(js["C"]) == pytest.approx(C)
    assert np.array(js["cov"]) == pytest.approx(K.force_covariance(C, 0.3), rel=1e-9)
