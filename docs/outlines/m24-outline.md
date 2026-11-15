# m24 outline · Interpolation, activation maps and isochrones

Stage 1 (outline) for module m24, written together with stages 2–6 (author request, 2026-11-15). Part IV: Python lab
only.

## Scope

How activation maps fill in between mapped points: linear (barycentric) interpolation and its error, inverse-distance
weighting and its flat spots, harmonic interpolation on a mesh and its free-boundary behavior, isochrone extraction
and spacing, interpolation across a line of block, and coverage with a fill threshold. Out of scope: conduction
velocity estimators (m25), uncertainty and point-density design (m26), products' interpolation algorithms (described
generically).

## Equations (tests in `tests/test_m24_interpolation.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m24-linear | barycentric interpolation; error ≤ h² max abs T'' / 8 | SymPy; exact for linear; focal line within the bound |
| eq-m24-idw | IDW; bounded; zero gradient at points for p > 1 | numeric bounds and gradients; SymPy limit |
| eq-m24-harmonic | L T = 0 between known vertices | linear reproduced with fixed boundary; maximum principle; free edge |
| eq-m24-isochrone | edge crossing fraction; spacing c Δτ | plane wave on a jittered mesh |
| eq-m24-block | apparent speed h / ΔT; coverage 1 − exp(−ρπr²) | numeric ramp; Monte Carlo coverage |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m24-d1 | exact | linear and IDW interpolation along a line with a block |
| m24-d2 | simulation | true and IDW isochrones from random points |

## Code lab (`labs/python/m24_lab.ipynb`)

A linear interpolation error; B IDW gradients; C harmonic interpolation and free edges; D isochrones; E block and
coverage.

## Sources

- PubMed: williams2018 (PMID 28379525), aziz2019 (PMID 31533463).
- Web (no PubMed record): Shepard 1968 (DOI 10.1145/800186.810616).
- Already in the bib: marchlinski1998, koawing2015, heil2023, cantwell2015, williams2021.
