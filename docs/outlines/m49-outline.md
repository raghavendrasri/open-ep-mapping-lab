# m49 outline · Fluoroscopy and radiation protection

Stage 1 (outline) for module m49, the first Part VIII module, written together with stages 2–6 (author decision,
2026-11-11: build m49 and m50 first). Plan source: `docs/outlines/part8-overview.md`.

## Scope

How a fluoroscopy image forms and what it costs: exponential attenuation, subject contrast, quantum noise, dose
quantities (air kerma, kerma-area product), reference levels, staff dose (time, distance, shielding, pulse rate),
and the evidence on low- and zero-fluoroscopy workflows. Out of scope: operating instructions for X-ray systems,
regulatory dose limits, advice on any individual patient.

## Learning goals

1. Compute transmission and half-value layers from tabulated attenuation coefficients.
2. Explain why catheters, bone and air are visible and blood against tissue is not.
3. Relate dose, photon count and contrast-to-noise ratio.
4. Explain kerma-area product and why it does not depend on distance along the beam.
5. Estimate relative staff dose from time, distance, pulse rate and shielding.
6. Read a reference-level survey and a low-fluoroscopy study by its design.

## Equations (tests in `tests/test_m49_fluoro.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m49-beer | I = I0 exp(−∫μ ds); HVL = ln 2/μ | SymPy ODE and HVL; exact ellipsoid chords against ray marching; NIST values |
| eq-m49-contrast | C = 1 − exp(−Δμ t) ≈ Δμ t | SymPy series; blood/tissue, platinum/blood, negative contrast |
| eq-m49-cnr | CNR = C√N; N needed = (CNR*/C)² | Poisson simulation; √2 per doubling |
| eq-m49-kap | K ∝ 1/d², A ∝ d², K·A constant | SymPy; numeric along the beam |
| eq-m49-staff | H ∝ f_p q τ 2^(−n) / r² | Scaling by distance, shielding, pulse rate, time |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m49-d1 | approximate model | Projection of a chest phantom with a catheter; noise set by photons per pixel; contrast and CNR of the heart, an electrode or the spine |
| m49-d2 | approximate model | Relative staff dose against distance, with time, shielding and pulse rate |

## Code lab (`labs/python/m49_lab.ipynb`)

A attenuation and half-value layers (NIST); B projection image, exact and ray-marched; C quantum noise and the dose
needed for each structure; D pulse rate against catheter lag; E kerma-area product invariance and a staff-dose
budget; F reference levels from synthetic dose logs, pooled third quartile against 75th percentile of facility
medians. No downloads.

## Sources

PubMed (abstracts checked 2026-11-11): heidbuchel2014, greffier2026, samara2026, zormpas2023, debreceni2023,
chen2026sheath, borlich2025, kour2026. Data: NIST SRD 126 (Hubbell and Seltzer) tables for soft tissue, whole blood,
adipose tissue and cortical bone (ICRU-44) and platinum, read on 2026-11-11.

## Open points for the author

- A single photon energy (60 keV) keeps the physics visible; beam hardening and scatter are named, not modelled.
- Phantom sizes, photon counts, pulse rates, staff positions and dose-log parameters are illustrative.
- @heidbuchel2014 is a position paper; its operator risk figure is an estimate, reported as such.
