"""m43 demos: the JS retrieval matches epml.retrieval, the m43-d2 corpus is up to date, and the
precomputed m43-d1 data match the tested Python."""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import retrieval as rt

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m43-common.js").as_posix()
CORPUS = ROOT / "demos" / "m43-d2-corpus.json"
DATA = ROOT / "demos" / "m43-d1-data.json"
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_m43_d2_corpus_is_up_to_date():
    stored = json.loads(CORPUS.read_text())
    assert stored == load_tool("make_m43_d2").compute(), (
        "demos/m43-d2-corpus.json is out of date: run python tools/make_m43_d2.py")
    assert CORPUS.stat().st_size < 2_000_000


@node
def test_js_search_matches_python():
    """eq-m43-tfidf and eq-m43-cosine in JS give the Python ranking for every test question."""
    queries = [q for q, _ in rt.QUESTIONS] + ["voltage map of scar", "zzz"]
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
import {{ readFileSync }} from "node:fs";
const c = JSON.parse(readFileSync("{CORPUS.as_posix()}", "utf8"));
const idx = m.buildIndex(c.docs, c.stop);
const qs = {json.dumps(queries)};
console.log(JSON.stringify(qs.map((q) => m.search(idx, q, 10))));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    index = rt.Index(rt.course_corpus())
    for q, hits in zip(queries, js):
        py = index.search(q, k=10)
        assert np.allclose([h["score"] for h in hits], [s for _, s in py], atol=1e-9)
        for j, (h, (pid, ps)) in enumerate(zip(hits, py)):
            tied = any(abs(ps - py[i][1]) < 1e-9 for i in (j - 1, j + 1) if 0 <= i < len(py))
            assert h["id"] == pid or tied, q


def test_precomputed_m43_d1_matches_python():
    fresh = load_tool("make_m43_d1").compute()
    stored = json.loads(DATA.read_text())
    assert stored["snaps"] == fresh["snaps"] and stored["groups"] == fresh["groups"]
    assert stored["rawProbeAuc"] == pytest.approx(fresh["rawProbeAuc"], abs=0.002)
    for mode in ("patient", "recording"):
        for a, b in zip(stored["modes"][mode]["frames"], fresh["modes"][mode]["frames"]):
            for key in ("sameCos", "otherCos", "nnAcc", "probeAuc"):
                assert a[key] == pytest.approx(b[key], abs=0.01), (mode, a["step"], key)
            assert np.allclose(a["xy"], b["xy"], atol=0.01)
        assert np.allclose(stored["modes"][mode]["loss"], fresh["modes"][mode]["loss"], atol=0.01)
    assert DATA.stat().st_size < 2_000_000
    # the demo's claim: patient-level positives pull a patient's recordings closer than augmentations do
    last = {m: stored["modes"][m]["frames"][-1] for m in ("patient", "recording")}
    assert last["patient"]["sameCos"] > last["recording"]["sameCos"]
    assert last["patient"]["probeAuc"] > stored["rawProbeAuc"]
