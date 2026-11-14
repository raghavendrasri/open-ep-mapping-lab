"""m11 demos: the JS AV node and PPI code matches epml.epstudy."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import epstudy as E

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m11-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m11-avnode, eq-m11-wenckebach and eq-m11-ppi in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{
  nct: [91, 150, 300].map((r) => m.nodalTime(r)),
  seq: m.avSequence(220, 30).map((v) => (Number.isFinite(v) ? v : null)),
  ratios: [300, 235, 220, 200, 150].map((c) => m.conductionRatio(m.avSequence(c, 60))),
  ppi: m.ppiMinusTcl(20, 0.5),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["nct"] == pytest.approx(list(E.nodal_time(np.array([91.0, 150.0, 300.0]))), abs=1e-9)
    ref = E.av_sequence(220.0, 30)
    assert [np.nan if v is None else v for v in js["seq"]] == pytest.approx(list(ref), abs=1e-9, nan_ok=True)
    for c, r in zip([300, 235, 220, 200, 150], js["ratios"]):
        assert tuple(r) == E.conduction_ratio(E.av_sequence(float(c), 60))
    assert js["ppi"] == pytest.approx(80.0)
