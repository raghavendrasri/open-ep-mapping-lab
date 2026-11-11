"""Write the corpus for demo m43-d2 (retrieval over the course glossary and formula sheet).

Run from the repository root after any change to the glossary or formula sheet:
    python tools/make_m43_d2.py
Writes demos/m43-d2-corpus.json. tests/test_m43_demos.py checks that it is up to date.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs" / "python"))

from epml import retrieval as rt  # noqa: E402


def compute():
    return {
        "docs": [{"id": i, "text": t} for i, t in rt.course_corpus()],
        "questions": [{"q": q, "gold": g} for q, g in rt.QUESTIONS],
        "stop": sorted(rt.STOP),
    }


if __name__ == "__main__":
    path = ROOT / "demos" / "m43-d2-corpus.json"
    path.write_text(json.dumps(compute(), ensure_ascii=False, separators=(",", ":")))
    print(path, path.stat().st_size, "bytes")
