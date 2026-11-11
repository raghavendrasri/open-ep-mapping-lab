"""m44 demos: the JS compounding formulas match epml.agent, and the precomputed m44-d1 traces match
a fresh run of the tested agent."""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import agent as ag

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m44-common.js").as_posix()
DATA = ROOT / "demos" / "m44-d1-data.json"
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_formulas_match_python():
    """eq-m44-chain, eq-m44-check, eq-m44-escape and eq-m44-mixture in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
console.log(JSON.stringify([m.chainSuccess(0.93, 7), m.checkedChain(0.9, 0.7, 12, 0.9), m.checkedStep(0.8, 0.5),
  m.escapedErrors(100, 0.62, 0.4), m.mixtureChain(0.99, 0.7, 0.2, 8)]));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    py = [ag.chain_success(0.93, 7), ag.checked_chain(0.9, 0.7, 12, 0.9), ag.checked_step(0.8, 0.5),
          ag.escaped_errors(100, 0.62, 0.4), ag.mixture_chain(0.99, 0.7, 0.2, 8)]
    assert js == pytest.approx(py, rel=1e-12)


def test_precomputed_m44_d1_matches_python():
    spec = importlib.util.spec_from_file_location("make_m44_d1", ROOT / "tools" / "make_m44_d1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fresh = mod.compute()
    stored = json.loads(DATA.read_text())
    assert stored == json.loads(json.dumps(fresh, ensure_ascii=False))
    assert DATA.stat().st_size < 2_000_000
    on, off = stored["runs"]["111"], stored["runs"]["000"]
    assert not (on["deleteRan"] or on["outsideWrite"] or on["unitSlipPassed"])
    assert off["deleteRan"] and off["outsideWrite"] and off["unitSlipPassed"]
    assert stored["runs"]["101"]["deleteRan"]        # approval alone does not stop an unknown tool
