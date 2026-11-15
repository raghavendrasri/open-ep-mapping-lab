# m22 outline · Electrogram annotation: local activation time, window of interest, reference, far-field rejection

Stage 1 (outline) for module m22, written together with stages 2–6 (author request, 2026-11-15). Part IV: Python lab
only.

## Scope

Local activation time against a reference; how reference error enters single-beat and multi-beat data; annotation
rules (unipolar steepest downstroke, bipolar peak, bipolar onset) on the m03 electrogram model; noise and timing jitter;
the window of interest for reentry; far-field rejection by sharpness, template subtraction and blanking. Out of scope:
products' annotation algorithms (described generically), interpolation (m24), conduction velocity (m25), map
uncertainty (m26), learned annotation (m39).

## Equations (tests in `tests/test_m22_annotation.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m22-lat | LAT; variance of differences within and across beats | sympy.stats variances; Monte Carlo |
| eq-m22-intrinsic | steepest downstroke at s = 0; bipolar peak at midpoint if d cos θ < 2√3 a | SymPy derivatives; numeric; split beyond the limit |
| eq-m22-onset | onset lead (a/c) sqrt(x_f) | SymPy root; numeric small spacing; grows with height |
| eq-m22-jitter | σ_t = σ_n / slope | Monte Carlo with smooth noise |
| eq-m22-woi | wrap into [w0, w0 + W) modulo T | wrap is a whole number of cycles; one jump; coverage W/T |
| eq-m22-farfield | sharpness c/a; least-squares template gain and its bias | SymPy ratio; numeric; bias formula |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m22-d1 | exact | unipolar and bipolar traces with steepest-downstroke, peak and onset markers |
| m22-d2 | approximate model | window of interest on an idealized macroreentry |

## Code lab (`labs/python/m22_lab.ipynb`)

A reference error and plane-fit speed; B annotation rules against height and spacing; C noise; D window of interest; E
far field.

## Sources

- PubMed: marchlinski1998 (PMID 9725163), koawing2015 (PMID 26247796), gu2022 (PMID 35792722), ragot2021 (PMID
  33694221), martinezmateu2019 (PMID 31015048), delcarpio2010 (PMID 21156773, no abstract: cited as a pointer only).
- Already in the bib: steinhaus1989, cantwell2015, heil2023, riccio2021, iafdb.
