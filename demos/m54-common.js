// m54 · Shared code for the m54 demos, as in labs/python/epml/nuclear.py. MIT License.
// tests/test_m54_demos.py checks these functions against Python.
import { erf, normCdf } from "./m35-common.js";

export const F18_HALF_LIFE_MIN = 109.73; // TUNL recommended value (2019)
export const PET_FWHM_MM = [4, 7]; // clinical PET resolution (Kinahan and Fletcher 2010)

// eq-m54-decay
export function activity(a0, t, halfLife = F18_HALF_LIFE_MIN) {
  return a0 * Math.exp((-Math.LN2 / halfLife) * t);
}

export function clockErrorBias(dt, halfLife = F18_HALF_LIFE_MIN) {
  return 2 ** (dt / halfLife) - 1;
}

// eq-m54-suv
export function suv(concKbqMl, injectedMbq, weightKg, minutes = 0, residualMbq = 0, halfLife = F18_HALF_LIFE_MIN) {
  return concKbqMl / (activity(injectedMbq - residualMbq, minutes, halfLife) / weightKg);
}

export function fwhmToSigma(fwhm) {
  return fwhm / (2 * Math.sqrt(2 * Math.LN2));
}

// eq-m54-recovery
export function slabProfile(x, width, sigma) {
  const r = Math.SQRT2 * sigma;
  return 0.5 * (erf((x + width / 2) / r) - erf((x - width / 2) / r));
}

export function rcPeak(width, sigma) {
  return erf(width / (2 * Math.SQRT2 * sigma));
}

export function rcMean(width, sigma) {
  const b = width / (Math.SQRT2 * sigma);
  return erf(b) - (1 - Math.exp(-b * b)) / (b * Math.sqrt(Math.PI));
}

// eq-m54-change
export function pCalledResponder(trueRatio, cv = 0.1, drop = 0.25) {
  const s = Math.SQRT2 * Math.sqrt(Math.log(1 + cv * cv));
  return normCdf((Math.log(1 - drop) - Math.log(trueRatio)) / s);
}
