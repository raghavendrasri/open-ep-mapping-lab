"""The blog (docs/decisions.md, 2026-11-28).

Placement follows the UI/UX plan: a top-menu item, a "Latest from the blog" strip on the home page, an RSS icon in the
footer, and links from modules' "Further reading" when a post fits. Blog pages have no course sidebar and keep post
dates visible. Posts follow the course rules; templates/blog-post-template.qmd explains how to add one.
"""
import datetime as dt
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "_quarto.yml").read_text())
BLOG = ROOT / "blog"
POSTS = sorted((BLOG / "posts").glob("*/index.qmd"))
CATEGORIES = {"Concept", "Paper", "Behind the module", "Reader questions", "Course news"}


def front(path):
    return yaml.safe_load(path.read_text().split("---", 2)[1])


def test_blog_is_built_and_in_the_top_menu():
    render = CFG["project"]["render"]
    assert "blog/index.qmd" in render and "blog/posts/*/index.qmd" in render
    left = CFG["website"]["navbar"]["left"]
    texts = [i["text"] for i in left]
    assert texts.index("Blog") == texts.index("Learning hub") + 1, "Blog sits after the course items"
    assert {"href": "blog/index.qmd", "text": "Blog"} in left


def test_blog_pages_have_no_course_sidebar_and_show_post_dates():
    meta = yaml.safe_load((BLOG / "_metadata.yml").read_text())
    assert meta["sidebar"] is False
    assert meta["body-classes"] == "epml-blog"
    assert meta["date-format"] == "MMMM D, YYYY"
    assert "body:not(.epml-blog) .quarto-title-meta {\n  display: none !important;" in (ROOT / "assets/theme.scss").read_text()
    nav = (ROOT / "assets/nav-current.html").read_text()
    assert r"[/\/blog\/posts\//, /\/blog\/$/]" in nav, "posts mark Blog as their section"


def test_post_list_page():
    fm = front(BLOG / "index.qmd")
    listing = fm["listing"]
    assert listing["contents"] == "posts" and listing["sort"] == "date desc"
    assert listing["feed"] is True and listing["categories"] is True and listing["filter-ui"] is True
    assert fm["citation"] is False and fm["body-classes"] == "epml-blog-list"
    assert "(index.xml)" in (BLOG / "index.qmd").read_text(), "a visible RSS link"


def test_every_post_follows_the_rules():
    assert POSTS, "at least one post"
    for post in POSTS:
        fm = front(post)
        folder = post.parent.name
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+", folder), folder
        assert str(fm["date"]) == folder[:10], f"{folder}: the folder starts with the post date"
        assert isinstance(fm["date"], dt.date)
        assert 60 <= len(fm["description"]) <= 160, f"{folder}: description length"
        assert fm["categories"] and set(fm["categories"]) <= CATEGORIES, f"{folder}: categories"
        text = post.read_text()
        assert "[← All posts](../../index.qmd)" in text


def test_post_template_is_ready_to_copy():
    template = ROOT / "templates/blog-post-template.qmd"
    fm = front(template)
    assert fm["draft"] is True, "new posts start as drafts"
    assert set(fm["categories"]) <= CATEGORIES
    text = template.read_text()
    for heading in ("## In short", "## Read next", "## Sources"):
        assert heading in text
    assert "blog/posts/YYYY-MM-DD-short-name/index.qmd" in text


def test_footer_rss_icon_and_home_strip():
    center = CFG["website"]["page-footer"]["center"]
    rss = [i for i in center if isinstance(i, dict) and i.get("icon") == "rss"]
    assert len(rss) == 1 and rss[0]["href"] == "/blog/index.xml" and rss[0]["aria-label"]
    home = (ROOT / "index.qmd").read_text()
    listing = front(ROOT / "index.qmd")["listing"]
    assert listing["id"] == "latest-posts" and listing["max-items"] == 3 and listing["contents"] == "blog/posts"
    assert "## Latest from the blog" in home and "::: {#latest-posts}" in home
    # Below the main buttons, never above them.
    assert home.index(".hero-actions") < home.index("## Latest from the blog")


def test_dark_filter_icon_is_not_a_white_box():
    """The blog filter's magnifier box must follow the dark theme."""
    dark = (ROOT / "assets" / "theme-dark.scss").read_text(encoding="utf-8")
    assert "$input-group-addon-bg:" in dark
