// m52 · Shared code for the m52 demos, as in labs/python/epml/mri.py. MIT License.
// tests/test_m52_demos.py checks these functions against Python.

export const GAMMA_BAR_MHZ_PER_T = 42.577478461; // CODATA 2022

// Bauner et al. 2012: mean T1 (ms) 10 minutes after contrast at 1.5 T.
export const T1_POST = { myocardium: 379, infarct: 238 };
// Blood T1 consistent with those values and an illustrative native blood T1 (1600 ms) and hematocrit (0.42).
export const T1_BLOOD_ILLUSTRATIVE = 248.68;

export function larmorMhz(b0) {
  return GAMMA_BAR_MHZ_PER_T * b0;
}

// eq-m52-ir
export function irMz(t, t1) {
  return 1 - 2 * Math.exp(-t / t1);
}

export function nullTime(t1) {
  return t1 * Math.LN2;
}

// eq-m52-lge
export function lgeSignal(ti, t1, magnitude = true) {
  const s = irMz(ti, t1);
  return magnitude ? Math.abs(s) : s;
}

export function bestTiSigned(t1m, t1s) {
  return Math.log(t1m / t1s) / (1 / t1s - 1 / t1m);
}

// eq-m52-iir: fraction above a threshold, Otsu's threshold, and Dice.
export function burden(values, threshold) {
  let n = 0;
  for (const v of values) if (v > threshold) n++;
  return n / values.length;
}

export function otsuThreshold(values, bins = 256) {
  let lo = Infinity;
  let hi = -Infinity;
  for (const v of values) {
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  const width = (hi - lo) / bins;
  const hist = new Float64Array(bins);
  for (const v of values) hist[Math.min(bins - 1, Math.floor((v - lo) / width))] += 1;
  const total = values.length;
  let mt = 0;
  for (let k = 0; k < bins; k++) mt += (hist[k] / total) * (lo + (k + 0.5) * width);
  let w0 = 0;
  let m = 0;
  let best = -1;
  let bestK = 0;
  for (let k = 0; k < bins; k++) {
    const w = hist[k] / total;
    w0 += w;
    m += w * (lo + (k + 0.5) * width);
    const w1 = 1 - w0;
    if (w0 <= 0 || w1 <= 1e-15) continue;
    const between = (mt * w0 - m) ** 2 / (w0 * w1);
    if (between > best) {
      best = between;
      bestK = k;
    }
  }
  return lo + (bestK + 1) * width;
}

export function dice(a, b) {
  let inter = 0;
  let sa = 0;
  let sb = 0;
  for (let k = 0; k < a.length; k++) {
    if (a[k]) sa++;
    if (b[k]) sb++;
    if (a[k] && b[k]) inter++;
  }
  return sa + sb === 0 ? 1 : (2 * inter) / (sa + sb);
}

export function thresholdFor(method, wall, bloodSd) {
  if (method.kind === "iir") return method.value;
  if (method.kind === "sd") return 1 + method.value * bloodSd;
  if (method.kind === "otsu") return otsuThreshold(wall);
  throw new Error(`unknown method ${method.kind}`);
}
