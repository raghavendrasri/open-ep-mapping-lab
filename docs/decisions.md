# Decisions log

Non-trivial choices, newest first. Each entry: date, decision, why, and how to undo it.

## 2026-11-02 · m03 code lab

- **Notebook committed without outputs.** CI executes it (nbmake), so outputs never go stale and
  the repo stays small. Colab and Jupyter users see outputs when they run it.
- **Real data is downloaded, not committed (for now).** The outline proposed keeping one iafdb
  record in `data/samples/`, but PhysioNet is not reachable from the authoring environment, so
  the file could not be fetched and checked there. `epml/data.py` downloads it, verifies it
  against PhysioNet's published SHA-256 list, and caches it in `data/cache/` (git-ignored). CI
  sets `EPML_REQUIRE_DATA=1`, so the real-data part must succeed in CI rather than skip, and
  caches the download between runs. Undo: commit the two files to `data/samples/` with a
  `data/registry.json` entry.
- **Octave copy uses anonymous functions, `fprintf` and `assert`** so the same file runs in GNU
  Octave and base MATLAB. CI runs it with figures off.
- **Labs have a 5-minute CI timeout**, enforcing CLAUDE.md §11.

## 2026-11-02 · m03 demos

- **Demo math mirrors the tested Python model.** `demos/m03-common.js` re-implements the
  functions in `labs/python/epml/electrograms.py`; `tests/test_m03_demo_math.py` runs it in Node
  and compares the numbers. Bessel J1 is computed from its integral form (no memorized
  coefficients) and checked against SciPy.
- **One tiny plotting helper, no libraries** (`demos/plot.js`): canvas plots, polar plots, labeled
  sliders, live text readouts. Okabe-Ito colors plus dashes, so curves stay distinguishable
  without color.
- **The render check now exercises every demo:** each must draw, label its canvases and sliders,
  and update its readout when an arrow key moves a slider. This caught a start-up-order bug.
- **Demo defaults and their sources:** c = 1.0 m/s [heil2023], h = 1 mm [riccio2021],
  d = 2 mm [iafdb; riccio2021 for the clique], 1-mm electrode as a 0.5-mm-radius disk [anter2015].
  The front width w = 0.3 mm is **TODO(source)**: it follows from an upstroke near 100 V/s
  [wang1991] only with an action-potential amplitude we have not yet sourced.
- **Far-field demo uses illustrative source strength and timing**, stated as such in its
  Assumptions; only the trend with distance is a claim.

## 2026-11-02 · Course map and placeholder pages

- **Every module has a page from day one.** Unwritten modules get a generated placeholder
  (`status: planned`) showing planned topics, learning paths and planned release, so the whole
  course structure can be shown to people now.
- **`docs/curriculum.md` is the single source of truth.** `tools/sync_curriculum.py` generates the
  placeholder pages, `_sidebar.yml` (loaded through `metadata-files`) and `course-map.qmd`. A test
  fails if they are out of date. Pages with any status other than `planned` are never overwritten.
- **Sidebar parts collapse** (`collapse-level: 1`) so 36 modules stay navigable.

## 2026-11-02 · m03 derivations

- **Arctangent wavefront model.** The rise of V_m across the front is modeled as an arctangent of
  width w. Its slope is a Lorentzian, so the unipolar electrogram has a closed form,
  U(s) = A s / (s² + a²) with a = w + h. This keeps every m03 result exact and testable. A
  tanh or ionic-model front would need numerics. Undo: swap the front model in
  `labs/python/epml/electrograms.py`; the tests compare against independent quadrature, so they
  would show what changes.
- **Omnipole direction = principal axis of the E-field loop.** The published method picks the
  angle whose projection best matches the unipolar derivative (cross-correlation). Both give the
  propagation direction for a plane wave. The text says which one we use.
- **Shared model code lives in `labs/python/epml/`.** Tests, labs and (later) demo data
  generation import the same functions. `tests/conftest.py` adds it to the import path.
- **New content rules:** every numbered equation must be named in a test, and every cited key
  must exist in `references.bib` (`tests/test_content_rules.py`).
- **Bibliography wired into Quarto** (`bibliography: references.bib` in `_quarto.yml`).
  Citations render as author-date with a reference list at the end of each page.

## 2026-11-02 · Publishing the pilot

- **Repo is public, and the site publishes to GitHub Pages** after CI passes on `main`
  (`deploy-pages.yml`, triggered by the CI workflow). A failing check never goes live. Undo:
  set the trigger back to `workflow_dispatch` only.
- **CI moved from Python 3.11 to 3.12.** Dependabot raised the SciPy minimum to 1.18.1, which
  requires Python 3.12, and the install step failed on 3.11. CLAUDE.md §7 now says 3.12+.

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
