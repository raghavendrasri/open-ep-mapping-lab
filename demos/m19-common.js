// m19 · Shared code for the m19 demos, as in labs/python/epml/motion.py. MIT License.
// tests/test_m19_demos.py checks these against Python. Lengths in mm, times in s.

// eq-m19-breathing
export const breathing = (t, period, amplitude, n = 2, zExhale = 0) => zExhale - amplitude * Math.cos((Math.PI * t) / period) ** (2 * n);
// eq-m19-gating
export const gatingDutyCycle = (w, amplitude, n = 2) => 1 - (2 / Math.PI) * Math.acos(Math.min(Math.max(w / amplitude, 0), 1) ** (1 / (2 * n)));
// eq-m19-reference
export const differenceSd = (sx, sr, rho) => Math.sqrt(sx * sx + sr * sr - 2 * rho * sx * sr);
// eq-m19-surrogate
export const residualSd = (sx, rho) => sx * Math.sqrt(1 - rho * rho);
