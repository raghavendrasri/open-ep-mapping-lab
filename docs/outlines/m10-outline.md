# m10 outline · Arrhythmia mechanisms: focal, macro-reentry, rotors, atrial fibrillation

Stage 1 (outline) for module m10, written together with stages 2–6 (author request, 2026-11-14). Part II: Python lab
only.

## Scope

Wavelength and the conditions for reentry; the excitable gap; restitution maps and alternans; rotors and phase
singularities (topological charge comes from m29 and is linked, not repeated); focal against reentrant activation;
atrial fibrillation triggers and the rotor debate as the studies report them. Out of scope: triggered activity and
afterdepolarization models, entrainment (m11), map-based mechanism algorithms (m24, m29, m41).

## Equations (tests in `tests/test_m10_arrhythmia.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m10-wavelength | $\lambda = \text{CV}\times\text{ERP}$ | arithmetic; ring simulations |
| eq-m10-circuit | CL, condition, gap | gap in mm = CV × gap in ms; Mitchell–Schaeffer ring sustains at 90 mm, fails at 80 mm |
| eq-m10-restitution | map and its linearization | SymPy slope $-f'$; alternating, growing deviations exactly when $f' > 1$ |
| eq-m10-alternans | closed-form onset | slope 1 at $\text{DI}_c$; paced cell steady at 300 ms, alternating at 210 ms |
| eq-m10-focal | centrifugal activation, span | span of a focus in a square; a circuit spans the cycle |

Also tested: one phase singularity with charge ±1 in a Barkley spiral, opposite charge for the mirror image.

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m10-d1 | exact | restitution map cobweb and APD sequence against pacing cycle length |
| m10-d2 | exact | ring with wavelength and excitable gap for circuit length, velocity and refractory period |

## Code lab (`labs/python/m10_lab.ipynb`)

A wavelength; B ring reentry; C restitution and alternans; D spiral wave and phase singularity; E focal against
reentrant activation span.

## Sources

- PubMed: Rensma et al. 1988 (PMID 3338122), Haïssaguerre et al. 1998 (PMID 9725923), Allessie et al. 1977 (PMID
  862147, no abstract: cited for the leading-circle concept stated in its title), Nolasco and Dahlen 1968 (PMID
  5666097, no abstract: cited for the graphic method in its title), Saoudi et al. 2001 (PMID 11440490, no abstract:
  cited as the classification statement), Narayan et al. 2012 (PMID 22818076), Buch et al. 2016 (PMID 26498260),
  Pastore et al. 1999 (PMID 10077525).
- Web search: Barkley 1991, Physica D 49:61–70.
- Already in the bib: bray2001, wijffels1995, nietoramos2023.
