"""m15 demos: the JS leakage and filter code matches epml.safety."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import safety as S

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m15-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m15-leakage and eq-m15-rf-filter in JS, and the cited thresholds."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{
  ic: m.capacitiveCurrent(120, 60, 3.3e-10), cm: m.maxCapacitance(2e-5, 230, 50),
  att: m.lowpassAttenuation(4.5e5, 700, 3), n: m.orderNeeded(7, 2e-6, 4.5e5, 700), sw: m.SWERDLOW_1999_UA,
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["ic"] == pytest.approx(S.capacitive_current(120, 60, 3.3e-10))
    assert js["cm"] == pytest.approx(S.max_capacitance(2e-5, 230, 50))
    assert js["att"] == pytest.approx(S.lowpass_attenuation(4.5e5, 700, 3))
    assert js["n"] == S.order_needed(7, 2e-6, 4.5e5, 700)
    s = S.SWERDLOW_1999_UA
    assert [js["sw"][k] for k in ("intermittentCapture", "continuousCapture", "ventricularFibrillation", "usStandardSingleFault")] == \
        [s[k] for k in ("intermittent_capture", "continuous_capture", "ventricular_fibrillation", "us_standard_single_fault")]
