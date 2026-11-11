"""m40 demos: the browser math must match the tested Python in labs/python/epml/imaging.py."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import imaging as im

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m40-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def run_node(script):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout)


@node
def test_js_closed_forms_match_python():
    """eq-m40-sphere, eq-m40-slab and eq-m40-offset as used by m40-d2."""
    cases = [(25, 1.0), (10, 0.5), (5, 2.0), (1.89, 1.0), (20, -3.0)]
    js = run_node(f"""
import * as m from "{COMMON}";
const c = {json.dumps(cases)};
console.log(JSON.stringify({{
  sphere: c.map(([R, d]) => m.sphereDice(R, d)),
  disc: c.map(([R, d]) => m.discDice(R, d)),
  slab: c.map(([t, d]) => m.slabDice(t, d)),
  lin: c.map(([R, d]) => m.offsetDiceFirstOrder(d, 4 * Math.PI * R * R, 4 / 3 * Math.PI * R ** 3)),
}}));
""")
    assert js["sphere"] == pytest.approx([float(im.sphere_dice(*c)) for c in cases])
    assert js["disc"] == pytest.approx([float(im.disc_dice(*c)) for c in cases])
    assert js["slab"] == pytest.approx([float(im.slab_dice(*c)) for c in cases])
    assert js["lin"] == pytest.approx([1 - 3 * abs(d) / (2 * R) for R, d in cases])


@node
def test_js_circle_island_metrics_match_python():
    """The m40-d1 readout (Dice, Hausdorff, ASSD, NSD) against epml.imaging.circle_island_metrics."""
    cases = [(20, 1.0, 2.0, 15, 4), (20, -2.5, 3.0, 2, 4), (10, 0.0, 0.0, 5, 1), (8, 3.0, 1.0, 1, 2.5)]
    js = run_node(f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({json.dumps(cases)}.map((c) => m.circleIslandMetrics(...c))));
""")
    for c, j in zip(cases, js):
        py = im.circle_island_metrics(*c)
        for k in ("dice", "hd", "assd", "nsd"):
            assert j[k] == pytest.approx(py[k], rel=1e-9, abs=1e-12), (c, k)
