// m48 · Shared code for the m48 demos, as in labs/python/epml/overview.py (and epml.ct for the wall readings).
// MIT License. tests/test_m48_demos.py checks these functions against Python.
import { erf, predictiveValues } from "./m35-common.js";
import { erfinv } from "./m53-common.js";

export { predictiveValues };

export const FWHM_PER_SIGMA = 2 * Math.sqrt(2 * Math.LN2);
export const fwhmToSigma = (fwhm) => fwhm / FWHM_PER_SIGMA;

// Published resolutions read as the FWHM of a Gaussian blur, in mm.
export const RESOLUTION_MM = [
  { label: "CT, photon-counting, thinnest section, high-resolution mode (0.34 mm)", fwhm: 0.34 }, // Rajendran et al. 2022
  { label: "CT, photon-counting, thinnest section, standard mode (0.64 mm)", fwhm: 0.64 }, // Rajendran et al. 2022
  { label: "MRI LGE, thin-wall protocol (about 1 mm)", fwhm: 1.0 }, // Kellman and Arai 2012
  { label: "MRI LGE, routine (1.5 mm)", fwhm: 1.5 }, // Kellman and Arai 2012
  { label: "MRI LGE, routine (2 mm)", fwhm: 2.0 }, // Kellman and Arai 2012
  { label: "PET, clinical, best case (4 mm)", fwhm: 4.0 }, // Kinahan and Fletcher 2010
  { label: "PET, clinical (7 mm)", fwhm: 7.0 }, // Kinahan and Fletcher 2010
];

// Left atrial wall thickness, mm (Beinart et al. 2011).
export const LA_WALL_MM = { mean: 1.89, min: 0.5, max: 3.5 };

// CT against TEE for appendage thrombus (Romero et al. 2013): 19 studies, 2,955 patients, 8.9% prevalence.
export const ROMERO2013 = {
  prevalence: 0.089,
  standard: { se: 0.96, sp: 0.92, ppv: 0.41, npv: 0.99 },
  delayed: { se: 1.0, sp: 0.99, ppv: 0.92, npv: 1.0 },
};

// eq-m51-wall: a wall of thickness w and unit contrast through a Gaussian blur.
export function slabProfile(x, width, sigma) {
  const r = Math.SQRT2 * sigma;
  return 0.5 * (erf((x + width / 2) / r) - erf((x - width / 2) / r));
}

export const slabPeak = (width, sigma) => erf(width / (2 * Math.SQRT2 * sigma));

function halfWidthAt(level, width, sigma) {
  let lo = 0;
  let hi = width / 2 + 10 * sigma;
  for (let k = 0; k < 80; k++) {
    const mid = (lo + hi) / 2;
    if (slabProfile(mid, width, sigma) > level) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

// Thickness read with a fixed threshold at `level` of the full contrast (0 if the peak never reaches it).
export function thresholdThickness(width, sigma, level = 0.5) {
  if (slabPeak(width, sigma) < level) return 0;
  return 2 * halfWidthAt(level, width, sigma);
}

// Thickness read as the full width at half of the profile's own peak.
export function fwhmThickness(width, sigma) {
  return 2 * halfWidthAt(0.5 * slabPeak(width, sigma), width, sigma);
}

// eq-m48-visibility
export const wallCnr = (contrast, noise, width, sigma) => (contrast / noise) * slabPeak(width, sigma);

export function minVisibleWall(contrast, noise, sigma, k) {
  const r = (k * noise) / contrast;
  return r >= 1 ? Infinity : 2 * Math.SQRT2 * sigma * erfinv(r);
}

// eq-m48-lr
export function likelihoodRatios(se, sp) {
  return { pos: se / (1 - sp), neg: (1 - se) / sp };
}

export function postTestProbability(pretest, lr) {
  const odds = (pretest / (1 - pretest)) * lr;
  return odds / (1 + odds);
}
