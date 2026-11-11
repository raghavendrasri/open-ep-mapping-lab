# m37 outline · AI on the surface ECG

Stage 1 (outline) for module m37, written together with stages 2–6 at the author's request
(2026-11-11: all stages per module, one pull request per module). Plan source:
`docs/outlines/part7-overview.md`.

## Scope

How a deep network turns ECG samples into class probabilities, what one output can see, which
rhythm features a model can use, why accuracy on a test set is only the first rung of evidence,
and what happens when a model moves to a new device or site. Builds on m04 (filters), m12
(surface ECG) and m35 (validation).

Out of scope: screening or treatment advice; vendor products.

## Learning goals

1. Derive the softmax cross-entropy gradient and read a convolution layer as a learned FIR filter.
2. Compute a network's receptive field in samples, seconds and beats.
3. Build rhythm features from RR intervals and a logistic model on them.
4. Place a study on the evidence ladder (retrospective, prospective, randomized).
5. Compute screening yield and correct probabilities for a new prevalence.
6. Design an external validation and name the shifts it tests.

## Equations (each tested in `tests/test_m37_aiecg.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m37-softmax | Softmax | Sums to one, shift invariance, no overflow |
| eq-m37-ce-grad | Cross-entropy gradient $p - y$ | SymPy and finite differences |
| eq-m37-logistic | Logistic regression | Two-class softmax; equals scikit-learn's probabilities |
| eq-m37-conv | Convolution layer (cross-correlation with stride) | Against `numpy.correlate` |
| eq-m37-kernel-response | Kernel frequency response | Gain on sinusoids; closed form for a difference kernel |
| eq-m37-receptive-field | Receptive field of a conv stack | Input-perturbation count; SymPy for equal layers |
| eq-m37-rr | RR features (mean, CV, nRMSSD) | Regular and alternating closed forms |
| eq-m37-yield | Screening yield, flags per case = 1/PPV | Against eq-m35-ppv |
| eq-m37-prior-shift | Prior-shift correction [saerens2002] | Recovers the Bayes posterior for binormal scores |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m37-d1 | exact | Receptive field over a synthetic ECG; beats per output |
| m37-d2 | exact | Screening yield versus prevalence; prior-shift curve |

Synthetic ECG: approximate model, Gaussian waves per beat after [mcsharry2003]; values illustrative.
JS math checked against Python in `tests/test_m37_demos.py`.

## Code lab (`labs/python/m37_lab.ipynb`)

A gradient and filters; B receptive field; C hidden patient-level signal and record-wise versus
patient-wise splits; D RR model versus NumPy CNN, inversion and ectopy, augmentation; E Challenge
2017 to PTB-XL external test with prevalence correction (CI downloads; skipped offline); F optional
PyTorch version (separate CI job).

## Sources (all looked up on PubMed or arXiv for this module)

hannun2019, ribeiro2020, attia2019, noseworthy2022, yao2021, adedinsewo2024, wagner2020,
clifford2017, kaur2023, kligfield2007, mcsharry2003, bollmann2006, pan1985, saerens2002,
svennberg2025, dayan2021, feeny2020, roth2022nvflare (arXiv), collins2024 (existing). Data sets:
ptbxl103 (PhysioNet page, CC BY 4.0, checked 2026-11-10), cinc2017data (ODC-By 1.0 per the AWS
Open Data registry listing; to confirm on PhysioNet).

Facts taken from full texts in PubMed Central: Challenge 2017 recording parameters, class
definitions, relabeling agreement and overtraining remarks (clifford2017); PTB-XL sampling rates,
folds and counts (wagner2020).

## Open points for the author

- Pin the SHA-256 of both SHA256SUMS.txt files in `data/registry.json` after the first CI run
  prints them.
- The synthetic ECG's parameters are illustrative; a reviewer may prefer cited reference values.
- The PTB-XL codes SR and AFIB are taken from the database's SCP statements; the lab fails
  loudly in CI if either is missing from fold 10.
