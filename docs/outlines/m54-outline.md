# m54 outline · Nuclear imaging in EP

Stage 1 (outline) for module m54, written together with stages 2–6 (author request, 2026-11-11: finish the
remaining Part VIII modules, one pull request each). Plan source: `docs/outlines/part8-overview.md`.

## Scope

What an engineer needs to read PET and SPECT numbers in EP: decay and timing, the standardized uptake value, partial
volume in the thin heart wall and its correction, and how test-retest noise interacts with a threshold on change. Then
the published uses: FDG PET in cardiac sarcoidosis with VT, and nuclear imaging for device infection. Out of scope:
detector physics beyond a sentence, tracer kinetics, reconstruction algorithms, patient preparation protocols, advice
on any patient.

## Learning goals

1. Apply radioactive decay to timing and decay correction.
2. Compute an SUV and name its error sources.
3. Derive the recovery coefficients of a blurred wall and correct a measurement with them.
4. Compute how often noise flips a 25% response rule.
5. Read the sarcoidosis and device-infection evidence by design.

## Equations (tests in `tests/test_m54_nuclear.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m54-decay | A = A0 e^(−λt), λ = ln2/T½; clock error bias 2^(Δt/T½) − 1 | SymPy half-lives; 6.5% for 10 min |
| eq-m54-suv | SUV = C/(A′/W) | Uniform distribution gives 1; residual activity |
| eq-m54-recovery | RC_max = erf(w/(2√2σ)); RC_mean = erf(b) − (1 − e^(−b²))/(b√π) | SymPy integral; numeric profiles; phantom correction within 10% |
| eq-m54-change | ln R_m ~ N(ln R, 2 ln(1 + c²)); P(called response) | Monte Carlo; 0.5 at R = 0.75 |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m54-d1 | exact | True and blurred wall profiles; recovery of max and mean against thickness |
| m54-d2 | exact | Fluorine-18 decay; uptake time; SUV bias from a clock error |

## Code lab (`labs/python/m54_lab.ipynb`)

A decay and timing; B SUV and its inputs; C partial volume; D an inflamed region on a synthetic ventricle with
partial-volume correction; E serial scans and a 25% response rule; F the evidence by design. No downloads.

## Sources

TUNL Nuclear Data Evaluation (fluorine-18 half-life, read through web search on 2026-11-11). PubMed (abstracts, and
the full text of kinahan2010, read 2026-11-11): kinahan2010, soret2007, muser2016, muser2018, bourque2024; birnie2014
by title only (no abstract).

## Open points for the author

- Wall thickness, uptake values, lesion shapes, doses and weights are illustrative; no source for normal ventricular
  wall thickness was read in this session.
- The ~10% test-retest figure comes from oncology studies; cardiac values may differ, and the page says so.
- The consensus on device infection is summarized from its abstract only.
