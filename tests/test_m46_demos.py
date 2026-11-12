"""m46 demos: the JS conformal sets and fairness formulas match epml.trust."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import trust as tr

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m46-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m46-conformal and eq-m46-fpr in JS."""
    rng = np.random.default_rng(0)
    L = rng.normal(size=(120, 3))
    P = np.exp(L) / np.exp(L).sum(axis=1, keepdims=True)
    y = rng.integers(0, 3, 120)
    Pl, yl = [[float(v) for v in r] for r in P], [int(v) for v in y]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const P = {json.dumps(Pl)}; const y = {json.dumps(yl)};
console.log(JSON.stringify({{q: m.conformalQuantile(P.slice(0, 60).map((p, i) => 1 - p[y[i]]), 0.1),
  a: m.conformalSets(P.slice(0, 60), y.slice(0, 60), P.slice(60), 0.1, false),
  b: m.conformalSets(P.slice(0, 60), y.slice(0, 60), P.slice(60), 0.2, true),
  ppv: m.ppv(0.1, 0.9, 0.05), f: m.fprFromPpv(0.3, 0.7, 0.85)}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    assert js["q"] == pytest.approx(tr.conformal_quantile(1 - P[:60][np.arange(60), y[:60]], 0.1))
    assert np.array_equal(np.array(js["a"]), tr.conformal_sets(P[:60], y[:60], P[60:], 0.1))
    assert np.array_equal(np.array(js["b"]), tr.conformal_sets(P[:60], y[:60], P[60:], 0.2, by_class=True))
    assert js["ppv"] == pytest.approx(tr.ppv(0.1, 0.9, 0.05)) and js["f"] == pytest.approx(tr.fpr_from_ppv(0.3, 0.7, 0.85))
