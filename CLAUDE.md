# CLAUDE.md — Open EP Mapping Lab

Read this file at the start of every session. It sets the rules for all work in this repo.
If a request conflicts with this file, say so and ask before going ahead.

## 1. What this project is

A free, open, interactive course on **cardiac electroanatomic mapping (EAM) systems**:
how mapping systems localize catheters, record and process electrograms, and build
activation and voltage maps.

- Working name: **Open EP Mapping Lab**. Do not call it "OpenEP"; that is a separate,
  established project (openep.io) that we build on and credit.
- The course format (parts, modules, live figures, code labs, formula sheet, interview
  questions, errata) is inspired by OpenUltrasoundLab. We borrow the idea only (see §6).
- **Education only. Not for diagnosis, treatment or any clinical decision.**

## 2. Audience and scope

Readers:
- Engineers joining EP device companies (software, signal processing, hardware)
- Clinical mapping specialists and field engineers
- EP fellows and physicians who want the engineering view
- Researchers using OpenEP, openCARP or ECG-imaging tools

Assume undergraduate engineering math (calculus, linear algebra, basic signals and systems).
Define every clinical term on first use and add it to the glossary.

In scope: physics, hardware principles, electrogram processing, map algorithms, simulation,
validation, regulation.

Out of scope: ablation-strategy advice, vendor operating instructions, anything meant for
patient care. Never write text that tells a clinician what to do for a patient.

Curriculum (6 parts, 36 modules, learning paths): see `docs/curriculum.md`.
Do not add, drop or renumber modules without the author's approval.

## 3. Module template

Every module has these sections, in this order:

1. **In 60 seconds** — the whole idea in one paragraph.
2. **From the field** — practical lessons from the mapping lab.
3. **Derivations with live figures** — each figure badged (§4).
4. **Key takeaways** — at the end of each section.
5. **Clinical correlate** — where this shows up in a real case. Mark it
   `status: pending clinical review` until an EP physician signs it off.
6. **Visual summary** and **How experts think**.
7. **Cheat sheet** and **Interview questions** with model answers.
8. **Code lab**, then a **Self-check**.
9. **Literature figures** with citations, and **Further reading**.

## 4. Figures and demos

Every figure or demo carries exactly one badge:

| Badge | Meaning |
| --- | --- |
| `exact` | Plots a closed-form result with no approximation beyond those stated in the derivation |
| `simulation` | Output of a numerical model (name the model, solver and key parameters) |
| `approximate model` | A simplified model chosen for intuition; state what it ignores |
| `schematic` | Illustrative drawing, not to scale, no quantitative claim |

Rules for every demo:
- An **Assumptions** list directly under it: model, simplifications, parameter values with
  sources, and what would change the result.
- Axis labels with units. Default parameters must be physiologically plausible and cited.
- Runs offline: no network calls at runtime; vendored libraries are pinned in `vendor/`.
- Heavy simulations are precomputed offline and shipped as small files (target ≤ 2 MB per demo).
- Keyboard-usable controls and a text description for screen readers.
- Original drawings only. No vendor screenshots. Reuse a published figure only if its license
  allows it (for example CC BY), with full attribution; otherwise regenerate from our own code.

## 5. Verification rules (non-negotiable)

Claude drafts. Humans sign off. Never mark a module, section or claim as "reviewed".

- **Equations:** every equation has a check in code: a numeric test in `tests/`, and a
  symbolic check with SymPy where feasible. A derivation without a passing test is not done.
- **Numbers:** every quantitative value (thresholds, amplitudes, conduction velocities,
  accuracies, sampling rates) comes from a cited source or from our own code. **Never invent
  a number.** If a source is missing, write `TODO(source)` and keep it out of releases.
- **Citations:** every citation is actually looked up before use (resolve the DOI or PMID;
  use the PubMed connector when available). Never cite from memory. Store entries in
  `references.bib` with DOI or PMID. If a source cannot be verified, mark it `[unverified]`
  and flag it in the pull request.
- **Quotations:** paraphrase. Short quotes only, in quotation marks, with a citation.
- **Clinical statements:** cite a guideline, consensus statement or primary paper, and leave
  the section marked pending clinical review.
- **Vendor-specific claims:** only from public sources (510(k) summaries, peer-reviewed papers,
  patents). Describe the principle generically.
- **Uncertainty:** when unsure of a fact, say so in the PR. Do not guess.
- Record open claims and corrections in `errata.json`; human sign-offs go in
  `review_record.json`.

## 6. Licenses and IP

| What | License |
| --- | --- |
| Text, figures, glossary, questions | CC BY 4.0 (`LICENSE-CONTENT`) |
| Code: labs, demos, build and test tools | MIT (`LICENSE`) |
| Datasets | Keep the source license; record it in `data/registry.json` |

- **OpenUltrasoundLab:** idea and format only. Never copy its text, figures, templates, site
  design or build tools.
- **openCARP** (Academic Public License): never commit its source or binaries here. Link to it,
  and publish only our own simulation outputs.
- **OpenEP:** use its parsers and data format as a dependency; credit it.
- **Trademarks** (CARTO, EnSite, Rhythmia, KODEX and others): use names only to describe the
  products, with a public source.
- **Patient data:** never commit identifiable patient data. Clinical datasets need ethics
  approval and a data-sharing agreement first.

## 7. Tech stack

Defaults below; the author may change them after the pilot module (record changes in
`docs/decisions.md`).

- **Site:** Quarto, static HTML, deployed to GitHub Pages.
- **Math:** LaTeX rendered with MathJax; numbered equations.
- **Demos:** plain ES modules; Canvas 2D or SVG for 2D, three.js for 3D meshes, WebGL for
  reaction–diffusion. No front-end build step unless the author approves one.
- **Labs:** Python 3.11+ with numpy, scipy, matplotlib, sympy, pyvista, wfdb; openep-py pinned
  to a specific commit (its API is unstable). Part I labs also get GNU Octave copies in
  `labs/octave/`.
- **Tests and CI:** pytest (equation tests and labs), nbmake for notebooks, Playwright for page
  and demo render checks, a link and anchor checker, all in GitHub Actions.
- **Data:** large datasets on Zenodo with DOIs; small samples (≤ 5 MB) in `data/samples/`.

## 8. Repository layout (target)

```
modules/            m01-<slug>.qmd … m36-<slug>.qmd
demos/              m03-d1-<slug>.js, one ES module per demo
labs/python/        m03_lab.ipynb and helpers
labs/octave/        Part I copies
tests/              equation and lab tests
data/registry.json  dataset DOIs, licenses, checksums
data/samples/       small sample files
glossary/  formula-sheet/  interview/
docs/               curriculum.md, decisions.md
vendor/             pinned third-party JS
errata.json  review_record.json  references.bib
```

## 9. Conventions

- IDs: modules `m01`–`m36`; demos `m03-d1`; equations `{#eq-m03-bipolar}`; figures
  `{#fig-m03-...}`.
- Units: voltage mV, time ms, distance mm, conduction velocity m/s, frequency Hz.
- Writing: American English, short sentences, plain words, every symbol defined on first use.
- One module per branch (`module/m03-electrograms`), one pull request per stage.

## 10. How Claude works on a module

1. Read this file, `docs/curriculum.md` and the module's outline, `docs/outlines/mNN-outline.md`
   (if any).
2. Work in stages and **stop for author review after each stage**:
   outline → derivations + tests → demos → code lab → cheat sheet + interview questions →
   self-check + literature figures.
3. The outline lists every planned equation, demo and lab, with the sources to be verified.
4. Run the full check suite before calling any stage done, and report what failed.
5. Log non-trivial choices in `docs/decisions.md`.

### Commands

```
pip install -r requirements.txt            # once
python -m playwright install chromium      # once, for the render check
pytest -q                                  # content rules, badge filter, equation tests
quarto render                              # build the site into _site/
quarto preview                             # live preview while writing
python tools/check_links.py _site          # internal links and anchors
python tools/check_render.py _site         # every page loads without errors
```

The full check suite = all four checks above (pytest, render, links, render check). CI runs
the same steps on every pull request.

### Starting a new module

1. Copy `templates/module-template.qmd` to `modules/mNN-<slug>.qmd`.
2. Add the file to the sidebar in `_quarto.yml`.
3. Keep every level-2 heading from the template, in order.

## 11. Definition of done (per module)

- [ ] All nine template sections present (§3)
- [ ] Every equation has a passing test
- [ ] Every demo is badged, lists its assumptions, runs offline and passes the render check
- [ ] The code lab runs in CI from a clean environment in under 5 minutes
- [ ] Every citation resolved (DOI or PMID) and present in `references.bib`
- [ ] No `TODO(source)` or `[unverified]` left
- [ ] New glossary terms and formula-sheet entries added
- [ ] At least 10 interview questions with model answers, and at least 5 self-check questions
- [ ] Expert review recorded in `review_record.json` (human)
- [ ] Clinical correlate signed off by an EP physician (human)
