# m25 outline · Conduction velocity estimation: triangulation, surface fitting, omnipolar methods

Stage 1 (outline) for module m25, written together with stages 2–6 (author request, 2026-11-15). Part IV: Python lab
only.

## Scope

Velocity from the activation-time gradient and the bias noise gives it; two-point and triangle estimators and their
error propagation; local least-squares plane fits and the noise–bias trade-off; potential-based (omnipolar) velocity
from a clique and its finite-spacing bias; a synthetic velocity map with a slow region. Out of scope: products'
velocity algorithms (described generically), restitution (m09, m10), uncertainty maps (m26).

## Equations (tests in `tests/test_m25_velocity.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m25-gradient | v = ∇T/abs(∇T)²; E abs(ĝ)² = abs(g)² + 2σ_g² | numeric; Monte Carlo; sympy.stats |
| eq-m25-pair | relative speed SD √2 σ c / h | SymPy propagation; Monte Carlo |
| eq-m25-triangle | E g = ΔT; covariance σ² E⁻¹ S E⁻ᵀ | exact recovery; Monte Carlo; equilateral isotropic; sliver |
| eq-m25-planefit | covariance σ² (Xcᵀ Xc)⁻¹ ≈ (2σ/(R√n))² | Monte Carlo; SymPy disk moment |
| eq-m25-omnipolar | v = −φ_t ∇φ/abs(∇φ)²; cross clique ratio 1 + (d/2)²/a² | SymPy for any U; SymPy ratio; numeric |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m25-d1 | exact | relative speed error against spacing for two points, triangles and plane fits |
| m25-d2 | exact | clique speed estimate against spacing, height and angle |

## Code lab (`labs/python/m25_lab.ipynb`)

A gradient noise and speed bias; B pairs and triangles; C plane-fit radius; D clique velocity; E a velocity map with a
slow region.

## Sources

- PubMed: bayly1998 (PMID 9581054), magtibay2019 (PMID 31400876), vicera2020 (PMID 32227530).
- Already in the bib: cantwell2015, heil2023, masse2016, deno2017, riccio2021.
