"""Make the shared lab code (labs/python/epml) importable in tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "labs" / "python"))
