# Part VII overview · AI in electrophysiology

Curriculum proposal for Part VII (modules m37–m45). Nothing here is course text yet. This file
defines each module's scope, use cases, planned equations, demos, labs and sources, so the author
can approve the plan before the stage-1 outlines are written.

Status: **draft, awaiting author review.**

## Why a Part VII

Parts I–VI teach how mapping systems work. AI now touches every step around them: the surface ECG
before a procedure, wearables and implants after it, electrogram analysis and imaging during it,
and the software that ties the steps together. Readers asked for this (author request, November
2026). Part VII applies the validation basics of m35 to real AI tasks in EP, and adds two topics
the course does not cover yet: foundation models and agentic AI.

Ground rules for Part VII (also added to `CLAUDE.md` §2):

- Report AI results as the cited study reports them: data set, split, metric and confidence
  interval. A retrospective accuracy is not proof of clinical benefit.
- "AI-guided" is not "autonomous". Every use case names the human checkpoint.
- Labs and demos run offline. They never call external AI services. Language-model and agent labs
  use a scripted stand-in model in CI; an optional cell can use a real model with the reader's own
  key, skipped in CI and never with patient data.
- No advice on patient care. Clinical correlates describe what studies found and stay
  `pending clinical review`.

Prerequisites for the whole part: m04 (recording chain) and m35 (machine-learning validation).
Each module lists its own extra prerequisites.

## Module list

| ID | Module | One-line scope | Builds on |
| --- | --- | --- | --- |
| m37 | AI on the surface ECG | Deep networks that read rhythm, and find disease a reader cannot see; why external validation decides | m04, m12, m35 |
| m38 | Wearables and implantable monitors | PPG and single-lead ECG screening, low prevalence, alert triage for loop recorders and devices | m04, m35, m37 |
| m39 | AI on intracardiac electrograms and maps | Electrogram classification, graph learning on mapping meshes, the AI-guided ablation trials | m22, m23, m29, m35 |
| m40 | AI for cardiac imaging and substrate | Atrial segmentation, scar and fibrosis models, automated chamber reconstruction | m20, m21, m35 |
| m41 | Locating arrhythmia origins from the ECG | Regression and deep learning on the 12-lead ECG, simulation-trained models, active pace-mapping | m06, m12, m32 |
| m42 | Physics-informed machine learning | PINNs, surrogate models and uncertainty for digital twins | m09, m33 |
| m43 | Foundation models and large language models | Self-supervised ECG encoders, how to evaluate LLMs on EP tasks, retrieval | m37 |
| m44 | Agentic AI in EP | Tool-using agents, workflow automation, guardrails and human oversight | m35, m43 |
| m45 | Evidence and regulation of AI in EP | From retrospective AUC to randomized trials, reporting checklists, change control and monitoring | m35, m36 |

## Use-case catalogue

How AI techniques are being used in EP, one example per row, each from a verified source (see
[Sources](#sources)). "Evidence" says what kind of study it is, so readers do not mistake a
retrospective result for a proven benefit.

| Technique | EP task | Example | Evidence | Module |
| --- | --- | --- | --- | --- |
| Deep convolutional network | Rhythm classes from single-lead ambulatory ECG | [hannun2019] | Retrospective, cardiologist-annotated test set | m37 |
| Deep convolutional network | Six abnormalities on the 12-lead ECG, compared with cardiology residents | [ribeiro2020] | Retrospective | m37 |
| Deep network, "hidden" signal | Signs of AF in an ECG recorded in sinus rhythm | [attia2019] | Retrospective | m37 |
| AI-ECG used to guide screening | Targeted AF screening | [noseworthy2022] | Prospective, non-randomized | m37 |
| AI-ECG used in care | Finding low ejection fraction in primary care | [yao2021] | Pragmatic randomized trial | m37, m45 |
| AI-guided screening | Cardiomyopathy in pregnancy, with a digital stethoscope | [adedinsewo2024] | Pragmatic randomized trial | m37, m45 |
| PPG irregular-pulse algorithm | AF notification from a smartwatch | [perez2019] | Large prospective single-arm study | m38 |
| PPG irregular-pulse algorithm | AF notification from fitness trackers | [lubitz2022] | Large prospective single-arm study | m38 |
| Implant-side detection algorithms | Fewer false loop-recorder alerts | [neiman2024], [covino2024] | Retrospective cohort; systematic review | m38 |
| Machine learning on device data | Alert filtering, event prediction, device programming | [antoun2025] | Narrative review | m38 |
| Supervised CNN with expert labels | Rotational activation in AF electrograms | [alhusseini2020] | Retrospective, labeled by experts | m39 |
| Spectral features plus ML, optical ground truth | AF driver detection by multi-electrode mapping | [zolotarev2020] | Ex vivo human hearts | m39 |
| Electrogram-dispersion detection (AI) | Choosing extra ablation areas beyond PVI | [seitz2017] (visual method), [deisenhofer2025] | Randomized trial (TAILORED-AF) and follow-ups | m39, m45 |
| 1-D CNN with saliency maps | Locating ganglionated plexi from bipolar electrograms | [guler2026] | Retrospective, held-out atria | m39 |
| Graph convolutional network | Isthmus areas of scar-related atrial tachycardia on mapping points | [saluja2024] | Retrospective, small cohort | m39 |
| Unsupervised clustering (Gaussian mixture) | Voltage-distribution phenotypes of atrial cardiomyopathy | [huttelmaier2026] | Retrospective, small cohort | m39 |
| Segmentation networks | Left atrium from late-gadolinium MRI | [xiong2020] | Open benchmark challenge | m40 |
| Deep survival model on images | Arrhythmic death risk from scar on cardiac MRI | [popescu2022] | Multicentre internal validation and an independent test set | m40 |
| Deep-learning reconstruction | Left-atrial shell from intracardiac echo, no manual contouring | [zou2026] | Before-and-after cohort | m40 |
| Linear and nonlinear regression | Ventricular activation origin from the 12-lead ECG | [zhou2018] | Pace-mapping data | m41 |
| Hybrid ML with active guidance | VT exit-site localization with few pacing sites | [missel2020] | Clinical pace-mapping data, separate test cohort | m41 |
| Bayesian optimization | Choosing the next pacing site (active pace-mapping) | [meisenzahl2024] | Simulation | m41 |
| Logistic regression on ECG features | Right versus left outflow-tract PVC origin | [botis2026] | Retrospective, small cohort | m41 |
| Physics-informed neural network | Tissue parameters from activation data | [herreromartin2022] | Simulation and optical mapping | m42 |
| Ensemble PINN | Atrial fibre orientation with uncertainty, from mapping activation times | [magana2025] | Method study, eight atrial anatomies | m42 |
| Contrastive pretraining (foundation model) | One ECG encoder for many prediction tasks | [ko2026], [khattak2026], [sangha2024] | Retrospective, external validation in [ko2026] | m43 |
| Large language model | Reading ECGs and pacemaker electrograms from images | [chai2026], [zeljkovic2025], [bozyel2025] | Benchmark studies | m43 |
| Local (on-site) language model | Questions over a patient's report history without sending data out | [vaid2024] | Feasibility study (echo reports) | m43, m44 |
| LLM agent with analysis tools | Heart rate from wearable PPG | [feli2025] | Benchmark against ECG reference | m44 |
| Agentic model search | Proposing, testing and selecting ECG model designs | [jamthikar2026] | Preprint, external validation | m44, m45 |
| NLP and agentic workflow | Literature review, guideline monitoring, report drafts | [patel2025] | Method description | m44 |
| ML versus risk scores | AF recurrence after ablation | [koh2026] | Meta-analysis | m45 |

## Agentic AI in EP

### What an agent is

An AI agent is a program in which a model, usually a large language model (LLM), decides step by
step which tool to call, reads the result, and carries on until the goal is met or it stops.
[khosravi2026] defines agents as AI that perceives and acts on its environment to reach a goal, and
names the parts: memory that persists across steps, retrieval of medical knowledge, and the use of
clinical software. It also describes ways to coordinate several agents (hierarchical,
collaborative, sequential) and a phased path from low-risk automation to whole workflows.

The pieces m44 builds, in the course's own words:

| Piece | What it does | EP example |
| --- | --- | --- |
| Model | Chooses the next action | Decides to check point density before computing conduction velocity |
| Tools | Do the real work, with typed inputs and units | `load_case`, `fill_distance`, `plane_fit_velocity`, `pubmed_lookup` |
| State and memory | Keeps what has been done and found | The audit log of a mapping-QC run |
| Control loop | Plan, act, observe, repeat, with a step limit | Up to 20 tool calls per task |
| Policy | Says which tools need human approval | Read and compute: automatic. Write or send: a human approves |

### Levels of autonomy (course framework, not a standard)

| Level | Name | Who acts | In scope for the course? |
| --- | --- | --- | --- |
| 0 | Tool | A person runs the model and acts | Yes |
| 1 | Assistant | The agent reads and drafts; a person acts | Yes |
| 2 | Supervised agent | The agent acts on reversible tasks; a person approves each write | Yes, main focus of m44 |
| 3 | Conditional autonomy | The agent acts within a pre-approved scope, with audit and rollback; people review samples | Discussed |
| 4 | Closed loop | The agent changes therapy or device settings without a person | Out of scope: regulated device territory (m36, m45) |

### Use cases

Each use case gives the goal, the tools the agent calls, the human checkpoint, the main risks, and
the evidence. "Illustrative" means we found no published end-to-end example; the course designs
one from published parts.

1. **Literature and guideline watch.** Goal: track new papers and guideline changes for a topic,
   and draft a summary with resolved citations. Tools: PubMed search, DOI resolver, a
   checklist scorer. Checkpoint: a person reads every cited source before use. Risks: invented
   citations, missed retractions, quotes too long for copyright. Evidence: [patel2025] describes
   such a workflow for EP; [sluha2025] tested whether LLMs can review AI-in-EP papers against the
   EHRA AI checklist. This course's own authoring workflow (draft with a PubMed connector, human
   sign-off, `review_record.json`) is a worked example.
2. **Wearable and Holter analysis.** Goal: answer a question about a recording ("what was the heart
   rate during the night?") by calling validated signal-processing tools instead of reading raw
   numbers. Tools: peak detector, heart-rate estimator, quality index. Checkpoint: a person reviews
   flagged segments. Risk: the model "reads" numbers and makes them up. Evidence: in [feli2025] an
   agent that called analysis tools estimated heart rate from PPG more accurately than LLMs given
   the data directly, with ECG as the reference.
3. **Remote-monitoring triage for loop recorders and implanted devices.** Goal: sort incoming
   transmissions so staff see likely true events first. Tools: a validated rhythm classifier, a
   report parser, a worklist writer. Checkpoint: a person adjudicates every alert; the agent never
   reprograms a device. Risks: a missed true event, automation bias, parsing errors across vendors.
   Evidence (components): historically about three in four loop-recorder alerts were false
   positives, and two newer remotely reprogrammable models with AI-based detection had 18.0% and
   38.3% false-positive alerts in one surveillance program ([neiman2024]; see also [covino2024]).
   [iwai2025] built an LLM-driven system that aggregated pacemaker remote-monitoring data
   (simulated files for 30 people) and estimated battery level, without the user writing code. [antoun2025] reviews AI for alert
   filtering, and notes reinforcement learning being explored for devices that adjust their own
   programming (level 4, out of scope). End-to-end agent: illustrative.
4. **Mapping-case quality check (research data).** Goal: load an exported case, check it, and
   draft a figure-backed summary for an analyst. Tools: OpenEP loader, fill distance and point
   density (m26), activation-time outlier check (m22), conduction velocity (m25). Checkpoint: the
   analyst reviews flagged points; nothing is written back to any clinical system. Risks: unit
   mix-ups (mm versus m), wrong reference channel, quietly dropping "bad" points. Evidence:
   illustrative; built on the course's own tested functions.
5. **Model development by agent ("agentic AutoML").** Goal: let an agent propose, train and compare
   model designs. Tools: training script, validation scorer, experiment log. Checkpoint: a person
   locks the external test set before the search starts and reads the trial log. Risk: choosing
   among many trials on the same validation data overfits it, the leakage problem of m35 in a new
   form. Evidence: [jamthikar2026] (preprint) used an LLM-driven loop to propose, validate and
   select ECG model designs, then tested them on external cohorts.
6. **Simulation and digital-twin runs.** Goal: choose parameters, run the model, check convergence
   and calibrate a twin to measured activation times. Tools: the m33 eikonal twin and calibrator,
   a convergence check, a Bayesian optimizer. Checkpoint: a person accepts the calibrated twin
   only with its cross-validation error. Risks: unconverged runs reported as results, compute
   cost. Evidence: [meisenzahl2024] chose the next pacing site by Bayesian optimization in
   simulation (a sequential-decision agent without an LLM); [missel2020] added active guidance to
   localization. LLM-driven orchestration: illustrative.
7. **Report drafting with a local model.** Goal: draft a structured procedure or device report
   from logs and notes. Tools: log parser, report template. Checkpoint: the clinician edits and
   signs. Risks: privacy (so a local model), a number in the report that no tool produced.
   Evidence: [vaid2024] ran an open-source LLM locally to answer questions over historic echo
   reports without sending data out. For EP: illustrative.
8. **Testing patient-information answers.** Goal (evaluation only): measure how accurate and
   consistent LLM answers about EP procedures are. Tools: a question bank, a grading rubric,
   retrieval over approved patient leaflets. Checkpoint: clinicians grade. Risk: a confident wrong
   answer. Evidence: [sritharan2024] and [kassar2024] graded LLM answers on EP procedures and on
   AF. The course teaches how to evaluate, not how to deploy.

A well-evaluated example from outside EP: DeepRare, a multi-agent system with more than 40 tools
for rare-disease diagnosis, linked each step of its reasoning to evidence, and experts agreed with
95.4% of its reasoning chains ([zhao2026]). m44 uses it as the model for how to evaluate an agent:
several data sets, outside centres, and an expert audit of the reasoning trace, not only the final
answer.

### Why agents must call tools for numbers

LLMs alone are not reliable readers of EP signals. In benchmark studies, general-purpose LLMs did
poorly at rhythm and axis on ECGs ([chai2026]), GPT-4's ECG accuracy changed with the clinical
context it was given ([zeljkovic2025]), and on pacemaker electrogram cases ChatGPT-4o was right 57%
of the time without context and 66% with it, falling to 30% and 25% in the complex scenarios
([bozyel2025]). The design rule in m44 follows: every number in an agent's output comes from a
tool, with the call logged.

### Failure modes and guardrails

| Failure | Guardrail taught in m44 |
| --- | --- |
| Invented numbers or citations | Numbers only from tool outputs; every citation resolved by DOI or PMID |
| Wrong tool arguments (units, lead order, sampling rate) | Typed tool schemas with units; tools validate their inputs |
| Instructions hidden in a document the agent reads (prompt injection) | Tool outputs are data, never instructions; the permission policy runs outside the model |
| Errors that compound over long chains | Step checks and retries; eq-m44-chain shows why |
| Patient data leaving the site | Local models, synthetic or public data only in the course |
| People trusting the agent too much (automation bias) | Show provenance and uncertainty; a person approves every write |
| The model or its version changes silently | Pin versions; rerun a fixed regression suite before use (links to m45) |
| Overfitting by agentic search | Lock the test set; log and count every trial |

## Module plans

Planned equations are candidates. Each gets a test in `tests/` at stage 2, as for every module.
Badges follow `CLAUDE.md` §4.

### m37 · AI on the surface ECG

**In 60 seconds.** Deep networks map raw ECG samples to labels and have matched or beaten physicians
on curated test sets: cardiologists for 12 rhythm classes on single-lead ambulatory ECGs
([hannun2019]), and cardiology residents for six abnormalities on 12-lead ECGs ([ribeiro2020]). They can also find signals no
reader uses, such as signs of AF in a sinus-rhythm ECG ([attia2019]). Whether that helps patients is
a separate question, answered only by prospective and randomized studies ([noseworthy2022],
[yao2021], [adedinsewo2024]).

**Learning goals.** (1) Explain a 1-D convolution as a learned FIR filter (link to m04) and compute
a network's receptive field. (2) Train and evaluate a rhythm classifier with patient-wise splits.
(3) Explain why performance drops on an external data set and measure it. (4) Read the evidence
level of an AI-ECG paper.

**Planned equations.** eq-m37-conv (1-D convolution), eq-m37-receptive-field
($r = 1 + \sum_l (k_l - 1)\prod_{j<l} s_j$), eq-m37-softmax-ce (softmax and cross-entropy), reuse of
eq-m35-ppv for screening yield.

**Demos.** m37-d1 "What a filter sees": a learned-looking kernel slides over an ECG, with the output
trace (exact). m37-d2 "Screening yield": positives found and false alarms per 1,000 people as
prevalence and threshold change (exact).

**Lab.** Train an AF detector on PhysioNet/CinC Challenge 2017 single-lead recordings
([clifford2017]), then test it unchanged on lead I of PTB-XL ([wagner2020]), whose recommended
folds keep each patient in one fold (PhysioNet page, checked 2026-11-10). Compare RR-irregularity
features with logistic regression against a small 1-D CNN (dependency question below). Report AUC,
calibration and the external drop.

### m38 · Wearables and implantable monitors

**In 60 seconds.** Smartwatches and trackers flag irregular pulse from PPG, and large prospective
studies measured how often a notification was followed by AF on an ECG patch ([perez2019],
[lubitz2022]). At low
prevalence even a good detector produces many false alerts. Loop recorders face the same problem
at clinic scale; newer detection algorithms cut the alert burden ([neiman2024], [covino2024],
[antoun2025]).

**Learning goals.** (1) Explain how PPG differs from ECG and what motion does to it. (2) Compute
positive predictive value and daily review workload for a clinic. (3) Design an alert triage with
a human in the loop. (4) Explain where an agent fits and where it must not act (link to m44).

**Planned equations.** eq-m38-hr (heart rate from inter-beat intervals), eq-m38-workload (false
alerts per day $= N\,\lambda\,(1 - \mathrm{PPV})$, with $N$ patients and $\lambda$ alerts per
patient per day), eq-m38-ptt (pulse arrival delay between ECG and PPG).

**Demos.** m38-d1 "Alert inbox": clinic size, alert rate and PPV give the daily review load
(exact). m38-d2 "PPG versus ECG beats": a synthetic PPG with motion artifact under its ECG
(approximate model).

**Lab.** Synthetic PPG built from ECG R-peaks with a pulse delay and motion noise; an irregularity
detector; a synthetic alert stream sorted by a triage rule. Synthetic data only, unless a public
PPG data set with a clear license is found (`TODO(source)`).

### m39 · AI on intracardiac electrograms and maps

**In 60 seconds.** Classifiers trained on expert labels can flag rotational activation
([alhusseini2020]), and optical mapping gives an independent ground truth for driver detection
([zolotarev2020]). The visually defined "spatiotemporal dispersion" of [seitz2017] became an AI
tool, and in the randomized TAILORED-AF trial AI-guided ablation of dispersion areas plus PVI was
superior to PVI alone at 1 year in persistent AF ([deisenhofer2025]). Follow-up analyses looked at
women, heart failure, later atrial tachycardias and redo procedures ([deisenhofer2025women],
[lakkireddy2025], [deisenhofer2025at], [hummel2026]). Mapping points also form a graph, so graph
networks can learn on them ([saluja2024]).

**Learning goals.** (1) Frame electrogram tasks as learning problems and say where labels come
from. (2) Explain graph convolution on a mapping mesh and relate it to the mesh Laplacian (m06).
(3) Choose metrics for spatial predictions: centroid distance and Dice, and why they can disagree.
(4) Describe what the AI-guided ablation trials did and did not test (clinical correlate, pending
review; no strategy advice).

**Planned equations.** eq-m39-gcn (one graph-convolution layer,
$H' = \sigma(\tilde D^{-1/2}\tilde A \tilde D^{-1/2} H W)$; source [kipf2017], to verify),
eq-m39-dice, eq-m39-centroid-distance (geodesic, from m06), eq-m39-gmm (Gaussian mixture
likelihood, for [huttelmaier2026]-style clustering).

**Demos.** m39-d1 "Graph convolution on a map": features spread over the mesh neighbours as layers
are added (exact). m39-d2 "Dispersion-like clusters": synthetic multipolar recordings with a
detector's score map (simulation, m29 models).

**Lab.** Synthetic cases from the m30 atrium with a slow region; electrogram features per point; a
NumPy graph network that predicts the slow region; case-wise split; Dice and centroid distance.
Teaching points: in [saluja2024] a median centroid distance of 7.3 mm in the test group came with
a mean Dice overlap of 13.9%; in [guler2026], with ganglionated-plexus windows near 3.5% of the
data, a recall of 0.85 came with a precision of 0.09 on validation, which is why m39 reports
precision–recall curves and not only ROC.

### m40 · AI for cardiac imaging and substrate

**In 60 seconds.** Segmentation networks outline the left atrium from MRI, and an open benchmark
compared many of them on the same data ([xiong2020]). Deep models on scar images have predicted
arrhythmic death risk ([popescu2022]). In the lab, a deep-learning module now builds the left-atrial
shell from intracardiac echo without manual contouring; one centre compared it with a historical
control group ([zou2026]).

**Learning goals.** (1) Compute Dice, Hausdorff and mean surface distance, and say when each
misleads. (2) Explain what a segmentation error does to a registered map (link to m21).
(3) Read a before-and-after study and name its biases.

**Planned equations.** eq-m40-dice, eq-m40-hausdorff, eq-m40-msd (mean surface distance).

**Demos.** m40-d1 "Segmentation metrics": move and blur a predicted contour, watch the metrics
(exact). m40-d2 "From mask to shell": a noisy mask becomes a mesh, and the error shows on the map
(simulation).

**Lab.** Synthetic atrial-like volumes with noise; threshold and a small network; metrics; effect on
voltage-map registration. Real imaging data only if an open license is confirmed (`TODO(source)`).

### m41 · Locating arrhythmia origins from the ECG

**In 60 seconds.** The QRS of a paced or ectopic beat carries its origin. Regression on simple QRS
features localized pacing sites on a generic left ventricle ([zhou2018]); active guidance and
Bayesian optimization pick the next pacing site to home in faster ([missel2020], [meisenzahl2024]).
Reviews summarize the field and its limits ([yang2024], [antoun2026]). Small single-centre models
need honest confidence intervals ([botis2026]).

**Learning goals.** (1) Build features from a simulated 12-lead ECG and fit a localization
regressor. (2) Measure error as geodesic distance on the heart surface (m06). (3) Derive the
Gaussian-process posterior and the expected-improvement rule. (4) Contrast learned localization
with physics-based ECG imaging (m32).

**Planned equations.** eq-m41-linear (origin = $W x + b$), eq-m41-geodesic-error, eq-m41-gp
(posterior mean and variance), eq-m41-ei (closed-form expected improvement).

**Demos.** m41-d1 "Active pace-mapping": the reader paces, a Gaussian process updates, the next
site is suggested (simulation). m41-d2 "Regression versus nearest neighbour" (simulation).

**Lab.** Synthetic sources on the m32 sphere model and the m30 atrium; regressors; then an active
loop. [meisenzahl2024] reported 3.9 ± 3.6 mm with 8.0 ± 4.0 pacing sites in simulation, a target to
compare against, with the caveat that our model is simpler.

### m42 · Physics-informed machine learning

**In 60 seconds.** A physics-informed neural network (PINN) fits data and a governing equation at
the same time. EP-PINNs estimated tissue parameters from activation data ([herreromartin2022]); an
ensemble of PINNs estimated atrial fibre directions with uncertainty ([magana2025]). Fast surrogates
of this kind could make the digital twins of m33 cheaper to calibrate ([corral2020],
[gillette2021]).

**Learning goals.** (1) Write a PINN loss for the eikonal equation. (2) Show how the physics term
helps where data are sparse. (3) Estimate uncertainty with an ensemble. (4) Know when a surrogate
is safe to use instead of the full model.

**Planned equations.** eq-m42-loss ($L = L_{\text{data}} + \lambda L_{\text{PDE}}$),
eq-m42-eikonal-residual ($v\,\lVert\nabla T\rVert - 1$), eq-m42-ensemble (mean and variance across
members). Source for PINNs in general: [raissi2019], to verify.

**Demos.** m42-d1 "Data versus physics": slide $\lambda$ and the number of points, see the fitted
activation map (simulation, precomputed). m42-d2 "Ensemble spread" (simulation).

**Lab.** A PINN-like fit without a deep-learning library: activation time as a sum of radial basis
functions, fitted by Gauss–Newton to points plus the eikonal residual. Compared with the m33
calibrated twin.

### m43 · Foundation models and large language models

**In 60 seconds.** A foundation model is pretrained once on many unlabeled ECGs and then adapted to
many tasks with few labels ([ko2026], [sangha2024], [ye2026]). Which data it was pretrained on
changes how well it transfers ([khattak2026], [yang2026] preprint); one model kept its accuracy
across demographic groups despite imbalanced training data ([hsieh2026]). General LLMs are not yet
reliable ECG or electrogram readers ([chai2026], [zeljkovic2025], [bozyel2025]), so evaluation
design matters more than prompts.

**Learning goals.** (1) Derive the contrastive (InfoNCE) loss and explain augmentations for ECG.
(2) Compare a linear probe on pretrained features with training from scratch, at several label
budgets. (3) Explain retrieval-augmented generation and build a retrieval step. (4) Design an LLM
evaluation: accuracy, consistency over repeats, and citation validity.

**Planned equations.** eq-m43-infonce, eq-m43-attention ($\mathrm{softmax}(QK^\top/\sqrt d)\,V$;
[vaswani2017], to verify), eq-m43-cosine (retrieval score).

**Demos.** m43-d1 "Contrastive embedding": augmented beats pull together, different patients push
apart (simulation). m43-d2 "Retrieval over the glossary": type a question, see ranked course
entries (exact, TF-IDF and cosine).

**Lab.** (A) Small contrastive pretraining on synthetic beats, then a linear probe. (B) Retrieval
over the course glossary and formula sheet. (C) An evaluation harness scored on recorded,
scripted answers; optional real-LLM cell, skipped in CI.

### m44 · Agentic AI in EP

Scope and use cases: see [Agentic AI in EP](#agentic-ai-in-ep) above.

**In 60 seconds.** An agent is a loop: a model chooses a tool, reads the result and chooses again.
That makes it useful for multi-step EP work (literature watch, data checks, report drafts,
simulation runs) and risky in new ways: errors compound, documents can carry hidden instructions,
and a confident summary can hide a number no tool produced. Good agents keep numbers in tools,
writes behind human approval, and every step in a log.

**Learning goals.** (1) Name the parts of an agent and build a minimal one. (2) Place a use case on
the autonomy scale and name its human checkpoint. (3) Derive how per-step reliability compounds over
a chain, and what a checking step buys. (4) Defend an agent against prompt injection with a policy
outside the model. (5) Evaluate an agent on a task suite and audit its traces ([zhao2026] as the
model).

**Planned equations.**

| ID | Equation | What it says | Badge of its figure |
| --- | --- | --- | --- |
| eq-m44-chain | $P_{\text{task}} = \prod_{i=1}^{n} p_i$ ($= p^n$ if equal) | Independent steps that each succeed with probability $p_i$ | exact (for the stated model) |
| eq-m44-check | $P_{\text{task}} = \left[1 - (1-p)(1-c)\right]^n$ | A check that catches a share $c$ of step errors, followed by a successful retry | exact (for the stated model) |
| eq-m44-escape | $E = N\,(1 - P_{\text{task}})(1 - r)$ | Expected wrong outputs that get past a human reviewer who catches a share $r$ | exact (for the stated model) |

All three assume independent steps; the module says so and shows a simulation where that fails.

**Demos.** m44-d1 "Agent trace explorer": step through a recorded run of the course's scripted
agent on a mapping-QC task; switch guardrails on and off (schema checks, approval gate, injection
filter) and see which steps are blocked (simulation, scripted agent). m44-d2 "Error compounding":
sliders for $p$, $n$, $c$ (exact).

**Lab.** About 150 lines of plain Python: a tool registry with typed, unit-checked schemas that
wraps course functions (`epml.mapping`, `epml.twin`); a scripted stand-in model so CI is
deterministic; a step-limited loop; permission tiers (read, compute, write); an approval callback;
a JSON-lines audit log; a prompt-injection test (a synthetic "mapping note" that asks the agent to
delete files must be blocked); and a 20-task evaluation suite compared with eq-m44-chain. Optional
cell: the same loop with a real model through a provider-neutral interface, skipped in CI.

**Clinical correlate (pending review).** Remote-monitoring triage (use case 3): what the published
components show, where a person must stay in the loop, and why level 4 is a regulated device.

### m45 · Evidence and regulation of AI in EP

**In 60 seconds.** Most AI-in-EP papers are retrospective. A meta-analysis found machine-learning
models discriminated AF recurrence better than risk scores, but calibration was rarely reported and
external validation was missing ([koh2026]). Reporting and appraisal tools exist for each stage:
TRIPOD+AI and PROBAST+AI for prediction models ([collins2024], [moons2025]), DECIDE-AI for early
clinical evaluation ([vasey2022]), SPIRIT-AI and CONSORT-AI for trials ([cruzrivera2020],
[liu2020]), and the EHRA AI checklist for EP ([svennberg2025]). Regulators handle model updates
through predetermined change control plans ([fdapccp2024]).

**Learning goals.** (1) Place a study on the evidence ladder: internal validation, external
validation, prospective silent use, randomized trial. (2) Apply PROBAST+AI and the EHRA checklist to
a recent EP paper (exercise: [wang2026], read neutrally). (3) Compute the sample size needed for a
target confidence-interval width on sensitivity. (4) Monitor a deployed model for drift and decide
when a change fits a PCCP. Overlap with m35 and m36: see the questions below.

**Planned equations.** eq-m45-n-sens (patients needed for a given CI width on sensitivity;
[buderer1996], to verify), eq-m45-cusum (cumulative-sum drift alarm; [page1954], to verify),
eq-m45-net-benefit (decision-curve net benefit; [vickers2006], to verify).

**Demos.** m45-d1 "Silent drift": a deployed model meets a shifted population; the CUSUM alarm
fires (simulation). m45-d2 "How many patients?" (exact).

**Lab (Part VII capstone).** Take the m37 detector; generate a TRIPOD+AI-style report card from the
lab's own outputs; simulate deployment with a population shift and monitor it; write a PCCP-style
change protocol with acceptance criteria, and test a retrained model against it.

## Data sets

| Data set | Used in | License | Status |
| --- | --- | --- | --- |
| PTB-XL 1.0.3, 12-lead ECG ([wagner2020]; DOI 10.13026/kfzx-aw45) | m37, m43, m45 | Creative Commons Attribution 4.0 | Verified on the PhysioNet page, 2026-11-10 |
| PhysioNet/CinC Challenge 2017, single-lead AF ([clifford2017]) | m37, m38 | Open Data Commons Attribution 1.0 | Verified on the AWS Open Data registry listing; confirm on PhysioNet at stage 1 |
| iafdb (already in m31) | m39 | As recorded in `data/registry.json` | Existing |
| EDGAR (already in m32) | m41 | As recorded in `data/registry.json` | Existing |
| Course simulations (m29, m30, m32, m33 models) | m39–m42, m44 | MIT (our code) | No license issue |
| Public PPG, MRI and implant-alert data sets | m38, m40 | Unknown | `TODO(source)` |

## Sources

All rows marked "Verified (PubMed)" were looked up on PubMed for this proposal. Bib entries are
added to `references.bib` at stage 2, when each module first cites them, as for Parts I–VI.

| Key | Source | Status |
| --- | --- | --- |
| hannun2019 | Hannun et al., Cardiologist-level arrhythmia detection and classification in ambulatory electrocardiograms using a deep neural network. Nat Med 25:65-69 (PubMed year 2019). DOI 10.1038/s41591-018-0268-3, PMID 30617320 | Verified (PubMed) |
| ribeiro2020 | Ribeiro et al., Automatic diagnosis of the 12-lead ECG using a deep neural network. Nat Commun 11:1760 (2020). DOI 10.1038/s41467-020-15432-4, PMID 32273514 | Verified (PubMed) |
| attia2019 | Attia et al., An artificial intelligence-enabled ECG algorithm for the identification of patients with atrial fibrillation during sinus rhythm: a retrospective analysis of outcome prediction. Lancet 394:861-867 (2019). DOI 10.1016/S0140-6736(19)31721-0, PMID 31378392 | Verified (PubMed) |
| yao2021 | Yao et al., Artificial intelligence-enabled electrocardiograms for identification of patients with low ejection fraction: a pragmatic, randomized clinical trial. Nat Med 27:815-819 (2021). DOI 10.1038/s41591-021-01335-4, PMID 33958795 | Verified (PubMed) |
| noseworthy2022 | Noseworthy et al., Artificial intelligence-guided screening for atrial fibrillation using electrocardiogram during sinus rhythm: a prospective non-randomised interventional trial. Lancet 400:1206-1212 (2022). DOI 10.1016/S0140-6736(22)01637-3, PMID 36179758 | Verified (PubMed) |
| adedinsewo2024 | Adedinsewo et al., Artificial intelligence guided screening for cardiomyopathies in an obstetric population: a pragmatic randomized clinical trial. Nat Med 30:2897-2906 (2024). DOI 10.1038/s41591-024-03243-9, PMID 39223284 | Verified (PubMed) |
| wagner2020 | Wagner et al., PTB-XL, a large publicly available electrocardiography dataset. Sci Data 7:154 (2020). DOI 10.1038/s41597-020-0495-6, PMID 32451379 | Verified (PubMed) |
| clifford2017 | Clifford et al., AF classification from a short single lead ECG recording: the PhysioNet/Computing in Cardiology Challenge 2017. Comput Cardiol 44 (PubMed year 2018). DOI 10.22489/CinC.2017.065-469, PMID 29862307 | Verified (PubMed) |
| perez2019 | Perez et al., Large-scale assessment of a smartwatch to identify atrial fibrillation. N Engl J Med 381:1909-1917 (2019). DOI 10.1056/NEJMoa1901183, PMID 31722151 | Verified (PubMed) |
| lubitz2022 | Lubitz et al., Detection of atrial fibrillation in a large population using wearable devices: the Fitbit Heart Study. Circulation 146:1415-1424 (2022). DOI 10.1161/CIRCULATIONAHA.122.060291, PMID 36148649 | Verified (PubMed) |
| neiman2024 | Neiman et al., Monitoring of remotely reprogrammable implantable loop recorders with algorithms to reduce false-positive alerts. J Am Heart Assoc 13:e032890 (2024). DOI 10.1161/JAHA.123.032890, PMID 38390808 | Verified (PubMed) |
| covino2024 | Covino et al., False-positive alarms in patients with implantable loop recorder followed by remote monitoring: a systematic review. Pacing Clin Electrophysiol 47:406-416 (2024). DOI 10.1111/pace.14941, PMID 38341627 | Verified (PubMed) |
| antoun2025 | Antoun et al., Artificial intelligence and the future of cardiac implantable electronic devices: diagnostics, monitoring, and therapy. J Clin Med 14:8824 (2025). DOI 10.3390/jcm14248824, PMID 41464726 | Verified (PubMed) |
| feli2025 | Feli et al., An LLM-powered agent for physiological data analysis: a case study on PPG-based heart rate estimation. Annu Int Conf IEEE Eng Med Biol Soc 2025:1-7. DOI 10.1109/EMBC58623.2025.11254428, PMID 41335782 | Verified (PubMed) |
| iwai2025 | Iwai et al., Evaluation of pacemaker battery level estimation using large language model and remote monitoring historical data. Annu Int Conf IEEE Eng Med Biol Soc 2025:1-6. DOI 10.1109/EMBC58623.2025.11251697, PMID 41336440 | Verified (PubMed) |
| alhusseini2020 | Already in `references.bib` | Verified (PubMed) |
| zolotarev2020 | Already in `references.bib` | Verified (PubMed) |
| seitz2017 | Seitz et al., AF ablation guided by spatiotemporal electrogram dispersion without pulmonary vein isolation: a wholly patient-tailored approach. J Am Coll Cardiol 69:303-321 (2017). DOI 10.1016/j.jacc.2016.10.065, PMID 28104073 | Verified (PubMed) |
| deisenhofer2025 | Deisenhofer et al., Artificial intelligence for individualized treatment of persistent atrial fibrillation: a randomized controlled trial. Nat Med 31:1286-1293 (2025). DOI 10.1038/s41591-025-03517-w, PMID 39953289 | Verified (PubMed) |
| deisenhofer2025women | Deisenhofer et al., Women with persistent atrial fibrillation need more than pulmonary vein isolation: personalised extra-pulmonary vein ablation strategy vs. pulmonary vein isolation alone in the TAILORED-AF trial. Europace 27 (2025). DOI 10.1093/europace/euaf281, PMID 41311304 | Verified (PubMed) |
| deisenhofer2025at | Deisenhofer et al., Targetable atrial tachycardias after artificial intelligence-guided ablation of persistent atrial fibrillation. Heart Rhythm 23:e357-e367 (PubMed year 2025). DOI 10.1016/j.hrthm.2025.11.018, PMID 41242590 | Verified (PubMed) |
| lakkireddy2025 | Lakkireddy et al., Artificial intelligence-guided personalized ablation improves freedom from atrial arrhythmia in heart failure: a sub-analysis of the TAILORED-AF trial. Heart Rhythm O2 7:390-392 (PubMed year 2025). DOI 10.1016/j.hroo.2025.12.007, PMID 41737944 | Verified (PubMed); no abstract, so not used for findings |
| hummel2026 | Hummel et al., Reablation of atrial fibrillation targeting electrogram dispersion in patients with isolated veins: the RESTART trial. Heart Rhythm 23:1083-1090 (2026). DOI 10.1016/j.hrthm.2026.01.042, PMID 41638617 | Verified (PubMed) |
| guler2026 | Guler et al., Convolutional neural network for real-time localization of ganglionated plexi from bipolar intracardiac electrograms. J Interv Card Electrophysiol 69:957-968 (2026). DOI 10.1007/s10840-026-02307-9, PMID 41903033 | Verified (PubMed) |
| saluja2024 | Saluja et al., Automated prediction of isthmus areas in scar-related atrial tachycardias using artificial intelligence. J Cardiovasc Electrophysiol 35:1401-1411 (2024). DOI 10.1111/jce.16299, PMID 38738814 | Verified (PubMed) |
| huttelmaier2026 | Huttelmaier et al., A novel signal distribution-based approach to characterize atrial cardiomyopathy. J Interv Card Electrophysiol 69:977-987 (2026). DOI 10.1007/s10840-026-02313-x, PMID 41973283 | Verified (PubMed) |
| xiong2020 | Xiong et al., A global benchmark of algorithms for segmenting the left atrium from late gadolinium-enhanced cardiac magnetic resonance imaging. Med Image Anal 67:101832 (PubMed year 2020). DOI 10.1016/j.media.2020.101832, PMID 33166776 | Verified (PubMed) |
| popescu2022 | Popescu et al., Arrhythmic sudden death survival prediction using deep learning analysis of scarring in the heart. Nat Cardiovasc Res 1:334-343 (2022). DOI 10.1038/s44161-022-00041-9, PMID 35464150 | Verified (PubMed) |
| zou2026 | Zou et al., Atrial fibrillation ablation using three-dimensional artificial intelligence module integration with intracardiac echocardiography. Europace 28 (2026). DOI 10.1093/europace/euag009, PMID 41546622 | Verified (PubMed); vendor module, describe generically |
| zhou2018 | Zhou et al., Localization of ventricular activation origin from the 12-lead ECG: a comparison of linear regression with non-linear methods of machine learning. Ann Biomed Eng 47:403-412 (PubMed year 2018). DOI 10.1007/s10439-018-02168-y, PMID 30465152 | Verified (PubMed) |
| missel2020 | Missel et al., A hybrid machine learning approach to localizing the origin of ventricular tachycardia using 12-lead electrocardiograms. Comput Biol Med 126:104013 (2020). DOI 10.1016/j.compbiomed.2020.104013, PMID 33002841 | Verified (PubMed) |
| meisenzahl2024 | Meisenzahl et al., BOATMAP: Bayesian optimization active targeting for monomorphic arrhythmia pace-mapping. Comput Biol Med 182:109201 (2024). DOI 10.1016/j.compbiomed.2024.109201, PMID 39342676 | Verified (PubMed) |
| yang2024 | Yang et al., Machine learning for localization of premature ventricular contraction origins: a review. Pacing Clin Electrophysiol 47:1481-1491 (2024). DOI 10.1111/pace.15089, PMID 39428720 | Verified (PubMed) |
| antoun2026 | Antoun et al., Artificial intelligence enabled noninvasive mapping of cardiac arrhythmia origins using the 12-lead electrocardiogram. J Cardiovasc Electrophysiol 37:847-853 (2026). DOI 10.1111/jce.70319, PMID 41845566 | Verified (PubMed) |
| botis2026 | Botis et al., Machine learning-based classification of right and left ventricular outflow tract premature ventricular contractions. Ann Noninvasive Electrocardiol 31:e70250 (2026). DOI 10.1111/anec.70250, PMID 42934986 | Verified (PubMed) |
| herreromartin2022 | Herrero Martin et al., EP-PINNs: cardiac electrophysiology characterisation using physics-informed neural networks. Front Cardiovasc Med 8:768419 (PubMed year 2022). DOI 10.3389/fcvm.2021.768419, PMID 35187101 | Verified (PubMed) |
| magana2025 | Magaña et al., Ensemble learning of the atrial fibre orientation with physics-informed neural networks. J Physiol 604:8201-8218 (PubMed year 2025). DOI 10.1113/JP288001, PMID 40973176 | Verified (PubMed) |
| corral2020, gillette2021 | Already in `references.bib` | Verified (PubMed) |
| ye2026 | Ye et al., Foundation models for cardiovascular diseases and medicine. Eur Heart J Digit Health 7:ztag113 (2026). DOI 10.1093/ehjdh/ztag113, PMID 42677193 | Verified (PubMed) |
| khattak2026 | Khattak et al., Data distribution impacts the performance and generalisability of contrastive learning-based foundation models of electrocardiograms. PLOS Digit Health 5:e0001623 (2026). DOI 10.1371/journal.pdig.0001623, PMID 42685022 | Verified (PubMed) |
| ko2026 | Ko et al., Development and external validation of a contrastive learning foundation model for ECG-based prediction of cardiovascular diseases and outcomes. Lancet Digit Health 101092 (2026). DOI 10.1016/j.landig.2026.101092, PMID 42680677 | Verified (PubMed) |
| hsieh2026 | Hsieh et al., Artificial intelligence electrocardiography for left ventricular systolic dysfunction demonstrates preserved performance across demographic training imbalances. Eur Heart J Digit Health 7:ztag080 (2026). DOI 10.1093/ehjdh/ztag080, PMID 42294406 | Verified (PubMed) |
| sangha2024 | Sangha et al., Biometric contrastive learning for data-efficient deep learning from electrocardiographic images. J Am Med Inform Assoc 31:855-865 (2024). DOI 10.1093/jamia/ocae002, PMID 38269618 | Verified (PubMed) |
| yang2026 | Yang et al., An ECG foundation model for generalizable cardiac function prediction across the lifespan. medRxiv (2026), preprint, not peer reviewed. DOI 10.64898/2026.05.26.26354128, PMID 42245005 | Verified (PubMed); preprint |
| chai2026 | Chai et al., Performance of large language models in electrocardiogram interpretation: a comparative study. J Electrocardiol 98:154411 (2026). DOI 10.1016/j.jelectrocard.2026.154411, PMID 42492187 | Verified (PubMed) |
| zeljkovic2025 | Zeljkovic et al., Beyond text: the impact of clinical context on GPT-4's 12-lead electrocardiogram interpretation accuracy. Can J Cardiol 41:1406-1414 (2025). DOI 10.1016/j.cjca.2025.01.036, PMID 39971004 | Verified (PubMed) |
| bozyel2025 | Bozyel et al., Large language models in intracardiac electrogram interpretation: a new frontier in cardiac diagnostics for pacemaker patients. Anatol J Cardiol 29:533-542 (2025). DOI 10.14744/AnatolJCardiol.2025.5238, PMID 40637685 | Verified (PubMed) |
| kassar2024 | Kassar et al., Performance of large language models as a resource for patients and healthcare professionals on atrial fibrillation. Heart Rhythm 21:2048-2050 (2024). DOI 10.1016/j.hrthm.2024.05.008, PMID 38734229 | Verified (PubMed); no abstract, read full text before citing findings |
| sritharan2024 | Sritharan et al., Utility of conversational artificial intelligence with large language models for patient information on cardiac electrophysiology procedures. Heart Rhythm 22:2131-2133 (PubMed year 2024). DOI 10.1016/j.hrthm.2024.10.007, PMID 39389520 | Verified (PubMed); no abstract, read full text before citing findings |
| vaid2024 | Vaid et al., Local large language models for privacy-preserving accelerated review of historic echocardiogram reports. J Am Med Inform Assoc 31:2097-2102 (2024). DOI 10.1093/jamia/ocae085, PMID 38687616 | Verified (PubMed) |
| patel2025 | Patel et al., Transforming electrophysiology workflows with natural language processing and agentic artificial intelligence. Heart Rhythm O2 6:1613-1620 (2025). DOI 10.1016/j.hroo.2025.07.013, PMID 41169964 | Verified (PubMed) |
| khosravi2026 | Khosravi et al., Agentic AI in radiology: evolution from large language models to future clinical integration. Radiol Artif Intell 8:e250651 (2026). DOI 10.1148/ryai.250651, PMID 41532836 | Verified (PubMed) |
| zhao2026 | Zhao et al., An agentic system for rare disease diagnosis with traceable reasoning. Nature 651:775-784 (2026). DOI 10.1038/s41586-025-10097-9, PMID 41708847 | Verified (PubMed) |
| jamthikar2026 | Jamthikar et al., Agentic autodiscovery of diastolic dysfunction phenotypes from surface electrocardiogram. medRxiv (2026), preprint, not peer reviewed. DOI 10.64898/2026.06.17.26355897, PMID 42396274 | Verified (PubMed); preprint |
| sluha2025 | Sluha et al., Reliability of large language models for reviewing research with artificial intelligence in cardiac electrophysiology using the European Heart Rhythm Association artificial intelligence checklist. Europace 27 (2025). DOI 10.1093/europace/euaf173, PMID 40795818 | Verified (PubMed); no abstract, read full text before citing findings |
| svennberg2025 | Svennberg et al., State of the art of artificial intelligence in clinical electrophysiology in 2025: a scientific statement of EHRA, HRS and the ESC Working Group on E-Cardiology. Europace 27 (2025). DOI 10.1093/europace/euaf071, PMID 40163651 | Verified (PubMed) |
| collins2024 | Already in `references.bib` (TRIPOD+AI) | Verified (PubMed) |
| moons2025 | Moons et al., PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods. BMJ 388:e082505 (2025). DOI 10.1136/bmj-2024-082505, PMID 40127903 | Verified (PubMed) |
| liu2020 | Liu et al., Reporting guidelines for clinical trial reports for interventions involving artificial intelligence: the CONSORT-AI extension. Nat Med 26:1364-1374 (2020). DOI 10.1038/s41591-020-1034-x, PMID 32908283 | Verified (PubMed) |
| cruzrivera2020 | Cruz Rivera et al., Guidelines for clinical trial protocols for interventions involving artificial intelligence: the SPIRIT-AI extension. Nat Med 26:1351-1363 (2020). DOI 10.1038/s41591-020-1037-7, PMID 32908284 | Verified (PubMed) |
| vasey2022 | Vasey et al., Reporting guideline for the early-stage clinical evaluation of decision support systems driven by artificial intelligence: DECIDE-AI. Nat Med 28:924-933 (2022). DOI 10.1038/s41591-022-01772-9, PMID 35585198 | Verified (PubMed) |
| koh2026 | Koh et al., Machine-learning versus traditional scoring methods for prediction of atrial fibrillation recurrence after catheter ablation: a systematic review and meta-analysis. Curr Probl Cardiol 52:103484 (2026). DOI 10.1016/j.cpcardiol.2026.103484, PMID 42880521 | Verified (PubMed) |
| wang2026 | Wang et al., Machine learning integration of ablation quality metrics for predicting atrial fibrillation recurrence: a multicenter study. JACC Clin Electrophysiol (2026). DOI 10.1016/j.jacep.2026.09.007, PMID 42886095 | Verified (PubMed) |
| fdapccp2024 | Already in `references.bib` (FDA PCCP final guidance for AI-enabled device software functions, December 2024) | Existing entry |
| fdaailist | FDA, Artificial Intelligence-Enabled Medical Devices (web page and device list), https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-enabled-medical-devices | Page found 2026-11-10; no counts quoted |
| ptbxl103 | Wagner et al., PTB-XL 1.0.3. PhysioNet (2022). DOI 10.13026/kfzx-aw45 | License checked on PhysioNet, 2026-11-10 |
| kipf2017 | Kipf and Welling, graph convolutional networks (ICLR 2017) | [unverified], look up at stage 1 |
| raissi2019 | Raissi, Perdikaris and Karniadakis, physics-informed neural networks (J Comput Phys 2019) | [unverified], look up at stage 1 |
| vaswani2017 | Vaswani et al., attention (NeurIPS 2017) | [unverified], look up at stage 1 |
| buderer1996 | Buderer, sample size for sensitivity and specificity (Acad Emerg Med 1996) | [unverified], look up at stage 1 |
| page1954 | Page, continuous inspection schemes (CUSUM; Biometrika 1954) | [unverified], look up at stage 1 |
| vickers2006 | Vickers and Elkin, decision curve analysis (Med Decis Making 2006) | [unverified], look up at stage 1 |

## Questions for the author

1. **Module list.** Nine modules, m37–m45, as above? Or fewer: for example fold m40 (imaging) into
   m39, or m42 (PINNs) into a second m33-style capstone.
2. **Overlap with m35 and m36.** Proposal: m35 keeps the validation basics (metrics, leakage,
   calibration), m36 keeps general device regulation, and AI-specific evidence and change control
   (PCCP, drift monitoring) move to m45, with pointers from m35 and m36. Approve?
3. **Deep-learning dependency.** m37, m40 and m43 need a small neural network. Add PyTorch (CPU) to
   `requirements.txt` (larger CI install), or keep NumPy-only implementations (more code, slower)?
   Recommendation: NumPy for m39, m41, m42 and m44; PyTorch CPU only for m37, m40 and m43.
4. **Real data in CI.** Ship small PTB-XL and Challenge 2017 subsets in `data/samples/` (both
   licenses allow redistribution with attribution; ≤ 5 MB each, with checksums), or download in
   CI?
5. **Real language models.** Allow one optional cell per LLM or agent lab that uses the reader's
   own API key (skipped in CI, synthetic data only)?
6. **Release.** Part VII as v1.5 after v1.0, or bring m44 forward because readers are asking for
   it?
7. **Learning paths.** The new "AI in EP" path is added. Should m42 also join the computational
   modeller path, and m37–m39 the clinical path?
