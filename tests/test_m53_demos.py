"""m53 demos: the JS lesion-gap and frame-rate code matches epml.lesion."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import lesion as L

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m53-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m53-gap and eq-m53-frame in JS."""
    cases = [(4.0, 1.5, 1.5), (2.0, 0.5, 2.5), (6.0, 3.0, 1.0), (1.0, 1.0, 3.0)]
    pts = [(0.0, 0.0), (0.4, 0.3), (2.0, -1.0), (-5.0, 0.0)]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const cases = {json.dumps(cases)};
const pts = {json.dumps(pts)};
console.log(JSON.stringify({{
  img: cases.map(([w, g, f]) => pts.map(([x, y]) => m.bandGapImage(x, y, w, g, m.fwhmToSigma(f)))),
  peak: cases.map(([w, g, f]) => m.bandPeak(w, m.fwhmToSigma(f))),
  center: cases.map(([w, g, f]) => m.gapCenter(w, g, m.fwhmToSigma(f))),
  gmin: cases.map(([w, g, f]) => {{ const v = m.minVisibleGap(w, m.fwhmToSigma(f)); return Number.isFinite(v) ? v : -1; }}),
  ft: [m.frameTimeMs(64, 3), m.frameTimeMs(128, 2.5, 2)], fps: [m.fps(64, 3), m.fps(200, 4, 4)],
  ref: [m.FPS_PASSIVE, m.FPS_ACTIVE],
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    for k, (w, g, f) in enumerate(cases):
        s = L.fwhm_to_sigma(f)
        for got, (x, y) in zip(js["img"][k], pts):
            assert got == pytest.approx(float(L.band_gap_image(x, y, w, g, s)), abs=1e-6)
        assert js["peak"][k] == pytest.approx(L.band_peak(w, s), abs=1e-6)
        assert js["center"][k] == pytest.approx(L.gap_center(w, g, s), abs=1e-6)
        gm = L.min_visible_gap(w, s)
        assert js["gmin"][k] == (pytest.approx(gm, abs=1e-4) if gm != float("inf") else -1)
    assert js["ft"] == pytest.approx([L.frame_time_ms(64, 3), L.frame_time_ms(128, 2.5, 2)])
    assert js["fps"] == pytest.approx([L.fps(64, 3), L.fps(200, 4, 4)])
    assert js["ref"] == [list(L.FPS_PASSIVE), L.FPS_ACTIVE]
