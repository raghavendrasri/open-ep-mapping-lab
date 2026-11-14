# m11 outline · The EP study: catheters, pacing protocols, intervals, entrainment

Stage 1 (outline) for module m11, written together with stages 2–6 (author request, 2026-11-14). Part II: Python lab
only.

## Scope

The His-bundle recording and the AH and HV intervals; premature-beat recovery curves and refractory periods;
incremental pacing and Wenckebach periodicity from an AV nodal recovery-curve model; entrainment and the post-pacing
interval in a simulated circuit. Out of scope: normal values for human intervals (no accessible primary source was
verified; none are quoted), specific catheter models and placements, and diagnostic criteria for particular
tachycardias.

## Equations (tests in `tests/test_m11_epstudy.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m11-intervals | AH, HV | steepest-slope times on a noisy synthetic recording within 0.2 ms |
| eq-m11-avnode | recovery curve | NCT_max at ERP_N, NCT_min at long recovery, block below ERP_N, monotone |
| eq-m11-wenckebach | CL_W = ERP_N + NCT_max, stability | 1:1 above 241 ms; 4:3 at 220 ms; 2:1 at 150 ms; lengthening before each block |
| eq-m11-ppi | PPI − TCL ≈ 2d/CV | Mitchell–Schaeffer ring with a branch: on the circuit < 20 ms; at 20 mm within 15 ms of 2d/CV; faster pacing lengthens the on-circuit PPI |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m11-d1 | exact | AV nodal recovery curve and beat-by-beat conduction for a pacing cycle length |
| m11-d2 | exact | PPI − TCL against distance for a chosen velocity |

## Code lab (`labs/python/m11_lab.ipynb`)

A intervals; B recovery curve; C Wenckebach periodicity; D entrainment and distance; E pacing rate and the PPI.

## Sources

- PubMed: Scherlag et al. 1969 (PMID 5782803, no abstract: cited for the recording technique in its title), Reid et
  al. 2003 (PMID 14678111), Xu et al. 2006 (PMID 16443539), Stevenson et al. 1993 (PMID 8403311), Waldo 1997 (PMID
  9083885).
