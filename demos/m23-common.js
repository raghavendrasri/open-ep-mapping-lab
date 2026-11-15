// m23 · Shared code for the m23 demos, as in labs/python/epml/voltage.py. MIT License.
// tests/test_m23_demos.py checks these against Python. Lengths in mm; voltages relative or in mV.

export const unipolar = (s, a, A = 1) => (A * s) / (s * s + a * a);

function grid(a, d, n = 2001) {
  const L = 0.5 * d + 6 * a;
  const s = new Array(n);
  for (let i = 0; i < n; i++) s[i] = -L + (2 * L * i) / (n - 1);
  return s;
}
const pp = (x) => Math.max(...x) - Math.min(...x);

// eq-m23-amplitude
export const unipolarPp = (a, A = 1) => A / a;
export function bipolarPp(a, d, theta = 0, A = 1) {
  const delta = 0.5 * d * Math.cos(theta);
  return pp(grid(a, d).map((s) => unipolar(s + delta, a, A) - unipolar(s - delta, a, A)));
}
export const bipolarPpSmall = (a, d, theta = 0, A = 1) => ((9 / 8) * A * d * Math.abs(Math.cos(theta))) / (a * a);
export const heightFactor = (a, extra, kind = "bipolar") => (a / (a + extra)) ** (kind === "bipolar" ? 2 : 1);

// eq-m23-direction
export const belowFraction = (q) => (2 / Math.PI) * Math.asin(Math.min(Math.max(q, 0), 1));
export function pairAndField(a, d, theta, nDir = 60) {
  const s = grid(a, d);
  const dx = 0.5 * d * Math.cos(theta), dy = 0.5 * d * Math.sin(theta);
  const bx = s.map((v) => unipolar(v + dx, a) - unipolar(v - dx, a));
  const by = s.map((v) => unipolar(v + dy, a) - unipolar(v - dy, a));
  let field = 0;
  for (let k = 0; k < nDir; k++) {
    const w = (Math.PI * k) / nDir, c = Math.cos(w), sn = Math.sin(w);
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < s.length; i++) { const v = c * bx[i] + sn * by[i]; if (v < lo) lo = v; if (v > hi) hi = v; }
    field = Math.max(field, hi - lo);
  }
  return { single: pp(bx), pair: Math.max(pp(bx), pp(by)), field };
}

// eq-m23-threshold
export function ndtr(x) {
  // Abramowitz and Stegun 7.1.26 for erf, |error| < 1.5e-7
  const z = Math.abs(x) / Math.SQRT2, t = 1 / (1 + 0.3275911 * z);
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-z * z);
  return x >= 0 ? 0.5 * (1 + y) : 0.5 * (1 - y);
}
export const lognormalCdf = (v, median, logSd) => ndtr((Math.log(v) - Math.log(median)) / logSd);
export function thresholdRates(cutoff, medScar, medNormal, sdScar, sdNormal) {
  return [lognormalCdf(cutoff, medScar, sdScar), 1 - lognormalCdf(cutoff, medNormal, sdNormal)];
}
