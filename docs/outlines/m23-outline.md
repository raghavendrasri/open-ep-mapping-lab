# m23 outline · Voltage mapping: amplitude, thresholds, dependence on wavefront direction

Stage 1 (outline) for module m23, written together with stages 2–6 (author request, 2026-11-15). Part IV: Python lab
only.

## Scope

Peak-to-peak amplitude of unipolar and bipolar electrograms in the m03 model and its dependence on electrode height and
spacing; the dependence of bipolar amplitude on wavefront direction, and what orthogonal bipoles and projections
recover; the noise floor; cutoffs, sensitivity and specificity; a synthetic voltage map. Out of scope: interpolation
(m24), point density (m26), learned substrate detection (m39, m40), imaging scar (m52), patient-care cutoffs.

## Equations (tests in `tests/test_m23_voltage.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m23-amplitude | pp(U) = A/a; bipolar limits for small and large spacing | SymPy extremes; numeric limits; height exponents |
| eq-m23-direction | P(abs cos < q) = (2/π) arcsin q; pair ≥ 1/√2; projection constant | SymPy measure; Monte Carlo; numeric |
| eq-m23-noise | expected peak-to-peak of n Gaussian samples | Monte Carlo; n = 2 closed form |
| eq-m23-threshold | log-normal sensitivity and specificity; Youden cutoff √(m_s m_n) | Monte Carlo; grid search; SymPy |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m23-d1 | exact | amplitude against wavefront angle for one bipole, a pair and the largest projection |
| m23-d2 | approximate model | log-normal scar and healthy voltages, a cutoff and extra electrode height |

## Code lab (`labs/python/m23_lab.ipynb`)

A amplitude against height and spacing; B direction; C noise floor; D cutoffs and ROC; E a synthetic voltage map.

## Sources

- PubMed: teijeira2018 (PMID 29572086), yavin2021 (PMID 34822200).
- Already in the bib (PubMed): marchlinski2000, anter2015, riccio2021, masse2016, deno2017; iafdb.
