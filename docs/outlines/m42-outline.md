# m42 outline · Physics-informed machine learning

Stage 1 (outline) for module m42, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md`.

## Scope

Physics-informed fitting of activation maps: the eikonal residual, the combined loss, fitting by
Levenberg–Marquardt on a radial-basis representation, what physics adds and what a wrong physical
assumption hides, ensemble uncertainty, and surrogates for twin calibration with their range of
validity. Out of scope: mapping workflow advice, vendor tools, clinical use.

## Learning goals

1. Write a physics-informed loss for the eikonal equation and explain the weight λ.
2. Fit it without a deep-learning library and know why the problem is nonlinear.
3. Show where the physics term helps (moderate data) and where it misleads (wrong physics).
4. Estimate uncertainty with an ensemble and check its coverage.
5. Build a surrogate shaped by physics and keep it inside its training range.

## Equations (tests in `tests/test_m42_pinn.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m42-eikonal | r = s|∇T| − 1 | SymPy point source; plane wave |
| eq-m42-loss | Data misfit + λ × mean residual² | Loss equals |r|²; λ = 0 gives ridge least squares |
| eq-m42-rbf | Gaussian RBF map and analytic gradient | Finite differences; constant column |
| eq-m42-lm | Levenberg–Marquardt step | Jacobian vs finite differences in three slowness modes; loss history non-increasing |
| eq-m42-ensemble | Ensemble mean and sample SD | numpy; zero spread for identical members |
| eq-m42-scaling | T(k s) = k T(s) | Eikonal solver on a heterogeneous mesh; SymPy for a path sum |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m42-d1 | simulation | Data-only and physics-informed fits for 12, 24, 48 points and λ = 0, 1, 10, 100 (precomputed by `tools/make_m42_d1.py`, 73 kB) |
| m42-d2 | simulation | One-dimensional randomized-prior ensemble, live in the browser |

## Code lab (`labs/python/m42_lab.ipynb`)

A RBF maps and the eikonal residual; B homogeneous tissue, data-only vs physics (six random draws);
C a slow disc (1.0 and 0.6 m/s, heil2023), map error vs speed bias; D ensemble uncertainty and its
coverage; E slowness-based surrogate of the eikonal model, calibration and out-of-range error;
F optional PyTorch PINN.

## Sources

raissi2017pinn (arXiv), raissi2020 (PubMed; an author affiliated with NVIDIA), sahlicostabal2020
(publisher page and PDF; Stanford co-author, affiliation checked), herreromartin2022 and magana2025
(PubMed), physicsnemo (PyPI metadata: version 2.2.2, Apache-2.0, released 2026-09-11), corral2020
and gillette2021 (already in `references.bib`). Figure descriptions were checked against the PMC full
text of herreromartin2022 and the publisher page of sahlicostabal2020.

## Open points for the author

- No real data: open clinical activation maps with independent ground truth were not found.
- The PhysicsNeMo citation is a software record (PyPI and GitHub), not a paper.
- λ, basis widths, speeds and noise levels are illustrative.
