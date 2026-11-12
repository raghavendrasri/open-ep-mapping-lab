# Curriculum

Seven parts, 47 modules. Part IV (map formation) is the core of the course and ships first.
Part VII (AI in electrophysiology) was added in November 2026; its plan is in
`docs/outlines/part7-overview.md`. Modules m46 and m47 were added to Part VII on 2026-11-11 with the
author's approval, after m45, so that no module was renumbered.
Change this list only with the author's approval.

## Part I · Math and bioelectric foundations

| ID | Module |
| --- | --- |
| m01 | Bioelectric sources: transmembrane current, dipoles and double layers |
| m02 | Volume conduction and Poisson's equation |
| m03 | Unipolar, bipolar and omnipolar electrograms as spatial filters |
| m04 | Sampling, filtering and the EP recording chain |
| m05 | Time–frequency tools: dominant frequency, Hilbert phase, wavelets |
| m06 | Triangle meshes, Laplace–Beltrami operators and geodesics |
| m07 | Inverse problems and regularization (Tikhonov, L-curve) |

## Part II · Cardiac electrophysiology for engineers

| ID | Module |
| --- | --- |
| m08 | Action potentials and ionic models, from FitzHugh–Nagumo to detailed atrial models |
| m09 | Propagation: cable theory, monodomain and bidomain, anisotropy |
| m10 | Arrhythmia mechanisms: focal, macro-reentry, rotors, atrial fibrillation |
| m11 | The EP study: catheters, pacing protocols, intervals, entrainment |
| m12 | The surface ECG and the forward problem |

## Part III · Hardware and localization

| ID | Module |
| --- | --- |
| m13 | Catheter design: electrode size and spacing, high-density grids, baskets, contact-force sensing |
| m14 | Biopotential front ends: instrumentation amplifiers, CMRR, noise, Wilson central terminal, ADCs |
| m15 | Patient safety: CF-type applied parts, leakage current, isolation, defibrillation and ablation-energy protection |
| m16 | Magnetic localization: field generators, sensor coils, pose solvers |
| m17 | Impedance (current-based) localization: patch fields, nonlinearity, field scaling |
| m18 | Hybrid and dielectric localization concepts |
| m19 | Motion and drift: respiration, cardiac gating, reference catheters |

## Part IV · Map formation

| ID | Module |
| --- | --- |
| m20 | Geometry from catheter positions: point clouds to surfaces |
| m21 | Image integration: CT/MRI segmentation, landmark and ICP registration |
| m22 | Electrogram annotation: local activation time, window of interest, reference, far-field rejection |
| m23 | Voltage mapping: amplitude, thresholds, dependence on wavefront direction |
| m24 | Interpolation, activation maps and isochrones |
| m25 | Conduction velocity estimation: triangulation, surface fitting, omnipolar methods |
| m26 | Map quality and uncertainty: point density, annotation error, interpolation error |

## Part V · Therapy and capstones

| ID | Module |
| --- | --- |
| m27 | RF ablation biophysics and lesion metrics (power, force, time, impedance drop) |
| m28 | Pulsed field ablation: electroporation and what it changes for mapping |
| m29 | Complex maps: fractionation, phase mapping, rotor and driver detection |
| m30 | Capstone: build a mini mapping system on a simulated atrium |
| m31 | Capstone: AF electrogram analysis on real recordings (PhysioNet iafdb) |
| m32 | Capstone: ECG imaging end to end (EDGAR) |
| m33 | Capstone: from map to digital twin (OpenEP to openCARP) |

## Part VI · Systems and practice

| ID | Module |
| --- | --- |
| m34 | Mapping-system software architecture: real-time pipeline, latency, data formats |
| m35 | Machine learning in EP mapping: annotation, driver detection, validation pitfalls |
| m36 | From prototype to product: FDA Class II (21 CFR 870.1425, product code DQK), 510(k), IEC 60601-1, IEC 62304, ISO 14971, EU MDR |

## Part VII · AI in electrophysiology

| ID | Module |
| --- | --- |
| m37 | AI on the surface ECG: rhythm classification, detecting hidden disease, external validation |
| m38 | Wearables and implantable monitors: PPG and single-lead ECG, alert triage, remote monitoring |
| m39 | AI on intracardiac electrograms and maps: electrogram classification, graph learning on mapping data, AI-guided ablation trials |
| m40 | AI for cardiac imaging and substrate: atrial segmentation, scar and fibrosis, automated chamber reconstruction |
| m41 | Locating arrhythmia origins from the ECG: regression and deep learning, simulation-trained models, active pace-mapping |
| m42 | Physics-informed machine learning: PINNs, surrogate models, uncertainty for digital twins |
| m43 | Foundation models and large language models: self-supervised ECG encoders, LLM evaluation, retrieval |
| m44 | Agentic AI in EP: tool-using agents, workflow automation, guardrails and human oversight |
| m45 | Evidence and regulation of AI in EP: study designs, reporting checklists, change control and monitoring |
| m46 | Trustworthy AI in EP: explanations, uncertainty and conformal prediction, fairness, out-of-distribution inputs and robustness |
| m47 | Data and deployment engineering for AI in EP: data formats, labelling, de-identification, versioning, quantization and model cards |

## Learning paths

| Path | Modules |
| --- | --- |
| Mapping-system software engineer | m01–m07, m20–m26, m30, m34, m35 |
| Localization and hardware engineer | m01–m04, m13–m19, m34, m36, plus bench track |
| Clinical mapping specialist or EP fellow | m03, m08–m12, m20–m29, m31 |
| Computational modeller | m01, m02, m05–m09, m12, m24, m25, m29, m33 |
| AI in EP (engineers and clinicians) | m03, m04, m12, m22, m35, m37–m47 |
| Interview prep | Interview questions across all modules |

## Release order

| Release | Modules |
| --- | --- |
| Pilot | m03 |
| v0.1 (MVP) | m03, m04, m20, m22, m23, m24, m25, m30 |
| v0.5 | Parts I–III, plus m21, m26 |
| v1.0 | Parts V–VI, formula sheet, glossary, interview bank |
| v1.5 | Part VII |
