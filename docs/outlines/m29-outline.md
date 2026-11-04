# m29 outline · Complex maps: fractionation, phase mapping, rotor and driver detection

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

Scope note: whether rotors or other drivers sustain human atrial fibrillation (AF), and whether
ablating them helps, is contested. This module teaches how the maps are computed, how to test the
algorithms against known ground truth, and what the trials reported, on both sides. It gives no
ablation advice (CLAUDE.md §2).

## Learning goals

After this module a reader can:

1. Define fractionation and compute an interval-based fractionation index; show how filter
   settings, electrode spacing and detection thresholds change it.
2. Compute dominant frequency (DF) and an organization index (OI) from an electrogram, with the
   preprocessing that makes them meaningful.
3. Compute instantaneous phase with the Hilbert transform and with sinusoidal recomposition, and
   explain why raw electrograms need the second.
4. Detect phase singularities (PS) with the topological charge, and explain how ring size and
   electrode count create false positives.
5. Relate the spatial resolution needed to find a rotor to the spatial wavelength of the arrhythmia.
6. Validate a driver detector on simulations with known truth (precision, recall, localization
   error), and summarize the clinical trials evenly.

Prerequisites: m03 (electrograms), m05 (time–frequency tools), m10 (arrhythmia mechanisms) and m24
(interpolation). Until m05 exists, m29 carries the DF and Hilbert definitions it needs (see
question 1).

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

During AF the atrium does not activate in one clean wave, so activation-time maps break down.
"Complex maps" replace one activation time per site with other summaries: how fragmented the
signal is, how fast it repeats, or where it sits in its cycle (phase). Points around which phase
winds through a full cycle are phase singularities, the signature of a rotor in theory. Every one
of these maps depends on processing choices and on electrode spacing, so each must be tested on
data where the truth is known.

### 2. From the field

Lessons tied to verified sources:

- Complex fractionated atrial electrograms (CFAE) were proposed as ablation targets in a large
  single-centre series ([nademanee2004]). A later randomized trial found no reduction in recurrence
  when CFAE ablation was added to pulmonary-vein isolation in persistent AF ([verma2015]).
- DF maps built from electroanatomic points identified sites of high-frequency activity during AF
  ([sanders2005]); DF estimates depend on bipolar vs unipolar recording, electrode spacing,
  preprocessing, far-field ventricular signals and window length ([ng2007tech]).
- In high-density epicardial recordings, at least eight electrodes in a detection ring were needed
  to avoid frequent false-positive PS due to chance ([kuklik2017]).
- The spatial resolution needed to identify rotors and focal sources is a linear function of the
  arrhythmia's spatial wavelength ([roney2017]).
- Rotors found by phase analysis of filtered epicardial electrograms coincided with regions of
  conduction block in a direct comparison with activation maps ([podziemski2018]).

### 3. Derivations

Notation: $x(t)$ electrogram, $X(f)$ its Fourier transform, $f_s$ sampling rate (Hz), $\varphi$
phase (rad), $\mathcal{H}$ Hilbert transform, $v$ conduction velocity (m/s), $\mathrm{CL}$ cycle
length (ms), $\lambda_s$ spatial wavelength (mm), $n$ topological charge.

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m29-fi | $\overline{\Delta t} = \dfrac{t_N - t_1}{N - 1}$ over deflections detected in a window | Interval-based fractionation index: mean interval between detected deflections | exact | Numeric: synthetic trains with known intervals; sensitivity to the detection threshold |
| eq-m29-df | $\mathrm{DF} = \arg\max_{f \in [f_{\text{lo}}, f_{\text{hi}}]} \lvert X(f)\rvert^2$ | Dominant frequency after preprocessing (band-pass, rectification, low-pass) | exact | Numeric: periodic synthetic train with known rate; recovers $1000/\mathrm{CL}$ Hz |
| eq-m29-oi | $\mathrm{OI} = \dfrac{\sum_{h=1}^{4} \text{area under harmonic peak } h}{\text{total spectral area}}$ | Organization index from the first four harmonics ([everett2001]) | exact | Numeric: periodic signal gives OI near 1; noise gives a low OI |
| eq-m29-hilbert | $z(t) = x(t) + i\,\mathcal{H}[x](t)$, $\varphi(t) = \arg z(t)$ | Instantaneous phase from the analytic signal | exact | SymPy: $\mathcal{H}[\cos\omega t] = \sin\omega t$; numeric: phase of a cosine is linear |
| eq-m29-recomposition | Each detected activation replaced by one sine period of length CL, weighted by the local negative slope | Sinusoidal recomposition before the Hilbert transform ([kuklik2014]); exact form to copy from the paper | approximate model | Numeric: one phase cycle per activation on synthetic electrograms |
| eq-m29-charge | $n = \dfrac{1}{2\pi}\oint \nabla\varphi\cdot d\boldsymbol{\ell} = \dfrac{1}{2\pi}\sum_{k} \mathrm{wrap}(\varphi_{k+1} - \varphi_k)$ | Topological charge around a closed ring; $\pm1$ at a PS, 0 elsewhere ([bray2002]) | exact | Numeric: spiral phase field $\varphi = \operatorname{atan2}(y, x) - \omega t$ gives $n = 1$; plane wave gives 0 |
| eq-m29-wavelength | $\lambda_s = v \cdot \mathrm{CL}$ | Spatial wavelength: distance between successive wavefronts | exact | Numeric: measured from a simulated plane-wave train |

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline. d2 and d3 use a small precomputed 2D
simulation (target ≤ 2 MB).

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m29-d1 | Spectra of AF-like signals | cycle length, jitter, fractionation, far-field ventricular amplitude, window length | Synthetic electrogram, its spectrum, DF and OI; how far-field signals and short windows move the DF | approximate model |
| m29-d2 | Phase and singularities | ring size, electrode spacing, noise, phase method (Hilbert, recomposition) | Phase map of a simulated rotor from a Mitchell–Schaeffer 2D model; detected PS vs the true tip trajectory | simulation |
| m29-d3 | Resolution and false drivers | electrode spacing, interpolation method | The same simulated field sampled on coarse and dense grids; PS count, localization error and false positives vs spacing / wavelength | simulation |

Assumptions to list under the demos: synthetic electrograms from the m03 model with added
fractionation (d1); monodomain 2D sheet, isotropic, Mitchell–Schaeffer kinetics, explicit finite
differences with stated grid and time step (d2, d3); electrograms approximated from the
transmembrane field as stated in the demo.

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: driver-guided ablation in trials, reported evenly. The CONFIRM trial reported better
outcomes when localized sources found by computational mapping were ablated in addition to
conventional ablation ([narayan2012]). The multicentre randomized REAFFIRM trial did not show
superiority of adding focal or rotational source ablation to conventional ablation in persistent
AF ([brachmann2025]). For CFAE, see [nademanee2004] and [verma2015]. The section describes what was
measured and found; it does not say what to do.

### 6. Visual summary and How experts think

- Visual summary: one simulated rotor shown four ways (activation, DF, phase, PS track), each with
  its processing chain. Badge: schematic.
- How experts think: "Would this detector find a rotor in noise alone?" Run every driver algorithm
  on data with no driver, and on data with a known driver, before trusting its map.

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including "why does a
phase singularity detector need a minimum number of electrodes?" and "what can shift the dominant
frequency without changing the activation rate?".

### 8. Code lab and Self-check

Lab: `labs/python/m29_lab.ipynb` (Python only).

| Part | Task | Data |
| --- | --- | --- |
| A | Fractionation index and DF/OI on synthetic electrograms; sensitivity to filter and threshold | Synthetic |
| B | Hilbert phase vs sinusoidal recomposition on unipolar-like signals | Synthetic |
| C | 2D Mitchell–Schaeffer sheet in NumPy; start a rotor by cross-field stimulation (small grid to fit the 5-minute CI limit) | Simulation |
| D | PS detection with topological charge; precision and recall against the true tip trajectory | Simulation |
| E | Electrode spacing and interpolation: resample the sheet on coarse grids; false positives and localization error vs $\lambda_s$ | Simulation |
| F | Null test: run the detectors on fields with no rotor (planar waves, random noise) | Synthetic |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. Candidates: phase-map figures in [kuklik2017] or
[roney2017] (licenses to check); otherwise regenerate from our own simulation.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| nademanee2004 | Nademanee K, et al. A new approach for catheter ablation of atrial fibrillation: mapping of the electrophysiologic substrate. J Am Coll Cardiol 2004;43(11):2044–2053. DOI 10.1016/j.jacc.2003.12.054, PMID 15172410 | Verified (PubMed) |
| verma2015 | Verma A, et al. Approaches to catheter ablation for persistent atrial fibrillation (STAR AF II). N Engl J Med 2015;372(19):1812–1822. DOI 10.1056/NEJMoa1408288, PMID 25946280 | Verified (PubMed) |
| sanders2005 | Sanders P, et al. Spectral analysis identifies sites of high-frequency activity maintaining atrial fibrillation in humans. Circulation 2005;112(6):789–797. DOI 10.1161/CIRCULATIONAHA.104.517011, PMID 16061740 | Verified (PubMed) |
| ng2007tech | Ng J, Kadish AH, Goldberger JJ. Technical considerations for dominant frequency analysis. J Cardiovasc Electrophysiol 2007;18(7):757–764. DOI 10.1111/j.1540-8167.2007.00810.x, PMID 17578346 | Verified (PubMed) |
| ng2007 | Ng J, Goldberger JJ. Understanding and interpreting dominant frequency analysis of AF electrograms. J Cardiovasc Electrophysiol 2007;18(6):680–685. DOI 10.1111/j.1540-8167.2007.00832.x, PMID 17472716 | Verified (PubMed) |
| everett2001 | Everett TH, et al. Frequency domain algorithm for quantifying atrial fibrillation organization to increase defibrillation efficacy. IEEE Trans Biomed Eng 2001;48(9):969–978. DOI 10.1109/10.942586, PMID 11534845 | Verified (PubMed) |
| botteron1995 | Botteron GW, Smith JM. A technique for measurement of the extent of spatial organization of atrial activation during atrial fibrillation in the intact human heart. IEEE Trans Biomed Eng 1995;42(6):579–586. DOI 10.1109/10.387197, PMID 7790014 | Verified (PubMed); source for the preprocessing chain (filter values to read from the full text) |
| gray1998 | Gray RA, Pertsov AM, Jalife J. Spatial and temporal organization during cardiac fibrillation. Nature 1998;392(6671):75–78. DOI 10.1038/32164, PMID 9510249 | Verified (PubMed) |
| bray2001 | Bray MA, et al. Experimental and theoretical analysis of phase singularity dynamics in cardiac tissue. J Cardiovasc Electrophysiol 2001;12(6):716–722. DOI 10.1046/j.1540-8167.2001.00716.x, PMID 11405407 | Verified (PubMed) |
| bray2002 | Bray MA, Wikswo JP. Use of topological charge to determine filament location and dynamics in a numerical model of scroll wave activity. IEEE Trans Biomed Eng 2002;49(10):1086–1093. DOI 10.1109/TBME.2002.803516, PMID 12374332 | Verified (PubMed) |
| kuklik2014 | Kuklik P, et al. Reconstruction of instantaneous phase of unipolar atrial contact electrogram using a concept of sinusoidal recomposition and Hilbert transform. IEEE Trans Biomed Eng 2015;62(1):296–302. DOI 10.1109/TBME.2014.2350029, PMID 25148659 | Verified (PubMed) |
| kuklik2017 | Kuklik P, et al. Identification of rotors during human atrial fibrillation using contact mapping and phase singularity detection: technical considerations. IEEE Trans Biomed Eng 2017;64(2):310–318. DOI 10.1109/TBME.2016.2554660, PMID 27101596 | Verified (PubMed) |
| roney2017 | Roney CH, et al. Spatial resolution requirements for accurate identification of drivers of atrial fibrillation. Circ Arrhythm Electrophysiol 2017;10(5):e004899. DOI 10.1161/CIRCEP.116.004899, PMID 28500175 | Verified (PubMed) |
| podziemski2018 | Podziemski P, et al. Rotors detected by phase analysis of filtered, epicardial atrial fibrillation electrograms colocalize with regions of conduction block. Circ Arrhythm Electrophysiol 2018;11(10):e005858. DOI 10.1161/CIRCEP.117.005858, PMID 30354409 | Verified (PubMed) |
| narayan2012 | Narayan SM, et al. Treatment of atrial fibrillation by the ablation of localized sources: CONFIRM trial. J Am Coll Cardiol 2012;60(7):628–636. DOI 10.1016/j.jacc.2012.05.022, PMID 22818076 | Verified (PubMed) |
| brachmann2025 | Brachmann J, et al. Prospective randomized trial of rotor ablation vs conventional ablation for persistent atrial fibrillation: REAFFIRM trial. J Am Heart Assoc 2025;14(13):e022346. DOI 10.1161/JAHA.121.022346, PMID 40530478 | Verified (PubMed) |
| mitchell2003 | Mitchell CC, Schaeffer DG. A two-current model for the dynamics of cardiac membrane. Bull Math Biol 2003;65(5):767–793. DOI 10.1016/S0092-8240(03)00041-7, PMID 12909250 | Verified (PubMed) |

## Still to source (before stage 2)

Each is `TODO(source)` until found:

- Typical AF cycle lengths and conduction velocities in human atria (for demo defaults and
  $\lambda_s$)
- The DF search band and preprocessing filter values (from [botteron1995] and [ng2007tech] full
  texts)
- Mitchell–Schaeffer parameter values for atrial tissue, and a tissue diffusion coefficient
- CFAE detection parameters used in published algorithms (described generically; vendor algorithms
  only from public sources)
- Electrode spacing of common multielectrode catheters (public specifications or papers), for d3

## Glossary terms to add

fractionation · complex fractionated atrial electrogram (CFAE) · dominant frequency (DF) ·
organization index (OI) · instantaneous phase · analytic signal · Hilbert transform · sinusoidal
recomposition · phase singularity (PS) · topological charge · rotor · focal source · driver ·
spatial wavelength · ground truth

## Formula-sheet entries

eq-m29-df · eq-m29-oi · eq-m29-hilbert · eq-m29-charge · eq-m29-wavelength

## Questions for the author

1. **Overlap with m05:** m05 (time–frequency tools) will define DF and Hilbert phase. Define them in
   m29 now (labelled `eq-m29-*`) and move them when m05 is written, or write m05 first?
2. **Simulation in the lab:** a NumPy Mitchell–Schaeffer sheet keeps the lab self-contained but
   limits grid size; precompute a larger run and ship it (≤ 5 MB in `data/samples/`), or keep it
   live?
3. **Clinical evidence:** CONFIRM, REAFFIRM, the CFAE series and STAR AF II give both sides. Add more
   trials or meta-analyses, or is this balance enough for an engineering course?
4. **Real recordings:** m29 stays synthetic and m31 handles iafdb. Agree?
