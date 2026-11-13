"""m05 demos: the JS FFT, analytic signal, periodogram and synthetic signals match epml.timefreq and scipy."""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from scipy import signal

from epml import timefreq as F

ROOT = Path(__file__).resolve().parents[1]
COMMON = (ROOT / "demos" / "m05-common.js").as_posix()
node = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")


@node
def test_js_matches_python():
    """eq-m05-analytic, eq-m05-leakage and eq-m05-resolution in JS."""
    out = subprocess.run(["node", "--input-type=module", "-e", f"""
import * as m from "{COMMON}";
const res = {{}};
for (const kind of ["sine", "single", "double"]) {{
  const s = m.makeSignal(kind, 1000, 4, 0.18);
  const mean = s.x.reduce((a, v) => a + v, 0) / s.x.length;
  const z = m.analytic(s.x.map((v) => v - mean));
  const ph = m.unwrappedPhase(z);
  res[kind] = {{ x: s.x.filter((_, i) => i % 37 === 0), zr: z.re.filter((_, i) => i % 37 === 0), zi: z.im.filter((_, i) => i % 37 === 0),
                turns: (ph[ph.length - 1] - ph[0]) / (2 * Math.PI), acts: s.activations }};
}}
const x = m.twoTone(200, 1, 6, 7);
res.freqs = [2, 6, 6.5, 7, 11];
res.pbox = m.periodogramAt(x, 200, res.freqs, "boxcar");
res.phann = m.periodogramAt(x, 200, res.freqs, "hann");
console.log(JSON.stringify(res));
"""], capture_output=True, text=True, check=True, cwd=ROOT)
    js = json.loads(out.stdout)
    fs, T, cl = 1000.0, 4.0, 0.18
    tt = np.arange(int(fs * T)) / fs
    w = 0.004
    g = lambda u: np.exp(-0.5 * (u / w) ** 2)
    times = np.arange(cl / 2, T, cl)
    sigs = {
        "sine": np.cos(2 * np.pi * (tt - cl / 2) / cl),
        "single": sum(-(tt - tk) / w * g(tt - tk) for tk in times),
    }
    sigs["double"] = sigs["single"] + sum(-0.8 * (tt - tk - 0.04) / w * g(tt - tk - 0.04) for tk in times)
    for kind, x in sigs.items():
        z = signal.hilbert(x - x.mean(), N=4096)[: len(x)]
        assert js[kind]["x"] == pytest.approx(list(x[::37]), abs=1e-9)
        assert js[kind]["zr"] == pytest.approx(list(z.real[::37]), abs=1e-6)
        assert js[kind]["zi"] == pytest.approx(list(z.imag[::37]), abs=1e-6)
        assert js[kind]["acts"] == len(times)
    assert js["sine"]["turns"] == pytest.approx(len(times), abs=1.0)
    assert js["double"]["turns"] == pytest.approx(2 * len(times), abs=1.0)
    t, x = F.two_tone(200.0, 1.0, 6.0, 7.0)
    for key, win in (("pbox", "boxcar"), ("phann", "hann")):
        f, P = F.periodogram(x, 200.0, win, nfft=2000)
        idx = [int(round(v * 10)) for v in js["freqs"]]
        assert js[key] == pytest.approx(list(P[idx]), rel=1e-9)
