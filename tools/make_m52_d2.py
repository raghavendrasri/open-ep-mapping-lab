"""Write the synthetic atrial wall for demo m52-d2 (how much "fibrosis" a threshold finds).

Run from the repository root after any change to epml.mri.synthetic_wall:
    python tools/make_m52_d2.py
Writes demos/m52-d2-wall.json. tests/test_m52_demos.py checks that it is up to date.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs" / "python"))

from epml import mri  # noqa: E402

SEED = 52


def compute():
    rng = np.random.default_rng(SEED)
    w = mri.synthetic_wall(rng)
    rep = mri.scan(rng, w["clean"])
    ny, nx = w["truth"].shape
    r3 = lambda a: [round(float(v), 3) for v in np.ravel(a)]  # noqa: E731
    return {
        "nx": nx, "ny": ny,
        "wall": r3(mri.iir(w["wall"], w["blood"])),
        "repeat": r3(mri.iir(rep["wall"], rep["blood"])),
        "truth": [int(v) for v in np.ravel(w["truth"])],
        "bloodSd": round(float(np.std(w["blood"] / w["blood"].mean())), 4),
        "bloodSdRepeat": round(float(np.std(rep["blood"] / rep["blood"].mean())), 4),
        "methods": [{"label": k, "kind": v[0], "value": v[1]} for k, v in mri.THRESHOLDS.items()],
    }


if __name__ == "__main__":
    path = ROOT / "demos" / "m52-d2-wall.json"
    path.write_text(json.dumps(compute(), ensure_ascii=False, separators=(",", ":")))
    print(path, path.stat().st_size, "bytes")
