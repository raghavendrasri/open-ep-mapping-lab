"""Precompute the m33-d2 demo data: reaction-diffusion vs eikonal activation on a 2D sheet.

Writes demos/m33-d2-data.json. Run from the repository root:

    python tools/make_m33_d2.py

Model: Mitchell-Schaeffer monodomain sheet (labs/python/epml/ionic.py), explicit finite
differences, against the eikonal solver of m30 (labs/python/epml/mapping.py) with speeds set to the
planar conduction velocities measured in the reaction-diffusion model. Conductivities are tuned with
eq-m33-cv-scaling so that the planar velocities match the cited targets: 1.0 m/s in normal-voltage
tissue and 0.6 m/s in low-voltage areas (Heil et al. 2023). Takes about a minute.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs" / "python"))

from epml import ionic, mapping, twin  # noqa: E402

# Mitchell-Schaeffer constants (ms): tau_in, tau_out, tau_open, tau_close, v_gate. Illustrative; the
# demo uses activation times only, which depend on these through the conduction velocity, and the
# velocity is tuned to cited targets below.
PARAMS = (0.3, 6.0, 120.0, 150.0, 0.13)
DX, DT = 0.2, 0.005  # mm, ms (D dt / dx^2 stays below 1/4 for D near 1.2 mm^2/ms)
SIZE = 30.0  # mm, square sheet
V_FAST, V_SLOW = 1.0, 0.6  # mm/ms = m/s, targets from Heil et al. 2023
STEP = 2  # keep every second node in the JSON (0.4 mm)


def cable_velocity(D):
    """Planar conduction velocity (mm/ms) of the model on a 1D cable with the sheet's dx and dt."""
    n = int(round(16.0 / DX))
    _, ups, _ = ionic.ms_cable(n, DX, DT, 40.0, D, PARAMS, [0.0], stim_cells=5, stim_amp=1.0,
                               stim_dur=2.0, record_every=10.0)
    i1, i2 = n // 4, 3 * n // 4
    return (i2 - i1) * DX / (ups[i2][0] - ups[i1][0])


def tuned_diffusion(target, D0=1.0, rounds=3):
    """Iterate eq-m33-cv-scaling, D <- D (target / v)^2, until the cable conducts at the target."""
    D = D0
    for _ in range(rounds):
        D = twin.conductivity_for_speed(D, target, cable_velocity(D))
    return D, cable_velocity(D)


def scenarios(x, y):
    """Masks for the four scenarios on node coordinates x, y (mm)."""
    c = SIZE / 2
    left = x < 0.61
    point = (x - c) ** 2 + (y - c) ** 2 <= 1.0**2
    slow = (x - 18.0) ** 2 + (y - c) ** 2 <= 6.0**2
    wall = (np.abs(x - c) <= 1.0) & ~(np.abs(y - c) <= 1.5)
    none = np.zeros_like(x, dtype=bool)
    return {
        "planar": dict(label="Planar wave, uniform tissue", stim=left, slow=none, scar=none),
        "point": dict(label="Point pacing, uniform tissue", stim=point, slow=none, scar=none),
        "slow": dict(label="Planar wave, slow region", stim=left, slow=slow, scar=none),
        "isthmus": dict(label="Planar wave, 3-mm isthmus in a line of block", stim=left, slow=none,
                        scar=wall),
    }


def main():
    n = int(round(SIZE / DX)) + 1
    xs = np.arange(n) * DX
    X, Y = np.meshgrid(xs, xs)
    D_fast, v_fast = tuned_diffusion(V_FAST)
    D_slow, v_slow = tuned_diffusion(V_SLOW, D0=D_fast * (V_SLOW / V_FAST) ** 2)
    verts, tris = mapping.plane_mesh(n, n, DX)
    cent = verts[tris].mean(axis=1)
    out = {
        "generator": "tools/make_m33_d2.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "params": {"mitchell_schaeffer": PARAMS, "dx_mm": DX, "dt_ms": DT, "size_mm": SIZE,
                   "D_fast_mm2_per_ms": D_fast, "D_slow_mm2_per_ms": D_slow,
                   "cv_fast_m_per_s": v_fast, "cv_slow_m_per_s": v_slow},
        "grid": {"n": len(xs[::STEP]), "spacing_mm": DX * STEP},
        "scenarios": {},
    }
    for key, s in scenarios(X, Y).items():
        excitable = ~s["scar"]
        D = np.where(s["slow"], D_slow, D_fast)
        rd = ionic.ms_sheet(n, n, DX, DT, 80.0, D, excitable, PARAMS, s["stim"])
        cx, cy = cent[:, 0], cent[:, 1]
        sc = scenarios(cx, cy)[key]
        speed = np.where(sc["scar"], 0.0, np.where(sc["slow"], v_slow, v_fast))
        sources = np.flatnonzero(s["stim"].ravel())
        ek = mapping.eikonal(verts, tris, sources, speed).reshape(n, n)
        ek[~excitable] = np.nan
        both = np.isfinite(rd) & np.isfinite(ek)
        t0 = twin.best_offset(ek[both], rd[both])
        diff = rd - (ek + t0)
        print(f"{key}: offset {t0:.2f} ms, mean |diff| {np.nanmean(np.abs(diff)):.2f} ms, "
              f"p95 {np.nanpercentile(np.abs(diff), 95):.2f} ms, max {np.nanmax(np.abs(diff)):.2f} ms")

        def pack(a):
            a = a[::STEP, ::STEP]
            return [None if not np.isfinite(v) else round(float(v), 1) for v in a.ravel()]

        out["scenarios"][key] = {
            "label": s["label"],
            "rd": pack(rd),
            "eikonal": pack(ek),
            "scar": [bool(v) for v in s["scar"][::STEP, ::STEP].ravel()],
            "slow": [bool(v) for v in s["slow"][::STEP, ::STEP].ravel()],
        }
    path = ROOT / "demos" / "m33-d2-data.json"
    path.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1024:.0f} KB); "
          f"cv fast {v_fast:.3f}, slow {v_slow:.3f} m/s; D fast {D_fast:.3f}, slow {D_slow:.3f}")


if __name__ == "__main__":
    main()
