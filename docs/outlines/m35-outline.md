# m35 outline · Machine learning in EP mapping: annotation, driver detection, validation pitfalls

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

## Learning goals

After this module a reader can:

1. Frame mapping tasks as learning problems: activation-time annotation, electrogram classification
   (local versus far-field, fractionated or not) and driver detection, and say where the labels
   come from.
2. Measure how much experts agree, and explain why label disagreement caps how good a model can
   look.
3. Recognize data leakage, in particular splitting records instead of patients, and show with a
   simulation how much it inflates accuracy.
4. Evaluate a model properly: sensitivity, specificity, predictive values at a given prevalence,
   ROC and AUC, calibration, and confidence intervals that resample patients.
5. Explain why external validation and an independent ground truth (for example optical mapping in
   explanted hearts) matter more than another internal split.
6. Report a model with a published checklist, and know how FDA handles changes to AI-enabled device
   software. Module m36 covers regulation in full.

Prerequisites: m03 (electrograms). m22 (annotation) and m29 (complex maps) are not written yet; m35
includes short recaps of activation-time annotation and of what a "driver" means.

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

Machine learning can annotate electrograms and flag candidate drivers faster and more consistently
than people, but only as well as its labels and its validation allow. Many ways a model can look
better than it is come from how data was split, labeled and evaluated, not from the model itself
([saeb2017], [vancalster2019]). This module is about those three things.

### 2. From the field

Lessons tied to verified sources:

- Experts labeling rotational activation in AF were consistent but not identical (κ = 0.79), and
  their labels were used to train a convolutional neural network ([alhusseini2020]).
- Machine learning on electrogram frequency spectra improved AF driver detection by multi-electrode
  mapping when validated against near-infrared optical mapping of explanted human atria
  ([zolotarev2020]).
- Cross-validation is only meaningful if the split mimics the real use case; splitting records from
  the same subjects across training and test sets overstates accuracy ([saeb2017]).
- Poor calibration can make an accurate model misleading ([vancalster2019]).

### 3. Derivations

Notation: $y \in \{0, 1\}$ true label, $\hat p$ predicted probability, $\pi$ prevalence,
$\mathrm{Se}$ sensitivity, $\mathrm{Sp}$ specificity, $p_o$ observed agreement, $p_e$ chance
agreement, $m$ records per patient, $r$ within-patient correlation.

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m35-kappa | $\kappa = (p_o - p_e)/(1 - p_e)$ | Agreement beyond chance between two labelers | exact | Numeric: against a hand-worked confusion matrix |
| eq-m35-ppv | $\mathrm{PPV} = \frac{\mathrm{Se}\,\pi}{\mathrm{Se}\,\pi + (1-\mathrm{Sp})(1-\pi)}$ | Predictive value depends on prevalence (Bayes' rule) | exact | SymPy and numeric |
| eq-m35-auc | $\mathrm{AUC} = P(\hat p_{+} > \hat p_{-})$ | AUC is the probability a random positive outranks a random negative (Mann–Whitney) | exact | Numeric: equals the trapezoidal area under the ROC curve |
| eq-m35-brier | $\mathrm{BS} = \frac1n \sum (\hat p_i - y_i)^2$; calibration slope from $\operatorname{logit} P(y=1) = \alpha + \beta \operatorname{logit} \hat p$ | Overall accuracy of probabilities, and whether they are too extreme ($\beta < 1$) or too timid ($\beta > 1$) | simulation | Numeric: recover a known miscalibration |
| eq-m35-design-effect | $n_{\text{eff}} = \frac{n}{1 + (m - 1) r}$ | Correlated records from one patient carry less information than independent ones | simulation | Simulation of clustered data |
| eq-m35-label-ceiling | With labels that disagree with the truth at rate $\epsilon$, measured accuracy of a perfect model is $1 - \epsilon$ | Label noise caps measured performance | exact | Numeric: simulation with flipped labels |

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline and compute in the browser.

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m35-d1 | Leakage explorer | within-patient correlation, records per patient, number of patients | Accuracy with record-wise versus patient-wise splits, against the true accuracy on new patients | simulation |
| m35-d2 | Threshold and prevalence | decision threshold, prevalence, class separation | ROC curve with the operating point, and PPV/NPV as prevalence changes | exact |
| m35-d3 | Calibration | miscalibration (slope, intercept) | Reliability diagram and Brier score | simulation |

Assumptions to list under the demos: Gaussian scores per class (d2); patient effects drawn from a
normal distribution (d1); synthetic probabilities with a set miscalibration (d3).

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: what "ground truth" means for AF driver detection. Expert labels vary ([alhusseini2020]);
optical mapping offers an independent reference in explanted hearts ([zolotarev2020]). AI-enabled
mapping software has been cleared by FDA; describe from public 510(k) summaries only, generically.
Describes findings only; no advice on patient care.

### 6. Visual summary and How experts think

- Visual summary: one flow from data to deployment with the four classic failure points marked:
  leakage, label noise, miscalibration, dataset shift. Badge: schematic.
- How experts think: "Split by patient, report by patient, validate on someone else's patients."

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including "your model has
0.98 AUC in cross-validation; what do you check first?"

### 8. Code lab and Self-check

Lab: `labs/python/m35_lab.ipynb` (Python only).

| Part | Task | Data |
| --- | --- | --- |
| A | Generate labeled electrograms (local versus far-field) from the m03 model, with patient-to-patient variation | Synthetic |
| B | Extract simple features (amplitude, steepest slope, width) and fit logistic regression with NumPy/SciPy | Synthetic |
| C | Compare record-wise and patient-wise cross-validation; measure the optimism | Synthetic |
| D | ROC, AUC, calibration and a patient-level bootstrap confidence interval | Synthetic |
| E | Flip a share of labels and watch the measured ceiling fall | Synthetic |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. Candidates: figures in [alhusseini2020] and [zolotarev2020]
(both in PubMed Central; licenses to check). Reporting: [collins2024]. Regulation: the FDA AI
guidances below.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| alhusseini2020 | Alhusseini et al., Machine learning to classify intracardiac electrical patterns during atrial fibrillation. Circ Arrhythm Electrophysiol 2020;13:e008160. DOI 10.1161/CIRCEP.119.008160, PMID 32631100 | Verified (PubMed) |
| zolotarev2020 | Zolotarev et al., Optical mapping-validated machine learning improves atrial fibrillation driver detection by multi-electrode mapping. Circ Arrhythm Electrophysiol 2020;13:e008249. DOI 10.1161/CIRCEP.119.008249, PMID 32921129 | Verified (PubMed) |
| saeb2017 | Saeb et al., The need to approximate the use-case in clinical machine learning. GigaScience 2017;6:1–9. DOI 10.1093/gigascience/gix019, PMID 28327985 | Verified (PubMed) |
| vancalster2019 | Van Calster et al., Calibration: the Achilles heel of predictive analytics. BMC Med 2019;17:230. DOI 10.1186/s12916-019-1466-7, PMID 31842878 | Verified (PubMed) |
| collins2024 | Collins et al., TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ 2024;385:e078378. DOI 10.1136/bmj-2023-078378, PMID 38626948 | Verified (PubMed) |
| fda-pccp-ai | FDA, Marketing Submission Recommendations for a Predetermined Change Control Plan for Artificial Intelligence-Enabled Device Software Functions. Final guidance, December 2024 | Confirmed final in news sources; check the FDA page in stage 2 |
| fda-ai-lifecycle | FDA, Artificial Intelligence-Enabled Device Software Functions: Lifecycle Management and Marketing Submission Recommendations. Draft guidance, January 2025; still listed as a draft to finalize in FDA's FY 2027 guidance agenda (October 2026) | Check the FDA page in stage 2 |
| kish1965 | Kish, Survey Sampling (design effect) | [unverified], look up in stage 2 |

## Still to source (before stage 2)

- A study measuring inter-rater agreement on local activation time annotation (for the label-noise
  section)
- Public 510(k) summaries of AI-enabled mapping software, verified on the FDA database
- Default demo values: typical numbers of patients and records per patient in published EGM
  datasets

## Glossary terms to add

label · ground truth · inter-rater agreement · Cohen's kappa · data leakage · cross-validation ·
record-wise and subject-wise split · sensitivity · specificity · positive predictive value ·
prevalence · ROC curve · AUC · calibration · Brier score · dataset shift · external validation ·
predetermined change control plan (PCCP)

## Formula-sheet entries

eq-m35-kappa · eq-m35-ppv · eq-m35-auc · eq-m35-brier · eq-m35-design-effect

## Questions for the author

1. **Dependencies:** the lab can use NumPy/SciPy only, or add `scikit-learn` to
   `requirements.txt`. Which?
2. **Deep learning:** keep the lab to logistic regression (fast, transparent, runs in CI in under 5
   minutes), and discuss neural networks in text only? Or add a small PyTorch part (heavier CI)?
3. **Real data:** iafdb has no expert labels for these tasks. Stay synthetic, or look for an openly
   licensed labeled dataset in stage 2?
4. **Overlap with m22 and m29:** m35 focuses on the ML method and validation, and leaves annotation
   and driver physics to those modules. OK?
