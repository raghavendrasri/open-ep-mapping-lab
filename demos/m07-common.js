// m07 · Shared code for the m07 demos, as in labs/python/epml/inverse.py. MIT License.
// tests/test_m07_demos.py checks these against Python.

export const N = 256; // grid points
export const LENGTH = 32; // mm, periodic
export const WIDTH = 0.3; // mm, front width as in m03-d1
export const FRONTS = [
  [8, 1],
  [18, 1],
  [21, -1],
]; // (position mm, sign): one front, then two fronts 3 mm apart moving toward each other

// Periodic grid: positions s (mm) and wavenumbers k (rad/mm) in numpy FFT order.
export function grid(n = N, length = LENGTH) {
  const s = new Float64Array(n);
  const k = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    s[i] = (i * length) / n;
    const m = i < n / 2 ? i : i - n;
    k[i] = (2 * Math.PI * m) / length;
  }
  return { s, k };
}

// eq-m07-continuation: the gain exp(-|k| h) of each harmonic across a source-free layer of thickness h
export const gain = (k, h) => Array.from(k, (v) => Math.exp(-Math.abs(v) * h));

// The band-limited periodic m03 front shape: (2 pi / L) sum_{m < nHarm} exp(-k_m a) sin(k_m s)
export function frontProfile(s, a, length = LENGTH, nHarm = N / 2) {
  const out = new Float64Array(s.length);
  for (let m = 1; m < nHarm; m++) {
    const km = (2 * Math.PI * m) / length;
    const amp = ((2 * Math.PI) / length) * Math.exp(-km * a);
    for (let i = 0; i < s.length; i++) out[i] += amp * Math.sin(km * s[i]);
  }
  return out;
}

export function tissueProfile(s, width = WIDTH, length = LENGTH, fronts = FRONTS, nHarm = N / 2) {
  const out = new Float64Array(s.length);
  for (const [pos, sign] of fronts) {
    const p = frontProfile(Array.from(s, (v) => v - pos), width, length, nHarm);
    for (let i = 0; i < s.length; i++) out[i] += sign * p[i];
  }
  return out;
}

// Direct DFT of a real signal (unnormalized, numpy sign convention) and the real part of its inverse.
const tables = new Map();
function table(n) {
  if (!tables.has(n)) {
    const c = new Float64Array(n);
    const sn = new Float64Array(n);
    for (let j = 0; j < n; j++) {
      c[j] = Math.cos((2 * Math.PI * j) / n);
      sn[j] = Math.sin((2 * Math.PI * j) / n);
    }
    tables.set(n, { c, sn });
  }
  return tables.get(n);
}

export function dft(x) {
  const n = x.length;
  const { c, sn } = table(n);
  const re = new Float64Array(n);
  const im = new Float64Array(n);
  for (let m = 0; m < n; m++) {
    let a = 0;
    let b = 0;
    for (let j = 0; j < n; j++) {
      const idx = (m * j) % n;
      a += x[j] * c[idx];
      b -= x[j] * sn[idx];
    }
    re[m] = a;
    im[m] = b;
  }
  return { re, im };
}

export function idftReal(re, im) {
  const n = re.length;
  const { c, sn } = table(n);
  const out = new Float64Array(n);
  for (let j = 0; j < n; j++) {
    let a = 0;
    for (let m = 0; m < n; m++) {
      const idx = (m * j) % n;
      a += re[m] * c[idx] - im[m] * sn[idx];
    }
    out[j] = a / n;
  }
  return out;
}

// Multiply each harmonic by a real factor g[m].
export function filterReal(x, g) {
  const { re, im } = dft(x);
  return idftReal(
    re.map((v, m) => v * g[m]),
    im.map((v, m) => v * g[m]),
  );
}

// eq-m07-filters: Tikhonov for a circulant operator, each harmonic multiplied by g / (g^2 + lam^2)
export const tikhonov = (b, g, lam) =>
  filterReal(
    b,
    g.map((v) => v / (v * v + lam * lam)),
  );

// eq-m07-error in the DFT basis: (1/n) sum (1 - f)^2 |X|^2 and sigma^2 sum f^2 / g^2, f = g^2 / (g^2 + lam^2)
export function expectedError(X2, g, sigma, lam) {
  const n = X2.length;
  let bias = 0;
  let variance = 0;
  for (let m = 0; m < n; m++) {
    const f = (g[m] * g[m]) / (g[m] * g[m] + lam * lam);
    bias += (1 - f) * (1 - f) * X2[m];
    variance += (f * f) / (g[m] * g[m]);
  }
  bias /= n;
  variance *= sigma * sigma;
  return { bias, variance, total: bias + variance };
}

// Reproducible standard normal numbers (mulberry32 and Box-Muller).
export function normals(n, seed = 7) {
  let a = seed >>> 0;
  const rand = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const out = new Float64Array(n);
  for (let i = 0; i < n; i += 2) {
    const u = Math.max(rand(), 1e-12);
    const v = rand();
    const r = Math.sqrt(-2 * Math.log(u));
    out[i] = r * Math.cos(2 * Math.PI * v);
    if (i + 1 < n) out[i + 1] = r * Math.sin(2 * Math.PI * v);
  }
  return out;
}

export const norm = (x) => Math.sqrt(x.reduce((a, v) => a + v * v, 0));
