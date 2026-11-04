# m30 outline · Capstone: build a mini mapping system on a simulated atrium

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

Release: v0.1 (MVP), together with m03, m04, m20, m22, m23, m24 and m25 (`docs/curriculum.md`).

Capstone format: a capstone has the same nine template sections as any module, but its derivations
are short (it reuses earlier modules) and most of the work is in the code lab, which is a guided
project with automatic checks at each milestone.

## Learning goals

After this capstone a reader can:

1. Build a ground-truth atrium: a surface mesh, an activation sequence with a known pacing site,
   a scar region that does not conduct and a zone of slow conduction.
2. Simulate what a mapping system sees: a roving catheter with localization noise and respiratory
   motion, and unipolar and bipolar electrograms at each acquired point.
3. Annotate local activation time (LAT) and voltage at each point (links to m22, m23).
4. Turn sparse points into maps: project points onto the surface, interpolate LAT and voltage, draw
   isochrones and estimate conduction velocity (links to m20, m24, m25).
5. Measure the map against the truth and explain each error source: too few points, localization
   error, annotation error and interpolation (links to m26).
6. Store the session in an open format (links to m34) and write a short validation report.

Prerequisites: m03, m04, m20, m22–m26. m30 can be read before them (see question 1).

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

A mapping system turns many small measurements into one picture: where the catheter was, what it
recorded and when the tissue under it activated. In this capstone you build each stage on a
simulated atrium where the true activation is known, so every map you make can be scored. The lesson
is that a map is an estimate with errors you can name and measure.

### 2. From the field

Lessons tied to verified sources:

- Activation-time annotation and conduction-velocity estimation have many competing methods, and
  sparse, uneven and uncertain data make velocity hard to compute ([cantwell2015]).
- Clinical exports are large and in proprietary formats; an open structure makes mapping data
  shareable and analysable ([williams2021]).
- Bipolar voltage depends on electrode size, spacing and orientation to the wavefront, not on tissue
  alone ([anter2016]; [takigawa2018]); a capstone map should show this effect, not hide it.
- Scar thresholds in voltage maps are conventions from specific studies (for example the ventricular
  bipolar thresholds in [marchlinski2000]); atrial thresholds need their own source.

### 3. Derivations

Notation: $S$ atrial surface, $T(\mathbf{x})$ activation time (ms), $v(\mathbf{x})$ conduction
velocity (m/s), $\mathbf{p}_i$ acquired point positions (mm), $T_i$ annotated LATs (ms), $N$ number
of points, $d(\cdot,\cdot)$ geodesic distance on $S$ (mm).

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m30-eikonal | $v(\mathbf{x})\,\lvert\nabla_S T(\mathbf{x})\rvert = 1$, $T(\mathbf{x}_0) = t_0$ | Ground-truth activation from the eikonal equation on the surface; scar has $v = 0$ | simulation | Numeric: on a flat sheet $T = \lvert\mathbf{x}-\mathbf{x}_0\rvert/v$; on a sphere $T$ = geodesic distance / $v$; error falls with mesh size |
| eq-m30-localization | $\hat{\mathbf{p}}_i = \mathbf{p}_i + \boldsymbol{\varepsilon}_i + \mathbf{d}(t_i)$ | Measured position = true position + random localization error + respiratory displacement | approximate model | Numeric: error statistics of simulated positions match the inputs |
| eq-m30-projection | $\mathbf{p}_i^{S} = \arg\min_{\mathbf{y}\in S} \lVert \mathbf{y} - \hat{\mathbf{p}}_i \rVert$ | Points off the surface are projected onto it before interpolation | exact | Numeric: projection of points on the surface is the identity; distance is minimal |
| eq-m30-idw | $\hat T(\mathbf{x}) = \dfrac{\sum_i w_i T_i}{\sum_i w_i}$, $w_i = d(\mathbf{x}, \mathbf{p}_i)^{-p}$ | Inverse-distance interpolation with geodesic distance (a baseline; m24 covers better methods) | exact | Numeric: reproduces data at the points; constant data stays constant |
| eq-m30-cv-plane | $\mathbf{v} = \dfrac{\nabla T}{\lvert\nabla T\rvert^{2}}$ from a local plane fit $T \approx a + \mathbf{g}\cdot\mathbf{x}$ | Conduction velocity vector from the activation gradient ([cantwell2015]) | exact | Numeric: recovers speed and direction of a plane wave exactly |
| eq-m30-errors | $\mathrm{RMSE} = \sqrt{\dfrac{1}{M}\sum_{j=1}^{M}\big(\hat T(\mathbf{x}_j) - T(\mathbf{x}_j)\big)^2}$; fill distance $h = \max_{\mathbf{x}\in S}\min_i d(\mathbf{x}, \mathbf{p}_i)$ | Map error on mesh vertices, and how well the points cover the surface | exact | Numeric: RMSE of a perfect map is 0; $h$ shrinks as points are added |

Each derivation subsection ends with a **Key takeaways** list. Equations owned by m20–m26 are cited
from those modules once they exist, not repeated.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline. Ground truth is precomputed (target
≤ 2 MB per demo).

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m30-d1 | Map it yourself | click to acquire points, localization noise, respiration, interpolation method, voltage threshold | The simulated atrium, acquired points, the electrogram at the last point, the growing LAT and voltage maps, and the truth for comparison | simulation |
| m30-d2 | How many points? | point count, acquisition pattern (random, systematic, clustered), noise | LAT RMSE, fill distance and missed slow-conduction zone vs number of points (precomputed curves) | simulation |
| m30-d3 | Same tissue, different voltage | electrode spacing, wavefront direction, threshold | Bipolar voltage map over the same scar and slow zone with different catheter settings | approximate model |

Assumptions to list under the demos: eikonal activation with isotropic velocity and a sharp scar
border (no partial conduction); electrograms from the m03 model; Gaussian localization error and
sinusoidal respiratory motion; no catheter-induced ectopy or contact loss unless toggled.

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: why the same atrium can produce different maps. Point density, annotation rules and voltage
thresholds are choices; each changes what the map shows. Sources for clinical point density and
atrial voltage thresholds are still to find (see below). The section describes measurement effects,
not procedures.

### 6. Visual summary and How experts think

- Visual summary: the full chain (truth → catheter → electrogram → annotation → interpolation →
  map → error) as one diagram, with the module that owns each step. Badge: schematic.
- How experts think: "What would this map look like if I were wrong?" Score every map against a
  known truth before trusting it on a patient whose truth is unknown.

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including a system-design
question ("sketch the data flow of a mapping system from amplifier to map") and error-budget
questions.

### 8. Code lab and Self-check

Lab: `labs/python/m30_lab.ipynb`, a guided project with an automatic check at each milestone
(Python only).

| Part | Milestone | Data |
| --- | --- | --- |
| A | Build the atrium: mesh (`pyvista`), pacing site, scar, slow zone; solve the eikonal ground truth | Synthetic |
| B | Roving catheter: path, localization error, respiration, contact flag | Synthetic |
| C | Electrograms at each point: unipolar and bipolar from the m03 model, noise and far-field | Synthetic |
| D | Annotation: LAT against a reference, voltage as peak-to-peak; compare with the truth | Synthetic |
| E | Maps: projection, interpolation, isochrones; LAT RMSE and fill distance | Synthetic |
| F | Conduction velocity and slow-zone detection; how many points are enough | Synthetic |
| G | Save the session in an OpenEP-style structure (m34) and write a one-page validation report | Synthetic |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. Candidate: figures in [williams2021] (open access, license to
check) and [cantwell2015] (license to check).

## Sources

| Key | Source | Status |
| --- | --- | --- |
| cantwell2015 | Cantwell CD, Roney CH, Ng FS, Siggers JH, Sherwin SJ, Peters NS. Techniques for automated local activation time annotation and conduction velocity estimation in cardiac mapping. Comput Biol Med 2015;65:229–242. DOI 10.1016/j.compbiomed.2015.04.027, PMID 25978869 | Verified (PubMed) |
| sethian1996 | Sethian JA. A fast marching level set method for monotonically advancing fronts. Proc Natl Acad Sci USA 1996;93(4):1591–1595. DOI 10.1073/pnas.93.4.1591, PMID 11607632 | Verified (PubMed) |
| mitchell2003 | Mitchell CC, Schaeffer DG. A two-current model for the dynamics of cardiac membrane. Bull Math Biol 2003;65(5):767–793. DOI 10.1016/S0092-8240(03)00041-7, PMID 12909250 | Verified (PubMed); only if the reaction–diffusion option is used (question 2) |
| williams2021 | OpenEP data format. Already in `references.bib` | Verified |
| anter2016, takigawa2018, marchlinski2000 | Bipolar voltage and thresholds. Already in `references.bib` | Verified |
| heil2023 | Left atrial conduction velocities. Already in `references.bib` | Verified; candidate source for velocity defaults |

## Still to source (before stage 2)

Each is `TODO(source)` until found:

- Fast marching on triangulated surfaces (Kimmel and Sethian, 1998, to look up), or a heat-method
  geodesic source if m06 uses it
- A realistic atrial geometry with an open license (OpenEP example data: license to check), or
  keep a simplified shape
- Atrial conduction velocity defaults: check whether [heil2023] gives values usable as defaults
- Localization error and respiratory displacement amplitudes of clinical systems (m16–m19 need these
  too)
- Atrial bipolar voltage thresholds used in studies, with their electrode settings
- Typical point counts in clinical atrial maps

## Glossary terms to add

ground truth · eikonal equation · fast marching · roving catheter · point projection · fill
distance · inverse distance weighting · isochrone · validation report

## Formula-sheet entries

eq-m30-eikonal · eq-m30-idw · eq-m30-cv-plane · eq-m30-errors

## Questions for the author

1. **Order of work:** m30 depends on m20 and m22–m26, none written yet. Write m30 now with its own
   minimal implementations (and refactor later), or write m20–m26 first? Both are in v0.1.
2. **Ground truth model:** eikonal only (fast, simple, recommended), or also a Mitchell–Schaeffer
   reaction–diffusion option for realistic electrograms near scar?
3. **3D in the browser:** d1 in 3D needs three.js vendored in `vendor/` (MIT, pinned). Approve, or
   start with an unfolded 2D atrium?
4. **Geometry:** a simplified analytic atrium (sphere with vein openings) we generate ourselves, or a
   real geometry from OpenEP's example data if its license allows?
