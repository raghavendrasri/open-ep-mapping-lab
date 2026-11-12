# m53 outline · Imaging ablation lesions and real-time MRI-guided EP

Stage 1 (outline) for module m53, written together with stages 2–6 (author request, 2026-11-11: finish the
remaining Part VIII modules, one pull request each). Plan source: `docs/outlines/part8-overview.md`.

## Scope

What imaging can and cannot see of ablation lesions: gaps under blur, acute edema against scar, and agreement between
image gaps and electrical reconnection. Then real-time MRI-guided ablation: frame budgets, active and passive catheter
visualization, electrograms recorded in the scanner, and the published feasibility evidence. How lesions form is in
m27 and m28; LGE physics is in m52. Out of scope: sequence design, MR thermometry beyond a mention, equipment
operation, advice on any patient.

## Learning goals

1. Compute when blur hides a gap of a given width, and how edema narrows apparent gaps.
2. Measure agreement between image gaps and reconnection with kappa, and explain what limits it.
3. Relate lines, repetition time, acceleration and frame rate in real-time MRI.
4. Explain why electrograms degrade inside the scanner and what filtering costs.
5. Read the evidence on lesion imaging and real-time MRI-guided ablation by design.

## Equations (tests in `tests/test_m53_lesion.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m53-gap | I = B(y)[1 − G(x)]; line and gap-center signals; smallest visible gap | Numerical Gaussian blur; SymPy inverse; ring-lesion detection follows the prediction |
| eq-m53-frame | T = N TR / R; motion v T | SymPy scaling; published frame-rate range |

Also tested: Cohen's kappa limits; the filter chain removes most illustrative interference, with 120 Hz leaving less
noise and less signal than 300 Hz.

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m53-d1 | exact | A lesion line with a gap, as made and blurred; profile along the line; gap, blur and line width |
| m53-d2 | exact | Frames per second against lines per frame for a TR and acceleration; reported passive and active rates; motion per frame |

## Code lab (`labs/python/m53_lab.ipynb`)

A gaps under blur; B a ring lesion around a vein; C image gaps against reconnection (kappa); D acute edema; E real-time
frame budget; F electrograms in the scanner; G the evidence by design. No downloads.

## Sources

PubMed (abstracts, and the full text of tampakis2023, read 2026-11-11): aljefairi2019, hopman2026, jahnke2024,
tampakis2023, fusco2024. Already in `references.bib`: akoum2024, kellman2012, achenbach2000.

## Open points for the author

- Lesion and gap widths, noise, edema margins, reconnection probabilities, repetition times and the electrogram and
  interference waveforms are illustrative.
- The kappa simulation is a teaching model; it is not calibrated to the published 0.37.
- Human real-time MRI-guided ablation in the cited work is typical flutter only.
