# m34 outline · Mapping-system software architecture: real-time pipeline, latency, data formats

Stage 1 of 6 (outline). Nothing here is course text yet. This file lists every planned equation,
demo, lab, test and source, so the author can approve the plan before writing starts.

Status: **draft, awaiting author review.**

## Learning goals

After this module a reader can:

1. Draw the data path of a mapping system as a pipeline of stages: acquisition, localization,
   signal processing and annotation, map building, display, storage and export.
2. Compute data rates and buffer sizes from channel count, sampling rate and sample width.
3. Build an end-to-end latency budget, and use Little's law and a simple queue model to explain why
   latency grows sharply as a stage nears full load.
4. Align streams sampled at different rates and on different clocks, and estimate the position error
   that a timing offset causes for a moving catheter.
5. Describe what a mapping-system export contains (geometry, points, electrograms, annotations) and
   how an open format such as OpenEP's stores it.
6. Explain how the software life-cycle standard's architecture rules (segregation of software items,
   third-party "SOUP" components) shape the design. Module m36 covers the standard itself.

Prerequisites: m03 (electrograms) and m04 (sampling and filtering). Until m04 exists, m34 includes a
short recap of sampling and filter delay.

## Section plan

Sections follow the module template (CLAUDE.md §3).

### 1. In 60 seconds

A mapping system is a real-time data pipeline: many channels sampled at high rates,
a localization stream at a different rate, processing stages that each add delay, and a display
the operator watches while moving the catheter. Architecture is about keeping that pipeline fast,
bounded and traceable, and about storing what it saw in a form others can read.

### 2. From the field

Lessons tied to sources, to be found and verified in stage 2:

- Exported mapping data is large and stored in proprietary formats; an open structure can be two
  orders of magnitude smaller than the compressed clinical export ([williams2021], verified).
- Where and when a point is acquired matters as much as its signal: timing and location errors move
  points on the map. (Source to find: a study of annotation timing or point-location error.)
- Further lessons from 510(k) summaries of mapping systems (public), described generically.

### 3. Derivations

Notation: $N$ channels, $f_s$ sampling rate (Hz), $b$ bits per sample, $\lambda$ arrival rate
(items/s), $\mu$ service rate (items/s), $\rho = \lambda/\mu$ utilization, $W$ mean time in a stage
(s), $L$ mean number in a stage.

| ID | Equation | What it says | Badge of its figure | Check in `tests/` |
| --- | --- | --- | --- | --- |
| eq-m34-data-rate | $R = N f_s b$ (+ framing overhead) | Raw data rate of the acquisition stream | exact | Numeric: count bytes from a simulated stream |
| eq-m34-buffer | $B \ge R\, T_{\max}$ | Buffer needed to ride out a stall of $T_{\max}$ without loss | exact | Simulation: drops occur only when the bound is violated |
| eq-m34-littles-law | $L = \lambda W$ | Items in a stage = arrival rate × time in stage, for any stable stage | simulation | Discrete-event simulation with random arrivals and service |
| eq-m34-mm1 | $W = 1/(\mu - \lambda)$ | Mean time in a single-server queue with random arrivals and service; grows without bound as $\rho \to 1$ | simulation | Discrete-event simulation agrees within sampling error |
| eq-m34-latency-budget | $T_{\text{e2e}} = \sum_i (T_{\text{proc},i} + T_{\text{queue},i}) + T_{\text{frame}}$ | End-to-end latency is a sum of stage delays plus up to one display frame | exact | Numeric: pipeline simulation, mean and worst case |
| eq-m34-fir-delay | $\tau = (M - 1)/(2 f_s)$ | Group delay of a linear-phase FIR filter with $M$ taps (links to m04) | exact | Numeric: delay of a filtered impulse |
| eq-m34-misregistration | $\Delta x \approx v\, \Delta t$; linear-interpolation error $\le \tfrac{1}{8} h^2 \max\lvert \ddot x\rvert$ | Position error from a timing offset $\Delta t$ at catheter speed $v$, and from interpolating a location stream sampled every $h$ seconds | approximate model | Numeric: interpolate a known trajectory |

Each derivation subsection ends with a **Key takeaways** list.

### 4. Demos

All demos are plain ES modules in `demos/`, run offline and compute in the browser.

| ID | Title | Learner controls | Shows | Badge |
| --- | --- | --- | --- | --- |
| m34-d1 | Pipeline latency | arrival rate, service time, buffer size | Latency distribution (mean, 99th percentile) and dropped items as load approaches capacity | simulation |
| m34-d2 | Data rate and storage | channels, sampling rate, bits, session length | Data rate, buffer size for a stall, storage per procedure | exact |
| m34-d3 | Stream alignment | timing offset, clock drift, location sampling rate, catheter speed | Where points land on a 2D trace when streams are misaligned | approximate model |

Assumptions to list under the demos: independent random arrivals and service times (d1); no
compression (d2); straight-line catheter motion at constant speed and a fixed clock drift (d3).

### 5. Clinical correlate

Marked **pending clinical review** until an EP physician signs it off.

Topic: how timing and latency show up in a real case. A point's local activation time is measured
against a reference signal, and its position comes from a separate stream; misalignment moves the
point in space or time. Source to find in stage 2 (study of annotation or registration error).
Describes findings only; no advice on patient care.

### 6. Visual summary and How experts think

- Visual summary: the pipeline as a block diagram with a data rate and a latency on every arrow.
  Badge: schematic.
- How experts think: "What is the worst case, not the average?" Every buffer has a bound, every
  stage a deadline, every stored value a timestamp and a unit.

### 7. Cheat sheet and Interview questions

Written in stage 5. At least 10 interview questions with model answers, including system-design
questions ("design the acquisition path for N channels").

### 8. Code lab and Self-check

Lab: `labs/python/m34_lab.ipynb` (Python only; Part VI has no Octave copy).

| Part | Task | Data |
| --- | --- | --- |
| A | Generate a multichannel stream from the m03 electrogram model; measure its data rate | Synthetic |
| B | Build a bounded-buffer pipeline with Python generators; measure latency percentiles under load | Synthetic |
| C | Check Little's law and the single-server queue formula with a discrete-event simulation | Synthetic |
| D | Align a location stream to the electrogram stream with timestamps; measure misregistration | Synthetic |
| E | Store a small session in an OpenEP-style structure and in WFDB format; read it back and compare | Synthetic, written with `wfdb` |

Self-check: at least 5 questions, numeric answers checked in tests.

### 9. Literature figures and Further reading

To select in stage 6, license-checked. Candidates: figures in [williams2021] (open access, license
to check) showing the OpenEP data structure.

## Sources

| Key | Source | Status |
| --- | --- | --- |
| williams2021 | Williams et al., OpenEP: a cross-platform electroanatomic mapping data format and analysis platform for electrophysiology research. Front Physiol 2021;12:646023. DOI 10.3389/fphys.2021.646023, PMID 33716795 | Verified (PubMed) |
| goldberger2000 | PhysioNet and the WFDB format. Already in `references.bib` | Verified |
| little1961 | Little, A proof for the queuing formula L = λW. Operations Research 1961 | [unverified], look up in stage 2 |
| iec62304 | IEC 62304:2006+A1:2015, Medical device software: software life cycle processes. Edition 2 is in development; its status was unclear in sources found on 2026-11-03 | Standard; cite the edition in force |
| 510(k) summaries | Public summaries for mapping systems cleared under 21 CFR 870.1425 (product code DQK), for generic system descriptions | Verify each on the FDA database in stage 2 |

## Still to source (before stage 2)

Every default demo parameter needs a citation (CLAUDE.md §5). Each is `TODO(source)` until found:

- Channel counts and sampling rates of mapping-system amplifiers (public 510(k) summaries or papers)
- Location update rates of magnetic and impedance localization (m16–m18 will need these too)
- Typical catheter-tip speed during mapping (mm/s)
- Crystal-oscillator frequency tolerance, for clock drift (ppm)
- A study of point-location or annotation-timing error, for the clinical correlate

## Glossary terms to add

pipeline · latency · jitter · throughput · utilization · buffer · ring buffer · timestamp · clock
drift · group delay · SOUP (software of unknown provenance) · data format · OpenEP · WFDB

## Formula-sheet entries

eq-m34-data-rate · eq-m34-buffer · eq-m34-littles-law · eq-m34-mm1 · eq-m34-fir-delay ·
eq-m34-misregistration

## Questions for the author

1. **Depth of queueing theory:** stop at Little's law and the single-server queue, or add
   multi-stage queues?
2. **Lab language:** Python generators are simple; would you rather show `asyncio`, or a C/C++
   snippet for the hard real-time part?
3. **Real export data:** OpenEP publishes example datasets; use one in the lab (license and size to
   check), or stay synthetic?
4. **Vendor examples:** describe architectures generically from 510(k) summaries only, as CLAUDE.md
   requires. OK?
