# m21 outline · Image integration: CT/MRI segmentation, landmark and ICP registration

Stage 1 (outline) for module m21, written together with stages 2–6 (author request, 2026-11-14). Part IV: Python lab
only.

## Scope

Threshold segmentation of a contrast image (Otsu), overlap measures, landmark registration by least squares (rigid and
similarity), surface registration by iterative closest point, and the motions a surface fit cannot constrain. Out of
scope: learned segmentation (m40), imaging physics (m51, m52), products' registration algorithms (described
generically), the closed-form target-error formula (m55).

## Equations (tests in `tests/test_m21_registration.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m21-threshold | variance decomposition; Otsu's threshold | SymPy decomposition; Otsu equals brute force |
| eq-m21-dice | Dice, Jaccard, D = 2J/(1 + J); Gaussian expected Dice | identity; closed form against simulation |
| eq-m21-procrustes | SVD least squares with sign fix; scale; translation | recovers R, t and scale 1.1; no reflection |
| eq-m21-icp | closest point plus least squares | monotone MSE; 10° converges; 170° wrong minimum |
| eq-m21-sliding | point-to-plane linearization; null space | sphere has 3 zero eigenvalues, ellipsoid none |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m21-d1 | simulation | 2D ICP from an adjustable starting rotation |
| m21-d2 | exact | Otsu threshold and expected Dice for two Gaussian classes |

## Code lab (`labs/python/m21_lab.ipynb`)

A threshold segmentation; B Dice and Jaccard; C landmark registration (FRE, TRE, similarity); D ICP from several
starts; E sliding on a sphere.

## Sources

- Web (no PubMed record): Besl and McKay 1992 (DOI 10.1109/34.121791); Umeyama 1991 (DOI 10.1109/34.88573); Otsu 1979
  (DOI 10.1109/TSMC.1979.4310076); Dice 1945 (DOI 10.2307/1932409).
- Already in the bib: kistler2006, dong2006, fitzpatrick1998.
