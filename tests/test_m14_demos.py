"""m14 demos: the JS CMRR and noise code matches epml.frontend."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import frontend as F

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m14-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m14-diffamp, eq-m14-imbalance and eq-m14-noise in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{
  wc: m.worstCaseCmrr(10, 0.001), imb: m.imbalanceCmrr(1e4, 1e8), comb: m.combinedCmrr(1e5, 3e4),
  th: m.thermalDensity(2200), tot: m.totalDensity(2200, 4e-9, 2e-12), opt: m.optimalSourceResistance(4e-9, 2e-12),
  db: m.toDb(3162.3),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["wc"] == pytest.approx(F.worst_case_cmrr(10, 0.001))
    assert js["imb"] == pytest.approx(F.imbalance_cmrr(1e4, 1e8))
    assert js["comb"] == pytest.approx(F.combined_cmrr(1e5, 3e4))
    assert js["th"] == pytest.approx(F.thermal_density(2200))
    assert js["tot"] == pytest.approx(F.total_density(2200, 4e-9, 2e-12))
    assert js["opt"] == pytest.approx(F.optimal_source_resistance(4e-9, 2e-12))
    assert js["db"] == pytest.approx(F.to_db(3162.3))
