# m51 outline · Cardiac CT for EP

Stage 1 (outline) for module m51, the third Part VIII module, written together with stages 2–6 (author request,
2026-11-11: finish the remaining Part VIII modules, one pull request each). Plan source:
`docs/outlines/part8-overview.md`.

## Scope

The CT physics an engineer or EP fellow needs to read a pre-procedural CT critically: attenuation and Hounsfield
units, contrast, projections and the central-slice theorem, filtered back-projection, quantum noise and dose, the
gating window and motion, and what blur and voxel size do to thin walls and small distances. Then the published
uses of CT before ablation (thrombus, esophagus, wall thickness, VT isthmuses) and the two kinds of registration
error. Registration itself stays in m21 (author decision). Out of scope: spiral and cone-beam geometry, iterative
reconstruction, dual-energy imaging, dose conversion to effective dose, scanner operation, advice on any patient.

## Learning goals

1. Define Hounsfield units and compute the effect of iodine from tabulated attenuation.
2. State the central-slice theorem and reconstruct a slice by filtered back-projection.
3. Relate image noise to photon count and dose.
4. Estimate the gating window and the motion blur it allows.
5. Predict how blur and voxel size change measured wall thickness and distances.
6. Distinguish the error a system reports from the error at a target.

## Equations (tests in `tests/test_m51_ct.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m51-hu | HU = 1000 (μ − μ_w)/(μ_w − μ_a) | SymPy (water 0, air −1000, inverse); NIST tissues |
| eq-m51-iodine | ΔHU = 1000 c 10⁻³ (μ/ρ)_I / μ_w | Linearity; 36.81 HU per mg/mL at 60 keV |
| eq-m51-radon | p_θ(s) as line integrals; ellipse chord formula | Against line sums through a raster (2%); equal totals per angle; disk |
| eq-m51-slice | P_θ(k) = F(k cos θ, k sin θ) | Disk in closed form (Bessel J1); rotated, off-center ellipse numerically |
| eq-m51-fbp | Back-project ramp-filtered projections | Disk value within 1%; phantom median error < 25 HU; streaks with 30 angles |
| eq-m51-ramlak | h[0] = 1/(4d²), −1/(π²n²d²) odd, 0 even | SymPy integral of the band-limited ramp, n = 0…6 |
| eq-m51-noise | Var ≈ e^p/N0 | Monte Carlo variance; image noise halves for 4× photons |
| eq-m51-gating | Δt ≈ T_rot/(2 N_src); b = vΔt | Against 125/66 ms at 0.25 s and 83 ms at 0.33 s (within 6%) |
| eq-m51-smear | Time-averaged moving disk; peak min(1, D/b) | Against Monte Carlo averaging; area conserved |
| eq-m51-wall | Erf profile of a blurred wall; peak erf(w/(2√2σ)) | SymPy; convolution; area = w; threshold and FWHM readings; blurred step width |

Also tested: on a 3-D atrium, wall thickness along rays within 1.5 voxels, the esophagus distance, blurred walls of
1 mm and more within 0.3 mm, coarse voxels inflating the thinnest walls.

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m51-d1 | simulation | Sinogram and reconstructed slice of a thorax phantom; number of angles, ramp filter on or off, photons per ray |
| m51-d2 | approximate model | A vessel smeared by motion during the gating window; rotation time, sources, published speeds, vessel diameter |

## Code lab (`labs/python/m51_lab.ipynb`)

A Hounsfield units and iodine; B projections and the central-slice theorem; C filtered back-projection; D noise and
dose; E the gating window and motion blur; F thin walls under blur; G wall thickness and esophagus distance on a 3-D
left atrium. No downloads; about half a minute.

## Sources

NIST SRD 126 (water and iodine at 60 keV, read on 2026-11-11 through a web search because a direct page fetch was not
approved in this session; tissue values as in m49). PubMed (abstracts checked 2026-11-11): achenbach2000 (coronary
speeds), petersilka2008 and mergen2023 (gating windows), tsao2005, ciaccio2024, moore2024, kistler2006, dong2006,
donal2016, radon1986 (translation). Book: kakslaney2001 (DOI from the publisher's site). Already in `references.bib`:
romero2013, beinart2011, nist126.

## Open points for the author

- Attenuation is monoenergetic (60 keV); clinical HU values differ. Lungs are drawn as air.
- The iodine concentration, phantom shapes, photon counts, scanner blur and the vessel diameter are illustrative.
- The gating model ignores the fan angle and data weighting; it matches the cited windows within 6%.
- Coronary speeds stand in for cardiac motion in general; no published speed for the left atrial wall was used.
- No openly licensed cardiac CT data set was added; the plan's optional public data set remains open.
- Two cited physics papers have authors employed by a CT manufacturer (petersilka2008, mergen2023); the module
  describes the principle generically.
