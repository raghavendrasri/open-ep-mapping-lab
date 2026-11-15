// m14 · Shared code for the m14 demos, as in labs/python/epml/frontend.py. MIT License.
// tests/test_m14_demos.py checks these against Python. SI units.

export const K_B = 1.380649e-23;   // J/K, exact in the SI (CODATA 2018)
export const T_BODY = 310.15;      // 37 degrees C

export const toDb = (r) => 20 * Math.log10(Math.abs(r));
// eq-m14-diffamp: worst-case CMRR of a difference amplifier of gain G with resistor tolerance tol
export const worstCaseCmrr = (gain, tol) => (1 + gain) / (4 * tol);
// eq-m14-imbalance: equivalent CMRR of an electrode impedance mismatch
export const imbalanceCmrr = (dz, zcm) => Math.abs(zcm / dz);
// 1/CMRR values add (worst case)
export const combinedCmrr = (...c) => 1 / c.reduce((s, v) => s + 1 / v, 0);
// eq-m14-noise
export const thermalDensity = (r, temp = T_BODY) => Math.sqrt(4 * K_B * temp * r);
export const totalDensity = (r, en, inn, temp = T_BODY) =>
  Math.sqrt(thermalDensity(r, temp) ** 2 + en * en + (inn * r) ** 2);
export const optimalSourceResistance = (en, inn) => en / inn;
