"""Open every page of the built site in headless Chromium and report errors.

Usage: python tools/check_render.py _site
Needs: pip install playwright && python -m playwright install chromium

Fails on JavaScript errors and on local files that fail to load. External resources
(for example the MathJax CDN) are reported as warnings only, so the check also works offline.
"""

import functools
import http.server
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(site):
    handler = functools.partial(QuietHandler, directory=str(site))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main(site_dir):
    site = Path(site_dir).resolve()
    pages = sorted(p.relative_to(site).as_posix() for p in site.rglob("*.html") if "site_libs" not in p.parts)
    server = serve(site)
    base = f"http://127.0.0.1:{server.server_address[1]}/"
    errors, warnings = [], []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for page_path in pages:
            page = browser.new_page()
            page.on("pageerror", lambda exc, p=page_path: errors.append(f"{p}: JavaScript error: {exc}"))

            def on_failed(request, p=page_path):
                target = errors if request.url.startswith(base) else warnings
                target.append(f"{p}: failed to load {request.url}")

            def on_response(response, p=page_path):
                if response.url.startswith(base) and response.status >= 400:
                    errors.append(f"{p}: HTTP {response.status} for {response.url}")

            page.on("requestfailed", on_failed)
            page.on("response", on_response)
            page.goto(base + page_path, wait_until="load")
            page.wait_for_timeout(300)
            page.close()
        browser.close()
    server.shutdown()

    for line in warnings:
        print("warning:", line)
    for line in errors:
        print("error:", line)
    print(f"Rendered {len(pages)} pages: {len(errors)} errors, {len(warnings)} external warnings.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "_site"))
