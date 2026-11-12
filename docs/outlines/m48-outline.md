# m48 outline · Imaging across the EP workflow

Stage 1 (outline) for module m48, written together with stages 2–6 (author request, 2026-11-11: finish the
remaining Part VIII modules, one pull request each; m48 last). Plan source: `docs/outlines/part8-overview.md`.

## Scope

One vocabulary for every modality: which question each answers, blur and resolution, contrast, noise and dose, and
the accuracy of an imaging test. The modalities themselves are in m49–m54; the thin-wall model is derived in m51 and
used here; diagnostic accuracy is introduced in m35 and applied here. Out of scope: choosing imaging for a patient,
vendor protocols.

## Learning goals

1. Describe any modality by resolution, contrast, noise, speed, dose and access.
2. Compute contrast-to-noise ratio, the effect of averaging and smoothing, and the visibility of a thin wall.
3. Turn sensitivity and specificity into predictive values and likelihood ratios for an imaging test.

## Equations (tests in `tests/test_m48_overview.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m48-psf | Gaussian PSF; Γ = 2√(2 ln 2) σ; a dip between two points only if d > 2σ | SymPy half-maximum and midpoint curvature; measured FWHM; dip depths |
| eq-m48-cnr | CNR = \|S_A − S_B\|/σ_n; √n gain from averaging | Simulation within 5% |
| eq-m48-smooth | σ_n' = σ_n Δ/(2√π σ_s); blurs add in quadrature | SymPy ∫h² = 1/(4πσ_s²); simulated smoothed noise; FWHM of two blurs |
| eq-m48-visibility | CNR_wall = (C/σ_n) erf(w/(2√2 σ)); w_min by erf⁻¹ | Noisy phantom within 5%; inverse round trip |
| eq-m48-lr | LR± and post-test odds = pre-test odds × LR | SymPy equivalence with eq-m35-ppv and NPV; published accuracy values |

Also tested: PPV is concave in prevalence (SymPy), so averaged per-study PPVs fall below the PPV at the mean
prevalence; the four-way phantom separates the mean wall from the esophagus at CT and MRI resolution only.

The planned eq-m48-thin-wall is not repeated: the page links to eq-m51-wall, where it is derived and tested.

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m48-d1 | exact | Thin wall through a Gaussian blur; presets from published resolutions; two readings of thickness |
| m48-d2 | exact | PPV and NPV against prevalence; presets from the CT meta-analysis, with the reported pooled values |

The planned "which modality for which question" demo became a table in the text (see decisions).

## Code lab (`labs/python/m48_lab.ipynb`)

A blur and two-point resolution; B thin walls at published resolutions; C where contrast comes from (m49, m51, m52
code); D CNR and averaging; E smoothing trade-off; F one cross-section at four resolutions; G accuracy of CT for
appendage thrombus, likelihood ratios and pooled PPV. Offline, about 3 s.

## Sources

PubMed (abstracts read 2026-11-12): rajendran2022 (new), donal2016 (re-read for the clinical correlate). Already in
`references.bib` and verified earlier: romero2013, kellman2012, kinahan2010, beinart2011, bauner2012, altman1994, and
the studies in the question table (greffier2026, debreceni2023, kanniyan2026, tsao2005, kistler2006, boyle2022,
guichard2024, aljefairi2019, muser2018, bourque2024).

## Open points for the author

- Each resolution is read as the FWHM of a Gaussian; the CT values are section-sensitivity widths of one
  photon-counting system, and the MRI values are voxel sizes. A reviewer may prefer other representative values.
- Contrasts, noise levels, the esophageal gap and geometry, the iodine concentration, the CNR target k = 3 and the
  simulated meta-analysis are illustrative.
- The explanation of why the pooled PPV (41%) differs from the formula (54%) is offered as one possible reason
  (concavity in prevalence), not as the meta-analysis's own account.
