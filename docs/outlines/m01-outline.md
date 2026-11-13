# m01 outline · Bioelectric sources: transmembrane current, dipoles and double layers

Stage 1 (outline) for module m01, written together with stages 2–6 (author request, 2026-11-12: start Part I,
m01–m07, one pull request per module). m03 already exists as the pilot; m01 sets up its sources with the same symbols
($\beta$, $\sigma$, $\Delta V$, $w$, $h$) and relative units.

## Scope

Point sources, current dipoles, double layers and solid angles, membrane current from the core-conductor model, and
the wavefront as a moving line of dipoles. Out of scope: boundaries and inhomogeneous media (m02), ionic currents
(m08), anisotropic propagation (m09).

## Learning goals

1. Derive the potential of a point source, a dipole and a uniform double layer in an infinite conductor.
2. Derive membrane current across a front from the core-conductor model and show that its net is zero and its
   dipole moment is $\beta\Delta V$.
3. Show that a front of width $w$ at height $h$ is a line of dipoles at height $w + h$ (the m03 closed form).

## Equations (tests in `tests/test_m01_sources.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m01-point | $\phi = I/(4\pi\sigma r)$ | SymPy Laplacian and flux; quadrature over a sphere |
| eq-m01-dipole | $\phi = \mathbf p\cdot\hat{\mathbf r}/(4\pi\sigma r^2)$ | SymPy limit of a source–sink pair; error ∝ d²; slopes −1 and −2 |
| eq-m01-double-layer | $\phi = \tau\Omega/(4\pi\sigma)$ | SymPy disk solid angle and 4π jump; quadrature against a sum of dipoles; closed surface gives zero |
| eq-m01-core | $I_i = -\beta V_m'$, $i_m = \beta V_m''$ | SymPy: net zero, first moment $\beta\Delta V$; numeric for several widths |
| eq-m01-moment | $p = \int s\,i_m\,ds = \beta\Delta V$ | SymPy integral; numeric for widths 0.1–3 mm |
| eq-m01-front-dipole | $\phi = p s/(2\pi\sigma(s^2 + h^2))$ | SymPy derivative of the 2-D Green's function; strip quadrature equals the m03 closed form to 1e-6 |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m01-d1 | exact | Log potential against log distance: point source, dipole, disk double layer (radius slider) |
| m01-d2 | exact | Front voltage and membrane current; potential of a front of width w against a thin front at the same height |

## Code lab (`labs/python/m01_lab.ipynb`, Octave copy `labs/octave/m01_lab.m` for parts A–E)

A point source; B pair to dipole; C double layer and solid angle; D membrane current across a front; E the front as a
line of dipoles; F why only fronts make potentials. Offline, about 3 s in Python and 4 s in Octave.

## Sources

PubMed (2026-11-12): holland1977 (no abstract; cited for solid-angle theory generally), clerc1976 (abstract; ratios
3.0, 9.4 and 2.7). Already in `references.bib`: plonsey2007, stevenson2005, debakker2019.

## Open points for the author

- No absolute conductivities, capacitances or current densities are given: PubMed abstracts found for them had no
  numbers (Geddes and Sadler 1973, Gabriel et al. 1996), so the module stays in relative units like m03.
- holland1977 is cited for the theory only; its text was not read.
