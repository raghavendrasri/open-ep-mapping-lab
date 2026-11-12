"""m54 demos: the JS decay, SUV and partial-volume code matches epml.nuclear."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import nuclear as N

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m54-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m54-decay, eq-m54-suv, eq-m54-recovery and eq-m54-change in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const ws = [2, 5, 10, 15, 25];
const fw = [4, 5.5, 7];
console.log(JSON.stringify({{
  a: [0, 60, 109.73, 300].map((t) => m.activity(370, t)),
  clk: [-10, 5, 10, 20].map((d) => m.clockErrorBias(d)),
  suv: [m.suv(5, 370, 70, 60), m.suv(5, 370, 70, 60, 7.4)],
  pk: fw.map((f) => ws.map((w) => m.rcPeak(w, m.fwhmToSigma(f)))),
  mn: fw.map((f) => ws.map((w) => m.rcMean(w, m.fwhmToSigma(f)))),
  prof: [-8, -3, 0, 4].map((x) => m.slabProfile(x, 10, m.fwhmToSigma(5.5))),
  resp: [1, 0.8, 0.7].map((r) => m.pCalledResponder(r)),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["a"] == pytest.approx([float(N.activity(370.0, t)) for t in (0, 60, 109.73, 300)])
    assert js["clk"] == pytest.approx([float(N.clock_error_bias(d)) for d in (-10, 5, 10, 20)])
    assert js["suv"] == pytest.approx([float(N.suv(5, 370, 70, 60)), float(N.suv(5, 370, 70, 60, residual_mbq=7.4))])
    for k, f in enumerate((4, 5.5, 7)):
        s = N.fwhm_to_sigma(f)
        assert js["pk"][k] == pytest.approx([N.rc_peak(w, s) for w in (2, 5, 10, 15, 25)], abs=1e-6)
        assert js["mn"][k] == pytest.approx([N.rc_mean(w, s) for w in (2, 5, 10, 15, 25)], abs=1e-6)
    assert js["prof"] == pytest.approx([float(N.slab_profile(x, 10, N.fwhm_to_sigma(5.5))) for x in (-8, -3, 0, 4)], abs=1e-6)
    assert js["resp"] == pytest.approx([float(N.p_called_responder(r)) for r in (1, 0.8, 0.7)], abs=1e-5)
