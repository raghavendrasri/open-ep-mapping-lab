# Part VIII overview · Imaging in electrophysiology

Curriculum proposal for Part VIII (modules m48–m55). Nothing here is course text yet. This file sets out
why imaging belongs in the course, what each modality is used for in EP, and each module's scope,
planned equations, demos, labs and sources, so that the author can approve the plan before any stage-1
outline is written. `docs/curriculum.md` is not changed until the module list is approved.

Status: **module list approved by the author on 2026-11-11** (answers below); module content is built stage by
stage, one pull request per module, starting with m49 and m50.

### Author decisions (2026-11-11)

1. **Eight modules,** m48–m55, as listed.
2. **Registration stays where it is.** Part VIII does not re-derive registration mathematics; it links to the
   existing modules (the author wrote "stay in m40"; m21 is where landmark and ICP registration are listed in
   the curriculum, and m40 covers segmentation and what boundary errors do to registration).
3. **Ultrasound stays lightweight** in m50: only what ICE needs, written from scratch.
4. **Open sources only:** synthetic phantoms from our own code and openly licensed data sets; no proprietary
   data or software.
5. **Review:** modules stay `draft` with clinical review pending; an imaging collaborator will review them later.
   No new reviewer role for now.
6. **Order and path:** build m49 and m50 first; add an "Imaging in EP" learning path.

Not yet decided: the release that carries Part VIII.

## Why a Part VIII

A mapping system knows where its catheter is and what the electrograms say. It does not see the wall, the
scar inside it, the esophagus behind it, a thrombus in the appendage, or a pericardial effusion. Imaging
answers those questions, before, during and after a procedure:

- **Before:** anatomy for planning, substrate (fibrosis and scar), thrombus, neighbouring structures.
- **During:** catheter and sheath position, transseptal access, contact, complications, fusion with the map.
- **After:** what the energy did (lesions and gaps), complications, follow-up of inflammation or infection.

The course already uses images in two places: m21 (registering CT and MRI to the map) and m40 (AI that
segments images). Neither explains how the images are formed, what they can resolve, what they cost in
radiation or time, or what the evidence for each use is. Part VIII does that, one modality per module.

Fluoroscopy is still central: a position paper in Europace called it the cornerstone of imaging in most
interventional EP procedures, and estimated that an operator's lifetime attributable excess cancer risk may
be around 1 in 100 [heidbuchel2014]. Much of current practice is about doing more with less of it, using
mapping systems and intracardiac echo [debreceni2023; zormpas2023]. That trade-off is what Part VIII teaches
engineers and clinicians to reason about.

**Who it is for:**

- **Engineers** in EP and imaging companies: image formation, resolution and noise, registration accuracy,
  radiation dose, MRI compatibility, data formats.
- **Clinical mapping specialists and EP fellows:** what each modality can and cannot show, and how strong the
  evidence is for each use.
- **Researchers** building digital twins and AI on images (links to m33, m40, m42).

**Ground rules** (the same as Parts I–VII, plus three for imaging):

- Education only. Clinical correlates describe what studies found and stay `pending clinical review`. No
  advice on which imaging a patient should have.
- Report results as the cited study reports them, with its design; observational comparisons are not
  equivalence.
- Vendor systems are described generically, from public sources only.
- **Radiation numbers** (doses, reference levels, risk estimates) come only from cited sources; lab and demo
  settings that are not sourced are labelled illustrative.
- **Ultrasound physics** in m50 is written from scratch for ICE. OpenUltrasoundLab is the format inspiration
  for this course; nothing is copied from it (CLAUDE.md §6).
- **Images** in labs are synthetic phantoms from our own code or openly licensed data sets recorded in
  `data/registry.json`. No vendor screenshots, no patient images without a licence.

**Prerequisites for the whole part:** m04 (sampling), m06 (meshes), m21 (registration) and m35 (diagnostic
accuracy). Each module lists its own.

## What each modality is for

| Modality | Physical principle | Before the procedure | During | After | Main limits | Module |
| --- | --- | --- | --- | --- | --- | --- |
| Fluoroscopy | X-ray transmission, projection | — | Catheter and sheath position, transseptal access, device leads | — | Ionizing radiation for patient and staff; 2-D projection; poor soft-tissue contrast | m49 |
| Intracardiac echo (ICE) | Ultrasound from a catheter | — | Transseptal puncture, catheter–tissue contact, effusion, anatomy shells | — | Field of view; operator skill; an extra venous catheter | m50 |
| Transesophageal and transthoracic echo | Ultrasound | Appendage thrombus, function | Guidance of appendage occlusion | Effusion, function | Esophageal probe and sedation (TEE); acoustic windows (TTE) | m50 |
| Cardiac CT | X-ray attenuation, tomography | Atrial and venous anatomy, appendage thrombus, esophagus, wall thickness, coronary arteries | Fused with the map | Pulmonary vein stenosis, complications | Radiation and iodinated contrast; motion; tissue characterization limited | m51 |
| Cardiac MRI | Nuclear magnetic resonance, relaxation contrast | Atrial fibrosis, ventricular scar, function | Fused with the map; real-time MRI-guided ablation (early) | Lesions and gaps, oedema | Time, cost; thresholds not standard; implanted devices and artefacts | m52, m53 |
| PET and SPECT | Radioactive tracers | Inflammation (for example cardiac sarcoidosis) | — | Response to treatment; device infection | Radiation; low spatial resolution; partial volume | m54 |

The rows summarize the use-case catalogue below; in the modules every clinical claim carries its own citation.

## Module list

| ID | Module | One-line scope | Builds on |
| --- | --- | --- | --- |
| m48 | Imaging across the EP workflow | Which modality answers which question; resolution, contrast, noise and dose as one vocabulary; diagnostic accuracy of imaging tests | m04, m21, m35 |
| m49 | Fluoroscopy and radiation protection | The X-ray image chain, dose quantities, reference levels, staff protection, low- and zero-fluoroscopy workflows | m48 |
| m50 | Intracardiac echocardiography, with TEE and TTE | Phased-array physics for a catheter probe, views, transseptal guidance, complication monitoring, ICE-built anatomy, evidence against TEE | m48, m20 |
| m51 | Cardiac CT for EP | Attenuation and Hounsfield units, reconstruction, ECG gating, contrast and dose; anatomy, thrombus, esophagus and wall thickness | m48, m21 |
| m52 | Cardiac MRI for EP | Relaxation and inversion recovery, late gadolinium enhancement, atrial fibrosis and ventricular scar, why thresholds matter, MRI with implanted devices | m48, m21, m40 |
| m53 | Imaging ablation lesions and real-time MRI-guided EP | Lesions, gaps and oedema after ablation; interventional MRI, its physics and its current limits | m27, m28, m52 |
| m54 | Nuclear imaging in EP | PET and SPECT physics, standardized uptake and partial volume; inflammation and device infection | m48 |
| m55 | Capstone: a multimodal image-guided procedure on a digital phantom | Segment, mesh, register to a simulated map, overlay on simulated fluoroscopy, and add up the error and dose budget | m21, m49–m52 |

Adding these eight modules takes the course from 47 to 55 modules; nothing is renumbered.

## How imaging is useful: use-case catalogue

One example per row, each from a source verified for this proposal (see [Sources](#sources)). "Evidence" says
what kind of study it is.

| Question | Modality | What was found | Evidence | Module |
| --- | --- | --- | --- | --- |
| How much radiation does an EP procedure give? | Fluoroscopy | Reference levels (third quartile of kerma-area product) ranged from 4.10 Gy·cm² for accessory-pathway ablation to 12.65 Gy·cm² for persistent AF ablation across 33 French centers [greffier2026] | National multicenter survey | m49 |
| Can AF ablation be done without fluoroscopy? | Mapping system and ICE | In seven studies (1,593 patients) the zero-fluoroscopy approach was feasible in 95.1% of patients, with no significant difference in success or complications [debreceni2023] | Meta-analysis of observational studies | m49, m50 |
| Do mapping systems reduce radiation? | Mapping system | Lower fluoroscopy time and dose for supraventricular ablations, often with longer procedures; no difference for VT [zormpas2023] | Multicenter registry | m49 |
| Does seeing the sheath on the map help? | Mapping system | Fluoroscopy time 11.43 vs 15.37 min with a sheath visualized on the map [chen2026sheath] | Randomized trial, 100 patients | m49 |
| Can ICE replace fluoroscopy or TEE for transseptal puncture? | ICE | Less fluoroscopy (mean difference −2.07 min) with similar first-pass success and no increase in safety events [abdalla2026] | Meta-analysis of randomized and observational studies | m50 |
| ICE or TEE for AF ablation? | ICE, TEE | No significant difference in complications, shorter fluoroscopy with ICE; certainty low to very low [kanniyan2026] | Meta-analysis (5 cohorts, 1 trial) | m50 |
| ICE or TEE for appendage occlusion? | ICE, TEE | Similar success; shorter procedures in adjusted analyses, but more effusions needing intervention and more residual septal defects with ICE [yaser2026] | Meta-analysis of observational studies | m50 |
| Is ICE use associated with outcomes? | ICE | 90-day readmission lower with ICE (hazard ratio 0.88) in a US database [deshpande2022]; less tamponade in VT ablation in a Japanese database [kitamura2021]; no improvement in procedural metrics with pulsed-field ablation [dellorusso2023] | Administrative databases; multicenter cohort | m50 |
| Is there a thrombus in the appendage? | CT, TEE | CT sensitivity 96%, specificity 92%, but positive predictive value 41% at 8.9% prevalence; with delayed imaging 100%, 99% and 92% [romero2013] | Meta-analysis, TEE as reference | m48, m51 |
| Where is the esophagus? | CT | Two main courses behind the left atrium; the esophagus touched the mid posterior wall in every patient [tsao2005] | Cross-sectional CT study | m51 |
| How thick is the wall, and does it matter? | CT | Atrial wall 1.89 mm on average, 0.5–3.5 mm [beinart2011]; ventricular wall thinning and its gradient near VT isthmuses [ciaccio2024; moore2024] | Small observational studies | m51 |
| How accurate is CT fused with the map? | CT + mapping | Registration error 2.3 mm with surface registration against 6.4 mm with landmarks [kistler2006]; ablation at CT-marked targets in dogs missed by 1.8–2.7 mm [dong2006] | Clinical series; animal study | m51, m55 |
| Does atrial fibrosis on MRI matter? | MRI | Associated with recurrence [marrouche2014]; ablating it added no benefit in a randomized trial [marrouche2022]; lesions did not uniformly become scar [akoum2024] | Cohort; randomized trial | m52 |
| Is "fibrosis" a stable measurement? | MRI | Average fibrosis burden ranged from 5.0% to 37.4% of the wall surface depending on the threshold [boyle2022]; reproducibility depended on the thresholding method [kamali2020]; thresholds defined from healthy volunteers [gunturiz2022] | Methods studies | m52 |
| Where are the VT channels? | MRI | Conducting channels on MRI colocalized with functional mapping targets [guichard2024]; ring-like scar was associated with VT recurrence [pittorru2026] | Single-center cohorts | m52 |
| Can patients with devices have MRI? | MRI | With devices not labelled MRI-conditional, scanned under a protocol: no device or lead failure when the protocol was followed, in 1,500 nonthoracic scans at 1.5 T [russo2017]; no long-term clinically significant adverse events in 2,103 scans [nazarian2017] | Prospective registries | m52 |
| Did the ablation leave gaps? | MRI | Scar gaps predicted the extent of vein reconnection but not its location (kappa 0.37) [aljefairi2019] | Prospective cohort | m53 |
| Can ablation be done inside the MRI scanner? | Real-time MRI | Acute isthmus block in 32 of 35 patients; technical challenges in 54% [hopman2026]; automatic meshes in about 16 s [jahnke2024] | Single-center series | m53 |
| Is there active inflammation? | FDG PET | In cardiac sarcoidosis with VT, lack of improvement on serial PET was associated with events [muser2016; muser2018] | Single-center cohorts | m54 |
| Is a device infected? | FDG PET/CT, SPECT | Multisociety consensus on uptake at device pockets and leads [bourque2024] | Expert consensus | m54 |

## How Part VIII fits the rest of the course

- **m21** keeps the mathematics of registration (landmarks, ICP, error). Part VIII supplies the images and,
  in m55, applies m21 end to end.
- **m40** keeps AI segmentation and its metrics. m51 and m52 use simple thresholds so that the physics stays
  visible, and point to m40 for learned methods.
- **m14** keeps the analog front end; m50 and m52 refer to it for electrogram recording near imaging hardware.
- **m27 and m28** explain how lesions form; m53 asks what imaging can see of them.
- **m35 and m45** supply diagnostic accuracy and evidence levels; m48 applies them to imaging tests.
- **m36** covers device regulation; imaging devices are not added there.

## Module plans

Equation labels below are proposals; each will get a test in `tests/` (CLAUDE.md §5). Physical constants and
tissue parameters marked "to verify" are looked up at stage 1 and never typed from memory.

### m48 · Imaging across the EP workflow

**In 60 seconds.** Every imaging test trades spatial resolution, temporal resolution, tissue contrast,
radiation and access. The EACVI/EHRA consensus reviews echo, MRI, CT and nuclear imaging for patients with AF
[donal2016]. Accuracy depends on prevalence as well as on the scanner: CT for appendage thrombus had 96%
sensitivity and 92% specificity against TEE, but a positive predictive value of 41% at 8.9% prevalence
[romero2013].

**Learning goals.** (1) Describe any modality by resolution, contrast, noise, speed, dose and access.
(2) Compute contrast-to-noise ratio and the blur of a thin structure. (3) Turn sensitivity and specificity into
predictive values for an imaging test (m35).

**Planned equations.** eq-m48-psf (a Gaussian point-spread function and its full width at half maximum);
eq-m48-cnr (contrast-to-noise ratio, $|S_A - S_B|/\sigma$); eq-m48-thin-wall (apparent contrast of a wall of
thickness $w$ blurred by the point-spread function, an error function).

**Demos.** m48-d1 "Thin walls and blur": wall thickness against resolution, apparent contrast (exact).
m48-d2 "Which modality for which question": an interactive table filtered by question, with each cell's
source (schematic).

**Lab.** One synthetic thorax phantom "imaged" four ways (blur, noise and contrast set per modality,
illustrative); measure CNR and wall visibility; predictive values from the published accuracy of CT for
thrombus [romero2013].

**Clinical correlate (pending review).** Choosing imaging around AF ablation as the consensus describes it
[donal2016], read for its evidence, not as advice.

### m49 · Fluoroscopy and radiation protection

**In 60 seconds.** An X-ray image is a shadow: transmitted intensity falls exponentially with attenuation
along each ray. Dose to the patient is reported as air kerma and kerma-area product; national surveys set
reference levels for EP procedures [greffier2026; samara2026]. Staff dose falls with distance, time and
shielding, and a position paper argued that these measures together could cut exposure by more than an order
of magnitude [heidbuchel2014]. Mapping systems, ICE and sheaths visible on the map have made low- and
zero-fluoroscopy workflows feasible [debreceni2023; chen2026sheath; borlich2025], although no randomized trial
has compared zero-fluoroscopy with fluoroscopy-guided pulsed-field ablation [kour2026].

**Learning goals.** (1) Derive image contrast from attenuation. (2) Explain air kerma, kerma-area product and
why the product does not change with distance from the source. (3) Estimate how distance and shielding change
staff dose. (4) Read a reference-level survey. (5) Judge zero-fluoroscopy evidence by its design.

**Planned equations.** eq-m49-beer ($I = I_0 e^{-\int \mu\, dx}$); eq-m49-contrast (contrast of a catheter or
contrast-filled structure); eq-m49-inverse-square (dose rate from a point source); eq-m49-kap (kerma-area
product as kerma times field area, constant along the beam).

**Demos.** m49-d1 "A shadow of the heart": a projected phantom with a catheter; attenuation and noise per
frame (simulation, illustrative values). m49-d2 "Time, distance, shielding": relative staff dose
(approximate model; inverse square and exponential shielding, parameters to verify).

**Lab.** Digitally reconstructed radiographs of a synthetic phantom from our own ray tracer; contrast against
attenuation; kerma-area product invariance checked numerically; analysis of a synthetic procedure dose log
against the published reference levels [greffier2026].

**Clinical correlate (pending review).** Radiation in the EP lab for patients and staff, and what
low-fluoroscopy studies show and do not show [heidbuchel2014; debreceni2023; kour2026].

### m50 · Intracardiac echocardiography, with TEE and TTE

**In 60 seconds.** An ICE catheter is a small phased-array ultrasound probe inside the heart. Its
frequency sets the trade between resolution and depth, and its element spacing decides whether a steered beam
has false copies (grating lobes). ICE guides transseptal puncture with less fluoroscopy and no increase in
safety events in pooled studies [abdalla2026]; against TEE for AF ablation the differences were not
significant, with low-certainty evidence [kanniyan2026]; for appendage occlusion it was associated with
shorter procedures in adjusted analyses but more effusions needing intervention [yaser2026]. Observational databases associate
ICE with fewer readmissions after AF ablation [deshpande2022] and less tamponade in VT ablation
[kitamura2021].

**Learning goals.** (1) Relate frequency, wavelength, axial resolution and penetration. (2) Steer a phased
array and state the grating-lobe condition. (3) Relate depth, number of lines and frame rate. (4) Build a 3-D
shell from tracked 2-D contours (link m20 and [zou2026]). (5) Read ICE-versus-TEE evidence.

**Planned equations.** eq-m50-axial ($\lambda = c/f$, axial resolution of a pulse of $n$ cycles
$n\lambda/2$); eq-m50-steer (element delays $\tau_k = k d \sin\theta / c$ and the condition
$d \le \lambda/2$); eq-m50-frame-rate ($c / (2 D N_{\text{lines}})$); eq-m50-doppler
($f_D = 2 f_0 v \cos\theta / c$). Speed of sound and attenuation in tissue: to verify.

**Demos.** m50-d1 "Steering a phased array": array factor against angle; element pitch, frequency and
steering angle (exact). m50-d2 "Depth, lines and frame rate" (exact).

**Lab.** Delay-and-sum beamforming of point scatterers with our own simulator; a synthetic interatrial
septum and fossa; the "tenting" of a sheath tip; a shell from tracked contours; reading the published
comparisons. Public echo data only if a licence allows (`TODO(source)`).

**Clinical correlate (pending review).** Transseptal access and complication monitoring with ICE, as the
cited studies describe them.

### m51 · Cardiac CT for EP

**In 60 seconds.** CT measures attenuation along many rays and reconstructs slices; Hounsfield units put
water at 0 and air at −1000. ECG gating freezes the heart, contrast fills the chambers, and dose is part of
the cost. Before ablation CT shows atrial and venous anatomy, appendage thrombus [romero2013], the course of
the esophagus [tsao2005] and wall thickness [beinart2011]; in VT, wall thinning and its gradient have been
studied as markers of isthmuses [ciaccio2024; moore2024]. Fused with the map, CT registered with surface
methods to within a few millimetres in early studies [kistler2006; dong2006].

**Learning goals.** (1) Define Hounsfield units. (2) Reconstruct a slice by filtered back-projection.
(3) Explain gating and temporal resolution. (4) Measure wall thickness and see what voxel size does to it.
(5) Distinguish the error a system reports from the error at a target (link m21, m55).

**Planned equations.** eq-m51-hu ($\mathrm{HU} = 1000\,(\mu - \mu_w)/(\mu_w - \mu_a)$); eq-m51-radon (the
Radon transform and the central-slice theorem); eq-m51-fbp (filtered back-projection); eq-m51-gating
(half-scan temporal resolution as a share of rotation time, an approximation). Dose conversion factors: to
verify.

**Demos.** m51-d1 "From sinogram to slice": projections, filter on and off (simulation, our own code).
m51-d2 "Motion and the gating window" (approximate model).

**Lab.** Radon transform and filtered back-projection in NumPy on a synthetic thorax; threshold
segmentation of the left atrium; wall thickness from a distance transform; landmark against surface
registration to simulated map points, compared with the magnitudes reported by [kistler2006] and [dong2006].
A public CT data set only if its licence allows (`TODO(source)`).

**Clinical correlate (pending review).** Pre-procedural CT for AF and VT ablation as the cited studies and
consensus describe it [donal2016].

### m52 · Cardiac MRI for EP

**In 60 seconds.** MRI images protons precessing in a magnetic field; contrast comes from how fast their
magnetization recovers. An inversion pulse timed to null normal myocardium after gadolinium makes scar bright:
late gadolinium enhancement [fusco2024] (relaxation times to verify at stage 1). Atrial fibrosis on MRI was associated
with recurrence after AF ablation [marrouche2014], but ablating it did not reduce recurrence in a randomized
trial [marrouche2022]. How much "fibrosis" a scan shows depends on the method and threshold [boyle2022;
kamali2020]. In the ventricle, MRI conducting channels colocalize with mapping targets [guichard2024].
Registries of patients with pacemakers and defibrillators not labelled MRI-conditional, scanned under strict
protocols, reported no long-term clinically significant adverse events [nazarian2017] and no lead failures
when the protocol was followed [russo2017].

**Learning goals.** (1) State the Larmor relation. (2) Derive the inversion-recovery null point.
(3) Explain LGE contrast and why the inversion time matters. (4) Compute an image intensity ratio and show
how fibrosis burden moves with the threshold. (5) Read the DECAAF evidence chain as association, then trial.

**Planned equations.** eq-m52-larmor ($\omega = \gamma B_0$); eq-m52-ir
($M_z(TI) = M_0 (1 - 2 e^{-TI/T_1})$, null at $TI = T_1 \ln 2$); eq-m52-lge-contrast (signal difference
between scar and myocardium against inversion time); eq-m52-iir (wall intensity over mean blood-pool
intensity). Gyromagnetic ratio and post-contrast T1 values: to verify.

**Demos.** m52-d1 "Choosing the inversion time": recovery curves for blood, myocardium and scar (exact,
T1 values to verify). m52-d2 "Fibrosis depends on the threshold": a synthetic atrial wall, burden against
threshold and method (simulation).

**Lab.** Bloch inversion-recovery simulation; a synthetic atrial wall with fibrosis patches, noise and a
repeat scan; IIR, Otsu and standard-deviation thresholds compared by Dice between methods and between scans,
in the spirit of [kamali2020] and [boyle2022]; blood-pool normalization on the Decathlon heart MRI already
used in m40 (not an LGE data set; an open LGE data set is `TODO(source)`).

**Clinical correlate (pending review).** Substrate imaging before AF and VT ablation, and MRI in patients with
devices, as reported [marrouche2022; guichard2024; russo2017; nazarian2017].

### m53 · Imaging ablation lesions and real-time MRI-guided EP

**In 60 seconds.** After ablation, enhancement and oedema-sensitive MRI sequences show the treated tissue
[fusco2024]. Three months after vein isolation, gaps in the scar predicted how many veins had reconnected,
but not where (kappa 0.37) [aljefairi2019], and lesions did not uniformly produce scar [akoum2024]. Real-time
MRI-guided ablation avoids ionizing radiation; in one early series of typical-flutter ablations acute block was
confirmed in 32 of 35 patients, with technical challenges in more than half [hopman2026]. Limits remain:
MRI-compatible ablation systems, electrograms under strong interference, catheter visualization and lesion
assessment [tampakis2023].

**Learning goals.** (1) Compute when blur hides a gap of a given width. (2) Relate lines, repetition time and
frame rate in real-time MRI. (3) Measure agreement between an image finding and an electrical finding with
kappa (m35).

**Planned equations.** eq-m53-gap (contrast of a gap of width $g$ under a Gaussian point-spread function);
eq-m53-frame-time ($N_{\text{lines}} \times TR$).

**Demos.** m53-d1 "Can the scan see the gap?": gap width against resolution (exact). m53-d2 "Real-time
MRI: lines, repetition time and frame rate" (exact).

**Lab.** A synthetic pulmonary-vein ring lesion with gaps; blur, noise and threshold; detection against
truth; kappa with simulated electrical reconnection; a frame-rate budget for catheter tracking.

**Clinical correlate (pending review).** Imaging lesions and gaps, and the state of interventional MRI, as
reported [aljefairi2019; hopman2026; jahnke2024].

### m54 · Nuclear imaging in EP

**In 60 seconds.** PET and SPECT image where a radioactive tracer goes. The standardized uptake value scales
activity by injected dose and body weight; low resolution makes thin myocardium look dimmer than it is
(partial volume). In cardiac sarcoidosis with VT, FDG uptake and its change over time were associated with
recurrence and events [muser2016; muser2018]; an HRS expert consensus covers arrhythmias in cardiac sarcoidosis
[birnie2014]. FDG PET/CT and leukocyte SPECT/CT are also used for suspected device infection [bourque2024].

**Learning goals.** (1) Apply radioactive decay to timing. (2) Compute a standardized uptake value. (3) Derive
the recovery coefficient of a thin slab. (4) Read a serial-PET response definition.

**Planned equations.** eq-m54-decay ($A(t) = A_0 e^{-\lambda t}$); eq-m54-suv; eq-m54-recovery (recovery
coefficient of a slab of thickness $w$ under a Gaussian point-spread function).

**Demos.** m54-d1 "Why thin myocardium looks dim" (exact). m54-d2 "Decay and scan timing" (exact).

**Lab.** A synthetic myocardium with inflamed regions; blur and noise; maximum, mean and partial-volume
corrected uptake; a serial-scan response defined as in [muser2018].

**Clinical correlate (pending review).** Inflammation imaging in cardiac sarcoidosis and device infection, as
reported [muser2016; bourque2024]; [birnie2014] is cited by title only because PubMed has no abstract.

### m55 · Capstone: a multimodal image-guided procedure on a digital phantom

**In 60 seconds.** One synthetic left atrium goes through the whole chain: CT-like and MRI-like volumes,
segmentation, a mesh, registration to simulated map points, an overlay on simulated fluoroscopy, and an error
and dose budget at the end. The error a registration reports at its own fiducials is not the error at a
target [fitzpatrick1998]; early clinical and animal studies of CT fusion show both kinds of number
[kistler2006; dong2006].

**Learning goals.** (1) Run the full pipeline and name each error source. (2) Predict target error from
fiducial error and geometry. (3) Project a 3-D model onto a C-arm view. (4) Add independent errors and doses
into a budget.

**Planned equations.** eq-m55-projection (pinhole projection of a C-arm); eq-m55-tre (expected target
registration error from fiducial localization error, number and layout of fiducials [fitzpatrick1998]);
eq-m55-budget (independent errors in quadrature).

**Demos.** m55-d1 "Fiducial error is not target error": move fiducials, watch both (simulation). m55-d2
"Overlay on a projection": a mesh projected onto a synthetic fluoroscopy frame with rotation and
registration error (simulation).

**Lab.** The full chain on our own phantom; the Decathlon heart MRI (already registered) for the segmentation
and registration steps on real anatomy; a final report of errors and dose. Optional MONAI segmentation, as in
m40.

## Data sets

| Data set | Used in | License | Status |
| --- | --- | --- | --- |
| Course phantoms (thorax, atria, ventricle, lesions) generated by our own code | m48–m55 | MIT (our code) | No licence issue |
| Medical Segmentation Decathlon, Task02 Heart (MRI, left atrium) | m52, m55 | Creative Commons Attribution-ShareAlike 4.0 | Already pinned in `data/registry.json` (m40) |
| An open cardiac CT data set with chamber labels | m51, m55 | Unknown | `TODO(source)`: licence and size to check at stage 1 |
| An open echocardiography or ICE data set | m50 | Unknown | `TODO(source)`; ICE images are rarely public |
| An open LGE-MRI data set | m52, m53 | Unknown | `TODO(source)` |

## Sources

All rows marked "Verified (PubMed)" were looked up on PubMed for this proposal and their abstracts read.
Bib entries are added to `references.bib` at stage 2, when a module first cites them.

| Key | Source | Status |
| --- | --- | --- |
| heidbuchel2014 | Heidbuchel et al., Practical ways to reduce radiation dose for patients and staff during device implantations and electrophysiological procedures. Europace 16:946–964 (2014). DOI 10.1093/europace/eut409, PMID 24792380 | Verified (PubMed) |
| greffier2026 | Greffier et al., Radiation dose reference levels for the most common image-guided interventional cardiac electrophysiology and pacing procedures: a French multicenter survey. Phys Med 148:105898 (2026). DOI 10.1016/j.ejmp.2026.105898, PMID 42472521 | Verified (PubMed) |
| samara2026 | Samara et al., Updating national diagnostic reference levels for adult cardiac interventional procedures in Switzerland. Phys Med 148:105869 (2026). DOI 10.1016/j.ejmp.2026.105869, PMID 42378754 | Verified (PubMed) |
| debreceni2023 | Debreceni et al., Zero fluoroscopy catheter ablation for atrial fibrillation: a systematic review and meta-analysis. Front Cardiovasc Med 10:1178783 (2023). DOI 10.3389/fcvm.2023.1178783, PMID 37396578 | Verified (PubMed) |
| zormpas2023 | Zormpas et al., Utilization of 3D mapping systems in interventional electrophysiology and its impact on procedure time and fluoroscopy: insights from the "Go for Zero Fluoroscopy" project. Pacing Clin Electrophysiol 46:875–881 (2023). DOI 10.1111/pace.14788, PMID 37483154 | Verified (PubMed) |
| chen2026sheath | Chen et al., The impact of a visualized steerable sheath on radiofrequency catheter ablation for first-time atrial fibrillation ablation: a prospective, randomized, single-blind study. Catheter Cardiovasc Interv 108:924–934 (2026). DOI 10.1002/ccd.70716, PMID 42402779 | Verified (PubMed) |
| borlich2025 | Borlich et al., Near-zero fluoroscopy workflow for pulmonary vein isolation in atrial fibrillation using a variable loop, 3D-integrated circular PFA catheter: initial single-center experience with the first 35 patients. J Interv Card Electrophysiol 68:877–884 (2025). DOI 10.1007/s10840-025-01981-5, PMID 39899143 | Verified (PubMed) |
| kour2026 | Kour et al., Fluoroless workflow for pulsed field ablation of atrial fibrillation using two 3D-integrated catheters (narrative review). J Clin Med 15:6838 (2026). DOI 10.3390/jcm15176838, PMID 42739841 | Verified (PubMed); vendor-specific, cite for its evidence summary only |
| chen2026tsp | Chen et al., Comparison of two ICE-guided transseptal puncture strategies for zero-fluoroscopy AF ablation: a randomized controlled trial. J Arrhythm 42:e70322 (2026). DOI 10.1002/joa3.70322, PMID 41953354 | Verified (PubMed) |
| abdalla2026 | Abdalla et al., Comparative outcomes of ICE versus TEE/fluoroscopy guidance transseptal puncture in LA procedures: a systematic review and meta-analysis. Ann Noninvasive Electrocardiol 31:e70186 (2026). DOI 10.1111/anec.70186, PMID 41952556 | Verified (PubMed) |
| kanniyan2026 | Kanniyan et al., Intracardiac versus transesophageal echocardiography for guidance of atrial fibrillation ablation: a systematic review and meta-analysis. Echocardiography 43:e70543 (2026). DOI 10.1111/echo.70543, PMID 42390195 | Verified (PubMed) |
| yaser2026 | Yaser et al., Intracardiac versus transesophageal echocardiography for left atrial appendage occlusion: a meta-analysis. JACC Adv 5:102815 (2026). DOI 10.1016/j.jacadv.2026.102815, PMID 42161029 | Verified (PubMed) |
| deshpande2022 | Deshpande et al., Impact of intracardiac echocardiography on readmission morbidity and mortality following atrial fibrillation ablation. J Cardiovasc Electrophysiol 33:2496–2503 (2022). DOI 10.1111/jce.15683, PMID 36128625 | Verified (PubMed) |
| kitamura2021 | Kitamura et al., Safety and effectiveness of intracardiac echocardiography in ventricular tachycardia ablation: a nationwide observational study. Heart Vessels 36:1009–1015 (2021). DOI 10.1007/s00380-020-01766-y, PMID 33475763 | Verified (PubMed) |
| dellorusso2023 | Dello Russo et al., Intracardiac echocardiography-guided pulsed-field ablation for successful ablation of atrial fibrillation: a propensity-matched analysis from a large nationwide multicenter experience. J Interv Card Electrophysiol 67:1257–1266 (2023). DOI 10.1007/s10840-023-01699-2, PMID 37985538 | Verified (PubMed) |
| romero2013 | Romero et al., Detection of left atrial appendage thrombus by cardiac computed tomography in patients with atrial fibrillation: a meta-analysis. Circ Cardiovasc Imaging 6:185–194 (2013). DOI 10.1161/CIRCIMAGING.112.000153, PMID 23406625 | Verified (PubMed) |
| tsao2005 | Tsao et al., Anatomic relationship of the esophagus and left atrium: implication for catheter ablation of atrial fibrillation. Chest 128:2581–2587 (2005). DOI 10.1378/chest.128.4.2581, PMID 16236927 | Verified (PubMed) |
| ciaccio2024 | Ciaccio et al., Wavefront curvature analysis derived from preprocedural imaging can identify the critical isthmus in patients with postinfarcted ventricular tachycardia. Heart Rhythm 21:2471–2480 (2024). DOI 10.1016/j.hrthm.2024.05.056, PMID 38848858 | Verified (PubMed); 6 patients |
| moore2024 | Moore et al., Multidetector computed tomography assessment of anatomical ventricular tachycardia isthmuses in repaired tetralogy of Fallot. JACC Clin Electrophysiol 10:857–866 (2024). DOI 10.1016/j.jacep.2024.102333, PMID 38456860 | Verified (PubMed) |
| kistler2006 | Kistler et al., Validation of three-dimensional cardiac image integration: use of integrated CT image into electroanatomic mapping system to perform catheter ablation of atrial fibrillation. J Cardiovasc Electrophysiol 17:341–348 (2006). DOI 10.1111/j.1540-8167.2006.00371.x, PMID 16643352 | Verified (PubMed) |
| dong2006 | Dong et al., Integrated electroanatomic mapping with three-dimensional computed tomographic images for real-time guided ablations. Circulation 113:186–194 (2006). DOI 10.1161/CIRCULATIONAHA.105.565200, PMID 16401772 | Verified (PubMed) |
| donal2016 | Donal et al., EACVI/EHRA expert consensus document on the role of multi-modality imaging for the evaluation of patients with atrial fibrillation. Eur Heart J Cardiovasc Imaging 17:355–383 (2016). DOI 10.1093/ehjci/jev354, PMID 26864186 | Verified (PubMed) |
| boyle2022 | Boyle et al., Elevated fibrosis burden as assessed by MRI predicts cryoballoon ablation failure. J Cardiovasc Electrophysiol 34:302–312 (2023; PubMed date 2022). DOI 10.1111/jce.15791, PMID 36571158 | Verified (PubMed) |
| kamali2020 | Kamali et al., Reproducibility of clinical late gadolinium enhancement magnetic resonance imaging in detecting left atrial scar after atrial fibrillation ablation. J Cardiovasc Electrophysiol 31:2824–2832 (2020). DOI 10.1111/jce.14743, PMID 32931635 | Verified (PubMed) |
| gunturiz2022 | Gunturiz-Beltrán et al., Quantification of right atrial fibrosis by cardiac magnetic resonance: verification of the method to standardize thresholds. Rev Esp Cardiol (Engl Ed) 76:173–182 (PubMed date 2022). DOI 10.1016/j.rec.2022.06.010, PMID 35809892 | Verified (PubMed) |
| guichard2024 | Guichard et al., Substrate mapping for ventricular tachycardia ablation through high-density whole-chamber double extra stimuli: the S3 protocol. JACC Clin Electrophysiol 10:1534–1547 (2024). DOI 10.1016/j.jacep.2024.04.023, PMID 38819348 | Verified (PubMed) |
| pittorru2026 | Pittorru et al., Ring-like scar architecture and arrhythmic outcomes of patients with nondilated left ventricular cardiomyopathy treated with ventricular tachycardia ablation. JACC Clin Electrophysiol (2026, in press). DOI 10.1016/j.jacep.2026.07.019, PMID 42714370 | Verified (PubMed); volume and pages not yet assigned |
| russo2017 | Russo et al., Assessing the risks associated with MRI in patients with a pacemaker or defibrillator. N Engl J Med 376:755–764 (2017). DOI 10.1056/NEJMoa1603265, PMID 28225684 | Verified (PubMed) |
| nazarian2017 | Nazarian et al., Safety of magnetic resonance imaging in patients with cardiac devices. N Engl J Med 377:2555–2564 (2017). DOI 10.1056/NEJMoa1604267, PMID 29281579 | Verified (PubMed) |
| sheagren2025 | Sheagren et al., Arrhythmia substrate identification using wideband motion-corrected late gadolinium enhancement MRI in a swine model of myocardial infarction with taped implantable cardioverter-defibrillators. Heart Rhythm O2 6:1419–1427 (2025). DOI 10.1016/j.hroo.2025.06.008, PMID 41280543 | Verified (PubMed); animal study, for device artefacts |
| aljefairi2019 | Al Jefairi et al., Relationship between atrial scar on cardiac magnetic resonance and pulmonary vein reconnection after catheter ablation for paroxysmal atrial fibrillation. J Cardiovasc Electrophysiol 30:727–740 (2019). DOI 10.1111/jce.13908, PMID 30847990 | Verified (PubMed) |
| hopman2026 | Hopman et al., Interventional cardiac magnetic resonance-guided flutter ablation: technical evolution and procedural insights from early clinical use. Heart Rhythm 23:e2789–e2796 (2026). DOI 10.1016/j.hrthm.2026.07.024, PMID 42476391 | Verified (PubMed) |
| jahnke2024 | Jahnke et al., Electrophysiological cardiovascular MR: procedure-ready mesh model generation for interventional guidance based on non-selective excitation compressed sensing whole heart imaging. Sci Rep 14:8974 (2024). DOI 10.1038/s41598-024-59230-0, PMID 38637577 | Verified (PubMed) |
| tampakis2023 | Tampakis et al., Real-time cardiovascular magnetic resonance-guided radiofrequency ablation: a comprehensive review. World J Cardiol 15:415–426 (2023). DOI 10.4330/wjc.v15.i9.415, PMID 37900261 | Verified (PubMed) |
| fusco2024 | Fusco et al., Radiofrequency ablation guided by real-time cardiovascular magnetic resonance. Radiol Med 129:1823–1829 (2024). DOI 10.1007/s11547-024-01911-x, PMID 39511064 | Verified (PubMed) |
| muser2016 | Muser et al., Long-term outcomes of catheter ablation of ventricular tachycardia in patients with cardiac sarcoidosis. Circ Arrhythm Electrophysiol 9 (2016). DOI 10.1161/CIRCEP.116.004333, PMID 27516457 | Verified (PubMed) |
| muser2018 | Muser et al., Prognostic role of serial quantitative evaluation of 18F-fluorodeoxyglucose uptake by PET/CT in patients with cardiac sarcoidosis presenting with ventricular tachycardia. Eur J Nucl Med Mol Imaging 45:1394–1404 (2018). DOI 10.1007/s00259-018-4001-8, PMID 29610956 | Verified (PubMed) |
| birnie2014 | Birnie et al., HRS expert consensus statement on the diagnosis and management of arrhythmias associated with cardiac sarcoidosis. Heart Rhythm 11:1305–1323 (2014). DOI 10.1016/j.hrthm.2014.03.043, PMID 24819193 | Verified (PubMed); no abstract, cited by title only |
| bourque2024 | Bourque et al., 18F-FDG PET/CT and radiolabeled leukocyte SPECT/CT imaging for the evaluation of cardiovascular infection in the multimodality context: ASNC Imaging Indications expert consensus recommendations (with HRS and others). J Nucl Cardiol 34:101786 (2024). DOI 10.1016/j.nuclcard.2023.101786, PMID 38472038 | Verified (PubMed) |
| fitzpatrick1998 | Fitzpatrick, West and Maurer, Predicting error in rigid-body point-based registration. IEEE Trans Med Imaging 17:694–702 (1998). DOI 10.1109/42.736021, PMID 9874293 | Verified (PubMed) |
| marrouche2014, marrouche2022, akoum2024, beinart2011, zou2026, xiong2020, razeghi2023, cardoso2022monai, antonelli2021msd | Already in `references.bib` (m40) | Verified at m40 |

**To verify at stage 1** (never typed from memory): speed of sound and attenuation in soft tissue (m50);
linear attenuation coefficients and Hounsfield values of blood, myocardium, fat and contrast (m49, m51);
CT and fluoroscopy dose conversion coefficients (m49, m51); the proton gyromagnetic ratio (m52); native and
post-contrast T1 of blood, myocardium and scar (m52); tracer half-lives (m54); licences of candidate open CT,
echo and LGE-MRI data sets.

## Questions for the author

1. **Module list.** Eight modules, m48–m55, as above? Or fewer: for example fold m53 (lesions and real-time
   MRI) into m52, and m54 (nuclear) into m48, for six modules.
2. **Overlap.** m21 keeps registration mathematics and m40 keeps AI segmentation; Part VIII links to both and
   m55 applies m21 end to end. Approve?
3. **Ultrasound depth.** m50 teaches only the ultrasound physics ICE needs, written from scratch. Should it
   also link to OpenUltrasoundLab for deeper physics?
4. **Data.** Synthetic phantoms from our own code, plus the Decathlon heart MRI already pinned. Should we look
   for an open CT data set (downloaded in CI, as in Part VII), or stay synthetic for CT?
5. **Dependencies.** The plan needs no new packages (Radon transform, beamforming and Bloch simulation in
   NumPy and SciPy; meshes with pyvista, already in the stack). Agree?
6. **Review.** Imaging sections would benefit from a cardiac imaging specialist as well as an EP physician.
   Add an "imaging reviewer" role to `review_record.json`?
7. **Order and release.** Build m49 (fluoroscopy) and m50 (ICE) first, because every EP lab uses them, then
   m51–m55 and m48 last? Release Part VIII as v2.0?
8. **Learning path.** Add an "Imaging in EP" path: m04, m06, m21, m35, m40, m48–m55?
