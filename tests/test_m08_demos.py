"""m08 demos: the JS FitzHugh-Nagumo and Mitchell-Schaeffer code matches epml.membrane."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import membrane as M

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m08-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m08-fhn, eq-m08-hopf, eq-m08-ms and eq-m08-apd in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const sim = m.fhnSimulate(50, 0.02, 0.1, 0.8);
console.log(JSON.stringify({{
  fp: m.fhnFixedPoint(0.2), hopf: m.fhnHopf(), fhn_end: [sim.v[sim.v.length - 1], sim.w[sim.w.length - 1]],
  closed: [20, 100, 400].map((d) => m.msApdClosed(d)),
  s1s2: [260, 300, 400].map((s) => m.s1s2(s).row),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["fp"] == pytest.approx(list(M.fhn_fixed_point(0.2)), abs=1e-10)
    assert js["hopf"] == pytest.approx(M.fhn_hopf_current(), abs=1e-12)
    _, v, w = M.fhn_simulate(50, 0.02, current=0.1, kick=0.8)
    assert js["fhn_end"] == pytest.approx([v[-1], w[-1]], abs=1e-9)
    assert js["closed"] == pytest.approx(list(M.ms_apd_closed(np.array([20, 100, 400]), **M.MS_PARAMS)), abs=1e-9)
    ref = M.s1s2(np.array([260.0, 300.0, 400.0]), M.MS_PARAMS)
    assert np.allclose(np.array(js["s1s2"]), ref, atol=0.05)
