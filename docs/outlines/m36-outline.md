# m36 outline · From prototype to product: FDA Class II, 510(k), IEC 60601-1, IEC 62304, ISO 14971, EU MDR

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

The module page will carry a second callout next to the education-only warning: **not legal or
regulatory advice**. Regulations and guidances change; every statement will carry the date it was
checked.

## Learning goals

After this module a reader can:

1. Trace the US route for a mapping system: classification under 21 CFR 870.1425 (programmable
   diagnostic computer, Class II, product code DQK), a 510(k) showing substantial equivalence to a
   predicate, and what a public 510(k) summary contains.
2. Outline the EU route under the Medical Device Regulation (EU) 2017/745: classification rules,
   notified body, technical documentation.
3. Map the standards onto the parts of a mapping system: electrical safety and essential
   performance (IEC 60601-1), electromagnetic compatibility (IEC 60601-1-2), software life cycle
   (IEC 62304), usability (IEC 62366-1), risk management (ISO 14971) and the quality system
   (ISO 13485, incorporated into FDA's Quality Management System Regulation since 2 February 2026).
4. Do the engineering math of verification: zero-failure sample sizes, binomial acceptance plans,
   exact confidence bounds and simple reliability models.
5. Build traceability from user needs to requirements, risk controls, verification tests and
   validation, and use it to judge what a change affects.
6. Explain how software changes after clearance are handled: when FDA expects a new 510(k), and
   how a predetermined change control plan (PCCP) works for AI-enabled functions (links to m35).

Prerequisites: none strictly. m34 (architecture) and m35 (ML validation) help.

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

A working prototype is the start of a product, not the end. The rest is evidence: that the device is
electrically safe, that its software was built under a defined life cycle, that its risks were
found and controlled, that it does what users need, and that all of this is traceable. In the US a
mapping system is a Class II device cleared through a 510(k); in the EU it goes through a notified
body under the MDR. The same engineering evidence feeds both.

### 2. From the field

Lessons tied to sources, from public documents only:

- Mapping systems are cleared as programmable diagnostic computers under 21 CFR 870.1425, product
  code DQK; their 510(k) summaries list intended use, predicates and the kinds of testing done
  (bench, software verification and validation, electrical safety, sometimes animal or clinical).
  Examples to verify on the FDA database in stage 2: K130750, K093455, K070240.
- FDA's software premarket guidance replaced "levels of concern" with Basic and Enhanced
  documentation levels, and accepts a declaration of conformity to IEC 62304 ([fda-software-2023]).
- Since 2 February 2026 the US quality system regulation incorporates ISO 13485:2016 by reference
  ([fda-qmsr]).
- Devices that contain software are treated as "cyber devices" under section 524B of the FD&C Act,
  which brings requirements such as a software bill of materials ([fda-cyber-2026]).

### 3. Derivations

Notation: $R$ reliability (probability a unit or test passes), $C$ confidence level, $n$ sample
size, $c$ allowed failures, $x$ observed successes, $\lambda$ failure rate, $P_1$ probability of a
hazardous situation, $P_2$ probability that it leads to harm.

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m36-success-run | $n = \left\lceil \frac{\ln(1 - C)}{\ln R} \right\rceil$ | Zero-failure sample size to show reliability $R$ with confidence $C$ (from $R^n \le 1 - C$) | exact | SymPy derivation from the binomial; numeric table |
| eq-m36-acceptance | $\sum_{k=0}^{c} \binom{n}{k} (1-R)^k R^{n-k} \le 1 - C$ | Sample size when $c$ failures are allowed | exact | Numeric: against `scipy.stats.binom` |
| eq-m36-clopper-pearson | $p_L = B^{-1}\!\left(\tfrac{\alpha}{2};\, x,\, n - x + 1\right)$ | Exact lower confidence bound on a pass rate from $x$ of $n$ | exact | Numeric: coverage by simulation |
| eq-m36-reliability | $R(t) = e^{-\lambda t}$, $\lambda_{\text{sys}} = \sum_i \lambda_i$, MTBF $= 1/\lambda$ | Constant-failure-rate model and a series system | exact | Numeric: Monte Carlo of component failures |
| eq-m36-harm | $P(\text{harm}) = P_1 P_2$ | One common way to split probability of harm for risk estimation | exact | Numeric; framing to verify against ISO 14971:2019 and ISO/TR 24971 in stage 2 |

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline and compute in the browser.

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m36-d1 | Verification sample size | target reliability, confidence, allowed failures | Required $n$, and the probability of passing for a true reliability | exact |
| m36-d2 | Standards map | click a block of a mapping system (amplifier, localization, software, user interface, network) | Which standards and guidances apply to that block, and why | schematic |
| m36-d3 | Series reliability | component failure rates, mission time | System reliability over time and which component dominates | exact |

Assumptions to list under the demos: independent trials (d1); constant failure rates (d3); the
standards map is a teaching simplification, not a regulatory determination (d2).

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: how a software change to a mapping system reaches the lab. FDA guidance on deciding when to
submit a 510(k) for a software change, and PCCPs that authorize planned changes in advance for
AI-enabled functions. Real case: a recent mapping-system clearance that includes a PCCP, from the
public FDA record (to verify in stage 2). Describes the process only; not legal or clinical advice.

### 6. Visual summary and How experts think

- Visual summary: the V-model, with each left-side document (user needs, requirements,
  architecture, design) linked to its right-side evidence (validation, system test, integration
  test, unit test), and risk management running across. Badge: schematic.
- How experts think: "Every requirement has a test, every hazard has a control, every control has
  a test, and every change starts with an impact analysis."

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including "a field issue
needs a software fix in two weeks; walk me through it."

### 8. Code lab and Self-check

Lab: `labs/python/m36_lab.ipynb` (Python only).

| Part | Task | Data |
| --- | --- | --- |
| A | Zero-failure and $c$-failure sample sizes; check by simulation | Synthetic |
| B | Clopper–Pearson bounds and their coverage | Synthetic |
| C | Series reliability by Monte Carlo against the closed form | Synthetic |
| D | Build a traceability matrix from YAML requirements to this course's own `pytest` tests; list requirements without tests | This repository |
| E | A small risk register: estimate risk, apply controls, check residual risk against an acceptability matrix the learner defines | Synthetic |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

Public FDA documents (510(k) summaries, guidances) are US government works; reuse terms to confirm
in stage 6. Standards are copyrighted and will be described, never quoted at length.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| cfr-870-1425 | 21 CFR 870.1425 Programmable diagnostic computer: identification and Class II (performance standards). eCFR | Verified (eCFR text, 2026) |
| fda-qmsr | FDA, Quality Management System Regulation: effective 2 February 2026, incorporates ISO 13485:2016 and clause 3 of ISO 9000:2015 by reference | Verified (FDA page) |
| fda-software-2023 | FDA, Content of Premarket Submissions for Device Software Functions. Final guidance, 14 June 2023 | Verified (FDA presentation); cite the guidance page in stage 2 |
| fda-cyber-2026 | FDA, Cybersecurity in Medical Devices: Quality Management System Considerations and Content of Premarket Submissions. Issued 3 February 2026, superseding the 27 June 2025 version | Verified (FDA PDF) |
| fda-pccp-ai | FDA, PCCP for AI-enabled device software functions. Final guidance, December 2024 | Confirmed in news sources; check the FDA page in stage 2 |
| fda-sw-change | FDA, Deciding When to Submit a 510(k) for a Software Change to an Existing Device | Named in a 2025 FDA clearance letter; check the guidance page in stage 2 |
| 510(k) summaries | K130750, K093455, K070240 and a recent clearance with a PCCP | Seen through a secondary index; verify each on the FDA database in stage 2 |
| iec60601-1, iec60601-1-2, iec62304, iec62366-1, iso14971, iso13485, eu-mdr | Standards and regulation; editions in force to confirm in stage 2. IEC 62304 Edition 2 is in development; sources found on 2026-11-03 disagree on its publication date | Confirm editions in stage 2 |

## Still to source (before stage 2)

- EU MDR classification of mapping systems (which Annex VIII rule applies, and the resulting class)
- Which particular standards of the IEC 60601-2 series, if any, apply to intracardiac recording
- The ISO 14971:2019 / ISO/TR 24971 framing of probability of harm, for eq-m36-harm
- A textbook or standard source for the success-run formula (it is also derived in-module and tested)

## Glossary terms to add

510(k) · substantial equivalence · predicate device · product code · Class II · special controls ·
De Novo · PMA · notified body · CE marking · essential performance · basic safety · SOUP ·
software safety class · risk control · residual risk · design controls · verification ·
validation · traceability matrix · PCCP · SBOM · cyber device · QMSR

## Formula-sheet entries

eq-m36-success-run · eq-m36-acceptance · eq-m36-clopper-pearson · eq-m36-reliability

## Questions for the author

1. **Scope:** US and EU only, or add Japan (PMDA) and other markets briefly?
2. **IEC 62304 Edition 2:** teach the edition in force (2006+A1:2015) and add a short "what is
   changing" box that we update when Edition 2 is published. OK?
3. **Real 510(k) summaries:** quote short passages from public FDA summaries (US government
   works), with links. OK?
4. **Reviewer:** this module would benefit from a regulatory-affairs reviewer as well as the EP
   physician. Do you have someone in mind for `review_record.json`?
