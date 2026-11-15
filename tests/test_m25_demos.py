"""m25 demos: the JS error and clique code matches epml.velocity."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import velocity as VE

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m25-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m25-pair, eq-m25-triangle, eq-m25-planefit and eq-m25-omnipolar in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{ pr: m.pairRelativeError(0.8, 1.2, 5), eq: m.equilateralGradientSd(1.0, 4),
  disk: m.diskFitSd(1.0, 20, 4), v: m.cliqueVelocity(1.0, 0.35, 1.3, 2.0), r: m.cliqueSpeedRatioAxis(2.0, 1.3) }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["pr"] == pytest.approx(VE.pair_relative_error(0.8, 1.2, 5))
    assert js["eq"] ** 2 == pytest.approx(VE.triangle_covariance(VE.equilateral(4.0), 1.0)[0, 0])
    assert js["disk"] == pytest.approx(VE.disk_fit_sd(1.0, 20, 4))
    assert np.allclose(js["v"], VE.clique_velocity(1.0, 0.35, 1.3, 2.0), rtol=1e-5)
    assert js["r"] == pytest.approx(VE.clique_speed_ratio_axis(2.0, 1.3))
