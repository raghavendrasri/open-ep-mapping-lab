// m04 · Shared code for the m04 demos, as in labs/python/epml/recording.py. MIT License.
// tests/test_m04_demos.py checks these against Python.

// eq-m04-sampling
export const aliasFrequency = (f, fs) => Math.abs(f - fs * Math.round(f / fs));

// First- or second-order Butterworth by the bilinear transform with prewarping; returns { b, a } with a[0] = 1.
export function butterDigital(fc, fs, order, kind) {
  const W = 2 * fs * Math.tan((Math.PI * fc) / fs);
  const K = 2 * fs;
  let b;
  let a;
  if (order === 1) {
    a = [K + W, W - K];
    b = kind === "low" ? [W, W] : [K, -K];
  } else {
    const q = Math.SQRT2;
    a = [K * K + q * W * K + W * W, 2 * (W * W - K * K), K * K - q * W * K + W * W];
    b = kind === "low" ? [W * W, 2 * W * W, W * W] : [K * K, -2 * K * K, K * K];
  }
  const a0 = a[0];
  return { b: b.map((v) => v / a0), a: a.map((v) => v / a0) };
}

// Direct-form filter, as scipy.signal.lfilter with zero initial state.
export function lfilter({ b, a }, x) {
  const y = new Float64Array(x.length);
  for (let n = 0; n < x.length; n++) {
    let acc = 0;
    for (let k = 0; k < b.length; k++) if (n - k >= 0) acc += b[k] * x[n - k];
    for (let k = 1; k < a.length; k++) if (n - k >= 0) acc -= a[k] * y[n - k];
    y[n] = acc;
  }
  return y;
}

export function apply(coef, x, zeroPhase = false) {
  let y = lfilter(coef, x);
  if (zeroPhase) y = lfilter(coef, Array.from(y).reverse()).reverse();
  return y;
}

// High-pass then low-pass, second order, as recording.chain(..., order=2).
export function chain(x, fs, { hp, lp, zeroPhase = false }) {
  let y = Float64Array.from(x);
  if (hp) y = apply(butterDigital(hp, fs, 2, "high"), y, zeroPhase);
  if (lp && lp < fs / 2) y = apply(butterDigital(lp, fs, 2, "low"), y, zeroPhase);
  return y;
}

// The m03 unipolar electrogram at a fixed electrode as the front passes at t = 0 (c in mm/ms).
export function unipolarEgm(tMs, c = 1, w = 0.3, h = 1) {
  const s = -c * tMs;
  const a = w + h;
  return s / (s * s + a * a);
}

// Time of the most negative slope, with parabolic refinement (as recording.steepest_downstroke).
export function steepestDownstroke(t, x) {
  const n = x.length;
  const d = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    if (i === 0) d[i] = (x[1] - x[0]) / (t[1] - t[0]);
    else if (i === n - 1) d[i] = (x[n - 1] - x[n - 2]) / (t[n - 1] - t[n - 2]);
    else d[i] = (x[i + 1] - x[i - 1]) / (t[i + 1] - t[i - 1]);
  }
  let k = 0;
  for (let i = 1; i < n; i++) if (d[i] < d[k]) k = i;
  if (k > 0 && k < n - 1) {
    const den = d[k - 1] - 2 * d[k] + d[k + 1];
    const off = den ? (0.5 * (d[k - 1] - d[k + 1])) / den : 0;
    return t[k] + off * (t[1] - t[0]);
  }
  return t[k];
}
