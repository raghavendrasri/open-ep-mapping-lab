"""Site menu and the light and dark themes.

Added 2026-11-23 (docs/decisions.md): a four-item menu with a "More" list, a search box in the menu, and a dark
theme ("night lab") layered on the light one. These tests check the menu structure, that the dark layer can
override the light colors, and that every text color meets WCAG 2.x AA contrast (4.5:1) on its background.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "_quarto.yml").read_text())
NAV = CFG["website"]["navbar"]
LIGHT = ROOT / "assets/theme.scss"
DARK = ROOT / "assets/theme-dark.scss"

AA = 4.5  # WCAG 2.x level AA for body-size text


# ---------------------------------------------------------------- menu


def test_menu_has_four_items_and_more():
    left = NAV["left"]
    assert [i["text"] for i in left] == ["Course map", "Learning hub", "Useful links", "About", "More"]
    assert [i["href"] for i in left[:4]] == [
        "course-map.qmd",
        "learning-hub/index.html",
        "useful-links.qmd",
        "about.qmd",
    ]


def test_more_menu_lists_the_other_pages_and_each_is_built():
    more = NAV["left"][4]["menu"]
    pages = [i for i in more if "href" in i]
    assert [i["text"] for i in pages] == [
        "Glossary",
        "Formula sheet",
        "AI competencies",
        "Pilot module",
        "Errata",
        "Disclaimer",
    ]
    render = CFG["project"]["render"]
    for item in pages:
        href = item["href"]
        built = href in render or any("*" in r and Path(href).match(r) for r in render)
        assert built, f"{href} is in the menu but not in project.render, so Quarto would drop it"
        assert (ROOT / href).exists(), href


def test_logo_and_search_box_are_in_the_menu():
    assert (ROOT / NAV["logo"]).exists()
    search = CFG["website"]["search"]
    assert search["location"] == "navbar" and search["type"] == "textbox"
    assert CFG["language"]["search-text-placeholder"].strip()


def test_current_page_marker_is_included():
    includes = CFG["format"]["html"]["include-after-body"]
    assert "assets/nav-current.html" in includes
    text = (ROOT / "assets/nav-current.html").read_text()
    assert 'aria-current", "page"' in text
    assert r"\/modules\/" in text and "course-map" in text  # module pages mark "Course map" as their section


# ---------------------------------------------------------------- themes


def test_light_and_dark_themes_are_configured():
    theme = CFG["format"]["html"]["theme"]
    assert theme["light"] == ["cosmo", "assets/theme.scss"]
    assert theme["dark"] == ["cosmo", "assets/theme.scss", "assets/theme-dark.scss"]
    assert CFG["format"]["html"]["respect-user-color-scheme"] is True


def scss_vars(path):
    """Variables from the scss:defaults section: name -> (value, has !default)."""
    defaults = path.read_text().split("/*-- scss:rules --*/")[0]
    out = {}
    for m in re.finditer(r"^\$([\w-]+):\s*([^;]+?)\s*(!default)?\s*;", defaults, re.M):
        out[m.group(1)] = (m.group(2).strip(), bool(m.group(3)))
    return out


def test_dark_layer_can_override_every_shared_color():
    """theme.scss is compiled before theme-dark.scss, so a shared variable needs !default in theme.scss."""
    light, dark = scss_vars(LIGHT), scss_vars(DARK)
    shared = sorted(set(light) & set(dark))
    assert {"epml-ink", "body-bg", "navbar-bg"} <= set(shared)
    stuck = [n for n in shared if not light[n][1]]
    assert not stuck, f"set without !default in theme.scss, so the dark theme cannot change them: {stuck}"


def resolve(name, *tables):
    for table in tables:
        if name in table:
            value = table[name][0]
            return resolve(value[1:], *tables) if value.startswith("$") else value
    raise KeyError(name)


def luminance(hex_color):
    h = hex_color.lstrip("#")
    assert len(h) == 6, hex_color
    channels = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def test_contrast_formula_matches_known_values():
    assert round(contrast("#000000", "#ffffff"), 1) == 21.0
    assert round(contrast("#777777", "#ffffff"), 2) == 4.48  # the classic "#777 just fails AA" example


def test_light_text_colors_meet_aa():
    v = scss_vars(LIGHT)
    for fg in ("epml-ink", "epml-muted", "epml-blue", "epml-red", "code-color"):
        for bg in ("body-bg", "epml-paper-tint"):
            ratio = contrast(resolve(fg, v), resolve(bg, v))
            assert ratio >= AA, f"light: ${fg} on ${bg} is {ratio:.2f}:1"


def test_dark_text_colors_meet_aa():
    d, light = scss_vars(DARK), scss_vars(LIGHT)
    fgs = ("epml-ink", "epml-muted", "epml-blue", "epml-red", "headings-color", "code-color", "navbar-fg")
    bgs = ("body-bg", "epml-paper-tint", "navbar-bg", "dropdown-bg", "dropdown-link-hover-bg")
    for fg in fgs:
        for bg in bgs:
            ratio = contrast(resolve(fg, d, light), resolve(bg, d, light))
            assert ratio >= AA, f"dark: ${fg} on ${bg} is {ratio:.2f}:1"


def rule_colors(path, selector):
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", path.read_text())
    assert m, selector
    body = m.group(1)
    bg = re.search(r"background(?:-color)?:\s*(#[0-9a-fA-F]{6})", body)
    fg = re.search(r"(?<![-\w])color:\s*(#[0-9a-fA-F]{6}|\$[\w-]+)", body)
    return bg.group(1), fg.group(1)


def test_dark_status_labels_and_hero_text_meet_aa():
    d, light = scss_vars(DARK), scss_vars(LIGHT)
    for status in ("planned", "draft", "in-review", "released"):
        bg, fg = rule_colors(DARK, f".status-{status}")
        fg = resolve(fg[1:], d, light) if fg.startswith("$") else fg
        assert contrast(fg, bg) >= AA, f"dark .status-{status}: {contrast(fg, bg):.2f}:1"
    text = DARK.read_text()
    hero_bg = re.search(r"\.hero-egm \{\s*background:\s*(#[0-9a-f]{6})", text).group(1)
    hero_fg = re.search(r'\[fill="#5b6875"\] \{ fill: (#[0-9a-f]{6}); \}', text).group(1)
    assert contrast(hero_fg, hero_bg) >= AA


def test_demos_stay_on_a_light_panel_in_the_dark_theme():
    """Demo plots use fixed colors drawn for white paper, so the dark theme keeps each demo on a light panel."""
    bg, fg = rule_colors(DARK, ".demo")
    assert luminance(bg) > 0.9 and contrast(fg, bg) >= 7
