# m26 outline · Map quality and uncertainty: point density, annotation error, interpolation error

Stage 1 (outline) for module m26, written together with stages 2–6 (author request, 2026-11-15). Part IV: Python lab
only.

## Scope

Gaussian-process interpolation of activation times with a variance at every site; leave-one-out error in closed form
as a ground-truth-free quality score; the per-point error budget (annotation, reference, position); point density and
nearest-point distance; choosing the next point where the map is least sure. Out of scope: GP on mesh manifolds (cited,
not implemented), products' quality indicators, AI calibration (m46).

## Equations (tests in `tests/test_m26_uncertainty.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m26-gp | posterior mean and variance | SymPy single point; 95% coverage on prior draws |
| eq-m26-loo | closed-form leave-one-out residuals and variances | equals refitting |
| eq-m26-budget | σ_n² = σ_a² + σ_r² + (σ_x/c)² | Monte Carlo; sympy.stats; GP SD at a point |
| eq-m26-density | E[D] = 1/(2√ρ); median √(ln 2/(πρ)) | SymPy integral; Monte Carlo |
| eq-m26-adaptive | next point at the largest posterior variance | variance independent of values; greedy beats random |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m26-d1 | simulation | 1D GP mean and band from random noisy points |
| m26-d2 | exact | per-point budget and map SD against distance to the nearest point |

## Code lab (`labs/python/m26_lab.ipynb`)

A GP map and calibration; B leave-one-out and length scale; C error budget; D point density; E greedy sampling.

## Sources

- PubMed: coveney2020 (PMID 32448072).
- Web (no PubMed record): Rasmussen and Williams 2006 (DOI 10.7551/mitpress/3206.001.0001).
- Already in the bib: williams2018, williams2021, heil2023.
