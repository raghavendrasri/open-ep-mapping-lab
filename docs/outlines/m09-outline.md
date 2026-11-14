# m09 outline · Propagation: cable theory, monodomain and bidomain, anisotropy

Stage 1 (outline) for module m09, written together with stages 2–6 (author request, 2026-11-14). Part II: Python lab
only.

## Scope

The passive cable; bidomain equations and their reduction to the monodomain model; velocity scaling with
conductivity; anisotropic spread and apparent velocity along a mapping line; curvature and source–sink failure.
Out of scope: discrete gap-junction models, fiber rotation through the wall, defibrillation, velocity estimation from
maps (m25).

## Equations (tests in `tests/test_m09_propagation.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m09-cable | passive cable, $\lambda$, $\tau_m$ | SymPy steady solution; second-order finite differences |
| eq-m09-bidomain | two-potential equations | SymPy 1D reduction (no net axial current) |
| eq-m09-monodomain | harmonic combination | same reduction; numeric value |
| eq-m09-cv | $\text{CV} \propto \sqrt D$; ratio | Mitchell–Schaeffer cable at $D$ and $4D$; Clerc's ratios give 2.82 against 3.0 measured |
| eq-m09-anisotropy | elliptical activation; ray speed | ray speed lies on the unit isochrone; 2D sheet ratio tends to 3 |
| eq-m09-curvature | $c \approx c_0 - D\kappa$ | radial simulation within 2% for r ≥ 3 mm |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m09-d1 | simulation | 1D cable: velocity against $D$ and grid spacing |
| m09-d2 | exact | elliptical isochrones and apparent velocity along a line, for fiber angle and velocity ratio |

## Code lab (`labs/python/m09_lab.ipynb`)

A passive cable; B velocity scaling and grid error; C bidomain to monodomain with Clerc's ratios; D anisotropic sheet;
E curvature and stimulus failure.

## Sources

- PubMed: Clerc 1976 (PMID 1255523, already in the bib, abstract rechecked), Roberts et al. 1979 (PMID 428066), Potse et
  al. 2006 (PMID 17153199), Kléber and Rudy 2004 (PMID 15044680), Fast and Kléber 1997 (PMID 9074688).
- Already in the bib: heil2023 (velocities, as used in m03 and m33), mitchell2003, nietoramos2023 (m08).
