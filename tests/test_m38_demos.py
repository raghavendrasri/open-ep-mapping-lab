"""m38 demos: the browser math must match the tested Python in labs/python/epml/wearables.py."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from epml import wearables as wr

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m38-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def run_node(script):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout)


@node
def test_js_runs_and_detection_match_python():
    """eq-m38-runs and eq-m38-detect in m38-d1."""
    cases = [(288, 0.05, 4), (1440, 0.2, 1), (96, 0.01, 10), (3, 0.5, 5)]
    det = [(6, 0.8, 4), (48, 0.5, 11), (2, 0.9, 1), (10, 0.3, 3)]
    js = run_node(f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{r: {json.dumps(cases)}.map(([n, q, k]) => m.expectedRuns(n, q, k)),
  d: {json.dumps(det)}.map(([L, p, k]) => m.detectionProbability(L, p, k))}}));
""")
    assert js["r"] == pytest.approx([wr.expected_runs(*c) for c in cases])
    assert js["d"] == pytest.approx([wr.detection_probability(*c) for c in det])


@node
def test_js_workload_and_filter_match_python():
    """eq-m38-workload and eq-m38-filter in m38-d2."""
    js = run_node(f"""
import * as m from "{COMMON}";
console.log(JSON.stringify({{w: m.alertWorkload(500, 0.1, 0.25, 3), f: m.filteredAlerts(0.25, 0.98, 0.7)}}));
""")
    w = wr.alert_workload(500, 0.1, 0.25, 3)
    assert js["w"]["hours"] == pytest.approx(w["hours"]) and js["w"]["false"] == pytest.approx(w["false"])
    new, shown, lost = wr.filtered_alerts(0.25, 0.98, 0.7)
    assert js["f"]["ppv"] == pytest.approx(new) and js["f"]["shown"] == pytest.approx(shown) and js["f"]["lost"] == pytest.approx(lost)
