"""Feedback button, form and relay (docs/decisions.md, 2026-11-25).

The form (assets/feedback.html) is on every page. Without a relay it opens a prefilled issue on GitHub; with the
Cloudflare Worker in services/feedback-worker it creates the issue directly. These tests check the settings, run the
Worker's own tests in Node, and drive the form in Chromium with every outside call intercepted, so CI stays offline.
"""
import functools
import http.server
import json
import re
import shutil
import subprocess
import threading
import tomllib
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import yaml
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "assets/feedback.html"
WORKER = ROOT / "services/feedback-worker"
VARS = yaml.safe_load((ROOT / "_variables.yml").read_text())
CFG = yaml.safe_load((ROOT / "_quarto.yml").read_text())

TEST_ENDPOINT = "https://feedback.example.test/"
TEST_SITEKEY = "1x00000000000000000000AA"  # Cloudflare's public test key; only ever used inside these tests


def form_settings(text=None):
    block = re.search(r"var FEEDBACK = \{(.*?)\};", text or FORM.read_text(), re.S).group(1)
    return dict(re.findall(r'(\w+): "([^"]*)"', block))


def kinds(text, pattern):
    block = re.search(pattern, text, re.S).group(1)
    return dict(re.findall(r'(\w+): "([^"]+)"', block))


# ---------------------------------------------------------------- settings


def test_form_is_on_every_page():
    assert "assets/feedback.html" in CFG["format"]["html"]["include-after-body"]


def test_form_settings_agree_with_variables():
    s = form_settings()
    assert s["repo"] == VARS["repo"]["url"]
    assert bool(s["endpoint"]) == bool(s["turnstileSiteKey"]), "set endpoint and turnstileSiteKey together"
    if s["endpoint"]:
        assert s["endpoint"].startswith("https://")
        assert not re.match(r"[123]x0{10}", s["turnstileSiteKey"]), "a Cloudflare test key was left in"


def test_worker_settings_agree_with_variables():
    cfg = tomllib.loads((WORKER / "wrangler.toml").read_text())
    site, repo = VARS["site"]["url"], VARS["repo"]["url"]
    v = cfg["vars"]
    assert v["SITE_URL"] == site
    assert v["ALLOWED_ORIGINS"] == site.rstrip("/")
    assert v["EXPECTED_HOSTNAME"] == urlparse(site).hostname
    assert f"https://github.com/{v['GITHUB_REPO']}" == repo
    assert not {"GITHUB_TOKEN", "TURNSTILE_SECRET"} & set(v), "secrets belong in `wrangler secret put`, not here"
    endpoint = form_settings()["endpoint"]
    if endpoint:
        domains = [r["pattern"] for r in cfg["routes"] if r.get("custom_domain")]
        assert urlparse(endpoint).hostname in domains


def test_form_and_worker_offer_the_same_kinds():
    form = kinds(FORM.read_text(), r"var KINDS = \{(.*?)\};")
    worker = kinds((WORKER / "src/index.js").read_text(), r"export const KINDS = \{(.*?)\};")
    assert form == worker and len(form) == 5


def test_no_credentials_in_the_repository():
    assert ".dev.vars" in (ROOT / ".gitignore").read_text().splitlines()
    token = re.compile(r"(ghp_|github_pat_|gho_|ghs_)[A-Za-z0-9_]{20,}")
    for path in [FORM, *WORKER.rglob("*")]:
        if path.is_file() and "node_modules" not in path.parts:
            assert not token.search(path.read_text(errors="ignore")), path


def test_worker_unit_tests_pass():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is not installed here (GitHub's CI runners have it)")
    files = [str(p.relative_to(WORKER)) for p in sorted(WORKER.glob("test/*.test.js"))]
    assert files
    run = subprocess.run([node, "--test", *files], cwd=WORKER, capture_output=True, text=True, timeout=120)
    assert run.returncode == 0, run.stdout[-4000:] + run.stderr[-2000:]


# ---------------------------------------------------------------- the form in a browser

PAGE_TITLE = "m03 · Electrograms – Open EP Mapping Lab"
CLAIM = "The bipolar spacing is 4 mm."


@pytest.fixture
def site(tmp_path):
    """Serve a page that holds the form; returns a function that writes it with the given settings."""
    (tmp_path / "modules").mkdir()

    def write(endpoint="", sitekey=""):
        html = FORM.read_text().replace('endpoint: ""', f'endpoint: "{endpoint}"')
        html = html.replace('turnstileSiteKey: ""', f'turnstileSiteKey: "{sitekey}"')
        page = (f"<!doctype html><html><head><meta charset='utf-8'><title>{PAGE_TITLE}</title></head>"
                f"<body><main><p id='claim'>{CLAIM}</p></main>{html}</body></html>")
        (tmp_path / "modules/m03.html").write_text(page)
        return f"http://127.0.0.1:{server.server_address[1]}/modules/m03.html"

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(tmp_path)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield write
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


def select_claim(page):
    page.evaluate("""() => { const r = document.createRange(); r.selectNodeContents(document.getElementById('claim'));
                             const s = getSelection(); s.removeAllRanges(); s.addRange(r); }""")


def test_form_without_relay_opens_a_prefilled_github_issue(site, browser):
    url = site()
    page = browser.new_page()
    outside = []
    page.on("request", lambda r: outside.append(r.url) if not r.url.startswith("http://127.0.0.1") else None)
    page.goto(url)
    page.evaluate("window.open = (u) => { window.__opened = u; return null; }")

    button = page.locator("#epml-feedback-open")
    assert button.is_visible()
    select_claim(page)
    button.click()
    dialog = page.locator("#epml-feedback")
    assert dialog.is_visible()
    assert page.locator("[data-page-title]").inner_text() == "m03 · Electrograms"
    assert page.locator("[data-selection]").inner_text() == CLAIM
    assert page.locator("[data-submit]").inner_text() == "Continue on GitHub"
    assert page.evaluate("document.activeElement.id") == "epml-feedback-message"

    page.locator("[data-submit]").click()
    assert "at least 10 characters" in page.locator("[data-status]").inner_text()
    assert page.evaluate("window.__opened") is None

    page.select_option("#epml-feedback-kind", "unclear")
    page.fill("#epml-feedback-message", "The caption and the text disagree on the electrode spacing.")
    page.locator("[data-submit]").click()
    opened = urlparse(page.evaluate("window.__opened"))
    assert f"{opened.scheme}://{opened.netloc}{opened.path}" == VARS["repo"]["url"] + "/issues/new"
    query = parse_qs(opened.query)
    assert query["title"] == ["Feedback (Something is unclear): modules/m03"]
    assert "labels" not in query  # the GitHub mobile app fails on it; a workflow labels the issue instead
    body = query["body"][0]
    assert url in body and "electrode spacing" in body and CLAIM in body

    page.keyboard.press("Escape")
    assert not dialog.is_visible()
    assert page.evaluate("document.activeElement.id") == "epml-feedback-open"
    assert outside == [], f"the form called outside addresses without a relay: {outside}"
    page.close()


# Stands in for Cloudflare's script: hands out a token after rendering and a fresh one after each reset.
TURNSTILE_STUB = """window.turnstile = {
  render: function (el, opts) {
    window.__opts = opts; el.textContent = 'spam check (stub)';
    if (!window.__noToken) setTimeout(function () { opts.callback('XXXX.DUMMY.TOKEN.XXXX'); }, 0);
    return 'w1';
  },
  reset: function () {
    window.__resets = (window.__resets || 0) + 1;
    var n = window.__resets + 1;
    setTimeout(function () { window.__opts.callback('TOKEN-' + n); }, 0);
  }
};
if (window.epmlTurnstileReady) window.epmlTurnstileReady();"""


def relay(page, answers):
    """Intercept the spam-check script and the relay; `answers` is a list of (status, json) for each POST."""
    posts = []
    page.route("https://challenges.cloudflare.com/**",
               lambda route: route.fulfill(status=200, content_type="text/javascript", body=TURNSTILE_STUB))

    def handle(route):
        origin = route.request.headers.get("origin", "")
        cors = {"Access-Control-Allow-Origin": origin, "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"}
        if route.request.method == "OPTIONS":
            return route.fulfill(status=204, headers=cors)
        posts.append(json.loads(route.request.post_data))
        status, payload = answers[len(posts) - 1]
        route.fulfill(status=status, headers=cors, content_type="application/json", body=json.dumps(payload))

    page.route(TEST_ENDPOINT + "**", handle)
    return posts


def status_contains(page, text):
    page.wait_for_function("t => document.querySelector('[data-status]').textContent.includes(t)", arg=text)


def test_form_with_relay_sends_the_feedback_and_shows_the_issue(site, browser):
    url = site(TEST_ENDPOINT, TEST_SITEKEY)
    page = browser.new_page()
    posts = relay(page, [(201, {"ok": True, "url": "https://github.com/o/r/issues/9", "number": 9}),
                         (502, {"error": "github-failed"})])
    page.goto(url)
    select_claim(page)
    page.locator("#epml-feedback-open").click()
    assert page.locator("[data-submit]").inner_text() == "Send feedback"
    page.wait_for_function("document.querySelector('[data-turnstile]').textContent.includes('stub')")
    assert page.locator("[data-github-link]").is_visible()

    page.fill("#epml-feedback-message", "Figure 2 shows 2 mm but the text says 4 mm.")
    page.locator("[data-submit]").click()
    status_contains(page, "issue #9")
    assert posts[0] == {
        "kind": "error",
        "message": "Figure 2 shows 2 mm but the text says 4 mm.",
        "page": url,
        "pageTitle": PAGE_TITLE,
        "selection": CLAIM,
        "token": "XXXX.DUMMY.TOKEN.XXXX",
        "website": "",
    }
    assert page.locator("[data-status] a").get_attribute("href") == "https://github.com/o/r/issues/9"
    assert page.input_value("#epml-feedback-message") == ""  # cleared after sending
    assert page.locator("[data-selection-box]").is_hidden()
    assert page.locator("[data-cancel]").inner_text() == "Close"
    assert page.evaluate("window.__resets") == 1  # each spam-check token is used once

    # A failure keeps the reader's text and offers GitHub instead.
    page.fill("#epml-feedback-message", "Second message, which the relay will fail to send.")
    page.wait_for_function("window.__resets === 1")
    page.wait_for_timeout(50)  # the stub hands out the next token
    page.locator("[data-submit]").click()
    status_contains(page, "didn't send")
    assert posts[1]["token"] == "TOKEN-2" and posts[1]["selection"] == ""
    assert page.input_value("#epml-feedback-message") == "Second message, which the relay will fail to send."
    assert page.locator("[data-status] a").get_attribute("href").startswith(VARS["repo"]["url"] + "/issues/new?")
    page.close()


def test_form_waits_for_the_spam_check(site, browser):
    url = site(TEST_ENDPOINT, TEST_SITEKEY)
    page = browser.new_page()
    posts = relay(page, [])
    page.add_init_script("window.__noToken = true")
    page.goto(url)
    page.locator("#epml-feedback-open").click()
    page.fill("#epml-feedback-message", "A message sent before the spam check has finished.")
    page.locator("[data-submit]").click()
    status_contains(page, "spam check")
    assert posts == []
    page.close()


# ---------------------------------------------------------------- labeling


def test_feedback_issues_are_labeled_by_a_safe_workflow():
    """Neither route sets labels (the GitHub mobile app failed on an unknown one); a workflow adds them."""
    wf = yaml.safe_load((ROOT / ".github/workflows/label-feedback.yml").read_text())
    on = wf.get("on", wf.get(True))  # PyYAML reads the key `on` as True
    assert on == {"issues": {"types": ["opened"]}}
    assert wf["permissions"] == {"issues": "write"}
    job = wf["jobs"]["label"]
    assert job["if"] == "startsWith(github.event.issue.title, 'Feedback (')"
    steps = job["steps"]
    assert not any("uses" in s and "checkout" in s["uses"] for s in steps), "no code is checked out"
    run = "\n".join(s.get("run", "") for s in steps)
    assert "github.event.issue.title" not in run and "${{" not in run, "event text never reaches the shell"
    assert "gh label create feedback" in run and "--force" in run and "--add-label feedback" in run
    # Both routes title issues so the workflow matches them.
    assert '"Feedback (" + KINDS[kind.value] + "): "' in FORM.read_text()
    assert "const title = `Feedback (${KINDS[value.kind]}): ${shortPath}`;" in (WORKER / "src/index.js").read_text()
