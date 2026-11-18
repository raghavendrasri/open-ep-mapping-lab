# m20 outline · Geometry from catheter positions

Stage 1 (outline) for module m20, written together with stages 2–6 (author request, 2026-11-14). Part IV: Python lab
only.

## Scope

Catheter positions near the wall of an illustrative chamber; convex hulls and their blindness to concavities;
inflate–fill–shrink reconstruction (morphological closing with hole filling); Laplacian and Taubin smoothing; mesh
volume and surface distances. Out of scope: products' surface algorithms (described generically), marching cubes in
code (cited), registration to imaging (m21).

## Equations (tests in `tests/test_m20_geometry.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m20-hull | convex hull; error at a notch | circle hull area; notch error above 6 mm |
| eq-m20-closing | fill(P dilate B_r) erode B_r | disk radius R + r and back; reconstruction error; gaps when sparse |
| eq-m20-smoothing | umbrella step, n-gon factor, Taubin | SymPy trig identity; numeric factors |
| eq-m20-volume | divergence-theorem volume; Hausdorff distance | SymPy tetrahedron; icosphere within 1%; concentric circles |
| eq-m20-distance | mean surface distance | used in the reconstruction checks |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m20-d1 | simulation | Laplacian against Taubin smoothing of a noisy outline |
| m20-d2 | simulation | convex hull and inflate–fill–shrink reconstructions of a 2D chamber |

## Code lab (`labs/python/m20_lab.ipynb`)

A chamber and positions; B hull; C inflate–fill–shrink; D smoothing; E volume and distance.

## Sources

- Web (no PubMed record): Lorensen and Cline 1987 (DOI 10.1145/37402.37422); Taubin 1995 (DOI 10.1145/218380.218473).
- Already in the bib: gepstein1997, beinart2011resp, rottner2021.
- No PubMed source found that measures geometry from catheter positions against imaging in a way usable here.
