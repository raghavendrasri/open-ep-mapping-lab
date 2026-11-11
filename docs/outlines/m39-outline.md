# m39 outline · AI on electrograms and maps

Stage 1 (outline) for module m39, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md`.

## Scope

Learning from intracardiac electrograms and from whole maps: graph convolution on a mapping mesh,
how to judge a predicted region (Dice, centroid distance), rare targets and loss choice,
clustering without labels, and how splits by window or by patient change the result. The
clinical correlate covers the published randomized trials of electrogram-guided software
(TAILORED-AF) and of an image-guided strategy (RESTART) as their papers report them. Out of scope:
ablation-strategy advice and vendor operating instructions.

## Learning goals

1. Write one graph-convolution layer on a mesh and say what repeated layers do to a map.
2. Judge a predicted region by overlap and by distance, and know when each misleads.
3. Explain why plain cross-entropy fails on rare targets and what weighting and the focal loss
   change.
4. Spot leakage from splitting windows of the same recording across training and test sets.
5. Read trials of AI-guided mapping by their endpoints, comparators and blinding.

## Equations (tests in `tests/test_m39_graphs.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m39-gcn | One graph-convolution layer with the normalized adjacency | Entries and symmetry; layer matches its definition; finite-difference gradients |
| eq-m39-smoothing | Fixed point of the normalized adjacency; repeated layers smooth | Eigenvector check; spectrum in (−1, 1] |
| eq-m39-dice | Area-weighted Dice coefficient | Closed forms on small examples, with and without area weights |
| eq-m39-lens | Dice of two discs from the lens area | Monte Carlo inside the smaller disc |
| eq-m39-focal | Focal loss and its gradient | γ = 0 gives α-weighted cross-entropy; finite differences; SymPy limit for easy examples |
| eq-m39-gmm | Gaussian mixture responsibilities and EM | Responsibilities sum to one; EM recovers a known mixture; agrees with scikit-learn (tol 1e-10) |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m39-d1 | exact | Graph smoothing on a 31 × 31 mesh: layers, region radius and noise |
| m39-d2 | exact | Dice of two discs against centroid distance |

## Code lab (`labs/python/m39_lab.ipynb`)

A normalized adjacency on a mesh; B synthetic eikonal cases with slow discs (conduction speeds
from heil2023); C per-point logistic regression against a NumPy graph network; D rare targets:
cross-entropy, weighted cross-entropy, focal loss; E Intracardiac AF Database: catheter position
from CS12 features, window-wise split against leave-one-patient-out (CI download); F optional
PyTorch graph network.

## Sources (looked up on PubMed or arXiv for this module)

seitz2017, deisenhofer2025, deisenhofer2025women, deisenhofer2025at, hummel2026, guler2026,
saluja2024, huttelmaier2026, alhusseini2020 (Stanford), zolotarev2020, rodrigo2022 (Stanford),
tang2022 (Stanford), ganesan2025 (Stanford), kipf2017, lin2017focal; iafdb and goldberger2000
(PhysioNet). Figure descriptions in "Literature figures" were checked against the PMC full texts
of alhusseini2020, zolotarev2020 and deisenhofer2025.

## Open points for the author

- Part E has not yet run against the real records (PhysioNet is not reachable from the build
  workspace); CI downloads them. The window length, filter band and frequency search range are
  illustrative analysis choices.
- Region sizes, timing noise and the voltage-like feature of the synthetic cases are illustrative.
- Trial results are reported as the papers report them; the clinical correlate stays pending
  clinical review.
