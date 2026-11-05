"""m33 demos: the browser code must match the tested Python models, and the precomputed m33-d2 data
must come from the current generator and show what the module says it shows.

Runs demos/m33-common.js in Node and compares with labs/python/epml/mapping.py and twin.py.
"""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import mapping as mp
from epml import twin

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "demos" / "m33-d2-data.json"
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")

NX, H = 21, 1.0


def speeds(tris, verts):
    """Fast tissue, a slow disc and a short line of block: one speed per triangle."""
    c = verts[tris].mean(axis=1)
    v = np.where((c[:, 0] - 12) ** 2 + (c[:, 1] - 10) ** 2 <= 16, 0.6, 1.0)
    v[(np.abs(c[:, 0] - 6) < 0.5) & (c[:, 1] < 8)] = 0.0
    return v


def run_node(script):
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True,
                         check=True, cwd=ROOT)
    return json.loads(out.stdout)


@node
def test_js_grid_and_eikonal_match_python():
    """eq-m30-eikonal as used by m33-d1: same triangles and the same converged activation times."""
    verts, tris = mp.plane_mesh(NX, NX, H)
    sp = speeds(tris, verts)
    T = mp.eikonal(verts, tris, [10 * NX], sp)
    js = run_node(f"""
import * as m from "{(ROOT / 'demos' / 'm33-common.js').as_posix()}";
const tris = m.gridTriangles({NX}, {NX});
const T = m.eikonalGrid({NX}, {NX}, {H}, tris, {json.dumps(sp.tolist())}, [{10 * NX}], 0, 1e-12);
console.log(JSON.stringify({{tris, T: Array.from(T, v => Number.isFinite(v) ? v : null)}}));
""")
    assert np.array_equal(np.array(js["tris"]), tris)
    Tjs = np.array([np.inf if v is None else v for v in js["T"]])
    assert np.array_equal(np.isfinite(Tjs), np.isfinite(T))
    assert Tjs[np.isfinite(T)] == pytest.approx(T[np.isfinite(T)], abs=1e-8)


@node
def test_js_offset_regions_and_calibration_match_python():
    """eq-m33-offset in JS equals the Python closed form; block regions match; the JS fit recovers
    the same two speeds as the Python fit (both close to the truth)."""
    verts, tris = mp.plane_mesh(NX, NX, H)
    c = verts[tris].mean(axis=1)
    region = (c[:, 0] > 10.0).astype(int)
    true_v = np.array([1.0, 0.6])
    src = 10 * NX
    T = mp.eikonal(verts, tris, src, true_v[region])
    rng = np.random.default_rng(5)
    pts = rng.choice(len(verts), 50, replace=False)
    meas = T[pts] + 20.0 + rng.normal(0, 0.5, pts.size)
    v_py, t0_py, _ = twin.calibrate_regions(verts, tris, region, src, pts, meas, v_init=0.8)
    blocks = np.minimum(1, np.floor(c[:, 0] / 20.0 * 2)).astype(int) + 2 * np.minimum(
        1, np.floor(c[:, 1] / 20.0 * 2)).astype(int)
    js = run_node(f"""
import * as m from "{(ROOT / 'demos' / 'm33-common.js').as_posix()}";
const tris = m.gridTriangles({NX}, {NX});
const grid = {{nx: {NX}, ny: {NX}, h: {H}, tris}};
const region = {json.dumps(region.tolist())};
const fit = m.calibrate(grid, region, 2, {src}, {json.dumps(pts.tolist())}, {json.dumps(meas.tolist())});
console.log(JSON.stringify({{
  off: m.bestOffset([1, 2, 4], [11, 13, 14]),
  blocks: m.blockRegions(tris, {NX}, {H}, 20, 2),
  fit,
}}));
""")
    assert js["off"] == pytest.approx(twin.best_offset([1, 2, 4], [11, 13, 14]))
    assert js["blocks"] == blocks.tolist()
    assert np.array(js["fit"]["speeds"]) == pytest.approx(v_py, rel=0.02)
    assert np.array(js["fit"]["speeds"]) == pytest.approx(true_v, rel=0.06)
    assert js["fit"]["offset"] == pytest.approx(t0_py, abs=0.3)


def load_scenario(d, key):
    n = d["grid"]["n"]
    s = d["scenarios"][key]
    rd = np.array([np.nan if v is None else v for v in s["rd"]]).reshape(n, n)
    ek = np.array([np.nan if v is None else v for v in s["eikonal"]]).reshape(n, n)
    return rd, ek


def test_d2_data_is_current_and_small():
    """The data file was written by the current generator (hash of tools/make_m33_d2.py) and stays
    below the 2 MB demo budget (CLAUDE.md §4)."""
    d = json.loads(DATA.read_text())
    gen = (ROOT / "tools" / "make_m33_d2.py").read_bytes()
    assert d["generator_sha256"] == hashlib.sha256(gen).hexdigest(), "run: python tools/make_m33_d2.py"
    assert DATA.stat().st_size < 2 * 1024 * 1024
    assert set(d["scenarios"]) == {"planar", "point", "slow", "isthmus"}


def test_d2_velocities_match_the_cited_targets():
    """eq-m33-cv-scaling was used to tune the conductivities: the planar velocities of the
    reaction-diffusion model are 1.0 and 0.6 m/s (Heil et al. 2023), and the planar map's activation
    advances 1 mm per ms along x."""
    d = json.loads(DATA.read_text())
    assert d["params"]["cv_fast_m_per_s"] == pytest.approx(1.0, rel=0.005)
    assert d["params"]["cv_slow_m_per_s"] == pytest.approx(0.6, rel=0.005)
    rd, _ = load_scenario(d, "planar")
    n, s = d["grid"]["n"], d["grid"]["spacing_mm"]
    x = np.arange(n) * s
    mid = rd[n // 2]
    sel = (x > 5) & (x < 25)
    slope = np.polyfit(x[sel], mid[sel], 1)[0]  # ms per mm
    assert 1 / slope == pytest.approx(1.0, rel=0.02)


def test_d2_claims_in_the_text():
    """Numbers quoted in the module: a planar wave agrees within about 1 ms after removing the offset;
    point pacing builds most of a 3-4 ms lag within 3 mm of the stimulus; the isthmus adds about
    2.7 ms of delay beyond the line of block."""
    d = json.loads(DATA.read_text())
    n, s = d["grid"]["n"], d["grid"]["spacing_mm"]
    X, Y = np.meshgrid(np.arange(n) * s, np.arange(n) * s)
    rd, ek = load_scenario(d, "planar")
    lag = rd - ek
    assert np.nanmax(np.abs(lag - np.nanmean(lag))) < 1.1
    rd, ek = load_scenario(d, "point")
    R = np.hypot(X - 15, Y - 15)
    lag = rd - ek
    near, far = np.nanmean(lag[np.abs(R - 3) < 0.3]), np.nanmean(lag[np.abs(R - 12) < 0.3])
    assert 3.0 <= far <= 4.5 and near > 0.65 * far
    rd, ek = load_scenario(d, "isthmus")
    lag = rd - ek
    before, after = np.nanmean(lag[np.abs(X - 10) < 0.3]), np.nanmean(lag[np.abs(X - 22) < 0.3])
    assert after - before == pytest.approx(2.7, abs=0.4)
