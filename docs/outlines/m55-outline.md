# m55 outline · Capstone: a multimodal image-guided procedure on a digital phantom

Stage 1 (outline) for module m55, written together with stages 2–6 (author request, 2026-11-11: finish the
remaining Part VIII modules, one pull request each). Plan source: `docs/outlines/part8-overview.md`.

## Scope

One synthetic left atrium through the whole chain: CT-like volume (m51), segmentation, surface, registration to
simulated map points, predicted and simulated target error, overlay on a simulated fluoroscopy view (m49), the same
registration on real anatomy, and an error and dose budget. Registration methods are derived in m21 (author decision);
the capstone uses them. Out of scope: deformable registration, vendor workflows, advice on any patient.

## Learning goals

1. Relate C-arm geometry to magnification and to what one view can and cannot show.
2. Segment, register and measure errors on a phantom where the truth is known.
3. Predict target registration error from landmark error and layout, and explain why FRE does not predict it.
4. Build an error budget and a dose budget and say what dominates.

## Equations (tests in `tests/test_m55_capstone.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m55-projection | u = SID x/(SOD + y); M = SID/(SOD + y) | SymPy similar triangles; rotation; visible and hidden parts of an error |
| eq-m55-tre | ⟨FRE²⟩ = (1 − 2/N)⟨FLE²⟩; ⟨TRE²⟩ ≈ ⟨FLE²⟩/N (1 + ⅓ Σ d_k²/f_k²) | Monte Carlo within 8% for three layouts at 2 mm; FRE layout-independent; FRE-TRE correlation < 0.1 |
| eq-m55-budget | σ_total = √(Σσ_i²) | Simulation of summed independent errors |

Also tested: least-squares rigid registration recovers a known transform; ICP converges from a rough start.

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m55-d1 | approximate model | Predicted TRE over a plane for a landmark layout; FRE for comparison |
| m55-d2 | exact | Atrial wireframe projected on a C-arm, true and with a registration error; visible and hidden parts |

## Code lab (`labs/python/m55_lab.ipynb`)

A projection; B segmentation of the m51 atrium; C landmark and surface registration with targets; D TRE prediction
against Monte Carlo; E overlay on the m49 projection; F registration on a Decathlon atrium (optional download); G error
and dose budget.

## Sources

PubMed (abstracts read 2026-11-11): fitzpatrick1998, danilchenko2011 (the TRE and FRE expressions were checked
against its PMC full-text summary through web search). Already in `references.bib`: kistler2006, dong2006,
greffier2026, antonelli2021msd.

## Open points for the author

- SOD, SID, noise levels, landmark choices, the catheter localization error and the fluoroscopy KAP rate are
  illustrative.
- CT dose is not in the dose budget; no source for it was read (m51 decision).
- Part F runs only in CI (the data host is blocked in this sandbox); it was dry-run on synthetic NIfTI files.
