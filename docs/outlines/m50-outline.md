# m50 outline · Intracardiac echocardiography with TEE and TTE

Stage 1 (outline) for module m50, the second Part VIII module, written together with stages 2–6 (author decision,
2026-11-11: build m49 and m50 first; keep ultrasound lightweight). Plan source: `docs/outlines/part8-overview.md`.

## Scope

Only the ultrasound physics an ICE user or engineer needs, written from scratch: echo time to depth and the
speed-of-sound assumption, axial resolution, attenuation and reach, phased-array steering and grating lobes, frame
rate, and shells from tracked planes. Then the published evidence on ICE for transseptal puncture and against TEE.
Out of scope: Doppler, harmonic imaging, transducer design, operating instructions, advice on any patient.

## Learning goals

1. Turn echo time into depth and predict the error from a wrong speed of sound.
2. Relate frequency, pulse length and axial resolution.
3. Budget round-trip attenuation against frequency and depth.
4. Steer a phased array and state when grating lobes appear; relate aperture to beam width.
5. Relate depth, line count and frame rate.
6. Read ICE-versus-TEE and ICE-versus-none studies by their design.

## Equations (tests in `tests/test_m50_ice.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m50-range | z = ct/2; displayed depth z c_assumed/c_true | SymPy; simulated echo read with the wrong speed |
| eq-m50-axial | λ = c/f; Δz = nλ/2 | Simulated n-cycle echoes stop overlapping between 0.97 and 1.03 of nλ/2 |
| eq-m50-attenuation | L = 2αfz; z_max = B/(2αf) | SymPy solve; numeric with published slopes |
| eq-m50-steer | τ_k = x_k sinθ0/c; array factor; grating lobes at sinθ0 + mλ/d; first null λ/(Nd) | Geometric series (SymPy); peak at θ0; lobes at full strength; null; delays align a plane wave |
| eq-m50-frame-rate | c/(2DN) | SymPy; scaling |

Also tested: delay-and-sum imaging finds a point and a 4-mm tent within 0.2 mm; tracked planes leave a largest gap
of π max(a, b)/n.

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m50-d1 | exact | Array factor against angle; steering angle, element spacing in wavelengths, element count |
| m50-d2 | exact | Round-trip loss against depth with a signal budget; frequency, depth, lines, attenuation slope; readouts of resolution, reach and frame rate |

## Code lab (`labs/python/m50_lab.ipynb`)

A depth and the speed-of-sound assumption; B echo overlap and axial resolution; C attenuation and reach; D steering
and grating lobes; E delay-and-sum sector image of a synthetic septum with tenting, and frame rate; F a 3-D shell from
tracked planes; G the evidence by design. No downloads.

## Sources

PubMed (abstracts checked 2026-11-11): morton2003 (ICE frequencies 7.5–10 MHz, isthmus anatomy), baldwin2007
(myocardial attenuation slopes), zhang2026sos (1540 m/s assumed in beamforming), xiao2024 (calf muscle 1560–1586 m/s
in vivo), abdalla2026, kanniyan2026, yaser2026, deshpande2022, kitamura2021, dellorusso2023, chen2026tsp,
romero2013; already in `references.bib`: zou2026.

## Open points for the author

- No open ICE image data set was found; the lab is synthetic (author decision: open sources only).
- Element counts, pulse length, signal budget, depths, line counts and phantom shapes are illustrative.
- Attenuation slopes are for myocardium and are applied to the whole path; blood is not modeled separately.
- The calf-muscle speed of sound is an example of real tissue differing from 1540 m/s, not a cardiac value.
