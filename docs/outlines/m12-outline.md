# m12 outline · The surface ECG and the forward problem

Stage 1 (outline) for module m12, written together with stages 2–6 (author request, 2026-11-14). Part II: Python lab
only.

## Scope

A dipole in a homogeneous, insulated spherical torso (centric closed form and the Legendre series for an off-center
source); lead vectors; Einthoven's law, the Wilson central terminal and the augmented leads; the frontal axis; a
heart vector from an activation front; the distortion of lead vectors by an off-center heart. Out of scope: ECG
interpretation criteria, precordial lead placement details (cited to the standards statement), inhomogeneous torso
models (m32) and real-data analysis (m37 uses PTB-XL; PhysioNet was not reachable from the build environment to test
a real-data part here).

## Equations (tests in `tests/test_m12_ecg.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m12-sphere | centric dipole, interior and surface | SymPy: harmonic, zero normal derivative, factor 3 |
| eq-m12-series | off-center source series | SymPy per-term boundary condition and surface value; near-centric dipole equals the closed form |
| eq-m12-lead | V = L·p, centric L | closed form; superposition for an eccentric dipole; lead I turns more than 10° off center |
| eq-m12-einthoven | I + III = II | SymPy |
| eq-m12-augmented | WCT, aVR, aVL, aVF | SymPy identities; WCT zero for a centric dipole, nonzero off center |
| eq-m12-axis | atan2(2 aVF/√3, I) | exact for random centric dipoles; more than 5° off with the heart 0.3 R to the left |
| eq-m12-forward | V(t) = L·p(t) | front across a ball: duration 2a/CV; axis from areas equals the front angle |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m12-d1 | exact | heart vector in the frontal plane and the six limb-lead voltages |
| m12-d2 | exact | limb-lead vectors for an off-center heart, against the equilateral triangle |

## Code lab (`labs/python/m12_lab.ipynb`)

A sphere and series; B lead vectors and identities; C axis and noise; D a QRS from a front; E an off-center heart.

## Sources

- PubMed: Burger and Van Milaan 1947 (PMID 18610067, no abstract: cited for the heart-vector and lead concept in its
  title), Frank 1956 (PMID 13356432, no abstract: cited for the orthogonal lead system in its title), Kligfield et al.
  2007 (PMID 17322457).
- Already in the bib: rudy1979 (eccentric spheres), wagner2020 (PTB-XL).
