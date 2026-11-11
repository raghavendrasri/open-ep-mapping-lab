"""m42 demos: the JS fits match numpy, and the precomputed m42-d1 data match the tested Python."""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m42-common.js").as_posix()
DATA = ROOT / "demos" / "m42-d1-data.json"
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def run_node(script):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout)


@node
def test_js_ridge_fit_matches_numpy():
    """eq-m42-rbf in one dimension and the ridge fit used by every member of m42-d2."""
    xs = [2.0, 6, 11, 15, 19, 24, 28, 33]
    ys = [6.6, 1.1, 3.3, 8.1, 10.6, 16.2, 18.8, 25.8]
    centres = [float(c) for c in np.arange(0, 61, 5.0)]
    js = run_node(f"""
import * as m from "{COMMON}";
const Phi = m.rbfDesign({xs}, {centres}, 5);
const a = m.ridgeFit(Phi, {ys}, 1e-3);
const same = m.ensemble1d({{ xs: {xs}, ys: {ys}, xEval: [0, 30, 60], centres: {centres}, h: 5, ridge: 1e-3, members: 3, noise: 0, priorScale: 0, seed: 1 }});
console.log(JSON.stringify({{a, same}}));
""")
    P = np.c_[np.exp(-0.5 * ((np.array(xs)[:, None] - np.array(centres)[None]) / 5) ** 2), np.ones(len(xs))]
    A = P.T @ P + 1e-3 * np.diag(np.r_[np.ones(len(centres)), 0])
    assert np.allclose(js["a"], np.linalg.solve(A, P.T @ np.array(ys)), rtol=1e-6, atol=1e-6)
    s = np.array(js["same"])
    assert np.allclose(s, s[0])


def test_precomputed_m42_d1_matches_python():
    spec = importlib.util.spec_from_file_location("make_m42_d1", ROOT / "tools" / "make_m42_d1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fresh = mod.compute()
    stored = json.loads(DATA.read_text())
    assert stored["N"] == fresh["N"] and stored["lambda"] == fresh["lambda"]
    assert np.allclose(stored["truth"], fresh["truth"])
    for key in ("12_0", "24_100", "48_10"):
        assert np.allclose(stored["fits"][key]["T"], fresh["fits"][key]["T"], atol=0.02)
        assert stored["fits"][key]["rmse"] == pytest.approx(fresh["fits"][key]["rmse"], abs=0.01)
    assert DATA.stat().st_size < 2_000_000
