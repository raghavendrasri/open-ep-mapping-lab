"""AI disclosure (docs/decisions.md, 2026-11-27): every page's footer says the site is developed using AI (Claude
and Gemini) and links to the About section that explains how AI drafts are checked."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "_quarto.yml").read_text())
ABOUT = (ROOT / "about.qmd").read_text()


def test_footer_discloses_ai_and_links_to_how_content_is_checked():
    left = CFG["website"]["page-footer"]["left"]
    assert "Education only. Not for clinical use." in left
    assert "Claude and Gemini" in left
    assert "(/about.html#how-the-content-is-written-and-checked)" in left


def test_about_names_both_assistants_where_the_footer_points():
    section = ABOUT.split("## How the content is written and checked", 1)[1].split("\n## ", 1)[0]
    assert "Claude" in section and "Gemini" in section
    assert re.search(r"checked against\s+written rules", section)
