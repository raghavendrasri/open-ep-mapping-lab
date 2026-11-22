"""The author's LinkedIn profile: one address in _variables.yml, shown in the navbar, footer and About page."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LINKEDIN = yaml.safe_load((ROOT / "_variables.yml").read_text())["author"]["linkedin"]
SITE = yaml.safe_load((ROOT / "_quarto.yml").read_text())["website"]


def test_linkedin_address_is_the_authors_public_profile():
    assert LINKEDIN == "https://www.linkedin.com/in/eraghavendrasri/"


def test_navbar_and_footer_show_an_accessible_linkedin_icon():
    items = [*SITE["navbar"]["right"], *SITE["page-footer"]["center"]]
    icons = [i for i in items if isinstance(i, dict) and i.get("icon") == "linkedin"]
    assert len(icons) == 2
    for item in icons:
        assert item["href"] == LINKEDIN
        assert item.get("aria-label"), "icon-only links need an aria-label for screen readers"


def test_about_page_links_the_profile_through_the_variable():
    text = (ROOT / "about.qmd").read_text()
    assert "{{< var author.linkedin >}}" in text and "linkedin.com" not in text
