// m15 · Shared code for the m15 demos, as in labs/python/epml/safety.py. MIT License.
// tests/test_m15_demos.py checks these against Python. SI units.

// Minimum 60-Hz intracardiac currents in 40 patients, microamperes (Swerdlow et al. 1999)
export const SWERDLOW_1999_UA = { intermittentCapture: 20, continuousCapture: 32, ventricularFibrillation: 49, usStandardSingleFault: 50 };

// eq-m15-leakage
export const capacitiveCurrent = (v, f, c) => 2 * Math.PI * f * c * v;
export const maxCapacitance = (limit, v, f) => limit / (2 * Math.PI * f * v);
// eq-m15-rf-filter
export const lowpassAttenuation = (f, fc, n) => 1 / Math.sqrt(1 + (f / fc) ** (2 * n));
export function orderNeeded(amp, allowed, f, fc) {
  let n = 1;
  while (amp * lowpassAttenuation(f, fc, n) > allowed && n < 20) n++;
  return n;
}
