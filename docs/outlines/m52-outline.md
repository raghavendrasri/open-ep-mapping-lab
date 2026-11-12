# m52 outline · Cardiac MRI for EP

Stage 1 (outline) for module m52, written together with stages 2–6 (author request, 2026-11-11: finish the
remaining Part VIII modules, one pull request each). Plan source: `docs/outlines/part8-overview.md`.

## Scope

The MRI physics needed to read LGE for EP: the Larmor relation, inversion recovery, gadolinium and T1, extracellular
volume, the choice of inversion time, and why atrial "fibrosis" burden depends on normalization and threshold. Then
the published evidence: DECAAF and DECAAF II, methods and reproducibility studies, LGE before VT ablation, and MRI with
implanted devices. Out of scope: k-space and pulse-sequence design, T2 and T2* mapping, cine and flow imaging,
scanner operation, device programming, advice on any patient. Real-time MRI-guided ablation and lesion imaging are in
m53.

## Learning goals

1. State the Larmor relation and compute scanner frequencies.
2. Derive the inversion-recovery null point.
3. Relate gadolinium concentration to T1, and T1 changes to ECV.
4. Choose an inversion time for LGE and explain magnitude against phase-sensitive images.
5. Compute an image intensity ratio and show how the burden moves with the threshold.
6. Read the DECAAF evidence chain as association, then trial.

## Equations (tests in `tests/test_m52_mri.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m52-larmor | f = (γ/2π) B0 | CODATA value; 63.87 MHz at 1.5 T |
| eq-m52-ir | Mz = M0 (1 − 2 e^(−t/T1)); null at T1 ln 2 | SymPy dsolve; full Bloch simulation within 2% |
| eq-m52-relaxivity | 1/T1 = 1/T1,0 + r1 [Gd] | Kellman and Arai's worked example (950 → ~300 ms) |
| eq-m52-ecv | ECV = (1 − Hct) ΔR1,myo/ΔR1,blood | Recovers a known ECV; Bauner et al. ratio check |
| eq-m52-lge | TI* = ln(T1m/T1s)/(1/T1s − 1/T1m) | SymPy derivative; numeric maximum; scar signal at the null |
| eq-m52-iir | IIR = I_wall / mean I_blood; burden above θ | Gain invariance; monotone burden; Otsu against brute force |

Also tested: published thresholds bracket the true burden on the synthetic wall; blood-pool normalization on a
synthetic volume (as used on the Decathlon data).

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m52-d1 | exact | Signal against TI for myocardium, scar and blood; magnitude or phase-sensitive |
| m52-d2 | simulation | Synthetic atrial wall with known patches; burden and Dice against truth and a repeat scan for each published threshold |

## Code lab (`labs/python/m52_lab.ipynb`)

A Larmor; B Bloch inversion recovery; C gadolinium, T1 and ECV; D choosing TI; E thresholds on a synthetic wall;
F blood-pool normalization on the Decathlon heart MRI (optional download, not LGE); G the evidence chain.

## Sources

CODATA 2022 (NIST wallet card, read through web search on 2026-11-11). PubMed (abstracts, and the full text of
kellman2012, read 2026-11-11): kellman2012, bauner2012, kamali2020, boyle2022, gunturiz2022, guichard2024,
pittorru2026, russo2017, nazarian2017, sheagren2025. Already in `references.bib`: marrouche2014, marrouche2022,
akoum2024, antonelli2021msd.

## Open points for the author

- Native blood T1 (1600 ms) and hematocrit (0.42) are illustrative; no source was read for them in this session.
- The synthetic wall's patch shape, fibrotic intensity, noise and 15% burden are illustrative; only its normal
  mean + 2 SD is tied to a published limit (right atrium, 3 T).
- No openly licensed atrial LGE data set was added (`TODO(source)` in the plan stays open); part F uses non-LGE MRI.
- The device section reports registry findings only and gives no operating instructions.
