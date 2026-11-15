# m19 outline · Motion and drift

Stage 1 (outline) for module m19, written together with stages 2–6 (author request, 2026-11-14). Part III: Python lab
only.

## Scope

An asymmetric breathing model; respiratory (and, by analogy, cardiac) gating and its duty cycle; reference catheters
and surrogate regression; drift estimation from landmark revisits; averaging filters and their delay. Out of scope:
products' compensation algorithms (described generically), 3D motion fields, image-based motion models (m21).

## Equations (tests in `tests/test_m19_motion.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m19-breathing | -b cos^(2n)(pi t / T) | extremes, periodicity, time near exhale grows with n |
| eq-m19-gating | duty cycle | SymPy derivation; numeric sampling within 1e-4 |
| eq-m19-reference | SD of a difference; helps iff rho > sr/(2 sx) | SymPy threshold; Monte Carlo |
| eq-m19-surrogate | residual sx sqrt(1 - rho^2) | SymPy minimization; numeric fit |
| eq-m19-drift | slope and standard error | Monte Carlo of 4000 fits within 5% |
| eq-m19-average | boxcar gain sinc(fW), delay W/2 | SymPy integral; numeric removal and gain |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m19-d1 | exact | breathing trace with gated segments |
| m19-d2 | exact | residual motion against correlation, subtraction and regression |

## Code lab (`labs/python/m19_lab.ipynb`)

A breathing; B gating; C references and surrogates; D drift; E averaging.

## Sources

- PubMed: Lujan et al. 1999 (PMID 10360531), Danias et al. 1999 (PMID 10587147), Beinart et al. 2011 (PMID 21607726).
- Already in the bib: wittkampf1999 (landmark reproducibility).
