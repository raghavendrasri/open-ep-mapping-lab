"""Search-engine metadata: module summaries, the About page, link previews and structured data.

Added 2026-11-22 (docs/decisions.md). Every module needs a one-sentence `description`: Quarto uses it as the page's
<meta name="description"> (the summary under a search result) and shows it under the title.
"""
import json
import re
from pathlib import Path

import yaml

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


def test_about_page_is_rendered_and_linked():
    assert "about.qmd" in CFG["project"]["render"]
    assert {"href": "about.qmd", "text": "About"} in CFG["website"]["navbar"]["right"]
    text = (ROOT / "about.qmd").read_text()
    for must in ("Education only", "None has been reviewed yet", "AI assistant", "/issues"):
        assert must in text, must


def test_link_previews_are_on():
    site = CFG["website"]
    assert site["open-graph"] is True and site["twitter-card"] is True
    assert (ROOT / site["image"]).exists()


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
