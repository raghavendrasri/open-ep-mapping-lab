// m10 · Shared code for the m10 demos, as in labs/python/epml/arrhythmia.py. MIT License.
// tests/test_m10_demos.py checks these against Python.

// Mitchell-Schaeffer parameters (ms) as reported by Nieto Ramos et al. 2023, based on Mitchell and Schaeffer 2003
export const MS = { tauIn: 0.3, tauOut: 6, tauOpen: 150, tauClose: 120, vGate: 0.13 };

// The m08 closed-form restitution APD = f(DI) and its slope
export function restitution(di, p = MS) {
  const hm = (4 * p.tauIn) / p.tauOut;
  return p.tauClose * Math.log((1 - (1 - hm) * Math.exp(-di / p.tauOpen)) / hm);
}
export function restitutionSlope(di, p = MS) {
  const hm = (4 * p.tauIn) / p.tauOut;
  const e = Math.exp(-di / p.tauOpen);
  return (p.tauClose * (1 - hm) * e) / (p.tauOpen * (1 - (1 - hm) * e));
}

// eq-m10-restitution: the fixed point APD* = f(CL - APD*), by bisection; [NaN, NaN] when there is none
export function fixedPoint(cl, p = MS) {
  let lo = 0;
  let hi = cl;
  const g = (a) => restitution(cl - a, p) - a;
  if (!(g(lo) > 0)) return [NaN, NaN];
  for (let k = 0; k < 200; k++) {
    const mid = (lo + hi) / 2;
    const val = g(mid);
    if (!Number.isFinite(val) || val < 0) hi = mid;
    else lo = mid;
  }
  return [lo, cl - lo];
}

// APD_{k+1} = f(CL - APD_k); NaN once the diastolic interval is not positive
export function iterateMap(cl, apd0, n, p = MS) {
  const out = [apd0];
  for (let k = 0; k < n; k++) {
    const di = cl - out[out.length - 1];
    out.push(di > 0 ? restitution(di, p) : NaN);
  }
  return out;
}

// eq-m10-circuit
export function circuit(L, cv, erp) {
  const lam = cv * erp;
  const cl = L / cv;
  return { wavelength: lam, cycleLength: cl, gapMm: L - lam, gapMs: cl - erp, sustained: L > lam };
}
