# Decisions log

Non-trivial choices, newest first. Each entry: date, decision, why, and how to undo it.

## 2026-11-02 · Site skeleton

- **Quarto for the site.** It handles math, cross-references, executed code and search with no
  custom build code. Undo: replace `_quarto.yml` and the `.qmd` front matter.
- **Badges enforced by a Lua filter** (`filters/badges.lua`). A demo without a valid badge stops
  the build, so the rule in CLAUDE.md §4 cannot be skipped by accident.
- **Content rules checked by pytest** (`tests/test_content_rules.py`): section order, front
  matter, demo badges and Assumptions, finished-work checks for released modules, and a doi or
  pmid on every reference.
- **GitHub Pages deploy is manual for now.** The repo is private, and Pages on a free plan needs a
  public repo. CI still builds the site and uploads it as a downloadable preview.
- **MathJax and theme fonts load from CDNs.** The render check reports external failures as
  warnings, not errors. Revisit before v0.1: vendor MathJax into `vendor/` if the site must work
  fully offline.
- **Lab packages added on demand.** `requirements.txt` holds only the build and test tools.
  pyvista, wfdb and openep-py (pinned to a commit) are added with the first lab that uses them.
- **Errata page is written by hand** until there are entries. Generate it from `errata.json`
  once the first correction lands.
