# m06 outline · Triangle meshes, Laplace–Beltrami operators and geodesics

Stage 1 (outline) for module m06, written together with stages 2–6 (author request, 2026-11-12). m06 supplies the
mesh operations that later modules use: m20 (geometry), m24 (interpolation), m25 (conduction velocity), m39 (graph
models), m41 (geodesic distance) and m42 (eikonal equation).

## Scope

Mesh counts and topology, per-face gradients and the conduction-velocity vector, the cotangent Laplacian and its
weights, the Laplace–Beltrami spectrum, and surface distance: edge paths, fast marching and the heat method. Out of
scope: surface reconstruction from points (m20), interpolation methods (m24) and velocity-estimation methods (m25).

## Equations (tests in `tests/test_m06_meshes.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m06-euler | $V - E + F = 2 - 2g$, $2E = 3F$ | icospheres of levels 0–3; a flat patch gives 1 |
| eq-m06-gradient | per-face gradient; $\mathbf v = \nabla T/\lvert\nabla T\rvert^2$ | SymPy: exact for linear data on any triangle; planar wave on a jittered patch |
| eq-m06-cotan | cotangent Laplacian | linear data on a jittered flat patch; $x^2 + y^2$ gives 4 on the regular lattice; sphere: median and integrated errors converge, worst error does not; sign of the edge weight |
| eq-m06-spectrum | $l(l+1)/R^2$, multiplicity $2l + 1$ | SymPy for an $l = 1$ harmonic; level-4 icosphere, $R = 2$ |
| eq-m06-geodesic | heat method | SymPy maximum of the lattice path ratio; Dijkstra on a 41 × 41 lattice equals the closed form; edge-path error does not converge on the sphere; heat-method error falls with each level |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m06-d1 | exact | Shortest edge path against the straight line on an equilateral lattice, for a chosen direction |
| m06-d2 | exact | Two triangles on a shared edge and its cotangent weight, for chosen opposite angles |

## Code lab (`labs/python/m06_lab.ipynb`, Octave copy `labs/octave/m06_lab.m` for parts A–E)

A meshes and counts; B gradients, a planar wave and timing noise; C the cotangent Laplacian and negative weights; D the
sphere's spectrum; E edge paths against the heat method.

## Sources

- Pinkall and Polthier 1993, the cotangent formula (DOI 10.1080/10586458.1993.10504266; found by web search, not in
  PubMed).
- Kimmel and Sethian 1998, fast marching on triangulated domains (PubMed, PMID 9671694).
- Crane, Weischedel and Wardetzky 2012, the heat method (arXiv 1204.6216, read through alphaXiv): the cotangent
  Laplacian, $t = h^2$.
- Already in `references.bib`: sethian1996, cantwell2015 (abstract rechecked on PubMed), williams2021 (abstract
  rechecked on PubMed).
