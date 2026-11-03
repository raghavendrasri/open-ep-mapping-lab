"""Download and verify public datasets used by the labs.

Files are fetched from PhysioNet, checked against PhysioNet's published SHA-256 list, and
cached under data/cache/ (not committed). Without network access, fetch functions raise
DataUnavailable so a lab can skip its real-data part. Set EPML_REQUIRE_DATA=1 (CI does) to
turn a missing download into an error instead.
"""

import hashlib
import os
import urllib.request
from pathlib import Path

IAFDB_URL = "https://physionet.org/files/iafdb/1.0.0/"
CACHE = Path(__file__).resolve().parents[3] / "data" / "cache" / "iafdb"


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

    for f in files:
        got = sha256(cache / f)
        if sums.get(f) != got:
            (cache / f).unlink(missing_ok=True)
            raise ValueError(f"{f}: SHA-256 {got} does not match PhysioNet's published {sums.get(f)}")
        print(f"verified {f}  sha256 {got}")
    return str(cache / record)
