"""The "Useful links" page (useful-links.qmd): outside resources for learners.

Checks the rules agreed when the page was added (docs/decisions.md, 2026-11-22): it is in the navbar, every outside
link uses https, no named individuals are listed (only society and journal accounts), and the addresses found
wrong or moved during the link check do not come back.
"""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "useful-links.qmd"
TEXT = PAGE.read_text()
LINKS = re.findall(r"\]\((https?://[^)\s]+)\)", TEXT)


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
                "fda.gov/medical-devices/medical-device-recalls)", "European-Heart-Rhythm-Association-(EHRA)"):
        assert bad not in TEXT, bad


def test_page_states_scope_and_check_date():
    assert "Education only" in TEXT
    assert "last checked on 2026-11-22" in TEXT
    assert "not an endorsement" in TEXT


def test_no_handle_is_read_as_a_citation():
    """An unescaped "@name" is a citation key to Quarto and renders as "(name?)"; write "\\@name"."""
    assert not re.search(r"(?<!\\)@[A-Za-z]", TEXT.split("---", 2)[2])
