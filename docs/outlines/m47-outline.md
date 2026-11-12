# m47 outline · Data and deployment engineering for AI in EP

Stage 1 (outline) for module m47, written together with stages 2–6. The module was added to the
curriculum on 2026-11-11 with the author's approval, after a gap review of Part VII; it follows m46, so no
module was renumbered.

## Scope

What happens to data before a model sees it and to a model after it is trained: units in file headers, labels
from several labellers, de-identification and re-identification risk, dataset versions, integer quantization for
small devices, and model cards. Validation basics stay in m35 (kappa and the label ceiling are reused from there),
evidence and change control in m45, trust checks in m46, the analog front end in m14. Out of scope: legal advice,
vendor export formats, regulatory submissions.

## Learning goals

1. Convert stored integers to physical units from a header, and audit new data for header mistakes.
2. Compute the accuracy of a majority of labellers and explain why shared hard cases limit it.
3. Compute re-identification risk from equivalence-class sizes and coarsen a table to reach a target.
4. Fingerprint a dataset with a checksum manifest and record its version with every result.
5. Quantize a signal and a model, predict the rounding noise, and test the quantized model.
6. Write a model card from a model's own results.

## Equations (tests in `tests/test_m47_deploy.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m47-adu | v = (d − b)/g; rounding error at most 1/(2g) | SymPy inverse; numeric round trip; WFDB write, read and header edit |
| eq-m47-majority | Σ_{j>m/2} C(m,j) p^j (1−p)^{m−j} | SymPy for m = 3 (3p² − 2p³); simulation for m = 5; mixture with shared hard cases |
| eq-m47-risk | r_i = 1/f_i; largest 1/k; average J/n | Small table by hand; mean of 1/f equals classes over records; coarsening lowers risk |
| eq-m47-affine | r = S(q − Z), S = (r_max − r_min)/(q_max − q_min), Z = q_min − round(r_min/S) | Scale and zero point by hand; zero exact; in-range error at most S/2 |
| eq-m47-qnoise | σ² = S²/12; SQNR ≈ 6.02b + 1.76 dB for a full-scale sine | SymPy integral and SQNR identity; simulated sine at 8 and 12 bits |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m47-d1 | approximate model | A synthetic beat quantized with b bits over its own range or ±5 mV; measured SQNR against the S²/12 prediction |
| m47-d2 | simulation | Re-identification risk in a synthetic registry of 2,000 procedures as fields are released or age is grouped |

## Code lab (`labs/python/m47_lab.ipynb`)

A WFDB round trip and an audit that catches a wrong gain and a wrong sampling rate; B a checksum manifest and a
dataset version; C labellers, majority votes, kappa and the label ceiling; D re-identification risk in a synthetic
registry and coarsening to k = 5; E quantizing a beat and the m46 network to 8 and 4 bits, per tensor and per
hidden unit; F a model card generated from parts B and E; G real PTB-XL and Challenge 2017 headers, PTB-XL label
fields and a cross-database amplitude audit (download); H optional PyTorch dynamic quantization.

## Sources

PubMed (abstracts checked 2026-11-11): eleman2008, chambon2023 (Stanford), ghazarian2021, wilkinson2016,
huang2026edgeecg, faraone2021; already in `references.bib`: wagner2020, clifford2017, hannun2019, cinc2017data.
arXiv and publisher pages (abstracts checked by web search): jacob2018quant (1712.05877), wu2020int8 (2004.09602,
NVIDIA), mitchell2019modelcards (1810.03993), gebru2018datasheets (1803.09010), liang2024modelcards (Stanford;
journal DOI, claims checked against the arXiv abstract 2402.05160). Web pages: the WFDB header format
(PhysioNet), the WFDB Python documentation, and the HHS de-identification guidance and workshop pages (checked
2026-11-11).

## Open points for the author

- Part G has not run locally (no PhysioNet access); exercised with the download skipped.
- The HIPAA material is a short US example, not legal advice; regulation outside the US is not covered.
- The audit percentiles, the k = 5 target, the age cut-offs and the ±5 mV range are illustrative.
