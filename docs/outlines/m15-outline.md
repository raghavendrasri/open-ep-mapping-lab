# m15 outline · Patient safety

Stage 1 (outline) for module m15, written together with stages 2–6 (author request, 2026-11-14). Part III: Python lab
only.

## Scope

Capacitive leakage through isolation barriers and its sum over devices; microshock as current concentration at a small
intracardiac electrode; defibrillation protection by series resistor and clamp; RF ablation energy, filtering and
demodulation by a nonlinearity. Out of scope: the text and limits of IEC 60601-1 and its collateral standards (not
available to read; only limits quoted in peer-reviewed papers are used), hospital wiring, pulsed field ablation details
(m28).

## Equations (tests in `tests/test_m15_safety.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m15-leakage | 2 pi f C V, phasor sum, maximum capacitance | SymPy rms of C dv/dt; numeric sums and inversion |
| eq-m15-density | J = I/(2 pi r^2), concentration ratio | SymPy flux; numeric scaling |
| eq-m15-defib | clamp current, resistor energy, diverted share | SymPy energy; numeric clamp behavior |
| eq-m15-rf-filter | Butterworth roll-off and order | numeric against the m04 Butterworth; order search |
| eq-m15-demod | baseband shift beta A^2 / 2 | SymPy time average; numeric |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m15-d1 | exact | total leakage against isolation capacitance, with published thresholds |
| m15-d2 | exact | Butterworth orders against the attenuation RF needs |

## Code lab (`labs/python/m15_lab.ipynb`)

A leakage; B current density; C defibrillation protection; D RF filtering and demodulation; E a safety budget.

## Sources

- PubMed: Swerdlow et al. 1999 (PMID 10330388), Jonsson et al. 2005 (PMID 16594299), Burgess 2019 (PMID 31277877).
- Already in the bib: berjano2006 (RF frequency range).
- Not used: the IEC 60601-1 text and its limits for normal condition, which appear only in non-peer-reviewed sources
  found by web search.
