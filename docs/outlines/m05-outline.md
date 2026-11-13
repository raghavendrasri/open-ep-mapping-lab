# m05 outline · Time–frequency tools: dominant frequency, Hilbert phase, wavelets

Stage 1 (outline) for module m05, written together with stages 2–6 (author request, 2026-11-12). m05 is the signal
processing foundation; m29 applies it (dominant frequency, organization index, phase maps) and owns those definitions,
which m05 links rather than repeats.

## Scope

DFT resolution, windows and leakage, periodogram variance and Welch averaging, line spectra of pulse trains and why
electrograms are preprocessed, the analytic signal and its limits, the time–frequency uncertainty relation and the
Morlet wavelet. Out of scope: DF/OI/phase-map definitions and clinical use (m29, m31).

## Equations (tests in `tests/test_m05_timefreq.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m05-resolution | $\Delta f = 1/T$ | two tones 1 Hz apart: resolved at 1 s, not at 0.5 s even with zero padding |
| eq-m05-leakage | windowed spectrum | sidelobes −13.26 and −31.47 dB; first nulls at 1 and 2 bins; SymPy Hann kernel zeros |
| eq-m05-welch | spread $1/\sqrt K$ | simulated white noise, K = 1, 4, 8; a 32-s record is no smoother |
| eq-m05-pulse-train | line spectrum | SymPy transform of a Gaussian-derivative pulse and its peak; raw peak at a harmonic, preprocessed at $1/T_0$ |
| eq-m05-analytic | $z = x + j\mathcal H[x]$ | sine and AM envelope; one vs two turns per activation |
| eq-m05-uncertainty | $\sigma_t\sigma_f \ge 1/(4\pi)$ | SymPy for a Gaussian; numeric; a non-Gaussian pulse exceeds it |
| eq-m05-morlet | Morlet CWT, $f = \omega_0/(2\pi s)$ | CWT of sines peaks at the right frequency |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m05-d1 | exact | Two tones: resolution against record length; rectangular or Hann window |
| m05-d2 | exact | Hilbert phase turns against activations for a sine, single and double deflections, and noise |

## Code lab (`labs/python/m05_lab.ipynb`, Octave copy `labs/octave/m05_lab.m` for parts A–E)

A resolution; B leakage; C variance and Welch; D pulse trains and preprocessing; E analytic signal; F uncertainty and
wavelets with a changing rate.

## Sources

Already in `references.bib` and used in m29: ng2007tech, ng2007, kuklik2014, sanders2005, gray1998, everett2001.
PubMed (2026-11-12): Botteron and Smith 1995 was found, but its abstract does not describe the band-pass, rectify,
low-pass chain, so it is not cited for it; m29's `TODO(source)` on the origin of that chain remains open.
