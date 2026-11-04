# m28 outline · Pulsed field ablation: electroporation and what it changes for mapping

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

Scope note: this module explains the physics of electroporation and what pulsed field ablation (PFA)
changes in the signals and maps a mapping system records. It does not recommend waveforms, catheters
or workflows for patients (CLAUDE.md §2). Vendor systems are described generically from public
sources only.

## Learning goals

After this module a reader can:

1. Explain electroporation: an external electric field induces a voltage across the cell membrane;
   above a threshold, the membrane becomes permeable, reversibly or irreversibly.
2. Derive the induced transmembrane voltage on a spherical cell (Schwan's equation) and its
   charging time constant, and explain why cell shape and orientation matter (spheroidal cells).
3. Compute the electric field around simple electrode configurations from Laplace's equation (links
   to m02), and draw the lesion boundary as an iso-field contour at a threshold field.
4. Compare the lesion-size scaling of PFA (set by the field) with RF (set by heat, m27), and
   estimate the Joule heating that a pulse train still causes.
5. Explain what PFA changes for mapping: signals can disappear right after an application without a
   full-thickness lesion; a stunned zone can recover; and maps taken at different times can differ.
6. Read published thresholds critically: in vitro values depend on cell type, waveform and pulse
   number, and do not transfer directly to tissue.

Prerequisites: m02 (volume conduction), m03 (electrograms) and m27 (RF biophysics, for comparison).

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

PFA delivers very short, high-voltage pulses. The field they create in tissue charges cell
membranes; where the induced membrane voltage is high enough, pores form and the cell may die.
The lesion is shaped by where the field exceeds a threshold, not by where tissue gets hot. For
mapping this matters twice: the field map, not a heat map, predicts the lesion; and electrograms
can vanish acutely in tissue that later recovers.

### 2. From the field

Lessons tied to verified sources:

- Electroporation is governed mainly by the local field and by waveform-dependent lethal thresholds,
  not by generator voltage alone; pulse shape, width, number and duty cycle all matter; high-voltage
  pulses can also cause Joule heating, electrochemical effects and bubbles ([anic2026]).
- Electrograms disappear promptly after PFA applications in the pulmonary veins, but in a beating
  heart model lesion depth still depended on contact and on repeating applications ([dibiase2024]).
- In one clinical study with a multi-spline catheter, a low unipolar voltage marked a stable "core"
  lesion, while a surrounding "halo" with higher voltage recovered ([na2026]).
- In vitro, the field needed to kill cells differed between cell types and with pulse number
  ([avazzadeh2021]; [avazzadeh2022]). These are bench values, not tissue thresholds.
- In a multicentre registry, mapping after single-shot PFA found residual pulmonary-vein
  connections in some veins ([mills2025]).

### 3. Derivations

Notation: $E$ applied field magnitude (V/m), $R$ cell radius (m), $\theta$ angle between the field
and the point on the membrane, $\Delta\Psi_m$ induced transmembrane voltage (V), $\tau_m$ membrane
charging time constant (s), $C_m$ membrane capacitance per area (F/m²), $\rho_i$, $\rho_e$ intra-
and extracellular resistivity (Ω·m), $V$ electrode voltage (V), $r_0$ electrode radius (m),
$E_{\text{th}}$ threshold field (V/m), $\sigma$ tissue conductivity (S/m).

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m28-schwan | $\Delta\Psi_m(\theta) = \tfrac{3}{2}\,E\,R\cos\theta$ | Steady-state induced voltage on a spherical cell with a non-conducting membrane; largest at the poles facing the electrodes | exact | SymPy: the exterior potential $-E\left(r + \frac{R^3}{2r^2}\right)\cos\theta$ satisfies Laplace's equation and the no-flux condition at $r = R$ |
| eq-m28-charging | $\Delta\Psi_m(\theta, t) = \tfrac{3}{2}\,E\,R\cos\theta\left(1 - e^{-t/\tau_m}\right)$, $\tau_m = R\,C_m\left(\rho_i + \tfrac{\rho_e}{2}\right)$ | First-order membrane charging; pulses much shorter than $\tau_m$ charge the membrane only partly | exact | Numeric: lumped RC model against the closed form; source for $\tau_m$ to verify ([kotnik2019]) |
| eq-m28-spheroid | $\Delta\Psi_m = f_s\,E\,R\cos\theta$, shape factor $f_s$ for prolate and oblate spheroids | Elongated cells (like cardiomyocytes) feel a different voltage depending on their orientation to the field | exact | Numeric: $f_s \to 3/2$ for a sphere; form to be copied from [kotnik2000] in stage 2 |
| eq-m28-field-sphere | $\varphi(r) = V\,\dfrac{r_0}{r}$, $E(r) = V\,\dfrac{r_0}{r^2}$ | Field around an isolated spherical electrode with the return far away | exact | SymPy: Laplace in spherical symmetry; numeric: finite-difference Laplace solve |
| eq-m28-lesion-radius | $r_L = \sqrt{\dfrac{V\,r_0}{E_{\text{th}}}}$ | Iso-field lesion radius for the sphere model; grows as $\sqrt{V}$, unlike the RF isotherm | exact | SymPy; numeric root finding on the finite-difference field |
| eq-m28-bipolar | $\varphi(\mathbf{x}) \approx V_1\dfrac{r_0}{\lvert\mathbf{x}-\mathbf{x}_1\rvert} + V_2\dfrac{r_0}{\lvert\mathbf{x}-\mathbf{x}_2\rvert}$ | Superposition for two small, well-separated electrodes (bipolar pair) | approximate model | Numeric: error against a finite-difference solve as separation shrinks |
| eq-m28-joule | $\Delta T \le \dfrac{\sigma E^2\, t_{\text{on}}}{\rho\,c}$ | Adiabatic upper bound on heating for total pulse on-time $t_{\text{on}}$; shows why PFA is "largely" rather than fully non-thermal | exact | Numeric: matches an explicit heat-equation run with conduction switched off |

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline and compute in the browser.

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m28-d1 | Charging a cell membrane | field strength, cell radius, pulse width, time constant, threshold | Induced voltage around the cell (polar plot) over time; which part of the membrane crosses threshold first | exact |
| m28-d2 | Field, threshold and lesion | electrode layout (monopolar, bipolar pair), voltage, threshold, tissue distance | Field magnitude from a 2D finite-difference Laplace solve, the iso-field lesion contour, and the m27 isotherm for comparison | simulation |
| m28-d3 | What the map sees after PFA | time after application, recovery time constant, core and halo sizes | Synthetic unipolar and bipolar voltage maps over a lesion with a permanent core and a recovering halo; the acute map vs the late map | approximate model |

Assumptions to list under the demos: non-conducting membrane and spherical or spheroidal cells
(d1); homogeneous tissue and blood with fixed conductivities, quasi-static field (d2); a two-zone
lesion with exponential recovery, and electrogram amplitudes from the m03 model (d3).

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: PFA in trials and in the mapping lab. In ADVENT, a randomized trial in drug-refractory
paroxysmal AF, PFA was noninferior to conventional thermal ablation for the primary efficacy end
point at 1 year ([reddy2023]). Mapping studies then asked what acute signal loss means for lesion
durability ([dibiase2024]; [na2026]) and where residual connections remain ([mills2025]). The
section describes these findings only.

### 6. Visual summary and How experts think

- Visual summary: side-by-side panels, RF (heat source, isotherm) and PFA (field, iso-field
  contour), with the same electrode. Badge: schematic.
- How experts think: "What does an empty electrogram prove?" Silence right after PFA is a
  necessary sign, not proof of a lasting lesion; time and contact change the answer.

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including "why does lesion
radius grow as the square root of voltage in the sphere model?" and "why can a voltage map taken
right after PFA overstate the lesion?".

### 8. Code lab and Self-check

Lab: `labs/python/m28_lab.ipynb` (Python only).

| Part | Task | Data |
| --- | --- | --- |
| A | Schwan's equation: compare the closed form with a numerical solution around a cell (axisymmetric finite differences) | Synthetic |
| B | Field around monopolar and bipolar layouts with a sparse Laplace solver (`scipy.sparse`); lesion contours at several thresholds | Synthetic |
| C | Scaling: lesion size vs voltage for PFA (field threshold) and vs power for RF (m27 isotherm) | Synthetic |
| D | Joule heating per pulse train: adiabatic bound vs a heat-equation run | Synthetic |
| E | Acute vs late voltage maps over a two-zone lesion; how the choice of map time changes measured lesion area | Synthetic |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. Candidate: [anic2026] is in PubMed Central (license to
check) and has engineering figures on field distribution and waveform design.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| kotnik2000 | Kotnik T, Miklavčič D. Analytical description of transmembrane voltage induced by electric fields on spheroidal cells. Biophys J 2000;79(2):670–679. DOI 10.1016/S0006-3495(00)76325-9, PMID 10920001 | Verified (PubMed) |
| kotnik2019 | Kotnik T, et al. Membrane electroporation and electropermeabilization: mechanisms and models. Annu Rev Biophys 2019;48:63–91. DOI 10.1146/annurev-biophys-052118-115451, PMID 30786231 | Verified (PubMed) |
| anic2026 | Anić A, et al. Pulsed field ablation: from concepts to technology. Europace 2026;28(Suppl 2):ii18–ii31. DOI 10.1093/europace/euag205, PMID 42905915 | Verified (PubMed); two authors list an industry affiliation, noted when cited |
| avazzadeh2021 | Avazzadeh S, et al. Establishing irreversible electroporation electric field potential threshold in a suspension in vitro model for cardiac and neuronal cells. J Clin Med 2021;10(22):5443. DOI 10.3390/jcm10225443, PMID 34830725 | Verified (PubMed) |
| avazzadeh2022 | Avazzadeh S, et al. Establishing electroporation thresholds for targeted cell specific cardiac ablation in a 2D culture model. J Cardiovasc Electrophysiol 2022;33(9):2050–2061. DOI 10.1111/jce.15641, PMID 35924470 | Verified (PubMed) |
| reddy2023 | Reddy VY, et al. Pulsed field or conventional thermal ablation for paroxysmal atrial fibrillation (ADVENT). N Engl J Med 2023;389(18):1660–1671. DOI 10.1056/NEJMoa2307291, PMID 37634148 | Verified (PubMed) |
| dibiase2024 | Di Biase L, et al. Application repetition and electrode-tissue contact result in deeper lesions using a pulsed-field ablation circular variable loop catheter. Europace 2024;26(9):euae220. DOI 10.1093/europace/euae220, PMID 39150065 | Verified (PubMed) |
| na2026 | Na J, et al. Unipolar voltage mapping to predict lesion durability during pulsed field ablation. Heart Rhythm 2026;23(8):e1397–e1407. DOI 10.1016/j.hrthm.2026.01.025, PMID 41581848 | Verified (PubMed) |
| mills2025 | Mills MT, et al. Characterization of acute residual pulmonary vein connections using electroanatomic mapping during pulsed-field ablation of atrial fibrillation. Heart Rhythm 2025;22(12):3140–3148. DOI 10.1016/j.hrthm.2025.06.037, PMID 40582685 | Verified (PubMed) |
| nakagawa2025 | Nakagawa H, et al. Real-time prediction of irreversible lesion size during pulsed field ablation: prospective validation of a novel ablation index based on contact force and number of applications in a swine beating heart model. Circ Arrhythm Electrophysiol 2025;18(12):e013911. DOI 10.1161/CIRCEP.125.013911, PMID 41328568 | Verified (PubMed); optional, for the link back to m27 metrics |
| badertscher2024 | Badertscher P, et al. Role of 3D electro-anatomical mapping on procedural characteristics and outcomes in pulsed-field ablation for atrial fibrillation. Europace 2024;26(4). DOI 10.1093/europace/euae075, PMID 38525649 | Verified (PubMed); abstract not available in PubMed, full text to read before use |

## Still to source (before stage 2)

Each is `TODO(source)` until found:

- Membrane capacitance per area and intra-/extracellular resistivities for cardiomyocytes (for
  $\tau_m$), and typical cardiomyocyte dimensions (for the spheroid model)
- Tissue and blood conductivities at the frequencies in a PFA pulse, and their change during
  electroporation (conductivity rises as membranes open)
- A tissue-level (in vivo) irreversible-electroporation threshold for myocardium, with its waveform
- Typical PFA pulse widths, amplitudes and train lengths (public 510(k) or PMA summaries, or
  peer-reviewed papers), described generically
- Whether PFA pulses disturb impedance-based catheter localization or electrogram recording during
  delivery (a primary source is needed before the module says anything about it)
- Recovery time course of reversibly electroporated (stunned) myocardium

## Glossary terms to add

pulsed field ablation (PFA) · electroporation · electropermeabilization · irreversible
electroporation · induced transmembrane voltage · Schwan's equation · membrane charging time ·
monophasic and biphasic pulse · iso-field contour · stunning (reversible injury) · single-shot
catheter · lesion durability

## Formula-sheet entries

eq-m28-schwan · eq-m28-charging · eq-m28-field-sphere · eq-m28-lesion-radius · eq-m28-joule

## Questions for the author

1. **Spheroidal cells:** derive the full spheroid formula, or quote it from [kotnik2000] and test
   only its sphere limit?
2. **3D vs 2D fields:** a 2D finite-difference field is enough for intuition; do you want an
   axisymmetric or 3D solve for quantitative lesion sizes?
3. **Industry-authored sources:** [anic2026] is a useful engineering review with authors from a PFA
   manufacturer. Cite it with a note, or prefer independent sources where possible?
4. **Clinical correlate scope:** keep to ADVENT plus the mapping studies, or add the other pivotal
   trials (each from its published paper)?
