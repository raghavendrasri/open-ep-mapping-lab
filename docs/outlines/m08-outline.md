# m08 outline · Action potentials and ionic models

Stage 1 (outline) for module m08, written together with stages 2–6 (author request, 2026-11-14: "complete m07 to
m12"). Part II module: Python lab only (CLAUDE.md §7 asks for Octave copies in Part I).

## Scope

The membrane circuit and Nernst potentials; Hodgkin–Huxley-type gates; excitability, threshold, refractoriness and the
onset of repetitive firing in the FitzHugh–Nagumo model; the Mitchell–Schaeffer cardiac model, a closed-form APD and
restitution; detailed human atrial models described from their abstracts; electrical remodeling. Out of scope:
implementing a detailed atrial model (dozens of parameters we could not verify from accessible sources), propagation
(m09) and alternans dynamics (m10).

## Equations (tests in `tests/test_m08_membrane.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m08-membrane | $C_m\,dV/dt = -I_{\text{ion}} + I_{\text{stim}}$ | SymPy passive step |
| eq-m08-nernst | Nernst potential | RT/F from exact SI constants; 61.54 mV per decade; sign and valence |
| eq-m08-gating | gate kinetics, $m^3h$ current | SymPy clamp solution; Euler converges |
| eq-m08-fhn | FitzHugh–Nagumo | fixed point and stability; all-or-none threshold; refractoriness |
| eq-m08-hopf | onset of repetitive firing | SymPy trace; simulation below and above $I_H$ |
| eq-m08-ms | Mitchell–Schaeffer | SymPy discriminant gives $h_{\min}$; simulated time to $h_{\min}$ equals $\tau_{\text{close}}\ln(h_{\text{up}}/h_{\min})$ |
| eq-m08-apd | closed-form APD and restitution | APD_max; S1–S2 gap 25–45 ms; monotone restitution; SymPy slope at DI → 0 |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m08-d1 | simulation | FitzHugh–Nagumo phase plane: kick and steady current |
| m08-d2 | simulation | Mitchell–Schaeffer S1–S2: action potentials and restitution, with the closing time constant |

## Code lab (`labs/python/m08_lab.ipynb`)

A circuit and Nernst; B gates and integrators; C FitzHugh–Nagumo; D Mitchell–Schaeffer restitution and refractory
period; E shorter action potentials as a stand-in for remodeling.

## Sources

- PubMed: Courtemanche et al. 1998 (PMID 9688927), Koivumäki et al. 2011 (PMID 21298076), Wijffels et al. 1995 (PMID
  7671380), FitzHugh 1961 (PMID 19431309; abstract only, full text not available as text), Hodgkin and Huxley 1952
  (PMID 12991237; cited for the gating formalism only).
- arXiv (alphaXiv): Nieto Ramos et al. 2023, arXiv 2311.10114, for the Mitchell–Schaeffer parameter values, which
  they state are based on the original paper. The original (Mitchell and Schaeffer 2003, already in the bib) was not
  accessible, so the values were not checked against it.
- Web search: CODATA 2018 (Tiesinga et al. 2021) for the exact SI constants.
