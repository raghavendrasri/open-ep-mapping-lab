// m22 · Shared code for the m22 demos, as in labs/python/epml/annotation.py. MIT License.
// tests/test_m22_demos.py checks these against Python. Times in ms, lengths in mm, speed in mm/ms (= m/s).

// The m03 arctangent-front unipolar potential at front distance s.
export const unipolar = (s, a, A = 1) => (A * s) / (s * s + a * a);
export const unipolarTrace = (t, c, a, t0 = 0) => unipolar(-c * (t - t0), a);
export function bipolarTrace(t, c, a, d, t0 = 0) {
  const delta = 0.5 * d;
  const s = -c * (t - t0);
  return unipolar(s + delta, a) - unipolar(s - delta, a);
}

function parabolic(t, y, i) {
  if (i <= 0 || i >= y.length - 1) return t[i];
  const den = y[i - 1] - 2 * y[i] + y[i + 1];
  const off = den ? (0.5 * (y[i - 1] - y[i + 1])) / den : 0;
  return t[i] + off * (t[1] - t[0]);
}

function gradient(t, x) {
  const n = x.length, d = new Array(n);
  d[0] = (x[1] - x[0]) / (t[1] - t[0]);
  d[n - 1] = (x[n - 1] - x[n - 2]) / (t[n - 1] - t[n - 2]);
  for (let i = 1; i < n - 1; i++) d[i] = (x[i + 1] - x[i - 1]) / (t[i + 1] - t[i - 1]);
  return d;
}

// eq-m22-intrinsic
export function steepestDownstroke(t, x) {
  const d = gradient(t, x);
  let i = 0;
  for (let k = 1; k < d.length; k++) if (d[k] < d[i]) i = k;
  return parabolic(t, d, i);
}
export function peakTime(t, x) {
  const y = x.map(Math.abs);
  let i = 0;
  for (let k = 1; k < y.length; k++) if (y[k] > y[i]) i = k;
  return parabolic(t, y, i);
}
// eq-m22-onset
export function onsetTime(t, x, fraction) {
  const y = x.map(Math.abs);
  let k = 0;
  for (let i = 1; i < y.length; i++) if (y[i] > y[k]) k = i;
  const level = fraction * y[k];
  let j = k;
  while (j > 0 && y[j - 1] >= level) j--;
  if (j === 0) return t[0];
  return t[j - 1] + ((level - y[j - 1]) / (y[j] - y[j - 1])) * (t[j] - t[j - 1]);
}
export function onsetLeadRatio(f) {
  const x = (-(2 * f + 1) + Math.sqrt(8 * f + 1)) / (2 * f);
  return Math.sqrt(x);
}
// eq-m22-woi
export function windowLat(tRel, w0, width, cycle) {
  const m = ((((tRel - w0) % cycle) + cycle) % cycle);
  const v = w0 + m;
  return v < w0 + width ? v : NaN;
}
export const ringActivation = (p, length, cycle, tStart = 0) => tStart + (cycle * p) / length;
