# m13 outline · Catheter design

Stage 1 (outline) for module m13, written together with stages 2–6 (author request, 2026-11-14: "continue with
remaining modules"). Part III: Python lab only.

## Scope

Electrode size and spreading resistance; bipole direction and perpendicular pairs on grids; spatial sampling against
electrode height; basket spline geometry and coverage; contact-force estimation from three strain sensors. Out of scope:
vendor catheter specifications (described generically), electrode–electrolyte interface impedance (m14), thermal
noise (m14), electrode averaging and omnipolar signals in detail (m03), ablation (m27, m28).

## Equations (tests in `tests/test_m13_catheters.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m13-spreading | disk, hemisphere and sphere spreading resistance | numeric equipotential of the 1/sqrt density and its resistance; on-axis quadrature and SymPy limit; SymPy hemisphere field |
| eq-m13-orthogonal | bipole amplitude and perpendicular pairs | numeric minimum 1/sqrt(2) at 45°; RSS equals 1 |
| eq-m13-alias | Poisson kernel, its spectrum, energy above Nyquist, spacing rule | SymPy transform and energy integral; FFT within 1% |
| eq-m13-basket | interspline arc | computed arcs between electrodes; fill distance ordering |
| eq-m13-force | least-squares force | exact recovery without noise; rank loss for collinear sensors |
| eq-m13-force-noise | covariance and 120° SDs | SymPy C^T C; Monte Carlo within 3%; 120° minimizes the condition number |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m13-d1 | exact | front profile at height h sampled at spacing Δ; spectrum and Nyquist line |
| m13-d2 | exact | three-sensor layout and the lateral-force error ellipse |

## Code lab (`labs/python/m13_lab.ipynb`)

A spreading resistance; B bipole direction; C spacing, height and aliasing; D basket coverage; E contact force.

## Sources

- Web (no PubMed record): Newman 1966, J Electrochem Soc 113:501, DOI 10.1149/1.2424003. The disk and hemisphere
  results were confirmed from the author's 1965 laboratory report on eScholarship.
- PubMed: Stinnett-Donnelly 2012 (PMID 22258280), Laughner 2016 (PMID 29766854), Yokoyama 2008 (PMID 19808430), Reddy
  2012 (PMID 22820056).
- Already in the bib: anter2015, deno2017, masse2016.
