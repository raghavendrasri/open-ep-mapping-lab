"""m02 demos: the JS image solutions and the SOR finite-difference solver match epml.volume."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import volume as V

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m02-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m02-images, eq-m02-interface and the eq-m02-fd scheme (eq-m02-poisson) in JS."""
    pts3 = [[0.5, 0.2, -1.0], [1.0, -0.5, 0.8], [3.0, 0.0, 2.5]]
    pts2 = [[0.5, -1.0], [1.0, 0.8], [-3.0, 2.5]]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const p3 = {json.dumps(pts3)}, p2 = {json.dumps(pts2)};
const sol = m.twoMediaProblem(24, 10, 1, 3, 2);
console.log(JSON.stringify({{
  k: m.reflectionCoefficient(1, 4),
  i3: p3.map(([x, y, z]) => m.imagePotential3d(1, 1, 4, 2, x, y, z)),
  i2: p2.map(([x, y]) => m.imagePotential2d(1, 1, 4, 2, x, y)),
  phi: Array.from(sol.phi),
  err: sol.err,
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["k"] == pytest.approx(V.reflection_coefficient(1.0, 4.0))
    assert js["i3"] == pytest.approx(list(V.image_potential_3d(1.0, 1.0, 4.0, 2.0, pts3)))
    p2 = np.array(pts2)
    assert js["i2"] == pytest.approx(list(V.image_potential_2d(1.0, 1.0, 4.0, 2.0, p2[:, 0], p2[:, 1])))
    X, Y, h = V.grid(24, 10.0)
    sig = np.where(Y <= 0, 1.0, 3.0)
    exact = V.image_potential_2d(1.0, 1.0, 3.0, 2.0, X, Y)
    phi = V.solve_poisson(sig, V.gaussian_source_2d(X, Y + 2.0, 1.0, 0.3), h, exact)
    assert np.max(np.abs(np.array(js["phi"]).reshape(24, 24) - phi)) < 1e-8
    assert js["err"] > 0
