"""Search-engine metadata: module summaries, the About page, link previews and structured data.

Added 2026-11-22 (docs/decisions.md). Every module needs a one-sentence `description`: Quarto uses it as the page's
<meta name="description"> (the summary under a search result) and shows it under the title.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "_quarto.yml").read_text())


def front_matter(path):
    return yaml.safe_load(path.read_text().split("---", 2)[1])


def test_every_module_has_a_distinct_search_summary():
    descs = {}
    for f in sorted((ROOT / "modules").glob("m*.qmd")):
        d = front_matter(f).get("description", "")
        assert 90 <= len(d) <= 160, f"{f.name}: description is {len(d)} characters; keep it 90-160"
        descs[f.name] = d
    assert len(descs) == 55
    assert len(set(descs.values())) == 55, "two modules share a description"


def test_every_top_level_page_has_a_search_summary():
    for rel in CFG["project"]["render"]:
        if "*" in rel:
            continue
        p = ROOT / rel
        d = front_matter(p).get("description", "")
        assert 60 <= len(d) <= 160, f"{rel}: description is {len(d)} characters; keep it 60-160"


def test_about_page_is_rendered_and_linked():
    assert "about.qmd" in CFG["project"]["render"]
    assert {"href": "about.qmd", "text": "About"} in CFG["website"]["navbar"]["left"]
    text = (ROOT / "about.qmd").read_text()
    for must in ("Education only", "None has been reviewed yet", "AI assistant", "/issues", "not affiliated"):
        assert must in text, must


def test_link_previews_and_canonicals_are_on():
    site = CFG["website"]
    assert site["open-graph"] is True and site["twitter-card"] is True
    assert CFG["format"]["html"]["canonical-url"] is True
    img = ROOT / site["image"]
    assert img.exists()
    assert Image.open(img).size == (1200, 630)


def test_robots_txt_and_seo_filter_configured():
    robots = (ROOT / "robots.txt").read_text()
    assert "Sitemap: https://openepengineering.org/sitemap.xml" in robots
    assert "robots.txt" in CFG["project"]["resources"]
    assert "assets/logo/og-card.png" in CFG["project"]["resources"]
    assert "filters/seo-schema.lua" in CFG["filters"]
    assert (ROOT / "filters" / "seo-schema.lua").exists()


def test_learning_hub_has_seo_metadata():
    hub = (ROOT / "learning-hub" / "index.html").read_text()
    for must in (
        '<meta name="description"',
        '<link rel="canonical" href="https://openepengineering.org/learning-hub/index.html"',
        'property="og:image"',
        'application/ld+json',
    ):
        assert must in hub, must


def test_update_sitemap_adds_learning_hub(tmp_path):
    (tmp_path / "learning-hub").mkdir()
    (tmp_path / "learning-hub" / "index.html").write_text("<html></html>")
    sm = tmp_path / "sitemap.xml"
    sm.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url><loc>https://openepengineering.org/</loc></url>\n'
        '</urlset>\n'
    )
    subprocess.run([sys.executable, str(ROOT / "tools" / "update_sitemap.py"), str(tmp_path)], check=True)
    text = sm.read_text()
    assert "https://openepengineering.org/learning-hub/index.html" in text
    # Running a second time is idempotent.
    subprocess.run([sys.executable, str(ROOT / "tools" / "update_sitemap.py"), str(tmp_path)], check=True)
    assert sm.read_text().count("learning-hub/index.html") == 1


def test_home_page_structured_data_is_valid_json():
    header = front_matter(ROOT / "index.qmd")["include-in-header"]["text"]
    data = json.loads(re.search(r"<script type=\"application/ld\+json\">(.*)</script>", header, re.S).group(1))
    types = {node["@type"]: node for node in data["@graph"]}
    course = types["Course"]
    assert types["WebSite"]["url"] == course["url"] == "https://openepengineering.org/"
    assert course["isAccessibleForFree"] is True
    assert course["offers"][0]["category"] == "Free"
    assert course["provider"]["name"] and course["description"]


def test_search_titles_lead_with_the_topic():
    """Each module's <title> (the search-result title) is its topic without the "mNN · " code, so the topic words
    come first; the page heading, breadcrumbs and sidebar keep the code."""
    for f in sorted((ROOT / "modules").glob("m*.qmd")):
        fm = front_matter(f)
        code, topic = fm["title"].split(" · ", 1)
        assert re.fullmatch(r"m\d\d", code), f.name
        assert fm["pagetitle"] == topic, f"{f.name}: pagetitle should be {topic!r}"
