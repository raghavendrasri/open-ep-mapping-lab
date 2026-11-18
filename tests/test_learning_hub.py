"""Learning Hub (learning-hub/index.html): built from its source, offline, cited, and within the course rules."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "learning-hub" / "index.html"


def page() -> str:
    return HUB.read_text(encoding="utf-8")


def test_hub_is_up_to_date_with_its_build(tmp_path):
    """The published page is exactly what tools/build_learning_hub.py makes from the source, so edits go through
    the build script and every replacement is visible there."""
    out = tmp_path / "hub.html"
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_learning_hub.py"), str(out)], check=True,
                   capture_output=True, cwd=ROOT)
    assert out.read_text(encoding="utf-8") == page(), "rerun python tools/build_learning_hub.py"


def test_hub_runs_offline():
    """CLAUDE.md §4: no network requests at runtime (fonts are self-hosted) and no embedded raster images."""
    s = page()
    assert "fonts.googleapis" not in s and "fonts.gstatic" not in s
    assert not re.search(r'<(link|script|img|iframe|source)\b[^>]*\b(href|src)="https?://', s)
    assert not re.search(r"url\(\s*['\"]?https?://", s)
    assert "data:image/" not in s, "raster images are not allowed; the hero is an original inline SVG"
    for font in re.findall(r'url\("\.\./(vendor/fonts/[^"]+)"\)', s):
        assert (ROOT / font).exists(), f"missing self-hosted font {font}"


def test_hub_citations_resolve():
    """Every citation link points to an entry in the page's reference list, and every listed reference is a
    references.bib entry with a DOI."""
    s = page()
    ids = set(re.findall(r'<li id="ref-([a-z0-9]+)">', s))
    cited = set(re.findall(r'href="#ref-([a-z0-9]+)"', s))
    assert cited and cited <= ids, f"citations without a reference: {sorted(cited - ids)}"
    assert ids <= cited, f"references never cited: {sorted(ids - cited)}"
    bib = (ROOT / "references.bib").read_text()
    for key in ids:
        entry = re.search(r"@\w+\{" + key + r",(.*?)\n\}", bib, re.S)
        assert entry and re.search(r"^\s*doi\s*=", entry.group(1), re.M), f"{key}: not in references.bib with a doi"


def test_hub_states_status_and_scope():
    """Education only, pending clinical review, and no ablation advice (CLAUDE.md §2)."""
    text = re.sub(r"<[^>]+>", " ", page())
    assert "Education only" in text and "pending clinical review" in text
    for phrase in ["ablate the", "never ablate", "highest-value target", "targets the red", "well-placed lesion",
                   "before committing to a lesion", "before ablating"]:
        assert phrase.lower() not in text.lower(), f"advice wording left in the hub: {phrase!r}"


def test_hub_is_in_the_navbar():
    quarto = (ROOT / "_quarto.yml").read_text()
    assert "href: learning-hub/index.html" in quarto and "- learning-hub/index.html" in quarto
