"""m06 demos: the JS lattice-path ratio, path decomposition and cotangent weight match epml.meshes."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import meshes as M

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m06-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m06-geodesic and eq-m06-cotan in JS."""
    thetas = [0.0, 0.3, np.pi / 6, 1.0, 2.0, 4.0]
    pairs = [(1.0, 1.0), (2.0, 1.5), (0.4, 2.5)]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const th = {json.dumps(thetas)}, pr = {json.dumps(pairs)};
console.log(JSON.stringify({{
  ratio: th.map((t) => m.latticePathRatio(t)),
  path: th.map((t) => m.latticePath(8, t)),
  w: pr.map(([a, b]) => m.edgeCotanWeight(a, b)),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["ratio"] == pytest.approx(list(M.lattice_path_ratio(np.array(thetas))))
    for t, p in zip(thetas, js["path"]):
        assert p["a"] + p["b"] == pytest.approx(8 * float(M.lattice_path_ratio(t)))
        e1 = np.array([np.cos(p["k"] * np.pi / 3), np.sin(p["k"] * np.pi / 3)])
        e2 = np.array([np.cos((p["k"] + 1) * np.pi / 3), np.sin((p["k"] + 1) * np.pi / 3)])
        assert p["a"] * e1 + p["b"] * e2 == pytest.approx([8 * np.cos(t), 8 * np.sin(t)], abs=1e-9)
    assert js["w"] == pytest.approx([float(M.edge_cotan_weight(a, b)) for a, b in pairs])
