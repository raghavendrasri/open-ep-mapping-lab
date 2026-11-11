# m45 outline · Evidence and regulation of AI in EP (Part VII capstone)

Stage 1 (outline) for module m45, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md`.

## Scope

The evidence ladder for AI in EP and the reporting and appraisal tools for each rung; sample size
for diagnostic-accuracy studies; decision curves; monitoring after deployment; change control with
acceptance criteria fixed in advance. General device regulation stays in m36; validation basics
(metrics, leakage, calibration) stay in m35. Out of scope: regulatory submissions, legal advice.

## Learning goals

1. Place a study on the evidence ladder and name the matching checklist.
2. Compute the sample size for a target interval on sensitivity or specificity.
3. Judge clinical usefulness with net benefit.
4. Monitor a deployed model for drift and interpret an alarm.
5. Write acceptance criteria for a model update before seeing the results, and apply them.

## Equations (tests in `tests/test_m45_evidence.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m45-n-sens | n = z²Se(1−Se)/(d²π), and for Sp with 1−π | SymPy solves the half-width equation; numbers; simulated Wilson half-widths |
| eq-m45-net-benefit | TP/n − FP/n · pt/(1−pt) | Perfect model = prevalence; treat all; treat none |
| eq-m45-cusum | S_t = max(0, S_{t−1} + x_t − μ0 − k), alarm at S > h | Recursion by hand; run lengths grow with h; delay ≈ h/(δ−k) for large shifts |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m45-d1 | simulation | Silent drift: daily standardized scores, a step shift on day 61, CUSUM with sliders for shift, k, h (live, fixed seed) |
| m45-d2 | exact | Patients needed against prevalence for sensitivity and specificity |

## Code lab (`labs/python/m45_lab.ipynb`)

A evidence ladder of Part VII studies; B sample size checked by simulation; C report card
(TRIPOD+AI-style numbers) and decision curve for the m37 RR detector on synthetic ECGs with 5% label
noise; D deployment with a population that has frequent early beats, CUSUM on daily mean score;
E change control: v1, retrained v2, re-tuned v2, v3 with a new input (outside the plan) against
pre-specified criteria; F Challenge 2017 → PTB-XL external validation and monitoring (download).

## Sources

PubMed: koh2026, wang2026, moons2025, vasey2022, cruzrivera2020, liu2020, buderer1996, vickers2006,
wu2021fda (Stanford; no abstract, cited by title only), sluha2025 (no abstract, cited by title
only); already in `references.bib`: collins2024, svennberg2025 (abstract checked for the checklist
figures), yao2021, noseworthy2022, adedinsewo2024, he2023, deisenhofer2025, dayan2021,
roth2022nvflare, fdapccp2024. Publisher and index pages found by web search: page1954 (Biometrika
41(1–2):100–115) and the FDA AI-enabled device page (fdaailist, checked 2026-11-11).

## Open points for the author

- Part F has not run locally (no PhysioNet access); exercised with stand-in recordings.
- The lab's acceptance criteria, label-noise rate and CUSUM settings are illustrative.
- While building m45 a bug was found in m37's lab (calibration intercept printed as slope); fixed and
  recorded as E1 in `errata.json` and on the errata page.
