"""Post-process _site/sitemap.xml for canonical URLs, static pages, and accurate lastmod dates.

Quarto writes _site/sitemap.xml only from rendered .qmd files, emits /index.html URLs that conflict
with canonical-url trailing-slash directory URLs (e.g. https://openepengineering.org/index.html vs
https://openepengineering.org/), and stamps every URL with the build timestamp.

This script:
  1. Rewrites each sitemap <loc> to match the <link rel="canonical"> inside the built HTML page
     (falling back to stripping trailing "index.html" for directory roots when HTML is absent).
  2. Adds standalone HTML pages published via project.resources (e.g. learning-hub/index.html).
  3. Replaces build-time <lastmod> values with the source file's last git commit timestamp when git
     history is available.
  4. Deduplicates and sorts URLs deterministically (home page first, then top-level, then modules).

Usage:
    python tools/update_sitemap.py _site
"""
from __future__ import annotations

import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://openepengineering.org/"
EXTRA_PAGES = ["learning-hub/index.html"]
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
CANONICAL_RE = re.compile(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
CANONICAL_RE_ALT = re.compile(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', re.I)


def _html_path_for_loc(site_dir: Path, loc: str) -> Path | None:
    if not loc.startswith(SITE_URL):
        return None
    rel = loc[len(SITE_URL):].lstrip("/")
    if not rel or rel.endswith("/"):
        return site_dir / rel / "index.html"
    return site_dir / rel


def _canonical_loc(site_dir: Path, loc: str) -> str:
    html_path = _html_path_for_loc(site_dir, loc)
    if html_path and html_path.is_file():
        head = html_path.read_text(encoding="utf-8", errors="replace")[:16384]
        match = CANONICAL_RE.search(head) or CANONICAL_RE_ALT.search(head)
        if match and match.group(1).startswith(SITE_URL):
            return match.group(1).strip()
    # Fallback when built HTML has no canonical tag (e.g. synthetic test): strip Quarto's /index.html
    # on directory roots, while preserving explicitly listed static EXTRA_PAGES.
    rel = loc[len(SITE_URL):].lstrip("/") if loc.startswith(SITE_URL) else ""
    if rel not in EXTRA_PAGES and (rel == "index.html" or rel.endswith("/index.html")):
        return loc[: -len("index.html")]
    return loc


def _source_for_loc(loc: str) -> Path | None:
    if not loc.startswith(SITE_URL):
        return None
    rel = loc[len(SITE_URL):].lstrip("/")
    candidates: list[Path] = []
    if rel in ("", "index.html"):
        candidates.append(ROOT / "index.qmd")
    elif rel.endswith("/"):
        candidates.extend([ROOT / f"{rel}index.qmd", ROOT / f"{rel}index.html"])
    elif rel.endswith(".html"):
        candidates.extend([ROOT / (rel[:-5] + ".qmd"), ROOT / rel])
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def _git_lastmod(source: Path) -> str | None:
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(source.relative_to(ROOT))],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    stamp = res.stdout.strip()
    return stamp if res.returncode == 0 and stamp else None


def _sort_key(loc: str) -> tuple[int, str]:
    if loc == SITE_URL:
        return (0, loc)
    if "/modules/" in loc:
        return (2, loc)
    return (1, loc)


def update_sitemap(site_dir: Path) -> int:
    sitemap = site_dir / "sitemap.xml"
    if not sitemap.exists():
        print(f"sitemap not found: {sitemap}")
        return 1

    ET.register_namespace("", NS)
    tree = ET.parse(sitemap)
    root = tree.getroot()

    # Collect existing entries, normalizing each <loc> to its page's canonical URL.
    entries: dict[str, str | None] = {}
    normalized = 0
    for url_el in list(root.findall(f"{{{NS}}}url")):
        loc_el = url_el.find(f"{{{NS}}}loc")
        if loc_el is None or not loc_el.text:
            continue
        raw_loc = loc_el.text.strip()
        canon_loc = _canonical_loc(site_dir, raw_loc)
        if canon_loc != raw_loc:
            normalized += 1
        lastmod_el = url_el.find(f"{{{NS}}}lastmod")
        lastmod = lastmod_el.text.strip() if (lastmod_el is not None and lastmod_el.text) else None
        if canon_loc not in entries:
            entries[canon_loc] = lastmod

    # Ensure standalone static pages published via project.resources are included.
    added = 0
    for rel in EXTRA_PAGES:
        if not (site_dir / rel).exists():
            continue
        loc = _canonical_loc(site_dir, SITE_URL + rel.lstrip("/"))
        if loc not in entries:
            entries[loc] = None
            added += 1

    # Refresh <lastmod> from git history when running against this repository's real pages.
    # (Skip when site_dir is a synthetic temp fixture outside the repo without built HTML for the repo.)
    use_git = (ROOT / ".git").exists() and site_dir.resolve().is_relative_to(ROOT)
    for loc in list(entries):
        if use_git:
            src = _source_for_loc(loc)
            git_ts = _git_lastmod(src) if src else None
            if git_ts:
                entries[loc] = git_ts

    # Rebuild <urlset> cleanly in deterministic order.
    for child in list(root):
        root.remove(child)
    for loc in sorted(entries, key=_sort_key):
        url_el = ET.SubElement(root, f"{{{NS}}}url")
        loc_el = ET.SubElement(url_el, f"{{{NS}}}loc")
        loc_el.text = loc
        if entries[loc]:
            lm_el = ET.SubElement(url_el, f"{{{NS}}}lastmod")
            lm_el.text = entries[loc]

    ET.indent(tree, space="  ")
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(f"updated {sitemap}: {len(entries)} URL(s) ({normalized} normalized, {added} added)")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_site")
    sys.exit(update_sitemap(target))
