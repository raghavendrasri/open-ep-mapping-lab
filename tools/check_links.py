"""Check internal links and anchors in the built site.

Usage: python tools/check_links.py _site

Every relative href and src in our HTML pages must point to a file that exists, and every
#anchor must match an id on the target page. External links are not checked here.
"""

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SKIP_SCHEMES = ("http", "https", "mailto", "javascript", "data", "tel")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("id", "name"):
            if attrs.get(key):
                self.ids.add(attrs[key])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


def parse(path, cache):
    if path not in cache:
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        cache[path] = parser
    return cache[path]


def main(site_dir):
    site = Path(site_dir).resolve()
    pages = [p for p in site.rglob("*.html") if "site_libs" not in p.parts]
    cache, problems = {}, []

    for page in pages:
        for link in parse(page, cache).links:
            parts = urlsplit(link)
            if parts.scheme in SKIP_SCHEMES or link.startswith("//"):
                continue
            target = page if not parts.path else (page.parent / unquote(parts.path)).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                problems.append(f"{page.relative_to(site)}: missing target {link}")
                continue
            if parts.fragment and target.suffix == ".html":
                if unquote(parts.fragment) not in parse(target, cache).ids:
                    problems.append(f"{page.relative_to(site)}: missing anchor {link}")

    for problem in problems:
        print(problem)
    print(f"Checked {len(pages)} pages: {len(problems)} broken internal links.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "_site"))
