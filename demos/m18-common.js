// m18 · Shared code for the m18 demos, as in labs/python/epml/hybrid.py. MIT License.
// tests/test_m18_demos.py checks these against Python. Lengths in mm.
import { linearEstimate, patchPairs, potentials } from "./m17-common.js";

export const EPS0 = 8.8541878128e-12;
export const ILLUSTRATIVE_SCALE = [1.12, 0.92, 1.05];
export const ILLUSTRATIVE_TISSUES = {
  "blood-like": { sigma: 0.7, epsInf: 60, deltaEps: 3.0e3, tau: 1.0e-6 },
  "wall-like": { sigma: 0.25, epsInf: 60, deltaEps: 4.0e4, tau: 1.5e-6 },
};

export function impedanceCoordinates(p, d = 150, scale = ILLUSTRATIVE_SCALE) {
  const P = patchPairs(d);
  return potentials(p, P).map((phi, i) => linearEstimate(phi, d) * scale[i]);
}

// Gaussian elimination with partial pivoting; B may have several columns
export function solve(A, B) {
  const n = A.length, m = B[0].length;
  const M = A.map((row, i) => [...row, ...B[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = c + 1; r < n; r++) {
      const f = M[r][c] / M[c][c];
      for (let j = c; j < n + m; j++) M[r][j] -= f * M[c][j];
    }
  }
  const X = Array.from({ length: n }, () => new Array(m).fill(0));
  for (let r = n - 1; r >= 0; r--) {
    for (let k = 0; k < m; k++) {
      let s = M[r][n + k];
      for (let j = r + 1; j < n; j++) s -= M[r][j] * X[j][k];
      X[r][k] = s / M[r][r];
    }
  }
  return X;
}

// eq-m18-affine: least squares x ~ A u + b, via normal equations
export function fitAffine(u, x) {
  const U = u.map((r) => [...r, 1]), q = U[0].length;
  const N = Array.from({ length: q }, (_, a) => Array.from({ length: q }, (_, b) => U.reduce((s, r) => s + r[a] * r[b], 0)));
  const R = Array.from({ length: q }, (_, a) => x[0].map((_, k) => U.reduce((s, r, i) => s + r[a] * x[i][k], 0)));
  return solve(N, R);      // rows: coefficients of u_1..u_d and 1; columns: outputs
}
export const applyAffine = (coef, u) => u.map((r) => coef[0].map((_, k) => [...r, 1].reduce((s, v, a) => s + v * coef[a][k], 0)));

// eq-m18-rbf: Gaussian RBF plus an affine part
const gauss = (r, s) => Math.exp(-0.5 * (r / s) ** 2);
const dist = (a, b) => Math.sqrt(a.reduce((s, v, i) => s + (v - b[i]) ** 2, 0));
export function fitRbf(u, x, scale, lam = 0) {
  const n = u.length, d = u[0].length, q = d + 1, K = [];
  for (let i = 0; i < n; i++) K.push([...u.map((v, j) => gauss(dist(u[i], v), scale) + (i === j ? lam : 0)), ...u[i], 1]);
  for (let a = 0; a < q; a++) K.push([...u.map((r) => (a < d ? r[a] : 1)), ...new Array(q).fill(0)]);
  const rhs = [...x.map((r) => r.slice()), ...Array.from({ length: q }, () => new Array(x[0].length).fill(0))];
  const sol = solve(K, rhs);
  return { centers: u, w: sol.slice(0, n), c: sol.slice(n), scale };
}
export function applyRbf(model, u) {
  return u.map((r) => model.w[0].map((_, k) => {
    let s = 0;
    model.centers.forEach((c, j) => { s += model.w[j][k] * gauss(dist(r, c), model.scale); });
    [...r, 1].forEach((v, a) => { s += v * model.c[a][k]; });
    return s;
  }));
}

// eq-m18-dielectric: phase of an impedance proportional to 1/sigma*, single Debye relaxation
export function impedancePhaseDeg(f, { sigma, epsInf, deltaEps, tau }) {
  const w = 2 * Math.PI * f, wt = w * tau, den = 1 + wt * wt;
  const epsRe = epsInf + deltaEps / den, epsIm = (-deltaEps * wt) / den;      // eps_r = epsRe + j epsIm
  const re = sigma - w * EPS0 * epsIm, im = w * EPS0 * epsRe;                  // sigma* = sigma + j w eps0 eps_r
  return (-Math.atan2(im, re) * 180) / Math.PI;
}
export function conductivityMagnitude(f, { sigma, epsInf, deltaEps, tau }) {
  const w = 2 * Math.PI * f, wt = w * tau, den = 1 + wt * wt;
  const epsRe = epsInf + deltaEps / den, epsIm = (-deltaEps * wt) / den;
  return Math.hypot(sigma - w * EPS0 * epsIm, w * EPS0 * epsRe);
}

// deterministic random numbers (mulberry32) for reproducible calibration points
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
