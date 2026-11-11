"""m39 demos: the browser math must match the tested Python in labs/python/epml/graphs.py."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import graphs as gr
from epml import mapping as mp

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m39-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def run_node(script):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout)


@node
def test_js_graph_layers_match_python():
    """eq-m39-gcn (A_hat applied three times) and the hop reach used by m39-d1."""
    nx = 9
    f = np.random.default_rng(1).normal(size=nx * nx)
    js = run_node(f"""
import * as m from "{COMMON}";
const neigh = m.gridNeighbors({nx}, {nx});
let g = {json.dumps(f.tolist())};
for (let l = 0; l < 3; l++) g = m.applyAhat(neigh, g);
console.log(JSON.stringify({{g, reach: m.hopReach(neigh, 40, 2)}}));
""")
    verts, tris = mp.plane_mesh(nx, nx, 2.0)
    A = gr.mesh_adjacency(tris, len(verts))
    Ah = gr.normalized_adjacency(A)
    g = f.copy()
    for _ in range(3):
        g = Ah @ g
    assert np.allclose(js["g"], g)
    assert np.array_equal(np.array(js["reach"]), gr.hop_reach(A, 40, 2))


@node
def test_js_disc_dice_matches_python():
    """eq-m39-lens and eq-m39-dice for discs, used by m39-d2."""
    cases = [(5, 5, 7.3), (8, 3, 6), (4, 6, 9), (5, 2, 1), (3, 3, 7), (5, 5, 0)]
    js = run_node(f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({json.dumps(cases)}.map(([R, r, d]) => m.discDice(R, r, d))));
""")
    assert js == pytest.approx([gr.disc_dice(*c) for c in cases])
