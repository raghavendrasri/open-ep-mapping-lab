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


def _get(url, timeout=60, attempts=4, wait_s=3.0):
    """Download a URL. Server errors (HTTP 5xx) and dropped connections are retried a few times with a
    growing wait, because PhysioNet occasionally answers 502 under load; other errors are raised."""
    import time
    import urllib.error

    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            if err.code < 500 or attempt == attempts - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == attempts - 1:
                raise
        time.sleep(wait_s * (attempt + 1))


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

    def __init__(self, name, version, cache=None, sums="SHA256SUMS.txt"):
        """sums: the checksum list, relative to the database root. Most databases have SHA256SUMS.txt
        at the root; older Challenge databases keep a SHA256SUMS file next to their records."""
        self.name, self.version, self.sums_file = name, version, sums
        self.base = f"{PHYSIONET}{name}/{version}/"
        self.cache = Path(cache) if cache else ROOT / "data" / "cache" / f"{name}-{version}"
        self._sums = None

    def _wrap(self, err):
        if require_data():
            raise err
        raise DataUnavailable(f"could not download from PhysioNet ({self.name} {self.version}): {err}") from err

    def checksums(self):
        """The database's checksum list as {path relative to the database root: hex digest}. The list's
        own hash is printed, and checked if data/registry.json pins it under '<name>-<version>/<sums>'."""
        if self._sums is None:
            if skip_real_data():
                raise DataUnavailable("EPML_SKIP_REAL_DATA=1")
            path = self.cache / self.sums_file
            try:
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(_get(self.base + self.sums_file))
            except OSError as err:
                self._wrap(err)
            got = sha256(path)
            key = f"{self.name}-{self.version}/"
            pinned = pinned_checksums(prefix=key).get(self.sums_file)
            print(f"{key}{self.sums_file}  sha256 {got}" + ("  (pinned)" if pinned else ""))
            if pinned and pinned != got:
                path.unlink(missing_ok=True)
                raise ValueError(f"{self.name} {self.sums_file} changed: {got}, registry has {pinned}")
            folder = self.sums_file.rsplit("/", 1)[0] + "/" if "/" in self.sums_file else ""
            sums = {}
            for line in path.read_text().splitlines():
                parts = line.split()
                if len(parts) == 2:
                    sums[folder + parts[1].lstrip("*").removeprefix("./")] = parts[0]
            self._sums = sums
        return self._sums

    def fetch(self, files, workers=8):
        """Download (if needed) and verify each relative path; return local paths in the same order.
        A file missing from the published list must be pinned in data/registry.json under
        '<name>-<version>/<path>'; until it is, its hash is printed so it can be pinned."""
        from concurrent.futures import ThreadPoolExecutor

        sums = self.checksums()
        pins = pinned_checksums(prefix=f"{self.name}-{self.version}/")

        def one(rel):
            local = self.cache / rel
            if not local.exists():
                local.parent.mkdir(parents=True, exist_ok=True)
                local.write_bytes(_get(self.base + rel))
            got = sha256(local)
            want = sums.get(rel) or pins.get(rel)
            if want is None:
                print(f"{self.name}-{self.version}/{rel}  sha256 {got}  (not in the published list; pin it)")
            elif want != got:
                local.unlink(missing_ok=True)
                raise ValueError(f"{rel}: SHA-256 {got} does not match the expected {want}")
            return local

        try:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                return list(pool.map(one, files))
        except OSError as err:
            self._wrap(err)


def load_challenge2017(n_per_class=100, classes=("N", "A"), seed=0, db=None):
    """Single-lead recordings of the PhysioNet/CinC Challenge 2017 training set (Clifford et al. 2017):
    300 Hz, lead I equivalent. Labels: N normal rhythm, A AF, O other rhythm, ~ noisy (REFERENCE-v3.csv,
    the final labels). Returns (list of signals in mV, labels, record names). License: Open Data
    Commons Attribution v1.0."""
    import numpy as np
    from scipy.io import loadmat

    db = db or PhysioNetDB("challenge-2017", "1.0.0", sums="training/SHA256SUMS")
    sums = db.checksums()
    (ref_path,) = db.fetch(["training/REFERENCE-v3.csv"])
    rows = [line.strip().split(",")[:2] for line in ref_path.read_text().splitlines() if "," in line]
    rows = [(Path(r.strip()).name, lab.strip()) for r, lab in rows]   # names may carry their subfolder
    where = {Path(f).stem: f[: -len(".mat")] for f in sums if f.endswith(".mat")}
    if not rows or not where:
        raise ValueError(f"Challenge 2017: {len(rows)} label rows, {len(where)} .mat files in the checksum list; "
                         f"first list entries {list(sums)[:3]}")
    rng = np.random.default_rng(seed)
    chosen, labels = [], []
    for c in classes:
        recs = sorted(r for r, lab in rows if lab == c and r in where)
        if not recs:
            raise ValueError(f"Challenge 2017: no '{c}' records; label rows look like {rows[:3]}, "
                             f"records like {list(where)[:3]}")
        pick = rng.choice(recs, size=min(n_per_class, len(recs)), replace=False)
        chosen += list(pick)
        labels += [c] * len(pick)
    paths = db.fetch([f"{where[r]}.{ext}" for r in chosen for ext in ("mat", "hea")])
    signals = []
    for i, r in enumerate(chosen):
        mat, hea = paths[2 * i], paths[2 * i + 1]
        fields = hea.read_text().splitlines()[1].split()
        gain = float(fields[2].split("/")[0].split("(")[0]) if len(fields) > 2 else 1000.0
        x = np.asarray(loadmat(mat)["val"], float).ravel() / gain   # stored as one row or one column
        print(f"{r}: {x.size} samples") if i < 2 else None
        if x.size < 100:
            raise ValueError(f"{r}: only {x.size} samples read from {mat.name}")
        signals.append(x)
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


def load_afdb_rr(records=("04015", "04043", "04048", "04126", "04746"), db=None):
    """Beat times and rhythm annotations from the MIT-BIH Atrial Fibrillation Database (Moody and Mark
    1983; PhysioNet, doi:10.13026/C2MW2D, Open Data Commons Attribution v1.0). Only the header, the
    unaudited beat annotations (.qrs) and the manual rhythm annotations (.atr) are fetched, a few hundred
    kilobytes per record. Returns {record: {"beats": seconds, "af": [(start_s, end_s), ...], "fs": Hz}}."""
    import wfdb

    db = db or PhysioNetDB("afdb", "1.0.0")
    db.fetch([f"{r}.{ext}" for r in records for ext in ("hea", "qrs", "atr")])
    out = {}
    for r in records:
        base = str(db.cache / r)
        fs = float(wfdb.rdheader(base).fs)
        beats = wfdb.rdann(base, "qrs").sample / fs
        atr = wfdb.rdann(base, "atr")
        notes = [(s / fs, (n or "").strip("\x00").strip()) for s, n in zip(atr.sample, atr.aux_note)]
        notes = [(t, n) for t, n in notes if n.startswith("(")]
        end = float(beats[-1])
        af = []
        for i, (t, n) in enumerate(notes):
            stop = notes[i + 1][0] if i + 1 < len(notes) else end
            if n == "(AFIB":
                af.append((t, stop))
        out[r] = {"beats": beats, "af": af, "fs": fs}
    return out


# ---------------------------------------------------------------------------------------------
# Medical Segmentation Decathlon, Task02_Heart (m40): 20 labelled cardiac MRI volumes with the left
# atrium outlined (Antonelli et al. 2022; data from the 2013 Left Atrial Segmentation Challenge,
# Tobon-Gomez et al. 2015), CC BY-SA 4.0. The archive is fetched from the MONAI consortium's
# AWS Open Data bucket and checked against the MD5 value that MONAI publishes for it
# (monai.apps.DecathlonDataset, MONAI 1.6.1). Its SHA-256 is printed so it can be pinned.

MSD_HEART_URL = "https://msd-for-monai.s3-us-west-2.amazonaws.com/Task02_Heart.tar"
MSD_HEART_MD5 = "06ee59366e1e5124267b774dbd654057"


def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_msd_heart(cache=None):
    """Download, verify and unpack Task02_Heart once; return [(image_path, label_path), ...] for the
    20 training cases, sorted by name. The archive (several hundred MB) is deleted after unpacking."""
    import shutil
    import tarfile

    if skip_real_data():
        raise DataUnavailable("EPML_SKIP_REAL_DATA=1")
    cache = Path(cache) if cache else ROOT / "data" / "cache" / "msd"
    root = cache / "Task02_Heart"
    done = cache / "Task02_Heart.verified"
    if not done.exists():
        cache.mkdir(parents=True, exist_ok=True)
        tar = cache / "Task02_Heart.tar"
        try:
            with urllib.request.urlopen(MSD_HEART_URL, timeout=120) as r, open(tar, "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
        except OSError as err:
            tar.unlink(missing_ok=True)
            if require_data():
                raise
            raise DataUnavailable(f"could not download Task02_Heart: {err}") from err
        got = _md5(tar)
        if got != MSD_HEART_MD5:
            tar.unlink(missing_ok=True)
            raise ValueError(f"Task02_Heart.tar: MD5 {got} does not match MONAI's published {MSD_HEART_MD5}")
        digest = sha256(tar)
        pinned = pinned_checksums(prefix="msd/").get("Task02_Heart.tar")
        print(f"msd/Task02_Heart.tar  sha256 {digest}" + ("  (pinned)" if pinned else ""))
        if pinned and pinned != digest:
            tar.unlink(missing_ok=True)
            raise ValueError(f"Task02_Heart.tar changed: {digest}, registry has {pinned}")
        with tarfile.open(tar) as t:
            members = [m for m in t.getmembers() if m.isfile() and m.name.endswith(".nii.gz")
                       and ("/imagesTr/" in m.name or "/labelsTr/" in m.name)
                       and not Path(m.name).name.startswith("._")]
            t.extractall(cache, members=members, filter="data")
        tar.unlink()
        done.write_text(f"md5 {got}\nsha256 {digest}\n")
    images = sorted(p for p in (root / "imagesTr").glob("*.nii.gz") if not p.name.startswith("._"))
    pairs = [(p, root / "labelsTr" / p.name) for p in images if (root / "labelsTr" / p.name).exists()]
    if len(pairs) != 20:
        raise ValueError(f"expected 20 labelled cases in {root}, found {len(pairs)}")
    return pairs
