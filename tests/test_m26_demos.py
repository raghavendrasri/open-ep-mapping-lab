"""m26 demos: the JS Gaussian-process, budget and density code matches epml.uncertainty."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import uncertainty as UN

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m26-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m26-gp, eq-m26-budget and eq-m26-density in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const [mu, vr] = m.gpPosterior([2, 9, 15, 30], [10, 4, 7, 22], [0, 5, 12, 40], 6, 100, 1.2, 9);
console.log(JSON.stringify({{ mu, vr, sp: m.singlePointVariance(3, 8, 400, 2), eb: m.errorBudget(1, 2, 2, 0.8),
  nn: m.nnDistanceMean(0.01) }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    X = np.array([[2.0], [9.0], [15.0], [30.0]])
    mu, var = UN.gp_posterior(X, [10, 4, 7, 22], np.array([[0.0], [5.0], [12.0], [40.0]]), 6.0, 100.0, 1.2, 9.0)
    assert np.allclose(js["mu"], mu, rtol=1e-9) and np.allclose(js["vr"], var, rtol=1e-9)
    assert js["sp"] == pytest.approx(UN.single_point_variance(3.0, 8.0, 400.0, 2.0))
    assert js["eb"] == pytest.approx(UN.error_budget(1.0, 2.0, 2.0, 0.8))
    assert js["nn"] == pytest.approx(UN.nn_distance_mean(0.01))
