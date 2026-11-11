"""m37 demos: the browser math must match the tested Python in labs/python/epml/aiecg.py."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import aiecg as ai

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m37-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def run_node(script):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout)


@node
def test_js_receptive_field_matches_python():
    """eq-m37-receptive-field in m37-d1."""
    cases = [([9] * 4, [1, 2, 2, 2]), ([3], [1]), ([31] * 10, [1] + [3] * 9), ([5, 7], [1, 1])]
    js = run_node(f"""
import * as m from "{COMMON}";
const cases = {json.dumps(cases)};
console.log(JSON.stringify(cases.map(([k, s]) => m.receptiveField(k, s))));
""")
    assert js == [ai.receptive_field(k, s) for k, s in cases]


@node
def test_js_beat_and_waves_match_python():
    t = np.linspace(-0.5, 0.6, 111)
    js = run_node(f"""
import * as m from "{COMMON}";
const t = {json.dumps(t.tolist())};
console.log(JSON.stringify({{a: t.map((v) => m.beat(v)), b: t.map((v) => m.beat(v, 0.7, false)), waves: m.WAVES}}));
""")
    assert np.allclose(js["a"], ai.beat(t))
    assert np.allclose(js["b"], ai.beat(t, 0.7, p_wave=False))
    assert [tuple(w) for w in js["waves"]] == [tuple(w) for w in ai.WAVES]


@node
def test_js_yield_and_prior_shift_match_python():
    """eq-m37-yield and eq-m37-prior-shift in m37-d2."""
    grid = [(0.02, 0.8, 0.9), (0.2, 0.95, 0.99), (0.005, 0.6, 0.7)]
    p = np.linspace(0.01, 0.99, 21)
    js = run_node(f"""
import * as m from "{COMMON}";
const grid = {json.dumps(grid)};
const p = {json.dumps(p.tolist())};
console.log(JSON.stringify({{y: grid.map(([pi, se, sp]) => m.screeningYield(1000, pi, se, sp)),
  s: p.map((v) => m.priorShift(v, 0.5, 0.02))}}));
""")
    for (pi, se, sp_), y in zip(grid, js["y"]):
        ref = ai.screening_yield(1000, pi, se, sp_)
        assert y["flagged"] == pytest.approx(ref["flagged"]) and y["perCase"] == pytest.approx(ref["per_case"])
    assert np.allclose(js["s"], ai.prior_shift(p, 0.5, 0.02))
