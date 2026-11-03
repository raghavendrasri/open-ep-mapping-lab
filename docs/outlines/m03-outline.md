# m03 outline · Unipolar, bipolar and omnipolar electrograms as spatial filters

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned
equation, demo, lab, test and source so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

## Learning goals

After this module a reader can:

1. Explain where a unipolar electrogram comes from, using the volume-conductor equation.
2. Show that a bipolar electrogram is a spatial difference, and so a directional spatial
   derivative when the electrodes are close.
3. Describe unipolar, bipolar and omnipolar recordings as spatial filters with a transfer
   function in spatial frequency, and use that view to explain far-field rejection.
4. Predict how electrode height, size, spacing and orientation change amplitude and shape.
5. Explain how an omnipolar signal is built from a clique of electrodes, and what it assumes.

Prerequisites: m01 (bioelectric sources) and m02 (volume conduction). Until those exist,
m03 includes a short recap of the volume-conductor equation.

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

One paragraph: a unipolar electrogram measures potential against a distant reference and sees
both local and far-field activity; a bipolar electrogram subtracts two nearby unipoles, which acts
like a spatial derivative that rejects far-field signals but depends on wavefront direction; an
omnipolar signal combines several bipoles to estimate the local electric field and remove most of
that direction dependence.

### 2. From the field

Practical lessons, each tied to a source:

- Unipolar recordings help with focal sources but carry far-field signal; bipolar recordings
  reject far-field signal but the local signal can sit under either electrode
  ([stevenson2005]).
- High-pass filtering a unipolar recording reduces far-field signal but limits what its shape can
  tell you ([stevenson2005]).
- Bipolar voltage changes with bipole orientation at the same site ([takigawa2018]).
- Smaller, closer electrodes record more distinct local signals in low-voltage areas
  ([anter2015]).

### 3. Derivations

Notation: σ extracellular conductivity (S/m); i_m membrane current per unit area of tissue
(A/m²); h electrode height above the tissue (mm); d interelectrode spacing (mm); u unit vector
along the bipole axis; n̂ propagation direction; θ angle between u and n̂; c conduction velocity
(m/s); k spatial frequency (rad/mm).

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m03-volume-conductor | φ(r,t) = (1/4πσ) ∫ i_m(r′,t) / ‖r − r′‖ dA′ | Unipolar potential from a thin sheet of membrane current in an infinite homogeneous medium ([plonsey2007]) | — | Numeric: closed-form point-source case |
| eq-m03-planar-wave | i_m(r,t) = g(t − n̂·r / c) | Planar wave model used for all demos | — | — |
| eq-m03-height-filter | φ̂(k) = e^{−‖k‖h} / (2σ‖k‖) · î_m(k) | Distance from tissue acts as a spatial low-pass filter | exact | SymPy: 2D Fourier transform of 1/√(ρ² + h²) equals 2π e^{−kh}/k |
| eq-m03-bipolar | V_bip(t) = φ(r₁,t) − φ(r₂,t) | Definition; polarity convention distal minus proximal | — | — |
| eq-m03-bipolar-transfer | H(k) = 2i sin(d k·u / 2), so ∣H∣ = 2∣sin(d‖k‖ cos θ / 2)∣ | Bipole is a spatial high-pass filter with nulls | exact | Numeric: apply to sampled spatial harmonics |
| eq-m03-bipolar-gradient | V_bip ≈ d u·∇φ when d‖k‖ ≪ 1 | Close bipole ≈ directional derivative; amplitude ∝ ∣cos θ∣ | approximate model | Numeric: error shrinks as d² |
| eq-m03-disk-average | multiply by 2J₁(‖k‖a) / (‖k‖a) | A disk electrode of radius a averages potential (low-pass) | exact | Numeric: average over a sampled disk |
| eq-m03-unipolar-slope | dU/dt = −c ∂φ/∂x for a planar wave along x | Unipolar slope scales with conduction velocity | — | Numeric: finite differences |
| eq-m03-intrinsic-deflection | LAT ≈ time of max −dU/dt | Activation marker from the unipolar downstroke; ideal conditions only ([steinhaus1989]) | approximate model | Numeric: matches true activation time in the ideal planar case |
| eq-m03-clique-field | E = −∇φ ≈ −D⁻¹ [φ₁ − φ₀, φ₂ − φ₀]ᵀ, D = [p₁ − p₀; p₂ − p₀] | Local field from a 3-electrode clique, assuming locally planar propagation ([deno2017], [riccio2021]) | — | Numeric: exact for a linear potential |
| eq-m03-omnipole | v_ω(t) = E(t)·ω, ω = direction of largest E-loop extent | Omnipolar signal along the activation direction ([deno2017], [masse2016]) | approximate model | Numeric: peak-to-peak stays constant as the wave rotates |
| eq-m03-farfield | distant monopole: unipolar ∝ 1/R, bipolar ∝ 1/R²; distant dipole: 1/R² vs 1/R³ | Why bipoles reject far-field signal | exact | Numeric: fitted log-log slopes |

The exact omnipole definition (how ω is chosen and the sign convention) will be confirmed from
the full text of [deno2017] in the derivations stage. The abstract supports the clique E-field
idea but not the precise formula.

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline, and compute in the browser
(the models are light enough; nothing is precomputed).

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m03-d1 | Wavefront passing one electrode | electrode height h, conduction velocity c | Unipolar shape (positive, sharp downstroke, negative) and where max −dU/dt falls versus true activation | approximate model |
| m03-d2 | Bipole orientation and spacing | angle θ, spacing d | The two unipoles, their difference, and bipolar amplitude versus θ on a polar plot | approximate model |
| m03-d3 | Spatial transfer functions | d, h, electrode radius a | ∣H(k)∣ for the bipole, the height low-pass, the disk average, and their product | exact |
| m03-d4 | Far-field rejection | distance to a distant source | A distant source dominating the unipole but not the bipole | approximate model |
| m03-d5 | Omnipole from a 3-electrode clique | wave direction | Two bipoles varying with direction while the omnipolar amplitude stays constant; the E-field loop | approximate model |

Assumptions to list under the demos: infinite homogeneous medium, thin 2D tissue sheet, planar
wave, point electrodes (except d3), no contact or blood-tissue boundary effects, no amplifier
filtering.

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: why the same tissue can look "healthy" or "low voltage" depending on the catheter.
Bipolar voltage cut-offs such as >1.5 mV for normal ventricular endocardium and <0.5 mV for dense
scar came from one catheter type in one setting ([marchlinski2000]). Orientation alone can change
bipolar voltage at the same site, most when the wavefront is parallel to one bipole and
perpendicular to the other ([takigawa2018]). Electrode size changes low-voltage area and
annotatable signals ([anter2015]), and omnipolar voltage reduces orientation effects
([magtibay2017]). See also the editorial [anter2016]. The section describes these findings only;
it gives no advice on patient care.

### 6. Visual summary and How experts think

- Visual summary: one schematic showing the chain tissue → height low-pass → electrode size
  low-pass → bipole high-pass → recorded signal. Badge: schematic.
- How experts think: "A bipolar voltage is a property of the tissue *and* the catheter and
  wavefront together." Ask which electrode the signal came from, which way the wave was going, and
  what the spacing was.

### 7. Cheat sheet and Interview questions

Written in stage 5. Cheat sheet draws on the equation table above. At least 10 interview
questions with model answers.

### 8. Code lab and Self-check

Lab: `labs/python/m03_lab.ipynb`, with an Octave copy `labs/octave/m03_lab.m` for parts A–D.

| Part | Task | Data |
| --- | --- | --- |
| A | Build the sheet forward model; compute a unipolar electrogram; find max −dU/dt | Synthetic |
| B | Rotate a bipole; confirm amplitude ∝ ∣cos θ∣ for small d and see where it breaks down | Synthetic |
| C | Apply the transfer functions to a 2D potential map with FFTs | Synthetic |
| D | Estimate E from a 3-electrode clique; check omnipolar amplitude under rotation | Synthetic |
| E | Look at real bipolar signals from a decapolar catheter; estimate the delay between neighboring bipoles; note what you cannot infer (no unipoles, uncalibrated amplitudes) | PhysioNet iafdb ([iafdb], [goldberger2000]) |

Self-check: at least 5 questions, written in stage 6.

### 9. Literature figures and Further reading

Literature figures (license to be checked for each before reuse; otherwise redraw from our code
and cite):

- Frontiers in Physiology papers ([riccio2021]) are usually CC BY. To confirm.
- de Bakker review ([debakker2019]) is in PubMed Central. License to confirm.

Further reading: [stevenson2005], [debakker2019], [anter2016], [magtibay2019].

## Sources

All looked up in PubMed or on the publisher's page during this stage. Entries are in
`references.bib`.

| Key | Source | Verified via |
| --- | --- | --- |
| plonsey2007 | Plonsey & Barr, *Bioelectricity: A Quantitative Approach*, 3rd ed., Springer 2007. DOI 10.1007/978-0-387-48865-3 | Springer page |
| stevenson2005 | Stevenson & Soejima, Recording techniques for clinical electrophysiology. J Cardiovasc Electrophysiol 2005. PMID 16174026 | PubMed |
| debakker2019 | de Bakker, Electrogram recording and analyzing techniques… PACE 2019. PMID 31609005 | PubMed |
| steinhaus1989 | Steinhaus, Estimating cardiac transmembrane activation and recovery times… Circ Res 1989. PMID 2917378 | PubMed |
| takigawa2018 | Takigawa et al., Effect of bipolar electrode orientation on local electrogram properties. Heart Rhythm 2018. PMID 30026016 | PubMed |
| anter2015 | Anter et al., High-resolution mapping of scar-related atrial arrhythmias using smaller electrodes… Circ Arrhythm Electrophysiol 2015. PMID 25792508 | PubMed |
| anter2016 | Anter & Josephson, Bipolar voltage amplitude: what does it really mean? Heart Rhythm 2016 (editorial). PMID 26432582 | PubMed |
| deno2017 | Deno et al., Orientation-independent catheter-based characterization of myocardial activation. IEEE Trans Biomed Eng 2017. PMID 27411215 | PubMed |
| masse2016 | Massé et al., Resolving myocardial activation with novel omnipolar electrograms. Circ Arrhythm Electrophysiol 2016. PMID 27406608 | PubMed |
| magtibay2017 | Magtibay et al., Physiological assessment of ventricular myocardial voltage using omnipolar electrograms. J Am Heart Assoc 2017. PMID 28862942 | PubMed |
| magtibay2019 | Magtibay et al., Reinserting physiology into cardiac mapping using omnipolar electrograms. Card Electrophysiol Clin 2019. PMID 31400876 | PubMed |
| riccio2021 | Riccio et al., Characterization of atrial propagation patterns… modified omnipolar electrogram strategy. Front Physiol 2021. PMID 34539424 | PubMed |
| marchlinski2000 | Marchlinski et al., Linear ablation lesions for control of unmappable ventricular tachycardia… Circulation 2000. PMID 10725289 | PubMed |
| goldberger2000 | Goldberger et al., PhysioBank, PhysioToolkit, and PhysioNet. Circulation 2000. PMID 10851218 | PubMed |
| iafdb | Intracardiac Atrial Fibrillation Database, PhysioNet. DOI 10.13026/C23S33. ODC-By 1.0 | PhysioNet page |

## Still to source (before stage 2)

Every default demo parameter needs a citation (CLAUDE.md §5). Each is `TODO(source)` until found:

- Conduction velocity ranges for atrial and ventricular myocardium (m/s)
- Typical electrode-to-tissue distance in contact (mm)
- Electrode diameters and spacings of common catheter designs (mm). Two are in hand: 2-5-2 mm
  decapolar spacing ([iafdb]); 1-mm and 3.5-mm electrodes ([anter2015]).
- Extracellular conductivity of myocardium and blood (S/m)
- Action-potential upstroke duration, used to set the wavefront width (ms)

## Glossary terms to add

unipolar electrogram · bipolar electrogram · omnipolar electrogram · indifferent (reference)
electrode · Wilson central terminal · near-field · far-field · local activation time ·
intrinsic deflection · clique · conduction velocity · volume conductor · spatial frequency ·
wavefront

## Formula-sheet entries

eq-m03-volume-conductor · eq-m03-height-filter · eq-m03-bipolar-transfer ·
eq-m03-bipolar-gradient · eq-m03-clique-field

## Questions for the author

1. **Polarity convention:** distal minus proximal for bipoles. OK?
2. **Omnipolar scope:** 2D cliques only, with 3D left to m13 (catheter design). OK?
3. **Real data in the lab (part E):** keep one small iafdb record (about 1 MB) in
   `data/samples/` so the lab runs without network, or download it at run time?
4. **Five demos** for one module. Enough, or too many for the pilot?
5. **Clinical correlate topic:** catheter-dependent voltage. Or would you prefer focal-source
   unipolar morphology?
