"""Download and verify public datasets used by the labs.

Files are fetched from PhysioNet, checked against PhysioNet's published SHA-256 list, and
cached under data/cache/ (not committed). Without network access, fetch functions raise
DataUnavailable so a lab can skip its real-data part. Set EPML_REQUIRE_DATA=1 (CI does) to
turn a missing download into an error instead.
"""

import hashlib
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
IAFDB_URL = "https://physionet.org/files/iafdb/1.0.0/"
CACHE = ROOT / "data" / "cache" / "iafdb"
REGISTRY = ROOT / "data" / "registry.json"


def pinned_checksums(prefix="iafdb/"):
    """SHA-256 values recorded in data/registry.json, as {file name: hex digest}."""
    if not REGISTRY.exists():
        return {}
    entries = json.loads(REGISTRY.read_text())
    return {e["name"][len(prefix):]: e["sha256"] for e in entries if e["name"].startswith(prefix)}


class DataUnavailable(RuntimeError):
    """Raised when a dataset cannot be downloaded (for example, no network)."""


def _get(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.read()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def published_checksums(base_url=IAFDB_URL):
    """PhysioNet's SHA256SUMS.txt for a database, as {file name: hex digest}."""
    text = _get(base_url + "SHA256SUMS.txt").decode()
    sums = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1].lstrip("*")] = parts[0]
    return sums


def fetch_iafdb(record="iaf1_svc", cache=CACHE):
    """Download one Intracardiac AF Database record (.hea and .dat), verified by SHA-256.

    Returns the local path stem to pass to wfdb.rdrecord. Data: Intracardiac Atrial
    Fibrillation Database, PhysioNet, doi:10.13026/C23S33, Open Data Commons Attribution v1.0.
    """
    cache = Path(cache)
    files = [f"{record}.hea", f"{record}.dat"]
    try:
        if not all((cache / f).exists() for f in files):
            cache.mkdir(parents=True, exist_ok=True)
            for f in files:
                (cache / f).write_bytes(_get(IAFDB_URL + f))
        sums = published_checksums()
    except OSError as err:  # URLError, HTTPError and timeouts are all OSErrors
        if os.environ.get("EPML_REQUIRE_DATA") == "1":
            raise
        raise DataUnavailable(f"could not download {record} from PhysioNet: {err}") from err

    pinned = pinned_checksums()
    for f in files:
        got = sha256(cache / f)
        if sums.get(f) != got:
            (cache / f).unlink(missing_ok=True)
            raise ValueError(f"{f}: SHA-256 {got} does not match PhysioNet's published {sums.get(f)}")
        if f in pinned and pinned[f] != got:
            raise ValueError(f"{f}: SHA-256 {got} differs from data/registry.json ({pinned[f]}); the source changed")
        print(f"verified {f}  sha256 {got}")
    return str(cache / record)


# ---------------------------------------------------------------------------------------------
# Generic PhysioNet access for the Part VII labs (m37, m38): many small files, fetched in parallel,
# each checked against the database's published SHA256SUMS.txt. The checksum list itself is pinned in
# data/registry.json once CI has printed its hash (see docs/decisions.md).

PHYSIONET = "https://physionet.org/files/"


def require_data():
    return os.environ.get("EPML_REQUIRE_DATA") == "1"


def skip_real_data():
    """EPML_SKIP_REAL_DATA=1 (used by the optional PyTorch CI job) skips downloads on purpose."""
    return os.environ.get("EPML_SKIP_REAL_DATA") == "1"


class PhysioNetDB:
    """Files of one PhysioNet database version, e.g. PhysioNet("ptb-xl", "1.0.3")."""

    def __init__(self, name, version, cache=None):
        self.name, self.version = name, version
        self.base = f"{PHYSIONET}{name}/{version}/"
        self.cache = Path(cache) if cache else ROOT / "data" / "cache" / f"{name}-{version}"
        self._sums = None

    def _wrap(self, err):
        if require_data():
            raise err
        raise DataUnavailable(f"could not download from PhysioNet ({self.name} {self.version}): {err}") from err

    def checksums(self):
        """The database's SHA256SUMS.txt as {relative path: hex digest}; cached and pinned if listed in
        data/registry.json under '<name>-<version>/SHA256SUMS.txt'."""
        if self._sums is None:
            if skip_real_data():
                raise DataUnavailable("EPML_SKIP_REAL_DATA=1")
            path = self.cache / "SHA256SUMS.txt"
            try:
                if not path.exists():
                    self.cache.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(_get(self.base + "SHA256SUMS.txt"))
            except OSError as err:
                self._wrap(err)
            got = sha256(path)
            pinned = pinned_checksums(prefix=f"{self.name}-{self.version}/").get("SHA256SUMS.txt")
            print(f"{self.name}-{self.version}/SHA256SUMS.txt  sha256 {got}" + ("  (pinned)" if pinned else ""))
            if pinned and pinned != got:
                path.unlink(missing_ok=True)
                raise ValueError(f"{self.name} SHA256SUMS.txt changed: {got}, registry has {pinned}")
            sums = {}
            for line in path.read_text().splitlines():
                parts = line.split()
                if len(parts) == 2:
                    sums[parts[1].lstrip("*")] = parts[0]
            self._sums = sums
        return self._sums

    def fetch(self, files, workers=8):
        """Download (if needed) and verify each relative path; return local paths in the same order."""
        from concurrent.futures import ThreadPoolExecutor

        sums = self.checksums()

        def one(rel):
            local = self.cache / rel
            if not local.exists():
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(_get(self.base + rel))
            if sums.get(rel) != sha256(local):
                local.unlink(missing_ok=True)
                raise ValueError(f"{rel}: checksum does not match {self.name}'s published SHA256SUMS.txt")
            return local

        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(one, files))
        except OSError as err:
            self._wrap(err)


def load_challenge2017(n_per_class=100, classes=("N", "A"), seed=0, db=None):
    """Single-lead recordings of the PhysioNet/CinC Challenge 2017 training set (Clifford et al. 2017):
    300 Hz, lead I equivalent. Labels: N normal rhythm, A AF, O other rhythm, ~ noisy. Returns
    (list of signals in mV, labels, record names). License: Open Data Commons Attribution v1.0."""
    import numpy as np
    from scipy.io import loadmat

    db = db or PhysioNetDB("challenge-2017", "1.0.0")
    sums = db.checksums()
    refs = sorted(f for f in sums if f.lower().endswith(".csv") and "reference" in f.lower())
    ref = next((f for f in refs if "v3" in f.lower()), refs[0] if refs else None)
    if ref is None:
        raise ValueError("no REFERENCE csv in the Challenge 2017 file list")
    (ref_path,) = db.fetch([ref])
    rows = [line.strip().split(",") for line in ref_path.read_text().splitlines() if "," in line]
    folder = ref.rsplit("/", 1)[0] + "/" if "/" in ref else ""
    names = {Path(f).stem for f in sums if f.endswith(".mat")}
    rng = np.random.default_rng(seed)
    chosen, labels = [], []
    for c in classes:
        recs = sorted(r for r, lab in rows if lab == c and r in names)
        pick = rng.choice(recs, size=min(n_per_class, len(recs)), replace=False)
        chosen += list(pick)
        labels += [c] * len(pick)
    prefix = next((f.rsplit("/", 1)[0] + "/" for f in sums if f.endswith(f"{chosen[0]}.mat") and "/" in f), folder)
    paths = db.fetch([f"{prefix}{r}.{ext}" for r in chosen for ext in ("mat", "hea")])
    signals = []
    for i, r in enumerate(chosen):
        mat, hea = paths[2 * i], paths[2 * i + 1]
        fields = hea.read_text().splitlines()[1].split()
        gain = float(fields[2].split("/")[0].split("(")[0]) if len(fields) > 2 else 1000.0
        signals.append(loadmat(mat)["val"][0].astype(float) / gain)
    return signals, labels, chosen


def load_ptbxl_lead(n_per_class=50, codes=("SR", "AFIB"), fold=10, lead="I", seed=0, db=None):
    """Lead I at 100 Hz from PTB-XL (Wagner et al. 2020), from one recommended fold (fold 10 is the
    suggested test fold; folds keep each patient in one fold). A record is labelled with the first of
    `codes` found among its SCP statements, and records holding more than one of them are dropped.
    Returns (array of signals in mV, labels, ecg ids, {code: number of eligible records in the fold}).
    License: Creative Commons Attribution 4.0."""
    import ast
    import csv

    import numpy as np
    import wfdb

    db = db or PhysioNetDB("ptb-xl", "1.0.3")
    sums = db.checksums()
    meta = next(f for f in sums if f.endswith("ptbxl_database.csv"))
    (meta_path,) = db.fetch([meta])
    root = meta.rsplit("/", 1)[0] + "/" if "/" in meta else ""
    by_code = {c: [] for c in codes}
    with open(meta_path, newline="") as fh:
        for row in csv.DictReader(fh):
            if int(float(row["strat_fold"])) != fold:
                continue
            present = [c for c in codes if c in ast.literal_eval(row["scp_codes"])]
            if len(present) == 1:
                by_code[present[0]].append((int(float(row["ecg_id"])), row["filename_lr"]))
    missing = [c for c in codes if not by_code[c]]
    if missing:
        raise ValueError(f"PTB-XL fold {fold} has no records with codes {missing}")
    rng = np.random.default_rng(seed)
    chosen = []
    for c in codes:
        items = sorted(by_code[c])
        idx = rng.choice(len(items), size=min(n_per_class, len(items)), replace=False)
        chosen += [(c,) + items[i] for i in sorted(idx)]
    db.fetch([f"{root}{fn}.{ext}" for _, _, fn in chosen for ext in ("hea", "dat")])
    signals, labels, ids = [], [], []
    for c, ecg_id, fn in chosen:
        rec = wfdb.rdrecord(str(db.cache / f"{root}{fn}"))
        signals.append(rec.p_signal[:, rec.sig_name.index(lead)])
        labels.append(c)
        ids.append(ecg_id)
    return np.array(signals), labels, ids, {c: len(v) for c, v in by_code.items()}
