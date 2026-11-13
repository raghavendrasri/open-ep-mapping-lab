# m02 outline · Volume conduction and Poisson's equation

Stage 1 (outline) for module m02, written together with stages 2–6 (author request, 2026-11-12). Builds on m01
(sources) and feeds m03 (electrograms), m07 (inverse problems), m12 and m32 (forward and inverse ECG).

## Scope

Poisson's equation from current conservation; interface conditions and the method of images; flux-conserving finite
differences and their accuracy; reciprocity and lead fields. Out of scope: anisotropic bidomain tissue (m09), the
torso forward problem in detail (m12), inverse problems (m07).

## Learning goals

1. Derive Poisson's equation and state the quasi-static assumption.
2. Solve a flat two-media problem with images and reason about insulating and conducting boundaries.
3. Build and verify a finite-difference solver, including where interfaces must sit.
4. Use reciprocity to compute and interpret an electrode's lead field.

## Equations (tests in `tests/test_m02_volume.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m02-poisson | $\nabla\cdot(\sigma\nabla\phi) = -I_v$ | SymPy: exact Gaussian-source potential satisfies it; total current |
| eq-m02-interface | continuity of $\phi$ and $\sigma\,\partial_n\phi$ | SymPy on the image solution; numeric one-sided differences |
| eq-m02-images | $k$, $\phi_1$, $\phi_2$ | SymPy: Laplace on each side, both interface conditions, insulator doubles |
| eq-m02-fd | harmonic-mean 5-point scheme | observed order 2 (homogeneous; interface on faces), 1 (interface on nodes) |
| eq-m02-reciprocity | $V = \mathbf p\cdot\nabla\psi$ | direct image solution vs reciprocity across the interface; m01 dipole |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m02-d1 | exact | Point source below an interface: potential along the vertical and 1 mm above the interface |
| m02-d2 | simulation | SOR finite-difference solve of the two-media problem, with its error against images |

## Code lab (`labs/python/m02_lab.ipynb`, Octave copy `labs/octave/m02_lab.m` for parts A–D)

A Gaussian source and solver convergence; B images and continuity; C two media on a grid; D reciprocity and lead
fields. Offline, a few seconds each.

## Sources

PubMed (2026-11-12): plonsey1967, brody1956, rudy1979 (no abstracts; cited for their subject only). Already in
`references.bib`: plonsey2007.

## Open points for the author

- No blood or tissue conductivity values: none could be verified from PubMed abstracts, so ratios are free parameters.
  A reviewer may want a cited blood-to-myocardium ratio for the demo default.
- The Octave copy uses Octave-only `merge` and chained indexing, so it does not run unchanged in MATLAB (noted in its
  header).
