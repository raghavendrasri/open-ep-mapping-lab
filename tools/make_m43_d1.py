"""Precompute demo m43-d1 (contrastive embedding) from the course's tested code in epml.foundation.

Run from the repository root:  python tools/make_m43_d1.py
Writes demos/m43-d1-data.json. tests/test_m43_demos.py regenerates the data and compares.
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs" / "python"))

from epml import foundation as fm  # noqa: E402
from epml.ml import auc_rank  # noqa: E402

SNAPS = [0, 5, 10, 20, 50, 100, 200, 300]
MODES = ["patient", "recording"]
N_DISPLAY, N_REC = 8, 6
THRESHOLD = 1.4  # QRS width factor above which a synthetic patient is labelled "wide" (illustrative)


def labelled_draws(n, draws, seed):
    """`draws` labelled sets of n patients, each with both classes present."""
    rng = np.random.default_rng(seed)
    out = []
    while len(out) < draws:
        p = fm.patient_params(n, rng)
        y = (p["width"] > THRESHOLD).astype(float)
        if 0 < y.sum() < n:
            out.append((fm.recordings(p, np.arange(n), rng), y))
    return out


def pca2(Z):
    Zc = Z - Z.mean(axis=0)
    _, _, vt = np.linalg.svd(Zc, full_matrices=False)
    P = Zc @ vt[:2].T
    for j in range(2):                      # fix the sign so the picture does not flip between steps
        if P[np.argmax(np.abs(P[:, j])), j] < 0:
            P[:, j] = -P[:, j]
    return P


def compute():
    rng = np.random.default_rng(1)
    params = fm.patient_params(2000, rng)
    std = fm.Standardizer(fm.recordings(params, np.arange(2000), rng))
    dp, rd = fm.patient_params(N_DISPLAY, np.random.default_rng(11)), np.random.default_rng(12)
    Xd = std(np.vstack([fm.recordings(dp, np.arange(N_DISPLAY), rd) for _ in range(N_REC)]))
    gd = np.tile(np.arange(N_DISPLAY), N_REC)
    nnp, rn = fm.patient_params(200, np.random.default_rng(13)), np.random.default_rng(14)
    Xn = std(np.vstack([fm.recordings(nnp, np.arange(200), rn) for _ in range(2)]))
    gn = np.tile(np.arange(200), 2)
    test = fm.patient_params(1000, np.random.default_rng(5))
    Xt = std(fm.recordings(test, np.arange(1000), np.random.default_rng(6)))
    yt = (test["width"] > THRESHOLD).astype(float)
    draws = [(std(X), y) for X, y in labelled_draws(10, 5, seed=100)]
    raw = float(np.mean([auc_rank(fm.logistic_score(fm.fit_logistic(X, y, lam=10.0), Xt), yt) for X, y in draws]))
    same = gd[:, None] == gd[None, :]
    off = ~np.eye(len(gd), dtype=bool)
    out = {"snaps": SNAPS, "groups": gd.tolist(), "rawProbeAuc": round(raw, 3), "chance": round(float(np.log(128)), 3),
           "modes": {}}
    for mode in MODES:
        frames = []

        def snap(step, enc):
            Z = enc.embed(Xd)
            S = Z @ Z.T
            probe = np.mean([auc_rank(fm.logistic_score(fm.fit_logistic(enc.features(X), y, lam=1.0),
                                                        enc.features(Xt)), yt) for X, y in draws])
            frames.append({
                "step": step,
                "xy": np.round(pca2(Z), 3).tolist(),
                "sameCos": round(float(S[same & off].mean()), 3),
                "otherCos": round(float(S[~same].mean()), 3),
                "nnAcc": round(fm.nearest_neighbour_accuracy(enc.embed(Xn), gn), 3),
                "probeAuc": round(float(probe), 3),
            })

        _, losses = fm.pretrain(params, std, steps=SNAPS[-1], positives=mode, seed=2, snapshots=SNAPS, callback=snap)
        out["modes"][mode] = {"frames": frames, "loss": np.round(losses, 3).tolist()}
    return out


if __name__ == "__main__":
    data = compute()
    path = ROOT / "demos" / "m43-d1-data.json"
    path.write_text(json.dumps(data, separators=(",", ":")))
    print(path, path.stat().st_size, "bytes")
    for mode, d in data["modes"].items():
        for f in d["frames"]:
            print(mode, f["step"], f["sameCos"], f["otherCos"], f["nnAcc"], f["probeAuc"])
    print("raw", data["rawProbeAuc"])
