"""m23 demos: the JS amplitude, direction and threshold code matches epml.voltage."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import voltage as VM

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m23-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m23-amplitude, eq-m23-direction and eq-m23-threshold in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const r = m.pairAndField(1.3, 0.2, 0.6, 180);
console.log(JSON.stringify({{ bp: m.bipolarPp(1.3, 2.0, 0.4), bs: m.bipolarPpSmall(1.3, 2.0, 0.4), hf: m.heightFactor(1.3, 1.0),
  bf: m.belowFraction(0.33), single: r.single, pair: r.pair, field: r.field, ref: m.bipolarPp(1.3, 0.2, 0),
  tr: m.thresholdRates(1.5, 0.2, 2.5, 0.7, 0.7) }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["bp"] == pytest.approx(VM.bipolar_pp(1.3, 2.0, 0.4), rel=1e-4)
    assert js["bs"] == pytest.approx(VM.bipolar_pp_small(1.3, 2.0, 0.4))
    assert js["hf"] == pytest.approx(VM.height_factor(1.3, 1.0))
    assert js["bf"] == pytest.approx(VM.below_fraction(0.33))
    assert js["single"] == pytest.approx(VM.bipolar_pp(1.3, 0.2, 0.6), rel=1e-4)
    assert js["pair"] == pytest.approx(max(VM.bipolar_pp(1.3, 0.2, 0.6), VM.bipolar_pp(1.3, 0.2, np.pi / 2 - 0.6)), rel=1e-4)
    assert js["field"] == pytest.approx(VM.field_pp(1.3, 0.2, 0.6, n_dir=180), rel=1e-3)
    assert js["field"] == pytest.approx(js["ref"], rel=5e-3)
    sens, spec = VM.threshold_rates(1.5, 0.2, 2.5, 0.7, 0.7)
    assert js["tr"][0] == pytest.approx(sens, abs=1e-6) and js["tr"][1] == pytest.approx(spec, abs=1e-6)
