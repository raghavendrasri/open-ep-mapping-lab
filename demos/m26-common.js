// m26 · Shared code for the m26 demos, as in labs/python/epml/uncertainty.py. MIT License.
// tests/test_m26_demos.py checks these against Python. Times in ms, lengths in mm, speed in mm/ms (= m/s).

// eq-m26-gp (1D inputs)
export const seKernel = (x1, x2, ell, s2) => s2 * Math.exp((-0.5 * (x1 - x2) ** 2) / (ell * ell));

function cholesky(A) {
  const n = A.length, L = A.map(() => new Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      let s = A[i][j];
      for (let k = 0; k < j; k++) s -= L[i][k] * L[j][k];
      L[i][j] = i === j ? Math.sqrt(Math.max(s, 1e-12)) : s / L[j][j];
    }
  }
  return L;
}
const forward = (L, b) => { const n = b.length, x = new Array(n); for (let i = 0; i < n; i++) { let s = b[i]; for (let k = 0; k < i; k++) s -= L[i][k] * x[k]; x[i] = s / L[i][i]; } return x; };
const backward = (L, b) => { const n = b.length, x = new Array(n); for (let i = n - 1; i >= 0; i--) { let s = b[i]; for (let k = i + 1; k < n; k++) s -= L[k][i] * x[k]; x[i] = s / L[i][i]; } return x; };

export function gpPosterior(X, y, Xs, ell, s2, noise, mean = 0) {
  const A = X.map((xi, i) => X.map((xj, j) => seKernel(xi, xj, ell, s2) + (i === j ? noise * noise : 0)));
  const L = cholesky(A);
  const alpha = backward(L, forward(L, y.map((v) => v - mean)));
  const mu = [], vr = [];
  for (const xs of Xs) {
    const k = X.map((xi) => seKernel(xi, xs, ell, s2));
    mu.push(mean + k.reduce((s, kv, i) => s + kv * alpha[i], 0));
    const v = forward(L, k);
    vr.push(Math.max(0, s2 - v.reduce((s, q) => s + q * q, 0)));
  }
  return [mu, vr];
}
export function singlePointVariance(d, ell, s2, noise) {
  const k = s2 * Math.exp((-0.5 * d * d) / (ell * ell));
  return s2 - (k * k) / (s2 + noise * noise);
}
// eq-m26-budget
export const errorBudget = (sa, sr, sx, c) => Math.sqrt(sa * sa + sr * sr + (sx / c) ** 2);
// eq-m26-density
export const nnDistanceMean = (rho) => 0.5 / Math.sqrt(rho);

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function gauss(r) {
  const u = Math.max(r(), 1e-12), v = r();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}
