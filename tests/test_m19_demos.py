"""m19 demos: the JS breathing, gating and reference code matches epml.motion."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import motion as MO

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m19-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m19-breathing, eq-m19-gating, eq-m19-reference and eq-m19-surrogate in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{ z: m.breathing(1.3, 4, 12, 3), d: m.gatingDutyCycle(2.5, 12, 2),
  ds: m.differenceSd(3, 2, 0.4), rs: m.residualSd(3, 0.4) }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["z"] == pytest.approx(MO.breathing(1.3, 4.0, 12.0, 3))
    assert js["d"] == pytest.approx(MO.gating_duty_cycle(2.5, 12.0, 2))
    assert js["ds"] == pytest.approx(MO.difference_sd(3.0, 2.0, 0.4))
    assert js["rs"] == pytest.approx(MO.residual_sd(3.0, 0.4))
