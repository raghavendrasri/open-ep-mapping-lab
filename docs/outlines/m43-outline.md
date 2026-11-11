# m43 outline · Foundation models and large language models

Stage 1 (outline) for module m43, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md`.

## Scope

Self-supervised (contrastive) pretraining of ECG encoders and linear probes; how the pretraining
cohort shapes transfer; attention and the transformer; retrieval over course text; and an offline
harness for evaluating language-model answers (accuracy with an interval, consistency, citations).
Out of scope: prompting recipes, vendor products, any clinical use of an LLM.

## Learning goals

1. Derive the InfoNCE loss and its gradient; explain positives, negatives and the temperature.
2. Compare a linear probe on pretrained features with training from the raw signal at several label
   budgets, against an untrained encoder of the same size.
3. Explain why the pretraining cohort matters.
4. Derive why attention divides by the square root of the key length.
5. Build and test a retrieval step (TF-IDF, cosine, recall@k, MRR).
6. Design an LLM evaluation: Wilson interval, number of questions, consistency (kappa), citation checks.

## Equations (tests in `tests/test_m43_foundation.py` and `tests/test_m43_retrieval.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m43-infonce | InfoNCE loss | Equal similarities give ln N; N = 2 is the logistic loss (SymPy); limit τ → 0 |
| eq-m43-infonce-grad | (P − I)/(Nτ) | Finite differences; rows sum to zero; encoder backward pass |
| eq-m43-attention | softmax(QKᵀ/√d)V | Rows sum to 1; permutation invariance; one-hot limit |
| eq-m43-scaling | Var(q·k) = d | SymPy (sympy.stats) for one term; Monte Carlo for d = 4, 64 |
| eq-m43-tfidf | Smoothed TF-IDF | Three-document corpus by hand |
| eq-m43-cosine | Cosine similarity | Scale invariance, symmetry, range, zero vector |
| eq-m43-wilson | Wilson score interval | Roots of the score equation (SymPy); k = 0 |
| eq-m43-questions | n ≈ z²p(1−p)/h² | Wilson half-width at that n; 385 at p = 0.5, h = 0.05 |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m43-d1 | simulation | Embeddings of 8 synthetic patients during contrastive pretraining, two kinds of positive pair (precomputed by `tools/make_m43_d1.py`, 17 kB) |
| m43-d2 | exact | TF-IDF retrieval over the course glossary and formula sheet, JS tested against Python (corpus written by `tools/make_m43_d2.py`) |

## Code lab (`labs/python/m43_lab.ipynb`)

A InfoNCE by hand; B pretraining on 2,000 synthetic patients and a linear probe at 10–300 labels
against raw samples and an untrained encoder; C a pretraining cohort without wide QRS; D attention
and √d; E retrieval over the course text (recall@k, MRR, misses); F evaluation harness with scripted
stand-in models and planted faults, optional real-model cell skipped in CI; G PTB-XL (download):
pretraining on 120 unlabeled fold-9 records, 10-record probe on fold 10; H optional PyTorch CNN.

## Sources

PubMed: ko2026, khattak2026 (PMC full text for figure descriptions), sangha2024, ye2026, hsieh2026,
yang2026 (preprint), chai2026, zeljkovic2025, bozyel2025, vaid2024, zakka2024 (Almanac, Stanford;
PMC full text for the retrieval threshold, citation and adversarial results). arXiv (alphaXiv):
oord2018cpc, chen2020simclr, vaswani2017, lewis2020rag, bedi2025medhelm (MedHELM, Stanford),
lee2025nvembed (NV-Embed, NVIDIA, ICLR 2025). Publisher records found by web search: wilson1927
(JASA 22(158):209–212), sparckjones1972 (J Documentation 28(1):11–21).

## Open points for the author

- Part G (PTB-XL) and part H (PyTorch) have not run locally: no PhysioNet access and no PyTorch here.
  Part G was exercised with synthetic stand-in records.
- The lab's question set was written by the course author, who also wrote the new glossary entries;
  retrieval scores on it are optimistic.
- `demos/m43-d2-corpus.json` must be regenerated (`python tools/make_m43_d2.py`) whenever the glossary
  or formula sheet changes; a test fails until it is.
