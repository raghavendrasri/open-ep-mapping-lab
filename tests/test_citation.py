"""How to cite the course (docs/decisions.md, 2026-11-27).

Three places carry the same citation, with the group author "Open EP Mapping Lab contributors" chosen by the author:
CITATION.cff (GitHub's "Cite this repository"), the site-wide citation settings in _quarto.yml (the "Citation" box at
the bottom of every page, and citation meta tags for Zotero and Google Scholar), and "How to cite" on the About page.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CFF = yaml.safe_load((ROOT / "CITATION.cff").read_text())
CFG = yaml.safe_load((ROOT / "_quarto.yml").read_text())
VARS = yaml.safe_load((ROOT / "_variables.yml").read_text())
ABOUT = (ROOT / "about.qmd").read_text()
GROUP = "Open EP Mapping Lab contributors"


def test_citation_file_is_valid():
    tool = shutil.which("cffconvert")
    if not tool:
        pytest.skip("cffconvert is not installed (it is in requirements.txt)")
    run = subprocess.run([tool, "--validate", "-i", str(ROOT / "CITATION.cff")], capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr


def test_citation_file_matches_the_site():
    assert CFF["cff-version"] == "1.2.0"
    assert CFF["authors"] == [{"name": GROUP}] and CFF["preferred-citation"]["authors"] == [{"name": GROUP}]
    assert CFF["url"] == VARS["site"]["url"] == CFF["preferred-citation"]["url"]
    assert CFF["repository-code"] == VARS["repo"]["url"]
    assert set(CFF["license"]) == {"CC-BY-4.0", "MIT"}
    assert CFF["preferred-citation"]["year"] == CFG["citation"]["issued"]
    assert CFF["title"] == CFF["preferred-citation"]["title"]


def test_every_page_gets_a_citation_box_with_the_group_author():
    assert CFG["author"] == [{"name": {"literal": GROUP}}], "a literal name keeps BibTeX from splitting the group"
    assert CFG["citation"]["type"] == "webpage"
    assert CFG["citation"]["container-title"] == "Open EP Mapping Lab"
    assert CFG["google-scholar"] is True


def test_about_page_citation_matches_the_citation_file():
    assert "## How to cite {#how-to-cite}" in ABOUT
    bib = re.search(r"```bibtex\n(.*?)```", ABOUT, re.S).group(1)
    assert "author = {{" + GROUP + "}}" in bib
    assert f"year = {{{CFF['preferred-citation']['year']}}}" in bib
    assert f"url = {{{CFF['url']}}}" in bib
    # Same title, apart from BibTeX case protection and title case.
    title = re.search(r"title = \{(.*?)\},\n", bib, re.S).group(1).replace("{", "").replace("}", "")
    title = " ".join(title.split())
    assert title.lower() == CFF["title"].lower()
    assert f"{GROUP}. {CFF['preferred-citation']['year']}." in ABOUT
    assert "/about.html#how-to-cite" in CFG["website"]["page-footer"]["right"]


def test_no_page_sets_a_date():
    """The title block is hidden (it would only repeat the author), so a page date would be hidden too."""
    pages = [p for p in ROOT.rglob("*.qmd") if "_site" not in p.parts and ".quarto" not in p.parts]
    for page in pages:
        front = page.read_text().split("---", 2)
        if len(front) > 2:
            assert not re.search(r"^date(-modified)?:", front[1], re.M), page.relative_to(ROOT)
