# m32 outline · Capstone: ECG imaging end to end (EDGAR)

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

Capstone format: same nine template sections; short derivations that build on m02, m07 and m12;
most of the work is a guided project in the code lab, first on an analytic model, then on an
EDGAR dataset.

## The data

EDGAR, the Experimental Data and Geometric Analysis Repository, run for the Consortium for ECG
Imaging ([aras2015]). From its user guide and paper, checked 2026-11-04:

- Free, curated experimental, clinical and simulated data for testing ECG imaging (ECGI) methods.
- Downloading needs an account (name, email, institution and purpose) on the repository's REDCap
  server, and agreement to an access statement; users pledge to cite each dataset's source and to
  acknowledge the Consortium.
- The guide names **no license** and does not say whether downloaded data may be redistributed.
- Formats: MATLAB `.mat` time series (a `potvals` field), geometry as `.mat` or text
  (`.pts`, `.fac`, `.tet`, millimetres), forward and inverse transforms as matrices, images as DICOM
  or NRRD.

These terms decide how the lab can get its data (question 1).

## Learning goals

After this capstone a reader can:

1. Describe the ECGI pipeline: geometry from imaging, electrode registration, a forward model, an
   inverse solution, and activation times on the heart surface ([ramanathan2004]).
2. Build a forward model for concentric spheres in closed form and show why the inverse problem is
   ill-posed: high spatial frequencies are attenuated almost to zero on the torso.
3. Solve the inverse problem with Tikhonov regularization and choose the regularization weight with
   the L-curve and the discrepancy principle (links to m07).
4. Run the same pipeline on an EDGAR dataset with a provided forward matrix, and compare the
   reconstruction with the measured heart-surface signals.
5. Measure accuracy with standard metrics (correlation, relative error, activation-time error,
   pacing-site localization error), and test sensitivity to noise and geometry error.
6. Explain the reported limits of clinical ECGI activation maps ([duchateau2019]).

Prerequisites: m02 (volume conduction), m07 (inverse problems) and m12 (the forward problem). Until
m07 exists, m32 carries the Tikhonov equations it needs (question 2).

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

ECGI estimates electrical activity on the heart from many electrodes on the body surface. The
forward step, from heart to body, is a well-behaved linear map. The inverse step is not: the torso
smooths away fine detail, so small noise can produce large errors unless the solution is
regularized. This capstone builds the pipeline twice, on spheres where everything is known and on
an EDGAR dataset where the heart was measured directly, and scores both.

### 2. From the field

Lessons tied to verified sources:

- ECGI has been applied in humans with a multielectrode vest and CT geometry to reconstruct heart-
  surface potentials, electrograms and isochrones ([ramanathan2004]).
- EDGAR was created so that different groups can test methods on shared data in a common format
  ([aras2015]).
- In a clinical comparison with invasive epicardial contact maps, agreement of ECGI activation maps
  was poor and varied between patients; lines of block and breakthrough sites were inaccurate, and
  artificial lines appeared in low-voltage regions ([duchateau2019]).

### 3. Derivations

Notation: $\boldsymbol{\varphi}_H$ heart-surface potentials, $\boldsymbol{\varphi}_B$ body-surface
potentials, $A$ forward (transfer) matrix, $\lambda$ regularization weight, $L$ regularization
operator, $s_i, \mathbf{u}_i, \mathbf{v}_i$ singular values and vectors of $A$, $r_H$, $r_T$ heart and
torso radii, $\rho = r_H/r_T$, $l$ spherical-harmonic degree.

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m32-forward | $\boldsymbol{\varphi}_B = A\,\boldsymbol{\varphi}_H + \mathbf{e}$ | Linear forward model with measurement noise $\mathbf{e}$ | exact | Numeric: on the sphere model $A$ matches the closed form below |
| eq-m32-sphere-transfer | $g_l = \dfrac{\varphi_l(r_T)}{\varphi_l(r_H)} = \dfrac{(2l+1)\,\rho^{\,l+1}}{(l+1)\,\rho^{\,2l+1} + l}$ | Potential transfer from a heart sphere to a no-flux torso sphere (homogeneous volume conductor) for degree $l$; $g_0 = 1$, and $g_l \approx 2\rho^{\,l+1}$ for large $l$ | exact | SymPy: solves Laplace's equation with the two boundary conditions; numeric: finite-difference check |
| eq-m32-tikhonov | $\hat{\boldsymbol{\varphi}}_H = \arg\min \lVert A\boldsymbol{\varphi}_H - \boldsymbol{\varphi}_B\rVert^2 + \lambda^2\lVert L\boldsymbol{\varphi}_H\rVert^2 = (A^\top A + \lambda^2 L^\top L)^{-1}A^\top\boldsymbol{\varphi}_B$ | Tikhonov-regularized inverse | exact | Numeric: normal-equation and SVD solutions agree; SymPy for the gradient condition |
| eq-m32-filter-factors | $\hat{\boldsymbol{\varphi}}_H = \sum_i f_i\,\dfrac{\mathbf{u}_i^\top\boldsymbol{\varphi}_B}{s_i}\,\mathbf{v}_i$, $f_i = \dfrac{s_i^2}{s_i^2 + \lambda^2}$ ($L = I$) | Regularization as a filter on singular components | exact | Numeric: matches eq-m32-tikhonov to machine precision |
| eq-m32-lambda | L-curve corner: maximum curvature of $\big(\log\lVert A\hat{\boldsymbol{\varphi}} - \boldsymbol{\varphi}_B\rVert, \log\lVert L\hat{\boldsymbol{\varphi}}\rVert\big)$; discrepancy: $\lVert A\hat{\boldsymbol{\varphi}} - \boldsymbol{\varphi}_B\rVert = \lVert\mathbf{e}\rVert$ | Two rules to choose $\lambda$ | simulation | Numeric: on synthetic problems both rules land near the error-minimizing $\lambda$ |
| eq-m32-metrics | $\mathrm{CC} = \dfrac{\operatorname{cov}(\hat\varphi, \varphi)}{\sigma_{\hat\varphi}\sigma_\varphi}$, $\mathrm{RE} = \dfrac{\lVert\hat{\boldsymbol\varphi} - \boldsymbol\varphi\rVert}{\lVert\boldsymbol\varphi\rVert}$, activation time $= \arg\min_t \dfrac{d\hat\varphi}{dt}$ | Standard accuracy metrics and activation from the steepest downstroke | exact | Numeric: perfect reconstruction gives CC = 1, RE = 0; known activation recovered |

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline.

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m32-d1 | Why the inverse is hard | radius ratio, noise level, regularization weight | $g_l$ vs degree on a log axis against the noise floor; Tikhonov filter factors; which degrees survive | exact |
| m32-d2 | Regularize it | noise, $\lambda$, rule (L-curve, discrepancy) | Reconstruction on a 2D annulus model (heart ring inside a torso ring) vs truth; the L-curve with the chosen corner | simulation |
| m32-d3 | Real heart, real torso | $\lambda$, time instant | Reconstructed vs measured heart-surface potentials and activation on an EDGAR geometry (precomputed by us) | see question 3 |

Assumptions to list under the demos: homogeneous torso, no lungs or other inhomogeneities, perfect
geometry and registration unless the learner adds error (d1, d2); for d3, the dataset's own forward
matrix and geometry, with their stated assumptions.

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: what ECGI activation maps can and cannot show today, from [ramanathan2004] and the clinical
comparison in [duchateau2019]. Descriptive only.

### 6. Visual summary and How experts think

- Visual summary: the pipeline as a block diagram (images → geometry → forward matrix → inverse →
  activation), with the main error source at each block. Badge: schematic.
- How experts think: "How much of this map is the data and how much is the regularizer?" Change
  $\lambda$ and the method; features that survive are more trustworthy than features that do not.

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including "why does noise
blow up without regularization?" and "what does the L-curve trade off?".

### 8. Code lab and Self-check

Lab: `labs/python/m32_lab.ipynb`, a guided project with automatic checks (Python only).

| Part | Milestone | Data |
| --- | --- | --- |
| A | Concentric-sphere forward model from spherical harmonics; check against eq-m32-sphere-transfer | Synthetic |
| B | SVD of the forward matrix; Picard plot; noise amplification without regularization | Synthetic |
| C | Tikhonov with L-curve and discrepancy rules; error vs $\lambda$ | Synthetic |
| D | Load an EDGAR dataset (geometry, forward matrix, torso and heart signals); register and check units | EDGAR |
| E | Reconstruct, compute activation times, compare with measured heart signals; CC, RE, activation-time error | EDGAR |
| F | Sensitivity: noise, removed leads, shifted heart position | EDGAR + synthetic perturbations |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. [aras2015] is in PubMed Central (license to check). All
reconstruction figures are our own.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| aras2015 | Aras K, Good W, Tate J, et al. Experimental Data and Geometric Analysis Repository—EDGAR. J Electrocardiol 2015;48(6):975–981. DOI 10.1016/j.jelectrocard.2015.08.008, PMID 26320369 | Verified (PubMed) |
| ramanathan2004 | Ramanathan C, Ghanem RN, Jia P, Ryu K, Rudy Y. Noninvasive electrocardiographic imaging for cardiac electrophysiology and arrhythmia. Nat Med 2004;10(4):422–428. DOI 10.1038/nm1011, PMID 15034569 | Verified (PubMed) |
| duchateau2019 | Duchateau J, et al. Performance and limitations of noninvasive cardiac activation mapping. Heart Rhythm 2019;16(3):435–442. DOI 10.1016/j.hrthm.2018.10.010, PMID 30385382 | Verified (PubMed) |
| edgarguide | EDGAR User's Guide, version 1.0 (2015). https://edgar.sci.utah.edu/images/docs/edgar-report.pdf | Official document; `@misc` with URL and access date |
| hansen1992 | Hansen PC. Analysis of discrete ill-posed problems by means of the L-curve. SIAM Rev 1992 | [unverified], not in PubMed; resolve the DOI in stage 2 |
| tikhonov | A primary or textbook source for Tikhonov regularization and the discrepancy principle (shared with m07) | [unverified], to find |
| cei2017 | The Consortium for ECG Imaging paper in PubMed Central (PMID 28451592) | [unverified], metadata to look up |

## Still to source (before stage 2)

Each is `TODO(source)` until found:

- EDGAR's terms on redistribution of downloaded data and of derived results (ask the EDGAR team if
  the guide stays silent)
- Which EDGAR dataset to use: one with measured heart-surface signals, torso signals, geometry and a
  provided forward matrix, with its own citation sentence
- Typical body-surface noise levels and electrode counts for d1/d2 defaults
- A radius ratio for the sphere model, or label it illustrative

## Glossary terms to add

electrocardiographic imaging (ECGI) · forward problem · inverse problem · transfer matrix ·
ill-posed problem · singular value decomposition · Tikhonov regularization · filter factor ·
L-curve · discrepancy principle · Picard plot · body surface potential map · registration

## Formula-sheet entries

eq-m32-forward · eq-m32-sphere-transfer · eq-m32-tikhonov · eq-m32-filter-factors · eq-m32-metrics

## Questions for the author

1. **Getting EDGAR data into CI:** EDGAR needs a personal account, and its terms do not mention
   redistribution. Options: (a) the lab downloads nothing, and the learner fetches the dataset with
   their own account (CI runs only the synthetic parts, with a documented exception to
   `EPML_REQUIRE_DATA`); (b) we ask the EDGAR team for permission to ship a small derived sample;
   (c) use a dataset that is also published elsewhere under an open license. Which do you prefer?
2. **Overlap with m07:** define Tikhonov, filter factors and the L-curve here (`eq-m32-*`) and move
   them to m07 later, or write m07 first?
3. **Badge for d3:** same question as m31: a real-data figure has no badge in CLAUDE.md §4.
4. **Formulation:** start with the potential-based formulation (heart-surface potentials) only, or
   also show an activation-based formulation?
