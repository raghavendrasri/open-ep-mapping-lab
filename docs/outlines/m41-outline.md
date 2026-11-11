# m41 outline · Locating arrhythmia origins from the ECG

Stage 1 (outline) for module m41, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md`.

## Scope

Learned localization of activation origins from the surface ECG: why QRS features carry the
origin, population and patient-specific regression, error along the heart surface, pace-map
similarity, and active pace-mapping with a Gaussian process and expected improvement. Out of scope:
ablation strategy, vendor operating instructions, clinical ECG criteria.

## Learning goals

1. Derive the QRS integral of a lead as a solid-angle-weighted sum of activation times in a
   double-layer model.
2. Fit population and patient-specific localization models and say what each needs.
3. Measure localization error along the surface.
4. Derive the Gaussian-process posterior and expected improvement, and use them to choose the next
   pacing site.
5. Read localization studies by their reference, split, metric and cohort.

## Equations (tests in `tests/test_m41_origins.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m41-integral | QRS integral = c Σ Ω (T − τ)+; = −c Σ Ω τ after full activation | Closed-surface solid angles; numeric integration; T term cancels |
| eq-m41-linear | Least-squares localization | Recovery of a known map; exact interpolation with p + 1 sites; lstsq |
| eq-m41-geodesic | Great-circle distance and chord | SymPy series and limits; icosphere edge paths 0–21% longer |
| eq-m41-corr | Mean Pearson correlation over leads | Identity, negation, scale and offset invariance |
| eq-m41-gp | GP posterior mean and variance | Dense formula; scikit-learn with fixed kernel; interpolation limit |
| eq-m41-ei | Expected improvement | Monte Carlo; SymPy integral; σ = 0 limit |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m41-d1 | simulation | Active pace-mapping on a 60-mm patch: GP estimate, EI map, EI against random (illustrative landscape with a decoy peak) |
| m41-d2 | exact | One-dimensional GP and expected improvement with four paced points |

The overview planned "regression versus nearest neighbour" for m41-d2; it became the
one-dimensional GP and EI demo, and regression comparisons moved to lab part B.

## Code lab (`labs/python/m41_lab.ipynb`)

A double-layer forward model on an ellipsoidal ventricle with nine electrodes and twelve leads;
B population regression (linear, support-vector, random forest; split by patient or by site);
C patient-specific regression from three leads, random against sequential pacing; D active
pace-mapping, EI against random; E training hearts that differ from test hearts; F optional PyTorch.
Synthetic only (see open points).

## Sources (looked up on PubMed or arXiv for this module)

zhou2018, zhou2018ecgi, zhou2020, zhou2020ct, zhou2021jaha, missel2020, meisenzahl2024, doste2022,
botis2026, yang2024, antoun2026, zheng2020otva (PubMed); frazier2018 (arXiv). Figure descriptions in
"Literature figures" were checked against the PMC full texts of zhou2021jaha and doste2022.

## Open points for the author

- **No real-data part.** No open data set with pacing-site coordinates could be verified. The open
  outflow-tract database of Zheng et al. 2020 (334 patients, figshare collection
  10.6084/m9.figshare.c.4668086.v2) labels right or left outflow-tract origin; figshare was not
  reachable from the build workspace, so its licence and file layout are unverified. A
  classification part on it can be added once they are checked.
- No Stanford or NVIDIA work specific to ECG origin localization was found in the searches for this
  module; the active pace-mapping loop is linked to the agentic-AI module (m44) only in concept.
- The forward model, electrode positions, speeds and noise levels are illustrative.
