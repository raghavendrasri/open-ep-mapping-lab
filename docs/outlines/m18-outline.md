# m18 outline · Hybrid and dielectric localization concepts

Stage 1 (outline) for module m18, written together with stages 2–6 (author request, 2026-11-14). Part III: Python lab
only.

## Scope

Correcting impedance coordinates with magnetic reference points (affine and radial-basis corrections), interpolation
error against coverage, inverse-variance fusion, and complex, frequency-dependent tissue conductivity as the idea behind
dielectric approaches. Out of scope: products' algorithms (not published; described generically), tissue
classification models, cryoballoon occlusion assessment.

## Equations (tests in `tests/test_m18_hybrid.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m18-affine | least-squares affine map | exact recovery; halves the distorted error |
| eq-m18-rbf | Gaussian RBF plus affine, block system | exact interpolation; beats affine with enough points; affine target gives zero weights |
| eq-m18-coverage | error against gap; linear bound h^2 f''/8 | rank correlation; bound attained for x^2 |
| eq-m18-fusion | inverse-variance weights | SymPy minimization; Monte Carlo |
| eq-m18-dielectric | complex conductivity, Debye relaxation, phase | SymPy phase; numeric; tissues separate near relaxation |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m18-d1 | simulation | a distorted grid corrected from magnetic reference points |
| m18-d2 | approximate model | impedance phase against frequency for two illustrative tissues |

## Code lab (`labs/python/m18_lab.ipynb`)

A distorted space; B affine and smooth corrections; C coverage; D fusion; E frequency-dependent impedance.

## Sources

- PubMed: Abeln et al. 2021 (PMID 33629788), Rottner et al. 2021 (PMID 34289168), Amorós-Figueras et al. 2018 (PMID
  29197656), Gabriel et al. 1996 (PMID 8938026).
- No peer-reviewed description of a commercial hybrid correction algorithm was found; the correction is generic.
