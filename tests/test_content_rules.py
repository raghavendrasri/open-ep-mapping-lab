"""Checks that course content follows the rules in CLAUDE.md.

Runs on every pull request. Each failure message says which rule was broken and where.
"""

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE_FILES = sorted((ROOT / "modules").glob("m[0-9][0-9]-*.qmd"))
TEMPLATE = ROOT / "templates" / "module-template.qmd"

# CLAUDE.md §3: level-2 headings every module has, in this order.
REQUIRED_HEADINGS = [
    "In 60 seconds",
    "From the field",
    "Derivations",
    "Clinical correlate",
    "Visual summary",
    "How experts think",
    "Cheat sheet",
    "Interview questions",
    "Code lab",
    "Self-check",
    "Literature figures",
    "Further reading",
]

# CLAUDE.md §4
ALLOWED_BADGES = {"exact", "simulation", "approximate model", "schematic"}
STATUSES = {"draft", "in-review", "released"}
CLINICAL_REVIEW = {"pending", "signed-off"}

# CLAUDE.md §5: markers that must not appear in released modules.
UNFINISHED_MARKERS = ["TODO(source)", "[unverified]"]


def split_front_matter(text):
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert match, "file must start with YAML front matter between --- lines"
    return yaml.safe_load(match.group(1)), match.group(2)


def h2_headings(body):
    return [m.group(1).strip() for m in re.finditer(r"^## (.+)$", body, re.M)]


def curriculum_ids():
    text = (ROOT / "docs" / "curriculum.md").read_text()
    return set(re.findall(r"^\| (m\d\d) \|", text, re.M))


def demo_divs(body):
    """Return (attributes, content) for every `.demo` fenced div, including nested ones."""
    demos, stack = [], []
    for line in body.splitlines():
        fence = re.match(r"^(:{3,})\s*(.*)$", line)
        if fence and fence.group(2):  # opening fence, with attributes
            stack.append({"attrs": fence.group(2), "lines": []})
        elif fence:  # closing fence
            if stack:
                div = stack.pop()
                if ".demo" in div["attrs"]:
                    demos.append((div["attrs"], "\n".join(div["lines"])))
                if stack:
                    stack[-1]["lines"].extend(div["lines"])
        elif stack:
            stack[-1]["lines"].append(line)
    return demos


def module_ids(path):
    return pytest.param(path, id=path.stem)


def test_at_least_one_module_exists():
    assert MODULE_FILES, "no modules found in modules/"


@pytest.mark.parametrize("path", [module_ids(p) for p in MODULE_FILES] + [pytest.param(TEMPLATE, id="template")])
def test_required_sections_in_order(path):
    _, body = split_front_matter(path.read_text())
    headings = h2_headings(body)
    assert headings == REQUIRED_HEADINGS, (
        f"{path.name}: level-2 headings must be exactly, in order:\n  {REQUIRED_HEADINGS}\n"
        f"found:\n  {headings}"
    )


@pytest.mark.parametrize("path", [module_ids(p) for p in MODULE_FILES])
def test_front_matter(path):
    meta, _ = split_front_matter(path.read_text())
    module_id = path.name[:3]
    assert meta.get("module-id") == module_id, f"{path.name}: module-id must be {module_id}"
    assert module_id in curriculum_ids(), f"{path.name}: {module_id} is not in docs/curriculum.md"
    assert str(meta.get("title", "")).startswith(f"{module_id} · "), (
        f"{path.name}: title must start with '{module_id} · '"
    )
    assert meta.get("part"), f"{path.name}: front matter needs a 'part'"
    assert meta.get("status") in STATUSES, f"{path.name}: status must be one of {sorted(STATUSES)}"
    assert meta.get("clinical-review") in CLINICAL_REVIEW, (
        f"{path.name}: clinical-review must be one of {sorted(CLINICAL_REVIEW)}"
    )


@pytest.mark.parametrize("path", [module_ids(p) for p in MODULE_FILES] + [pytest.param(TEMPLATE, id="template")])
def test_demos_have_badge_and_assumptions(path):
    _, body = split_front_matter(path.read_text())
    for attrs, content in demo_divs(body):
        badge = re.search(r'badge="([^"]*)"', attrs)
        assert badge and badge.group(1) in ALLOWED_BADGES, (
            f"{path.name}: demo {{{attrs}}} needs badge= one of {sorted(ALLOWED_BADGES)}"
        )
        assert re.search(r"^\*\*Assumptions\*\*", content, re.M), (
            f"{path.name}: demo {{{attrs}}} needs an **Assumptions** list"
        )
        assert re.search(r"#m\d\d-d\d+", attrs) or "#mNN-d" in attrs, (
            f"{path.name}: demo {{{attrs}}} needs an ID like #m03-d1"
        )


@pytest.mark.parametrize("path", [module_ids(p) for p in MODULE_FILES])
def test_released_modules_are_finished(path):
    meta, body = split_front_matter(path.read_text())
    if meta.get("status") != "released":
        pytest.skip("only released modules are checked for unfinished work")
    for marker in UNFINISHED_MARKERS:
        assert marker not in body, f"{path.name}: released module still contains {marker}"
    assert meta.get("clinical-review") == "signed-off", (
        f"{path.name}: released module needs clinical-review: signed-off (set by a human)"
    )
    assert "**Key takeaways**" in body, f"{path.name}: released module needs Key takeaways"


def test_references_have_doi_or_pmid():
    text = (ROOT / "references.bib").read_text()
    entries = re.split(r"\n(?=@)", text)
    for entry in entries:
        if not entry.strip().startswith("@"):
            continue
        key = re.match(r"@\w+\{([^,]+),", entry.strip())
        assert re.search(r"^\s*(doi|pmid)\s*=", entry, re.M | re.I), (
            f"references.bib: entry {key.group(1) if key else '?'} needs a doi or pmid field"
        )


def test_record_files_are_valid_json_lists():
    for name in ["errata.json", "review_record.json", "data/registry.json"]:
        data = json.loads((ROOT / name).read_text())
        assert isinstance(data, list), f"{name} must contain a JSON list"


def test_datasets_record_license_and_checksum():
    for entry in json.loads((ROOT / "data" / "registry.json").read_text()):
        for field in ["name", "source", "license", "sha256"]:
            assert entry.get(field), f"data/registry.json: entry {entry} needs '{field}'"
