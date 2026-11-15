# m14 outline · Biopotential front ends

Stage 1 (outline) for module m14, written together with stages 2–6 (author request, 2026-11-14). Part III: Python lab
only.

## Scope

Differential and common mode; the four-resistor difference amplifier and its tolerance-limited CMRR; the
three-op-amp instrumentation amplifier; electrode impedance mismatch; the driven right leg; input noise (thermal,
voltage, current) and the optimum source resistance; the Wilson central terminal with electrode impedances; converter
resolution and oversampling. Out of scope: patient safety and isolation (m15), filter design (m04), specific products.

## Equations (tests in `tests/test_m14_frontend.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m14-cmrr | mode split, CMRR | SymPy identities |
| eq-m14-diffamp | difference amplifier, worst-case CMRR | SymPy nodal solution; first-order series in tolerance; Monte Carlo bound |
| eq-m14-inamp | input-stage gain and CMRR multiplication | SymPy stage outputs; numeric CMRR = G1 x stage CMRR |
| eq-m14-imbalance | mismatch conversion | SymPy first-order series; complex input impedance |
| eq-m14-drl | common mode with feedback | SymPy solve |
| eq-m14-noise | quadrature sum, optimum source resistance | SymPy minimum; Monte Carlo quadrature; numeric optimum |
| eq-m14-wct | weighted central terminal | SymPy equal-impedance mean; numeric bias and its cure |
| eq-m14-oversampling | input step, bits, averaging gain | numeric with white noise |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m14-d1 | exact | CMRR budget: amplifier against electrode mismatch |
| m14-d2 | exact | noise density against source resistance |

## Code lab (`labs/python/m14_lab.ipynb`)

A difference amplifier; B instrumentation amplifier; C mains interference and the driven right leg; D noise budget; E
central terminal and converter.

## Sources

- PubMed: Huhta and Webster 1973 (PMID 4688314) and Winter and Webster 1983 (PMID 6826188), no abstracts, cited as
  pointers by title only; Gargiulo 2015 (PMID 26495303); Venkatachalam et al. 2011 (PMID 22203661, no abstract, cited
  by title); Al-Ahmad et al. 2021 (PMID 34554634).
- Web: Nyquist 1928, Physical Review 32:110, DOI 10.1103/PhysRev.32.110.
- Already in the bib: codata2018, kligfield2007.
