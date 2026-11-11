# m40 outline · AI for cardiac imaging and substrate

Stage 1 (outline) for module m40, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md`.

## Scope

How segmentations of the atria (and risk models built on images) are judged: overlap and surface
metrics, what a boundary error costs for structures of different shape, the concordance index for
survival models, and how image-derived substrate has fared in trials. Out of scope:
ablation-strategy advice, imaging protocols and vendor operating instructions.

## Learning goals

1. Compute Dice, Jaccard, Hausdorff distance, HD95, ASSD and normalized surface Dice, and say when
   each misleads.
2. Predict the Dice cost of a boundary error from surface-to-volume ratio.
3. Explain what a segmentation error does to a shell used with mapping points.
4. Read the concordance index and know what it does not measure.
5. Tell an association study from a randomized test of a strategy built on imaging.

## Equations (tests in `tests/test_m40_imaging.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m40-jaccard | Dice = 2J/(1 + J) | Random masks; SymPy inverse |
| eq-m40-hausdorff | Hausdorff distance and HD95 | Shifted boxes with anisotropic voxels; island; concentric spheres |
| eq-m40-assd | Average symmetric surface distance | Concentric spheres; island |
| eq-m40-nsd | Normalized surface Dice at tolerance τ | Concentric spheres above and below τ |
| eq-m40-offset | First-order Dice after a uniform offset | SymPy slopes for sphere, cube and cylinder |
| eq-m40-sphere | Exact Dice of concentric spheres | Voxel spheres at 0.25 mm |
| eq-m40-slab | Exact Dice of a shifted wall | Voxel walls, integer shifts |
| eq-m40-cindex | Harrell's concordance index | Brute force over pairs with ties; limits |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m40-d1 | exact | Dice, HD, ASSD and NSD for a boundary error and a stray island (2-D, closed forms and quadrature) |
| m40-d2 | exact | Dice versus boundary error for a sphere, a cylinder and a wall (Beinart 2011 thickness) |

The overview planned a "mask to shell" simulation for m40-d2; it became an exact comparison of
structure sizes, and the mask-to-shell question moved to lab part D.

## Code lab (`labs/python/m40_lab.ipynb`)

A metrics with known answers; B synthetic atria; C threshold against a voxel classifier; D distance
from points on the true wall to the predicted shell; E Medical Segmentation Decathlon Task02_Heart
(20 labelled MRI volumes, CC BY-SA 4.0, CI download): shape, offsets, islands, tight against loose
box; F optional 2-D U-Net (MONAI if installed).

## Sources (looked up on PubMed or arXiv for this module)

xiong2020, antonelli2022 and antonelli2021msd (arXiv, per-task table), tobongomez2015,
isensee2021, ronneberger2015 (arXiv), cardoso2022monai and diazpinto2022monailabel (arXiv; NVIDIA
and King's College London), maierhein2024, reinke2024, beinart2011, popescu2022, razeghi2023
(Stanford), ouyang2020 and he2023 (Stanford), zou2026 (vendor module, described generically),
marrouche2014, marrouche2022, akoum2024, harrell1982. Figure descriptions in "Literature figures"
were checked against the PMC full texts of antonelli2022, popescu2022 and he2023.

## Open points for the author

- Part E has not yet run on the real volumes (the archive is not reachable from the build
  workspace); its code path was exercised with stand-in NIfTI files. Pin the archive's SHA-256 in
  `data/registry.json` after CI prints it.
- New lab dependency: nibabel (reads NIfTI). The PyTorch CI job now also installs MONAI.
- Synthetic shapes, intensities and the 25-mm sphere and 5-mm cylinder defaults are illustrative.
