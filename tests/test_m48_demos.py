"""m48 demos: the JS wall-reading, visibility and predictive-value code matches epml.overview and epml.ct."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import overview as O

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m48-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m51-wall readings, eq-m48-visibility and eq-m48-lr (with eq-m35-ppv) in JS, and the same published values."""
    cases = [(0.5, 1.0), (1.89, 1.5), (0.3, 4.0), (3.0, 0.64), (6.0, 7.0)]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const cases = {json.dumps(cases)};
const out = {{}};
out.walls = cases.map(([w, g]) => {{
  const s = m.fwhmToSigma(g);
  return [m.slabPeak(w, s), m.fwhmThickness(w, s), m.thresholdThickness(w, s), m.slabProfile(0.3, w, s)];
}});
out.vis = [[1, 0.2, 0.5, 3], [1, 0.2, 1.2, 2], [1, 0.5, 0.5, 3]].map(([c, n, s, k]) => m.minVisibleWall(c, n, s, k));
out.cnr = m.wallCnr(1, 0.25, 0.8, m.fwhmToSigma(1.5));
out.lr = [[0.96, 0.92], [1.0, 0.99], [0.8, 0.7]].map(([a, b]) => m.likelihoodRatios(a, b));
out.pv = [[0.96, 0.92, 0.089], [1.0, 0.99, 0.089], [0.8, 0.7, 0.3]].map(([a, b, p]) => m.predictiveValues(a, b, p));
out.post = m.postTestProbability(0.089, 12);
out.res = m.RESOLUTION_MM.map((r) => r.fwhm);
out.romero = m.ROMERO2013;
out.wall = m.LA_WALL_MM;
console.log(JSON.stringify(out, (k, v) => (v === Infinity ? "inf" : v)));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    for got, (w, g) in zip(js["walls"], cases):
        s = float(O.sigma_from_fwhm(g))
        want = [O.slab_peak(w, s), O.fwhm_thickness(w, s), O.threshold_thickness(w, s), float(O.slab_profile(0.3, w, s))]
        assert got == pytest.approx(want, abs=1e-4)  # JS erf is accurate to 1.5e-7
    want = [O.min_visible_wall(c, n, s, k) for c, n, s, k in [(1, 0.2, 0.5, 3), (1, 0.2, 1.2, 2), (1, 0.5, 0.5, 3)]]
    assert js["vis"][:2] == pytest.approx(want[:2], abs=1e-6) and js["vis"][2] == "inf" and want[2] == np.inf
    assert js["cnr"] == pytest.approx(float(O.wall_cnr(1, 0.25, 0.8, O.sigma_from_fwhm(1.5))), abs=1e-6)
    for got, (a, b) in zip(js["lr"], [(0.96, 0.92), (1.0, 0.99), (0.8, 0.7)]):
        assert [got["pos"], got["neg"]] == pytest.approx(list(O.likelihood_ratios(a, b)))
    for got, (a, b, p) in zip(js["pv"], [(0.96, 0.92, 0.089), (1.0, 0.99, 0.089), (0.8, 0.7, 0.3)]):
        assert [got["ppv"], got["npv"]] == pytest.approx(list(O.ppv_npv(a, b, p)))
    assert js["post"] == pytest.approx(float(O.post_test_probability(0.089, 12.0)))
    assert js["res"] == list(O.RESOLUTION_MM.values())
    r = O.ROMERO2013
    assert js["romero"]["prevalence"] == r["prevalence"]
    assert js["romero"]["standard"] == r["standard"] and js["romero"]["delayed"] == r["delayed imaging"]
    assert js["wall"] == O.LA_WALL_MM
