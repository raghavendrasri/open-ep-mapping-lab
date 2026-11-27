"""Page-view counting with Cloudflare Web Analytics (docs/decisions.md, 2026-11-27).

assets/analytics.html is on every Quarto page and on the Learning hub. It does nothing until a token is set, and even
then loads Cloudflare's beacon only on the live site, never when the browser sends Global Privacy Control or Do Not
Track. The browser tests serve the snippet as if from openepengineering.org with every outside call intercepted, so CI
stays offline and is never counted.
"""
import re
from pathlib import Path

import pytest
import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SNIPPET = (ROOT / "assets/analytics.html").read_text()
CFG = yaml.safe_load((ROOT / "_quarto.yml").read_text())
BEACON = "https://static.cloudflareinsights.com/beacon.min.js"
TEST_TOKEN = "0123456789abcdef0123456789abcdef"  # made up; only ever used inside these tests


def token():
    return re.search(r'var CLOUDFLARE_ANALYTICS_TOKEN = "([^"]*)";', SNIPPET).group(1)


def test_snippet_is_on_every_page_and_the_hub():
    assert "assets/analytics.html" in CFG["format"]["html"]["include-after-body"]
    assert SNIPPET in (ROOT / "learning-hub/index.html").read_text()


def test_token_is_empty_or_well_formed():
    assert token() == "" or re.fullmatch(r"[A-Za-z0-9]{16,64}", token()), "paste only the token value"


def test_only_cloudflare_is_contacted():
    urls = set(re.findall(r"https?://[^\s\"'<>]+", SNIPPET))
    assert urls == {BEACON}


def test_privacy_note_matches_the_snippet():
    about = (ROOT / "about.qmd").read_text()
    assert "## Page views and privacy {#privacy}" in about
    for phrase in ("Cloudflare Web Analytics", "no cookies", "Global Privacy Control", "Do Not Track"):
        assert phrase in about, phrase
    for guard in ('"openepengineering.org"', "globalPrivacyControl", "doNotTrack"):
        assert guard in SNIPPET, guard


# ---------------------------------------------------------------- in a browser


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


def visit(browser, host, tok, init=""):
    """Load a page holding the snippet from `host`; return the beacon requests and the beacon tag's config."""
    html = SNIPPET.replace('var CLOUDFLARE_ANALYTICS_TOKEN = "";', f'var CLOUDFLARE_ANALYTICS_TOKEN = "{tok}";')
    page = browser.new_page()
    if init:
        page.add_init_script(init)
    seen = []
    page.route(f"http://{host}/**", lambda r: r.fulfill(status=200, content_type="text/html",
                                                        body=f"<!doctype html><html><body><p>page</p>{html}</body></html>"))
    page.route("https://static.cloudflareinsights.com/**",
               lambda r: (seen.append(r.request.url), r.fulfill(status=200, content_type="text/javascript", body="")))
    page.goto(f"http://{host}/modules/m03.html")
    page.wait_for_timeout(100)
    config = page.evaluate("() => { const s = document.querySelector('script[data-cf-beacon]'); "
                           "return s && s.getAttribute('data-cf-beacon'); }")
    page.close()
    return seen, config


def test_counts_on_the_live_site_once_a_token_is_set(browser):
    seen, config = visit(browser, "openepengineering.org", TEST_TOKEN)
    assert seen == [BEACON]
    assert config == '{"token":"%s"}' % TEST_TOKEN


def test_never_counts_without_a_token(browser):
    assert visit(browser, "openepengineering.org", "") == ([], None)


def test_never_counts_local_previews_or_ci(browser):
    assert visit(browser, "127.0.0.1:4200", TEST_TOKEN) == ([], None)
    assert visit(browser, "localhost", TEST_TOKEN) == ([], None)


def test_respects_global_privacy_control_and_do_not_track(browser):
    gpc = "Object.defineProperty(navigator, 'globalPrivacyControl', {get: () => true});"
    dnt = "Object.defineProperty(navigator, 'doNotTrack', {get: () => '1'});"
    assert visit(browser, "openepengineering.org", TEST_TOKEN, gpc) == ([], None)
    assert visit(browser, "openepengineering.org", TEST_TOKEN, dnt) == ([], None)
