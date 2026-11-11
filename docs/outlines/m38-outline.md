# m38 outline · Wearables and implantable monitors

Stage 1 (outline) for module m38, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md`.

## Scope

Always-on rhythm detection in consumer wearables (PPG, single-lead ECG) and implanted monitors:
pulse timing versus beat timing, windowed detection with a consecutive-window rule, alert workload
and triage filters, and where agents could help. Out of scope: monitoring or device-programming
advice; vendor operating instructions.

## Learning goals

1. Explain what PPG measures and why pulse intervals differ from RR intervals.
2. Derive false notifications and missed episodes for a "k windows in a row" rule.
3. Turn alert rates into review hours, and evaluate a triage filter by what it hides.
4. Read wearable and ILR studies by their numerators and denominators.

## Equations (tests in `tests/test_m38_wearables.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m38-hr | Heart rate from intervals | Closed forms |
| eq-m38-ibi | Pulse interval = RR + change in delay | Identity on random data |
| eq-m38-ibi-var | Pulse-interval variance with AR(1) delays | Simulation at three correlations; SymPy |
| eq-m38-runs | Expected runs of ≥ k positives | Exact enumeration; simulation of 288 windows |
| eq-m38-detect | Episode detection probability (recursion) | Exact enumeration |
| eq-m38-workload | Alerts, false alerts and review hours | Closed form |
| eq-m38-filter | PPV after a triage filter | Equals eq-m35-ppv; SymPy limits |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m38-d1 | exact | False notifications per day and episode capture versus k |
| m38-d2 | exact | Review inbox: PPV after triage and true alerts hidden |

## Code lab (`labs/python/m38_lab.ipynb`)

A pulse timing; B window detector (q, p); C k-in-a-row rule, independent versus clumped noise;
D clinic inbox with a triage score; E MIT-BIH AF Database beat and rhythm annotations (CI
download); F optional PyTorch network on RR-interval windows.

## Sources (looked up on PubMed for this module)

perez2019 (Stanford), lubitz2022, neiman2024, covino2024, antoun2025, rodrigo2022 (Stanford),
feli2025, iwai2025, allen2007; afdb (PhysioNet page and AWS registry: ODC-By 1.0, DOI
10.13026/C2MW2D). Figure descriptions in "Literature figures" were checked against the PMC full
texts of lubitz2022 and neiman2024; perez2019's algorithm description is in its supplement.

## Open points for the author

- Pin the afdb SHA256SUMS.txt hash after CI prints it.
- The synthetic PPG and rhythm parameters are illustrative.
- Device and vendor names from @neiman2024 are kept out of the text; the module describes the
  models generically.
