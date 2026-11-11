// m45 · Shared code for the m45 demos, as in labs/python/epml/evidence.py. MIT License.
// tests/test_m45_demos.py checks these functions against Python.

export const Z95 = 1.959963984540054;

// eq-m45-cusum: S_t = max(0, S_{t-1} + (x_t - target) - k); first alarm when S_t > h.
export function cusum(x, target, k, h) {
  let s = 0;
  let alarm = null;
  const S = x.map((v, t) => {
    s = Math.max(0, s + (v - target) - k);
    if (alarm === null && s > h) alarm = t;
    return s;
  });
  return { S, alarm };
}

// eq-m45-n-sens: patients needed for a sensitivity interval of half-width d at a given prevalence.
export function nForSensitivity(se, d, prevalence, z = Z95) {
  return Math.ceil((z * z * se * (1 - se)) / (d * d * prevalence));
}

export function nForSpecificity(sp, d, prevalence, z = Z95) {
  return Math.ceil((z * z * sp * (1 - sp)) / (d * d * (1 - prevalence)));
}

// A small seeded generator (mulberry32) and standard normal draws (Box–Muller), for repeatable demos.
export function normals(n, seed) {
  let a = seed >>> 0;
  const uni = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const out = [];
  while (out.length < n) {
    const u = Math.max(uni(), 1e-12);
    const v = uni();
    const r = Math.sqrt(-2 * Math.log(u));
    out.push(r * Math.cos(2 * Math.PI * v), r * Math.sin(2 * Math.PI * v));
  }
  return out.slice(0, n);
}
