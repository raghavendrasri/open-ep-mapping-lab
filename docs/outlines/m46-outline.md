# m46 outline · Trustworthy AI in EP

Stage 1 (outline) for module m46, written together with stages 2–6. The module was added to the
curriculum on 2026-11-11 with the author's approval, after a gap review of Part VII; it follows m45, so no
module was renumbered.

## Scope

Five checks a reader can run on any AI model in EP: explanations (integrated gradients and the
randomization test), uncertainty (split conformal prediction), fairness (group error rates and
predictive values), unfamiliar inputs (a Mahalanobis score with abstention) and robustness (small
adversarial changes). Validation basics stay in m35; evidence, reporting and monitoring in m45; data
engineering and deployment in m47. Out of scope: patient-care advice, legal definitions of fairness.

## Learning goals

1. Compute integrated gradients, check completeness, and run a randomization test.
2. Build conformal prediction sets and check their coverage per class and per group.
3. Explain why equal error rates and equal predictive values conflict when prevalences differ.
4. Score how familiar an input is and choose an abstention threshold from a false-alarm rate.
5. Compute how small a change flips a linear decision, and compare it with noise.

## Equations (tests in `tests/test_m46_trust.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m46-ig | IG_i = (x_i − x'_i)∫∂F/∂x_i dα; Σ IG_i = F(x) − F(x') | Completeness for a small network; closed form for logistic regression; input gradient by finite differences |
| eq-m46-conformal | q̂ = ⌈(n+1)(1−α)⌉-th score; C = {k : 1 − p̂_k ≤ q̂}; coverage ≥ 1 − α | Quantile by hand; simulated coverage in [1−α, 1−α+1/(n+1)] on average; per-class version |
| eq-m46-fpr | FPR = π/(1−π)·(1−PPV)/PPV·TPR | SymPy from the definitions; group rates on a confusion table |
| eq-m46-mahalanobis | d² = (f−μ)ᵀΣ⁻¹(f−μ) ~ χ²_k | False-alarm rate on Gaussian data matches the chi-square quantile |
| eq-m46-fgsm | x + ε sign(∇L); abs(Δz) ≤ ε‖w‖₁; ε* = abs(z)/‖w‖₁ | The attack moves a linear score by exactly ε‖w‖₁ and flips it at ε* |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m46-d1 | simulation | Conformal sets for three synthetic classes: coverage per class and set sizes against α, one threshold or one per class (live, fixed seeds) |
| m46-d2 | exact | PPV against prevalence for one detector in two groups; the FPR group B would need for equal PPV |

## Code lab (`labs/python/m46_lab.ipynb`)

A integrated gradients and the randomization check on a small NumPy network (wide-QRS beats); B conformal
sets for sinus rhythm, AF and frequent early beats; C error rates and PPV in two synthetic groups; D a
Mahalanobis score, abstention and accuracy on noisy recordings; E how small an attack flips a linear model on
raw beats; F Challenge 2017 → PTB-XL fold 10, subgroups by PTB-XL's sex code and age, and conformal coverage
across databases (download); G optional PyTorch integrated gradients.

## Sources

PubMed: han2020, noseworthy2020, hughes2021, ghorbani2020 (Stanford), abstracts checked 2026-11-11; already
in `references.bib`: kaur2023 (Stanford), svennberg2025, hsieh2026, wagner2020, clifford2017, cinc2017data.
arXiv (title and ID checked in the arXiv listing): sundararajan2017ig (1703.01365), adebayo2018sanity
(1810.03292), angelopoulos2021conformal (2107.07511), chouldechova2017 (1703.00056), goodfellow2015fgsm
(1412.6572), lee2018mahalanobis (1807.03888).

## Open points for the author

- No NVIDIA source was found for this module's topics; m47 cites NVIDIA's integer-quantization paper.
- The arXiv entries were verified by title and ID; author lists come from the arXiv listing where shown.
- Part F has not run locally (no PhysioNet access); exercised with stand-in recordings. PTB-XL's sex field is
  reported as the database's code, not interpreted.
- The age cut (65 years), separations in d1 and attack settings are illustrative.
