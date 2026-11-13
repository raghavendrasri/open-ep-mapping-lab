"""m07 demos: the JS grid, front profile, continuation, Tikhonov filter and expected error match epml.inverse."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from epml import inverse as I

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m07-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m07-continuation, eq-m07-filters and eq-m07-error in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const {{ s, k }} = m.grid();
const x = m.tissueProfile(s, m.WIDTH);
const g = m.gain(k, 1.0);
const up = m.filterReal(x, g);
const z = m.normals(m.N, 7);
const b = Array.from(up, (v, i) => v + 0.01 * z[i]);
const X = m.dft(x);
const X2 = Array.from(X.re, (v, j) => v * v + X.im[j] * X.im[j]);
console.log(JSON.stringify({{
  s: Array.from(s), k: Array.from(k), x: Array.from(x), up: Array.from(up), z: Array.from(z),
  rec: Array.from(m.tikhonov(b, g, 0.01)),
  err: [1e-3, 1e-2, 1e-1].map((lam) => m.expectedError(X2, g, 0.01, lam)),
}}));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    s, k = I.grid(256, 32.0)
    x = I.tissue_profile(s, 0.3, 32.0, n_harm=128)
    assert np.allclose(js["s"], s) and np.allclose(js["k"], k)
    assert np.allclose(js["x"], x, atol=1e-10)
    assert np.allclose(js["up"], I.continue_up(x, k, 1.0), atol=1e-10)
    z = np.array(js["z"])
    assert abs(z.mean()) < 0.2 and 0.8 < z.std() < 1.2
    gain = I.continuation_gain(k, 1.0)
    b = I.continue_up(x, k, 1.0) + 0.01 * z
    assert np.allclose(js["rec"], I.fourier_tikhonov(b, gain, 0.01), atol=1e-8)
    for lam, e in zip([1e-3, 1e-2, 1e-1], js["err"]):
        ref = I.fourier_expected_error(gain, np.fft.fft(x), 0.01, I.tikhonov_factors(gain, lam))
        assert [e["bias"], e["variance"], e["total"]] == pytest.approx(list(ref), rel=1e-8)
