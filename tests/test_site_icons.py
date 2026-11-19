"""The site icons (favicon) made from the author's logo by tools/make_favicons.py."""
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def test_icon_files_have_the_expected_sizes():
    assert Image.open(ROOT / "favicon.png").size == (64, 64)
    assert Image.open(ROOT / "apple-touch-icon.png").size == (180, 180)
    assert sorted(Image.open(ROOT / "favicon.ico").info["sizes"]) == [(16, 16), (32, 32), (48, 48)]
    assert (ROOT / "assets" / "logo" / "logo.png").exists()


def test_quarto_links_and_publishes_the_icons():
    cfg = yaml.safe_load((ROOT / "_quarto.yml").read_text())
    assert cfg["website"]["favicon"] == "favicon.png"
    resources = cfg["project"]["resources"]
    assert "favicon.ico" in resources and "apple-touch-icon.png" in resources


def test_learning_hub_uses_the_site_icon():
    hub = (ROOT / "learning-hub" / "index.html").read_text()
    assert '<link rel="icon" type="image/png" href="../favicon.png" />' in hub
    assert 'href="data:,"' not in hub


def test_home_page_shows_the_logo_beside_one_title():
    """index.qmd draws its own header (logo + title) and has no `title`, so Quarto adds no second title."""
    text = (ROOT / "index.qmd").read_text()
    front = yaml.safe_load(text.split("---")[1])
    assert "title" not in front and front["pagetitle"] == "Open EP Mapping Lab"
    assert "{.home-header}" in text and "assets/logo/logo-mark.png" in text
    assert len([l for l in text.splitlines() if l.startswith("# ")]) == 1
    assert Image.open(ROOT / "assets" / "logo" / "logo-mark.png").size == (256, 256)
