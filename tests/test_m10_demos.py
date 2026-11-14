"""m10 demos: the JS restitution map and circuit code matches epml.arrhythmia."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import arrhythmia as A

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m10-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m10-restitution, eq-m10-alternans and eq-m10-circuit in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{
  fp: [300, 200, 160].map((c) => m.fixedPoint(c)),
  slope: [20, 55, 120].map((d) => m.restitutionSlope(d)),
  seq: m.iterateMap(150, 100, 8),
  circ: m.circuit(200, 0.8, 150),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    for cl, fp in zip([300, 200, 160], js["fp"]):
        assert fp == pytest.approx(list(A.fixed_point(cl)), abs=1e-6)
    assert js["slope"] == pytest.approx(list(A.restitution_slope(np.array([20, 55, 120]))), abs=1e-12)
    assert js["seq"] == pytest.approx(list(A.iterate_map(150, 100, 8)), abs=1e-9)
    ref = A.circuit(200, 0.8, 150)
    assert js["circ"]["cycleLength"] == pytest.approx(ref["cycle_length"]) and js["circ"]["gapMm"] == pytest.approx(ref["gap_mm"])
