# m16 outline · Magnetic localization

Stage 1 (outline) for module m16, written together with stages 2–6 (author request, 2026-11-14). Part III: Python lab
only.

## Scope

Dipole fields of generator coils; sensor-coil voltages; the measurement model and least-squares pose solving;
precision from the Jacobian and its growth with distance; five against six degrees of freedom; distortion from
conductors as an induced dipole. Out of scope: specific products' layouts and frequencies (described generically),
closed-form trio solutions, eddy-current phase models, hybrid systems (m18), motion (m19).

## Equations (tests in `tests/test_m16_magnetic.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m16-dipole | dipole field | SymPy gradient of the scalar potential; divergence and curl; numeric match |
| eq-m16-emf | coil voltage amplitude | SymPy derivative |
| eq-m16-coupling | readings G(p) n and least squares | exact recovery from noise-free readings |
| eq-m16-crlb | covariance sigma^2 (J^T J)^-1 | Monte Carlo of 800 solves within 8% |
| eq-m16-sensitivity | axial range error r dB/(3B) | SymPy; r^4 ratio; full-pose slope above 4 far away |
| eq-m16-5dof | roll invisibility, rank 5 | numeric invariance; Jacobian rank |
| eq-m16-distortion | induced-dipole bias | first-order bias against full solve; decay with distance |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m16-d1 | exact | predicted position error against height |
| m16-d2 | approximate model | first-order bias vectors from a nearby conductor |

## Code lab (`labs/python/m16_lab.ipynb`)

A field and voltage; B pose solving; C precision against distance; D five and six degrees of freedom; E distortion.

## Sources

- PubMed: Gepstein et al. 1997 (PMID 9118532), Franz et al. 2014 (PMID 24816547).
- Web: Raab et al. 1979, IEEE TAES 15(5):709–718, DOI 10.1109/TAES.1979.308860 (abstract and first page seen).
- Already in the bib: codata2018 (mu0).
