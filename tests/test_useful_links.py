"""The "Useful links" page (useful-links.qmd): outside resources for learners.

Checks the rules agreed when the page was added (docs/decisions.md, 2026-11-22): it is in the navbar, every outside
link uses https, no watchlist of individuals' social accounts (only society and journal accounts on X), and the
addresses found wrong or moved during the link check do not come back.

The "Videos and courses" section (2026-11-26) is generated from links/videos.yml by tools/build_video_links.py.
Lecturers are credited only as the source of their own public lectures. The tests below check its data, that the
generated file is up to date, that every "Read next" module exists, and that no manufacturer channel is listed.
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "useful-links.qmd"
TEXT = PAGE.read_text()
VIDEOS_MD = (ROOT / "links/_videos.md").read_text()
VIDEOS = yaml.safe_load((ROOT / "links/videos.yml").read_text())
LINK = r"\]\((https?://[^)\s]+)(?:\s+\"[^\"]*\")?\)"
LINKS = re.findall(LINK, TEXT) + re.findall(LINK, VIDEOS_MD)


def test_page_is_rendered_and_in_the_navbar():
    # Quarto renders only the files listed under project.render, and silently drops a navbar entry whose page
    # is not rendered, so both are checked.
    cfg = yaml.safe_load((ROOT / "_quarto.yml").read_text())
    assert "useful-links.qmd" in cfg["project"]["render"]
    assert {"href": "useful-links.qmd", "text": "Useful links"} in cfg["website"]["navbar"]["left"]


def test_outside_links_use_https():
    assert len(LINKS) > 40
    assert all(u.startswith("https://") for u in LINKS), [u for u in LINKS if not u.startswith("https://")]


def test_only_organization_accounts_on_x():
    accounts = {u.split("x.com/")[1] for u in LINKS if "x.com/" in u and "/search?" not in u}
    assert accounts == {"HRSonline", "ESC_Journals", "ACCinTouch"}


def test_addresses_found_wrong_or_moved_stay_out():
    for bad in ("pacejournal.com", "jceonline.com", "journalofarrhythmia.org", "eplabdigest.com", "acutus.com",
                "fda.gov/medical-devices/medical-device-recalls)", "European-Heart-Rhythm-Association-(EHRA)",
                # 2026-11-26: retired Coursera course (404), and a hospital channel of short promotional clips
                "coursera.org/learn/bioelectricity", "MemorialHealthcare"):
        assert bad not in TEXT + VIDEOS_MD, bad


def test_page_states_scope_and_check_date():
    assert "Education only" in TEXT
    assert "last checked on 2026-11-22" in TEXT
    assert "videos\nand courses on 2026-11-26" in TEXT or "videos and courses on 2026-11-26" in TEXT
    assert str(VIDEOS["checked"]) == "2026-11-26"
    assert "not an endorsement" in TEXT


def test_no_handle_is_read_as_a_citation():
    """An unescaped "@name" is a citation key to Quarto and renders as "(name?)"; write "\\@name"."""
    assert not re.search(r"(?<!\\)@[A-Za-z]", TEXT.split("---", 2)[2])
    outside_urls = re.sub(r"\]\([^)]*\)", "]", VIDEOS_MD)  # "@" inside a link address is fine
    assert not re.search(r"(?<!\\)@[A-Za-z]", outside_urls)


# ---------------------------------------------------------------- videos and courses

ITEMS = VIDEOS["items"]
YOUTUBE = re.compile(r"https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}")
MANUFACTURERS = ("johnson & johnson", "biosense", "abbott", "boston scientific", "medtronic", "affera", "philips",
                 "siemens", "ge healthcare", "kardium", "stereotaxis", "acutus", "enchannel", "volta medical",
                 "vektor medical")


def test_video_section_is_included_and_up_to_date():
    assert "{{< include links/_videos.md >}}" in TEXT
    run = subprocess.run([sys.executable, "tools/build_video_links.py", "--check"], cwd=ROOT, capture_output=True,
                         text=True)
    assert run.returncode == 0, run.stdout + run.stderr


def test_video_items_are_complete_and_consistent():
    ids = [i["id"] for i in ITEMS]
    urls = [i["url"] for i in ITEMS]
    assert len(ids) == len(set(ids)) and len(urls) == len(set(urls)) and len(ITEMS) >= 30
    for it in ITEMS:
        assert it["topic"] in VIDEOS["topics"], it["id"]
        assert it["level"] in {"intro", "intermediate", "advanced"}, it["id"]
        assert it["kind"] in {"video", "lecture", "collection", "course", "website", "methods"}, it["id"]
        assert it["url"].startswith("https://") and it["title"].strip() and it["source"].strip(), it["id"]
        assert 20 <= len(it["why"]) <= 160 and it["why"].endswith("."), it["id"]
        if "youtube.com" in it["url"]:
            # YouTube items carry the length and views YouTube showed on the check date.
            assert YOUTUBE.fullmatch(it["url"]), it["url"]
            assert re.fullmatch(r"(\d{1,2}:)?\d{1,2}:\d{2}", it["length"]), it["id"]
            assert re.fullmatch(r"\d+(\.\d)?[KM]?", str(it["views"])), it["id"]
        else:
            assert not it["views"], f"{it['id']}: views only for YouTube items"
    for topic in VIDEOS["topics"]:
        assert any(i["topic"] == topic for i in ITEMS), f"empty topic {topic}"


def test_read_next_links_point_to_real_modules():
    for it in ITEMS:
        if it.get("next"):
            assert len(list((ROOT / "modules").glob(f"{it['next']}-*.qmd"))) == 1, it["id"]


def test_no_manufacturer_channels():
    """The list stays vendor-neutral: companies are listed once, with links only, under "Companies in the field"."""
    for it in ITEMS:
        text = f"{it['source']} {it['title']} {it['url']}".lower()
        assert not any(m in text for m in MANUFACTURERS), it["id"]
    for ch in VIDEOS["channels"]:
        assert not any(m in ch["name"].lower() for m in MANUFACTURERS), ch["name"]


def test_watch_paths_use_listed_youtube_items():
    ids = {i["id"]: i for i in ITEMS}
    assert len(VIDEOS["paths"]) == 3
    for path in VIDEOS["paths"]:
        assert 4 <= len(path["items"]) <= 8
        for iid in path["items"]:
            assert iid in ids and ids[iid]["length"], iid


def test_watch_path_totals_are_sums_of_lengths():
    sys.path.insert(0, str(ROOT / "tools"))
    from build_video_links import hours_minutes, seconds

    assert seconds("1:02:03") == 3723 and seconds("7:50") == 470
    assert hours_minutes(11940) == "3 h 19 min" and hours_minutes(600) == "10 min"
    ids = {i["id"]: i for i in ITEMS}
    for path in VIDEOS["paths"]:
        total = hours_minutes(sum(seconds(ids[i]["length"]) for i in path["items"]))
        assert f"**{path['title']}** · for {path['for']} · {total} in all" in VIDEOS_MD


def test_authors_bookmarks_are_marked():
    assert sum(1 for i in ITEMS if i.get("bookmark")) == VIDEOS_MD.count("★ Author's pick")
