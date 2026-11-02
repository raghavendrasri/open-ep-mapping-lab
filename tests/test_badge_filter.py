"""Checks that filters/badges.lua labels valid demos and stops the build on bad badges."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILTER = ROOT / "filters" / "badges.lua"

pytestmark = pytest.mark.skipif(shutil.which("quarto") is None, reason="Quarto is not installed")


def run_filter(markdown):
    return subprocess.run(
        ["quarto", "pandoc", "--from", "markdown", "--to", "html", "--lua-filter", str(FILTER)],
        input=markdown,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("badge", ["exact", "simulation", "approximate model", "schematic"])
def test_valid_badge_is_labeled(badge):
    result = run_filter(f'::: {{.demo #m03-d1 badge="{badge}"}}\nbody\n:::\n')
    assert result.returncode == 0, result.stderr
    slug = badge.replace(" ", "-")
    assert f'class="badge badge-{slug}"' in result.stdout


@pytest.mark.parametrize("attrs", ['badge="guess"', ""])
def test_missing_or_unknown_badge_fails(attrs):
    result = run_filter(f"::: {{.demo #m03-d1 {attrs}}}\nbody\n:::\n")
    assert result.returncode != 0
    assert "needs badge=" in result.stderr


def test_other_divs_are_untouched():
    result = run_filter("::: {.callout-note}\nbody\n:::\n")
    assert result.returncode == 0, result.stderr
    assert "badge" not in result.stdout
