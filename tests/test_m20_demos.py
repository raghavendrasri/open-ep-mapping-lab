"""m20 demos: the JS reconstruction, hull, distances and smoothing match epml.geometry."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import geometry as G

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m20-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m20-hull, eq-m20-closing, eq-m20-distance and eq-m20-smoothing in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const P = m.wallSamples(200, 2, 7);
const R = m.reconstruct(P, 5), H = m.hullMask(P), T = m.truthMask();
const poly = Array.from({{ length: 12 }}, (_, i) => [3 * Math.cos(2 * Math.PI * i / 12), 3 * Math.sin(2 * Math.PI * i / 12)]);
console.log(JSON.stringify({{ P, R: Array.from(R), H: Array.from(H), T: Array.from(T), sr: m.surfaceStats(R, T),
  step: m.umbrellaStep(poly, 0.4), f: m.polygonFactor(12, 0.4, -0.45) }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    ax = np.arange(-50.0, 50.001, 1.0)
    P = np.array(js["P"])
    shape = (len(ax), len(ax))
    _, T = G.truth_mask(1.0, 50.0, 2)
    assert np.array_equal(np.array(js["T"], bool).reshape(shape), T)
    R = G.reconstruct(P, ax, 5.0)
    assert np.mean(np.array(js["R"], bool).reshape(shape) != R) < 1e-3
    assert np.mean(np.array(js["H"], bool).reshape(shape) != G.hull_mask(P, ax)) < 2e-3
    assert js["sr"]["hausdorff"] == pytest.approx(G.hausdorff(R, T, ax), abs=1.0)
    assert js["sr"]["mean"] == pytest.approx(G.mean_surface_distance(R, T, ax), abs=0.2)
    V, nb = G.polygon(12, 3.0)
    assert np.array(js["step"]) == pytest.approx(G.umbrella_step(V, nb, 0.4))
    assert js["f"] == pytest.approx(G.polygon_factor(12, 0.4, -0.45))
