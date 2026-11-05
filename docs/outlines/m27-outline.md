# m27 outline · RF ablation biophysics and lesion metrics (power, force, time, impedance drop)

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

Scope note: this module explains the physics behind radiofrequency (RF) lesions and behind the
numbers a mapping system shows during an application. It does not recommend power, force, time or
index targets for patients (CLAUDE.md §2). Published target values appear only as study findings,
with their source.

## Learning goals

After this module a reader can:

1. Explain RF ablation as resistive (Joule) heating: current spreads from a small electrode, the
   current density falls with distance, and the heating falls even faster.
2. Write the bioheat equation and say what each term means: storage, conduction, the RF source and
   blood perfusion. Explain why cooling at the electrode (blood flow, irrigation) matters.
3. Link temperature to injury with two models: an isotherm (a temperature threshold) and an
   Arrhenius damage integral (a rate process). State what each ignores.
4. Model the electrical circuit (generator, electrode, tissue, blood, dispersive patch) and explain
   why impedance falls as tissue heats.
5. Define the lesion metrics a mapping system displays: energy, force–time integral and weighted
   indices that combine power, force and time. Say what each one integrates and what it leaves out.
6. Explain why every one of these numbers is a surrogate for the lesion, not a measurement of it.

Prerequisites: m02 (volume conduction) and m13 (catheter design, contact-force sensing). Until m13
exists, m27 includes a short recap of contact-force sensing.

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

An RF generator drives current from the catheter tip to a patch on the skin. Near the tip the
current is crowded into a small volume, so tissue heats there. Heat then spreads by conduction and
is carried away by blood. Tissue that stays hot enough for long enough dies and stops conducting.
Power, contact force, time and the fall in impedance are the inputs and clues a mapping system can
show; the lesion itself is never measured directly during the procedure.

### 2. From the field

Lessons tied to verified sources:

- In an isolated-tissue model, tissue temperature fell with distance from the electrode in a
  hyperbolic way, close to a derived thermodynamic model ([haines1989]).
- With the electrode–tissue interface temperature held constant, lesion radius grew in proportion to
  electrode radius ([haines1990]). This is the scaling the steady-state model in §3 predicts.
- In isolated guinea-pig papillary muscle, heating for 60 s caused reversible loss of excitability
  over a range of temperatures (42.7 to 51.3 °C) and irreversible loss at 50 °C or more
  ([nath1993]). A zone that is stunned but alive is one reason an acute map can differ from a late
  map.
- In a bench model with a moving tissue contact, the area under the contact-force curve (the
  force–time integral) tracked lesion size ([shah2010]).
- In an ex vivo model, the drop in local impedance during an application correlated with lesion size
  ([kawano2022]). Described generically; no vendor-specific claims.

### 3. Derivations

Notation: $I$ current (A), $\sigma$ electrical conductivity (S/m), $r_0$ electrode radius (m),
$r$ distance from the electrode centre (m), $J$ current density (A/m²), $q$ power density (W/m³),
$k$ thermal conductivity (W/(m·K)), $\rho$ density (kg/m³), $c$ specific heat (J/(kg·K)),
$\omega_b$ perfusion rate (1/s), $T_b$ blood/body temperature (°C), $F$ contact force (g, as
displayed clinically; N in the derivations), $P$ power (W).

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m27-current-density | $J(r) = \dfrac{I}{4\pi r^2}$, $r \ge r_0$ | Current density around a spherical electrode in an infinite homogeneous medium | exact | SymPy: flux through any sphere equals $I$; numeric: finite-volume solve |
| eq-m27-power-density | $q(r) = \dfrac{J^2}{\sigma} = \dfrac{I^2}{16\pi^2\sigma r^4}$ | Heating falls as $1/r^4$, so it is concentrated in a thin shell | exact | SymPy: $\int_{r_0}^\infty q\,4\pi r^2\,dr = I^2 R_s$ with eq-m27-spreading |
| eq-m27-spreading | $R_s = \dfrac{1}{4\pi\sigma r_0}$ (sphere); $R_s = \dfrac{1}{4\sigma a}$ (disk of radius $a$ on a half-space) | Spreading resistance near the electrode dominates the tissue part of the circuit | exact | SymPy for the sphere; numeric finite-difference check for the disk (Newman's result, source to verify) |
| eq-m27-bioheat | $\rho c\,\dfrac{\partial T}{\partial t} = \nabla\cdot(k\nabla T) + q - \omega_b\rho_b c_b\,(T - T_b)$ | Pennes bioheat equation: storage = conduction + RF source − perfusion loss | simulation | Numeric: solver converges to the steady state below; energy balance check |
| eq-m27-steady-temperature | $T(r) = T_b + \dfrac{A}{r} - \dfrac{I^2}{32\pi^2\sigma k\,r^2}$ | Steady state with the $1/r^4$ source, no perfusion, constant properties; $A$ set by the interface temperature | exact | SymPy: solves the radial ODE and boundary conditions; numeric: finite differences |
| eq-m27-isotherm | $r_L$ such that $T(r_L) = T_L$ | Lesion boundary as an isotherm; with the source-free part only, $r_L \propto r_0$ (matches [haines1990]) | exact | SymPy: scaling with $r_0$; numeric root finding |
| eq-m27-arrhenius | $\Omega(t) = \int_0^t A\, e^{-E_a/(R\,T(\tau))}\,d\tau$, injury where $\Omega \ge 1$ | Damage as a rate process: time at temperature, not peak temperature alone | approximate model | Numeric: constant-temperature case matches the closed form; $\Omega$ increases monotonically |
| eq-m27-diffusion-length | $\ell \approx \sqrt{4\alpha t}$, $\alpha = k/(\rho c)$ | How far heat spreads by conduction in time $t$; why lesions keep growing after the surface heats | approximate model | Numeric: 1D heat equation front position vs $\sqrt{t}$ |
| eq-m27-impedance | $Z \approx R_s\big(\sigma(T)\big) + R_{\text{blood}} + R_{\text{body}}$, $\sigma(T) \approx \sigma_0[1 + \alpha_\sigma (T - T_0)]$ | Impedance drop as heated tissue conducts better; a linear temperature model | approximate model | Numeric: impedance trace from the simulated temperature field |
| eq-m27-fti | $\mathrm{FTI} = \int_0^{t_a} F(t)\,dt$; $E = \int_0^{t_a} P(t)\,dt$ | Force–time integral and delivered energy | exact | Numeric: trapezoid integration of sampled traces |
| eq-m27-weighted-index | $\mathcal{I} = g\!\left(\int_0^{t_a} F(t)^{a}\,P(t)^{b}\,dt\right)$ | Generic weighted index: a monotone function $g$ of a weighted integral. Commercial formulas are not reproduced | approximate model | Numeric: index is monotone in $F$, $P$ and $t$; ranks simulated lesions (Spearman) |

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline and compute in the browser.

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m27-d1 | Where the heat is made | current, electrode radius, conductivity | $J(r)$ and $q(r)$ on log axes; fraction of power deposited within a given distance of the tip | exact |
| m27-d2 | Lesion growth | power, duration, perfusion, electrode cooling (convective coefficient), contact depth | Temperature field over time (axisymmetric finite differences), the isotherm and Arrhenius $\Omega = 1$ contours, and the impedance trace | simulation |
| m27-d3 | Same metric, different lesion | force trace shape (steady, variable, intermittent), power | FTI, energy and a generic weighted index next to the lesion depth from the d2 model; shows two histories with equal FTI and unequal lesions | approximate model |

Assumptions to list under the demos: homogeneous, isotropic tissue with constant properties except
$\sigma(T)$ in d2; no tissue boiling or char; contact modelled as electrode depth and a coupling
factor; one fixed electrode geometry. d2 names its solver (explicit finite differences on an
axisymmetric grid), grid spacing and time step; it is precomputed only if it cannot run in the
browser within the time budget.

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: what contact force and lesion indices have been linked to in studies. In TOCCATA, a small
study of paroxysmal AF ablation with a force-sensing catheter, all patients treated with a low
average contact force had recurrences ([reddy2012]). A later study related segment-level values of a
weighted index and of FTI to pulmonary-vein reconnection at a planned repeat study ([das2017]). The
section describes these findings and their limits; it gives no targets.

### 6. Visual summary and How experts think

- Visual summary: circuit diagram (generator, tip, tissue, blood, patch) beside the radial profiles
  of $J$, $q$ and $T$. Badge: schematic.
- How experts think: "Which part of the circuit is the tissue, and where does the heat go?" Power
  set at the generator is not power in the tissue; a number on the screen is a model's estimate.

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including "why does
impedance fall during an application?" and "why can two applications with the same FTI give
different lesions?".

### 8. Code lab and Self-check

Lab: `labs/python/m27_lab.ipynb` (Python only; Part V has no Octave copy).

| Part | Task | Data |
| --- | --- | --- |
| A | Spreading resistance and the $1/r^4$ heating profile; check the power balance numerically | Synthetic |
| B | 1D spherical bioheat solver (method of lines with `scipy.integrate.solve_ivp`); verify against eq-m27-steady-temperature | Synthetic |
| C | Lesion radius from the isotherm and from the Arrhenius integral; sensitivity to perfusion and electrode cooling | Synthetic |
| D | Impedance drop from the temperature field with a linear $\sigma(T)$ | Synthetic |
| E | Metrics vs lesion: compute energy, FTI and a generic weighted index for many simulated applications; rank correlation with lesion depth | Synthetic |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. Candidate: [berjano2006] is open access in BioMedical
Engineering OnLine (license to check) and reviews RF modelling.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| pennes1948 | Pennes HH. Analysis of tissue and arterial blood temperatures in the resting human forearm. J Appl Physiol 1948;1(2):93–122. DOI 10.1152/jappl.1948.1.2.93, PMID 18887578 | Verified (PubMed) |
| haines1989 | Haines DE, Watson DD. Tissue heating during radiofrequency catheter ablation: a thermodynamic model and observations in isolated perfused and superfused canine right ventricular free wall. Pacing Clin Electrophysiol 1989;12(6):962–976. DOI 10.1111/j.1540-8159.1989.tb05034.x, PMID 2472624 | Verified (PubMed) |
| haines1990 | Haines DE, Watson DD, Verow AF. Electrode radius predicts lesion radius during radiofrequency energy heating. Validation of a proposed thermodynamic model. Circ Res 1990;67(1):124–129. DOI 10.1161/01.res.67.1.124, PMID 2364487 | Verified (PubMed) |
| nath1993 | Nath S, et al. (with Haines DE). Cellular electrophysiological effects of hyperthermia on isolated guinea pig papillary muscle. Implications for catheter ablation. Circulation 1993;88(4 Pt 1):1826–1831. DOI 10.1161/01.cir.88.4.1826, PMID 8403328 | Verified (PubMed) |
| henriques1947 | Henriques FC, Moritz AR. Studies of thermal injury: I. The conduction of heat to and through skin and the temperatures attained therein. Am J Pathol 1947;23(4):530–549. PMID 19970945 (no DOI) | Verified (PubMed). The Arrhenius rate paper of the series (part V, Arch Pathol 1947) is not in PubMed: [unverified] |
| moritz1947 | Moritz AR, Henriques FC. Studies of thermal injury: II. The relative importance of time and surface temperature in the causation of cutaneous burns. Am J Pathol 1947;23(5):695–720. PMID 19970955 (no DOI) | Verified (PubMed) |
| pearce2013 | Pearce JA. Comparative analysis of mathematical models of cell death and thermal damage processes. Int J Hyperthermia 2013;29(4):262–280. DOI 10.3109/02656736.2013.786140, PMID 23738695 | Verified (PubMed); source for the limits of Arrhenius models at hyperthermic temperatures |
| berjano2006 | Berjano EJ. Theoretical modeling for radiofrequency ablation: state-of-the-art and challenges for the future. Biomed Eng Online 2006;5:24. DOI 10.1186/1475-925X-5-24, PMID 16620380 | Verified (PubMed) |
| shah2010 | Shah DC, et al. Area under the real-time contact force curve (force-time integral) predicts radiofrequency lesion size in an in vitro contractile model. J Cardiovasc Electrophysiol 2010;21(9):1038–1043. DOI 10.1111/j.1540-8167.2010.01750.x, PMID 20367658 | Verified (PubMed) |
| reddy2012 | Reddy VY, et al. The relationship between contact force and clinical outcome during radiofrequency catheter ablation of atrial fibrillation in the TOCCATA study. Heart Rhythm 2012;9(11):1789–1795. DOI 10.1016/j.hrthm.2012.07.016, PMID 22820056 | Verified (PubMed) |
| das2017 | Das M, et al. Ablation index, a novel marker of ablation lesion quality: prediction of pulmonary vein reconnection at repeat electrophysiology study and regional differences in target values. Europace 2017;19(5):775–783. DOI 10.1093/europace/euw105, PMID 27247002 | Verified (PubMed) |
| kawano2022 | Kawano D, et al. Time dependency in the radiofrequency lesion formation for a local impedance guided catheter in an ex vivo experimental model. J Arrhythm 2022;38(6):1080–1087. DOI 10.1002/joa3.12789, PMID 36524038 | Verified (PubMed) |

## Still to source (before stage 2)

Every default demo parameter needs a citation (CLAUDE.md §5). Each is `TODO(source)` until found:

- Electrical and thermal properties of myocardium and blood: $\sigma$, $k$, $\rho$, $c$ (a published
  property table, for example the IT'IS tissue database, license to check, or [berjano2006])
- Temperature coefficient of tissue conductivity $\alpha_\sigma$ (%/°C)
- Arrhenius coefficients $A$ and $E_a$ for myocardium
- Perfusion rate of myocardium, and convective coefficients for blood flow and irrigation at the tip
- Generator frequency range of clinical RF systems ([haines1990] used 500 kHz in its setup; a
  general source is still needed)
- Newman's spreading resistance of a disk electrode on a half-space (original paper to look up)
- Any public description of a commercial weighted index (patent or peer-reviewed paper), if the
  author wants one shown; otherwise only the generic form is used

## Glossary terms to add

radiofrequency (RF) ablation · Joule heating · current density · spreading resistance · dispersive
electrode · bioheat equation · perfusion · irrigation · isotherm · Arrhenius damage integral ·
thermal diffusivity · impedance drop · contact force · force–time integral (FTI) · lesion index ·
transmurality · steam pop (if used, with a source)

## Formula-sheet entries

eq-m27-current-density · eq-m27-power-density · eq-m27-spreading · eq-m27-bioheat ·
eq-m27-steady-temperature · eq-m27-arrhenius · eq-m27-diffusion-length · eq-m27-fti

## Questions for the author

1. **Weighted indices:** show only the generic form (recommended), or also a commercial formula if
   a public patent or paper gives it in full?
2. **Depth of the thermal model:** is a 1D spherical solver in the lab plus a 2D axisymmetric demo
   enough, or do you want a 3D finite-element example (would need an extra dependency such as
   scikit-fem)?
3. **Cryoablation:** out of scope for m27 (title names RF only), or a short comparison box?
4. **Clinical correlate:** TOCCATA and the ablation-index study are both small; add a larger
   randomized trial of force-guided ablation in stage 2, or keep the correlate to these two?
