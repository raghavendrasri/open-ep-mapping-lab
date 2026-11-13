# m04 outline · Sampling, filtering and the EP recording chain

Stage 1 (outline) for module m04, written together with stages 2–6 (author request, 2026-11-12). Builds on m03 (the
unipolar model is the test signal) and feeds m05 (time–frequency), m14 (front ends), m22 (annotation).

## Scope

Sampling and aliasing, timing resolution, quantization noise, RC and Butterworth filters, group delay and zero-phase
filtering, mains notch filters, and their effect on a unipolar electrogram. Out of scope: amplifier design and
safety (m14, m15), vendor filter defaults.

## Equations (tests in `tests/test_m04_recording.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m04-sampling | alias frequency | identical samples for f and its alias |
| eq-m04-quantization | $q^2/12$; $6.02N + 1.76$ dB | SymPy variance and SQNR; simulated 10- and 12-bit converters |
| eq-m04-highpass | RC high-pass | SymPy: −3 dB and 45° at $f_c$; differentiator limit |
| eq-m04-butterworth | $\lvert H\rvert^2 = 1/(1 + (f/f_c)^{2n})$ | scipy analog responses; hand-built digital coefficients equal scipy.signal.butter |
| eq-m04-delay | group delay $1/(2\pi f_c)$, $\sqrt2/(2\pi f_c)$ | SymPy limit; measured delay of a slow bump; zero phase removes it |
| eq-m04-notch | second-order notch | equals scipy.signal.iirnotch; zero at $f_0$; bandwidth $f_0/Q$ |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m04-d1 | exact | A sinusoid, its samples and its alias |
| m04-d2 | approximate model | The m03 unipolar electrogram through published bands, causal or zero-phase; timing shift |

## Code lab (`labs/python/m04_lab.ipynb`, Octave copy `labs/octave/m04_lab.m` for parts A–E)

A sampling and timing; B quantization; C filters by hand; D three bands on a unipolar electrogram; E notch.

## Sources

PubMed (2026-11-12): delacretaz2001 (abstract: bands 0.5–500, 100 and 30–500 Hz; 205 sites, 40 patients; r = 0.85;
3.8 ± 3.5 vs 9.2 ± 5.2 ms); stevenson2005 (abstract re-read). Venkatachalam et al. 2011 and Tedrow and Stevenson 2011
were found but have no abstracts, so they are not cited. iafdb (1 kHz, 14 bits) as in m31.

## Open points for the author

- The demo applies bipolar and unipolar bands to one model unipolar signal; real systems' filter types and orders
  differ and are not described here.
- The timing experiment uses a slower front (0.5 m/s) so the downstroke spans a few samples at 1 kHz.
