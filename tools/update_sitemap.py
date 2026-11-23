"""Ensure static HTML pages published via project.resources appear in _site/sitemap.xml.

Quarto builds _site/sitemap.xml only from rendered .qmd files, so standalone HTML pages such as
learning-hub/index.html are omitted unless added after `quarto render`.

Usage:
    python tools/update_sitemap.py _site
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SITE_URL = "https://openepengineering.org/"
EXTRA_PAGES = ["learning-hub/index.html"]
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def update_sitemap(site_dir: Path) -> int:
    sitemap = site_dir / "sitemap.xml"
    if not sitemap.exists():
        print(f"sitemap not found: {sitemap}")
        return 1

    ET.register_namespace("", NS)
    tree = ET.parse(sitemap)
    root = tree.getroot()
    existing = {el.text.strip() for el in root.findall(f".//{{{NS}}}loc") if el.text}

    added = 0
    for rel in EXTRA_PAGES:
        if not (site_dir / rel).exists():
            continue
        loc = SITE_URL + rel.lstrip("/")
        if loc in existing:
            continue
        url_el = ET.SubElement(root, f"{{{NS}}}url")
        loc_el = ET.SubElement(url_el, f"{{{NS}}}loc")
        loc_el.text = loc
        added += 1

    if added:
        ET.indent(tree, space="  ")
        tree.write(sitemap, encoding="utf-8", xml_declaration=True)
    print(f"updated {sitemap}: added {added} URL(s)")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("_site")
    sys.exit(update_sitemap(target))
