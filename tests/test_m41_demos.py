"""m41 demos: the browser GP and expected improvement must match the tested Python in epml/origins.py."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import origins as og

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m41-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def run_node(script):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout)


@node
def test_js_gp_and_ei_match_python():
    """eq-m41-gp and eq-m41-ei as used by m41-d1 and m41-d2."""
    rng = np.random.default_rng(5)
    Xtr, ytr, Xte = rng.uniform(0, 60, (6, 2)), rng.normal(size=6), rng.uniform(0, 60, (25, 2))
    js = run_node(f"""
import * as m from "{COMMON}";
const p = m.gpPosterior({json.dumps(Xtr.tolist())}, {json.dumps(ytr.tolist())}, {json.dumps(Xte.tolist())}, 12, 0.5, 0.01, 0.1);
const ei = p.mu.map((mu, i) => m.expectedImprovement(mu, Math.sqrt(p.variance[i]), 0.3, 0.02));
console.log(JSON.stringify({{mu: p.mu, variance: p.variance, ei}}));
""")
    mu, var = og.gp_posterior(Xtr, ytr, Xte, 12, 0.5, 0.01, mean=0.1)
    assert np.allclose(js["mu"], mu) and np.allclose(js["variance"], var, atol=1e-10)
    assert np.allclose(js["ei"], og.expected_improvement(mu, np.sqrt(var), 0.3, 0.02), atol=1e-6)


@node
def test_js_pacing_sequence_matches_python_rule():
    """The EI sequence of m41-d1 equals epml.origins.active_pacemap on the same grid and landscape."""
    js = run_node(f"""
import * as m from "{COMMON}";
const NX = 31, H = 2;
const grid = Array.from({{ length: NX * NX }}, (_, k) => [(k % NX) * H, Math.floor(k / NX) * H]);
const values = grid.map(([x, y]) => m.similarity(x, y));
console.log(JSON.stringify({{seq: m.pacingSequence(grid, values, 10, {{ ell: 12, sf: 0.5, sn: 0.01 }}), values}}));
""")
    g = np.array([[(k % 31) * 2.0, (k // 31) * 2.0] for k in range(31 * 31)])
    vals = np.array(js["values"])
    seq = og.active_pacemap(vals, g, [0, len(g) - 1], 10, ell=12, sf=0.5, sn=0.01, rule="ei")
    assert js["seq"] == seq
