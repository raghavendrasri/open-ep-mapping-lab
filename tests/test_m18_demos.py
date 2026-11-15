"""m18 demos: the JS correction and dielectric code matches epml.hybrid."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import hybrid as H

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m18-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m18-affine, eq-m18-rbf and eq-m18-dielectric in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const r = m.rng(5), cal = [];
for (let i = 0; i < 25; i++) cal.push([(2 * r() - 1) * 40, (2 * r() - 1) * 40]);
const u = cal.map((p) => m.impedanceCoordinates([p[0], p[1], 0]).slice(0, 2));
const q = [[10, -5], [-20, 30]], uq = q.map((p) => m.impedanceCoordinates([p[0], p[1], 0]).slice(0, 2));
const aff = m.fitAffine(u, cal), rbf = m.fitRbf(u, cal, 25, 1e-6);
console.log(JSON.stringify({{ cal, u, uq, aff: m.applyAffine(aff, uq), rbf: m.applyRbf(rbf, uq),
  ph: m.impedancePhaseDeg(1e5, m.ILLUSTRATIVE_TISSUES["wall-like"]), mag: m.conductivityMagnitude(1e5, m.ILLUSTRATIVE_TISSUES["wall-like"]) }}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    cal, u, uq = np.array(js["cal"]), np.array(js["u"]), np.array(js["uq"])
    pts = np.hstack([cal, np.zeros((len(cal), 1))])
    assert u == pytest.approx(H.impedance_coordinates(pts)[:, :2])
    A, b = H.fit_affine(u, cal)
    assert js["aff"] == pytest.approx(H.apply_affine(A, b, uq), rel=1e-7)
    assert js["rbf"] == pytest.approx(H.apply_rbf(H.fit_rbf(u, cal, 25.0, 1e-6), uq), rel=1e-6)
    t = H.ILLUSTRATIVE_TISSUES["wall-like"]
    assert js["ph"] == pytest.approx(H.impedance_phase_deg(1e5, **t))
    assert js["mag"] == pytest.approx(abs(H.complex_conductivity(1e5, **t)))
