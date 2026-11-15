# m17 outline · Impedance (current-based) localization

Stage 1 (outline) for module m17, written together with stages 2–6 (author request, 2026-11-14). Part III: Python lab
only.

## Scope

The potential of a skin-patch pair; the nonlinearity along its axis; a uniform-field (linear) map and its distortion;
field scaling from electrodes of known spacing as a local metric; stretching of apparent distance across conductivity
boundaries; precision from voltage noise. Out of scope: products' scaling algorithms (described generically), bounded
torso models, respiration and drift (m19), hybrid systems (m18).

## Equations (tests in `tests/test_m17_impedance.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m17-pair | patch-pair potential | SymPy Laplacian and oddness; numeric |
| eq-m17-axis | axis potential, central field, stretch | SymPy identity, derivative, exact stretch and series |
| eq-m17-linear | phi / E0 map | exact near the center, error far out |
| eq-m17-metric | l^2 = dphi^T M dphi | SymPy identity; least-squares fit recovers (J J^T)^-1; new pair distance |
| eq-m17-interface | field ratio at an interface | SymPy; 1D layered model |
| eq-m17-precision | position noise | numeric scaling with d^2 |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m17-d1 | exact | reported against true position along a patch pair's axis |
| m17-d2 | exact | a grid mapped by the uniform-field assumption |

## Code lab (`labs/python/m17_lab.ipynb`)

A pair and nonlinearity; B linear map in 3D; C field scaling; D conductivity layers; E precision.

## Sources

- PubMed: Wittkampf et al. 1999, Circulation (PMID 10077514); Wittkampf et al. 1999, J Electrocardiol (PMID 10688296).
