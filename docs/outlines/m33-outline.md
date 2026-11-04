# m33 outline · Capstone: from map to digital twin (OpenEP to openCARP)

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

Capstone format: same nine template sections; short derivations that build on m08, m09, m24 and
m30; most of the work is a guided project in the code lab.

Licensing rules that shape this capstone (CLAUDE.md §6):

- **openCARP** is never committed here, as source or binaries; we link to it and publish only our
  own simulation outputs. Its license page, checked 2026-11-04, says the simulator is mixed-license:
  the core simulator paths are under the non-commercial Academic Public License 1.1, other parts
  under Apache 2.0, and every binary is subject to the Academic Public License. The `carputils`
  Python framework is listed under Apache 2.0.
- **OpenEP** (openep-py) is used as a dependency, pinned to a commit, and credited.
- No identifiable patient data. Clinical datasets need ethics approval and a data-sharing agreement.

## Learning goals

After this capstone a reader can:

1. Say what a cardiac digital twin is: a model whose anatomy and parameters are fitted to one
   patient's data so that it reproduces the observations ([corral2020]; [gillette2021]).
2. Load a mapping case with openep-py and inspect its mesh, points, activation times and voltages.
3. Prepare a simulation model from the map: mesh quality and resolution, region labels from voltage,
   and (optionally) fibre directions.
4. Calibrate conduction velocity per region so that a fast eikonal model matches the measured
   activation times, with the unknown timing offset solved in closed form.
5. Validate the twin on held-out points and show where the data cannot pin down the parameters
   (identifiability).
6. Export the calibrated model to openCARP's file formats, run it where openCARP is installed, and
   compare the reaction–diffusion result with the eikonal one.

Prerequisites: m08 (ionic models), m09 (propagation), m24 (interpolation) and m30 (mini mapping
system).

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

A map shows what was measured; a twin is a model that can be asked "what if?". To build one, take
the map's geometry, decide which tissue is which, and tune the model until its activation matches
the measured points. The hard part is honesty: a model that fits the points it was tuned on can
still be wrong between them, and different parameter sets can fit equally well. This capstone builds
a small twin and tests it that way.

### 2. From the field

Lessons tied to verified sources:

- Digital twins are proposed as a route to patient-specific diagnosis, prognosis and treatment in
  cardiology; the position paper reviews early steps and the challenges ahead ([corral2020]).
- A published framework builds electrophysiology twins from clinical 12-lead ECGs, and names
  efficiency, robustness and accuracy of the twinning steps as the main barriers ([gillette2021]).
- A reaction–eikonal model reproduced extracellular potentials, electrograms and ECGs of a full
  bidomain model at a computational cost lower by more than three orders of magnitude ([neic2017]).
- A feasibility study used personalized atrial models to choose ablation targets and loaded them
  into a clinical mapping system in ten patients ([boyle2019]).
- openCARP and its Python framework carputils are built to automate and share simulation pipelines
  for reproducibility ([plank2021]).

### 3. Derivations

Notation: $T(\mathbf{x})$ activation time (ms), $\mathbf{f}$ unit fibre direction, $v_f$, $v_t$
velocities along and across fibres (m/s), $D$ velocity tensor, $\boldsymbol\theta$ model parameters
(for example one velocity per region), $T_i^{\mathrm{meas}}$ measured LAT at point $i$, $t_0$
unknown timing offset (ms), $\sigma$ monodomain conductivity (S/m).

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m33-eikonal-aniso | $\sqrt{\nabla T^\top D\,\nabla T} = 1$, $D = v_f^2\,\mathbf{f}\mathbf{f}^\top + v_t^2\,(I - \mathbf{f}\mathbf{f}^\top)$ | Anisotropic eikonal model: fast activation with direction-dependent speed (form to check against [neic2017]) | simulation | Numeric: on a flat sheet with uniform fibres the isochrones are ellipses with axis ratio $v_f/v_t$ |
| eq-m33-offset | $J(\boldsymbol\theta, t_0) = \sum_i \big(T_i(\boldsymbol\theta) + t_0 - T_i^{\mathrm{meas}}\big)^2$, $t_0^\ast = \dfrac{1}{N}\sum_i \big(T_i^{\mathrm{meas}} - T_i(\boldsymbol\theta)\big)$ | Least-squares fit with the reference offset solved in closed form | exact | SymPy: $\partial J/\partial t_0 = 0$ gives $t_0^\ast$; numeric: optimizer agrees |
| eq-m33-cv-scaling | $v \propto \sqrt{\sigma}$ (fixed membrane model and surface-to-volume ratio) $\Rightarrow \sigma_{\text{new}} = \sigma_{\text{old}}\left(v_{\text{target}}/v_{\text{sim}}\right)^2$ | How to turn a calibrated velocity into a monodomain conductivity; the basis of iterative tuning ([costa2013]) | approximate model | Numeric: 1D Mitchell–Schaeffer cable; one or two iterations reach the target within tolerance |
| eq-m33-holdout | $E_{\mathrm{CV}} = \sqrt{\dfrac{1}{N}\sum_{k}\sum_{i \in \mathcal{F}_k}\big(T_i(\hat{\boldsymbol\theta}_{-k}) + t_0^\ast - T_i^{\mathrm{meas}}\big)^2}$ | Cross-validated error: each fold is predicted by a twin fitted without it | exact | Numeric: equals in-sample error when the model is exact and noise-free; exceeds it when overfitting |

Region labelling from voltage uses the thresholds and sources from m23 and m30. Each derivation
subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline.

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m33-d1 | Calibrate a twin | number of measured points, noise, number of regions, region shapes | A 2D sheet with a hidden slow region; regional velocities fitted with an eikonal model; in-sample vs held-out error as regions are added | simulation |
| m33-d2 | Eikonal vs reaction–diffusion | scar edge sharpness, pacing site, curvature | Activation times from the eikonal model and from a Mitchell–Schaeffer monodomain run (precomputed, our own code) and their difference | simulation |

Assumptions to list under the demos: 2D sheet, isotropic unless fibres are switched on, sharp
region borders, Gaussian annotation noise (d1); explicit finite differences with stated grid, time
step and Mitchell–Schaeffer parameters (d2).

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: where twins have been tried, from [boyle2019] (feasibility in ten patients) and
[gillette2021] (twins from 12-lead ECGs), with the open problems in [corral2020]. Descriptive only;
no claim that twins should guide therapy.

### 6. Visual summary and How experts think

- Visual summary: the pipeline OpenEP case → mesh → labels → parameters → eikonal calibration →
  openCARP export → simulation → comparison, with the file format at each step. Badge: schematic.
- How experts think: "Which of these parameters did the data actually determine?" Report held-out
  error and the spread of parameter sets that fit equally well, not just the best fit.

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including "why solve the
timing offset separately?" and "how do you tell overfitting from a good twin?".

### 8. Code lab and Self-check

Lab: `labs/python/m33_lab.ipynb`, a guided project with automatic checks (Python only).

| Part | Milestone | Data |
| --- | --- | --- |
| A | Load a case with openep-py (pinned commit) and inspect it | OpenEP example case (license to check) or the m30 synthetic case |
| B | Mesh preparation: quality checks and remeshing with `pyvista` | Same |
| C | Region labels from voltage; how the threshold choice moves the labels | Same |
| D | Eikonal calibration of regional velocities with `scipy.optimize`; closed-form offset | Same |
| E | Cross-validation and identifiability: repeated fits from many starts; spread of good fits | Same |
| F | Export mesh, labels and parameters in openCARP formats; convert velocities to conductivities | Same |
| G | Optional: run openCARP where it is installed, load results back with openep-py, compare with the eikonal twin (skipped in CI unless approved, question 2) | Our own simulation output |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. Candidates: [gillette2021] and [neic2017] (licenses to
check); otherwise our own figures.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| plank2021 | Plank G, et al. The openCARP simulation environment for cardiac electrophysiology. Comput Methods Programs Biomed 2021;208:106223. DOI 10.1016/j.cmpb.2021.106223, PMID 34171774 | Verified (PubMed) |
| corral2020 | Corral-Acero J, et al. The 'Digital Twin' to enable the vision of precision cardiology. Eur Heart J 2020;41(48):4556–4564. DOI 10.1093/eurheartj/ehaa159, PMID 32128588 | Verified (PubMed) |
| gillette2021 | Gillette K, et al. A framework for the generation of digital twins of cardiac electrophysiology from clinical 12-leads ECGs. Med Image Anal 2021;71:102080. DOI 10.1016/j.media.2021.102080, PMID 33975097 | Verified (PubMed) |
| neic2017 | Neic A, et al. Efficient computation of electrograms and ECGs in human whole heart simulations using a reaction-eikonal model. J Comput Phys 2017;346:191–211. DOI 10.1016/j.jcp.2017.06.020, PMID 28819329 | Verified (PubMed) |
| costa2013 | Costa CM, et al. Automatic parameterization strategy for cardiac electrophysiology simulations. Comput Cardiol 2013;40:373–376. PMID 24729986, PMCID PMC3980367 (no DOI in PubMed) | Verified (PubMed) |
| boyle2019 | Boyle PM, et al. Computationally guided personalized targeted ablation of persistent atrial fibrillation. Nat Biomed Eng 2019;3(11):870–879. DOI 10.1038/s41551-019-0437-9, PMID 31427780 | Verified (PubMed) |
| williams2021 | OpenEP data format. Already in `references.bib` | Verified |
| sethian1996, mitchell2003 | Fast marching; Mitchell–Schaeffer model. See the m30 and m29 outlines | Verified (PubMed) |
| opencarplicense | openCARP license page, https://opencarp.org/download/license | Official page; `@misc` with URL and access date |

## Still to source (before stage 2)

Each is `TODO(source)` until found:

- The full text of the Academic Public License 1.1, for any terms on simulation results, citation
  or use in teaching
- License of OpenEP's example datasets (openep-py test data, and the Zenodo record
  "openep-testingdata"), and which case to use
- openep-py functions for openCARP export (readers exist; the writer to check at the pinned commit)
- Atrial fibre rules or an atlas with an open license, if fibres are used
- Mitchell–Schaeffer parameters for atrial tissue and a monodomain conductivity (shared with m29)
- A source for the $v \propto \sqrt{\sigma}$ scaling statement, if [costa2013] does not state it

## Glossary terms to add

digital twin · calibration · identifiability · reaction–eikonal model · anisotropy · fibre direction
· region labelling · cross-validation · openCARP · carputils · OpenEP case

## Formula-sheet entries

eq-m33-eikonal-aniso · eq-m33-offset · eq-m33-cv-scaling · eq-m33-holdout

## Questions for the author

1. **Data for Part A:** use an OpenEP example case (if its license allows use in a CC BY / MIT
   course), or keep the whole capstone on the synthetic case from m30?
2. **openCARP in CI:** the lab can export to openCARP and stop, so CI never needs openCARP. Or CI
   could install the official openCARP package at run time (never committed) to run Part G. The
   binaries are under a non-commercial academic license; is that acceptable for this course's CI?
3. **Fibres:** isotropic surface model (simpler, recommended for a capstone), or add rule-based
   fibres?
4. **Badge for real-case figures:** same question as m31 if Part A uses a real case.
