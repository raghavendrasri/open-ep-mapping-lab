// m47 · Shared code for the m47 demos, as in labs/python/epml/deploy.py. MIT License.
// tests/test_m47_demos.py checks these functions against Python.

// Seeded uniform draws on [0, 1) (mulberry32), for repeatable demos.
export function uniforms(n, seed) {
  let a = seed >>> 0;
  const out = [];
  for (let i = 0; i < n; i++) {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    out.push(((t ^ (t >>> 14)) >>> 0) / 4294967296);
  }
  return out;
}

// Round half to even, as numpy.round and Python's round do.
export function rint(v) {
  const f = Math.floor(v);
  const d = v - f;
  if (d > 0.5) return f + 1;
  if (d < 0.5) return f;
  return f % 2 === 0 ? f : f + 1;
}

// eq-m47-affine: scale S and zero point Z for r = S (q - Z); the range is widened to contain 0.
export function qparams(rmin, rmax, bits = 8, signed = false) {
  const lo = Math.min(rmin, 0);
  const hi = Math.max(rmax, 0);
  const qmin = signed ? -(2 ** (bits - 1)) : 0;
  const qmax = signed ? 2 ** (bits - 1) - 1 : 2 ** bits - 1;
  const S = (hi - lo) / (qmax - qmin) || 1;
  const Z = Math.min(qmax, Math.max(qmin, rint(qmin - lo / S)));
  return { S, Z, qmin, qmax };
}

export function fakeQuant(r, { S, Z, qmin, qmax }) {
  return r.map((v) => S * (Math.min(qmax, Math.max(qmin, rint(v / S) + Z)) - Z));
}

export function sqnrDb(x, xq) {
  let ps = 0;
  let pe = 0;
  x.forEach((v, i) => {
    ps += v * v;
    pe += (v - xq[i]) ** 2;
  });
  return 10 * Math.log10(ps / pe);
}

// eq-m47-qnoise: rounding noise variance S^2 / 12.
export function predictedSqnrDb(x, S) {
  const ps = x.reduce((s, v) => s + v * v, 0) / x.length;
  return 10 * Math.log10(ps / ((S * S) / 12));
}

// Equivalence-class size of each record over the given columns (arrays of equal length).
export function classSizes(columns) {
  const n = columns[0].length;
  const keys = Array.from({ length: n }, (_, i) => columns.map((c) => c[i]).join("|"));
  const count = new Map();
  keys.forEach((k) => count.set(k, (count.get(k) || 0) + 1));
  return keys.map((k) => count.get(k));
}

// eq-m47-risk: largest risk 1/min f, average risk mean(1/f) = classes / records, share unique.
export function reidRisk(sizes) {
  const k = Math.min(...sizes);
  return {
    max: 1 / k,
    average: sizes.reduce((s, f) => s + 1 / f, 0) / sizes.length,
    unique: sizes.filter((f) => f === 1).length / sizes.length,
    k,
  };
}
