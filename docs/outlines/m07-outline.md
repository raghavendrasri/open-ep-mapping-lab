# m07 outline · Inverse problems and regularization (Tikhonov, L-curve)

Stage 1 (outline) for module m07, written together with stages 2–6 (author request, 2026-11-12). m07 is the
foundation for every inverse problem in the course; m32 (ECG imaging) applies it and keeps its own equations, which
m07 links rather than repeats.

## Scope

Ill-posedness and the condition number; harmonic continuation across a source-free layer as the worked example (it
reproduces the m03 front shape exactly); the SVD view of the naive inverse and the discrete Picard condition; truncated
SVD and Tikhonov filters; the bias–noise error budget; choosing the parameter (discrepancy, L-curve, GCV); the Gaussian
(Bayesian) reading of Tikhonov. Out of scope: torso models and ECG-imaging validation (m32), nonlinear and sparse
regularization.

## Equations (tests in `tests/test_m07_inverse.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m07-model | $\mathbf b = A\mathbf x + \mathbf e$; error bound with $\kappa = s_1/s_n$ | random perturbations; equality case; $\kappa = e^{\pi h/\Delta x}$ for the continuation matrix |
| eq-m07-continuation | gain $e^{-\lvert k\rvert h}$; $k_{\max} = \ln(1/\varepsilon)/h$ | SymPy harmonicity; periodic closed form; width $w$ continued by $h$ is width $w + h$; best truncation for a flat spectrum |
| eq-m07-svd | naive solution = truth + divided noise | exact decomposition; error > 10⁴ at 0.1% noise; clean coefficients over gains equal the tissue spectrum |
| eq-m07-filters | TSVD and Tikhonov factors | normal equations equal the filter form; TSVD equals the pseudo-inverse of the truncation; $f = 1/2$ at $s = \lambda$ |
| eq-m07-error | bias + noise | Monte Carlo (4000 draws); SymPy single-component optimum; DFT form equals SVD form |
| eq-m07-choice | discrepancy and GCV | GCV from SVD equals explicit trace; monotone residual; each rule within 1.35× of the best error at h = 1 mm; L-curve failure at h = 0.5 mm, 0.1% noise |
| eq-m07-bayes | posterior mean and covariance | SymPy scalar case; equals the conditioning formula; 95% coverage |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m07-d1 | exact | Bias, noise and total expected error against λ for the continuation problem |
| m07-d2 | simulation | One noisy record deblurred with a chosen λ; residual against the noise norm |

## Code lab (`labs/python/m07_lab.ipynb`, Octave copy `labs/octave/m07_lab.m` for parts A–E)

A forward map and condition number; B naive inverse and Picard plot; C filters, error budget and resolution; D choosing
λ; E Bayesian reading and coverage.

## Sources

- Already in `references.bib`: hansen1992, hansen1993 (L-curve; the 1993 abstract was rechecked by web search: the
  L-curve is reported more robust than GCV with correlated errors), rudy1988, messinger1990, riccio2021.
- Web search (not in PubMed): Hansen 1990, BIT 30:658–672 (discrete Picard condition); Hansen 1990, SIAM J Sci Stat
  Comput 11:503–518 (TSVD and Tikhonov similar under the Picard condition); Golub, Heath and Wahba 1979,
  Technometrics 21:215–223 (GCV).
- PubMed: Khoury et al. 1995 (PMID 7828314), Liu et al. 1997 (PMID 9106427), Schilling et al. 1998 (PMID 9738644).
- Not cited: the discrepancy principle's original paper (Morozov) was not looked up; the page describes the rule
  without attributing it.
