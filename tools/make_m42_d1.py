"""Precompute the m42-d1 demo data: data-only and physics-informed fits of an activation map.

Writes demos/m42-d1-data.json. Run from the repository root:

    python tools/make_m42_d1.py

Model (labs/python/epml/pinn.py): activation from a point source at (8, 30) mm spreading at 1.0 m/s
over a 60-by-60-mm square, measured at N random points with 1 ms of Gaussian noise (seed 101),
fitted with 81 Gaussian radial basis functions (width 8 mm) by Levenberg-Marquardt, with the eikonal
term weighted by lambda and one unknown speed. Takes a few seconds.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs" / "python"))

from epml import pinn  # noqa: E402

SRC, V, SEED = np.array([8.0, 30.0]), 1.0, 101
NS, LAMS = (12, 24, 48), (0, 1, 10, 100)


def compute():
    XG = pinn.grid_centres(0, 60, 31)
    XC = pinn.grid_centres(0, 60, 21)
    cent = pinn.grid_centres(0, 60, 9)
    truth = np.linalg.norm(XG - SRC, axis=1) / V
    rng = np.random.default_rng(SEED)
    Xall = rng.uniform(0, 60, (max(NS), 2))
    tall = np.linalg.norm(Xall - SRC, axis=1) / V + rng.normal(0, 1.0, max(NS))
    fits = {}
    for N in NS:
        for lam in LAMS:
            f = pinn.ActivationFit(cent, 8.0, "scalar", s_prior=1.2)
            f.fit(Xall[:N], tall[:N], XC, lam=lam, iters=80)
            T = f.T(XG)
            fits[f"{N}_{lam}"] = {
                "T": np.round(T, 2).tolist(),
                "rmse": round(float(np.sqrt(np.mean((T - truth) ** 2))), 3),
                "speed": round(float(1 / f.b[0]), 3),
            }
    return {
        "grid": {"n": 31, "spacing_mm": 2.0},
        "source_mm": SRC.tolist(),
        "speed_m_per_s": V,
        "points": np.round(Xall, 3).tolist(),
        "times_ms": np.round(tall, 3).tolist(),
        "truth": np.round(truth, 2).tolist(),
        "N": list(NS),
        "lambda": list(LAMS),
        "fits": fits,
    }


if __name__ == "__main__":
    out = ROOT / "demos" / "m42-d1-data.json"
    out.write_text(json.dumps(compute(), separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} kB)")
