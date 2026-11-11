// m41 · Gaussian process, expected improvement and an illustrative pace-map landscape. MIT License.
// The GP and EI mirror labs/python/epml/origins.py and are tested against it (tests/test_m41_demos.py).

export function rbf(a, b, ell, sf) {
  let d2 = 0;
  for (let k = 0; k < a.length; k++) d2 += (a[k] - b[k]) ** 2;
  return sf * sf * Math.exp(-0.5 * d2 / (ell * ell));
}

function cholesky(A) {
  const n = A.length;
  const L = A.map(() => new Array(n).fill(0));
  for (let i = 0; i < n; i++) {
    for (let j = 0; j <= i; j++) {
      let s = A[i][j];
      for (let k = 0; k < j; k++) s -= L[i][k] * L[j][k];
      L[i][j] = i === j ? Math.sqrt(Math.max(s, 1e-18)) : s / L[j][j];
    }
  }
  return L;
}

function solveLower(L, b) {
  const x = new Array(b.length);
  for (let i = 0; i < b.length; i++) {
    let s = b[i];
    for (let k = 0; k < i; k++) s -= L[i][k] * x[k];
    x[i] = s / L[i][i];
  }
  return x;
}

function solveUpperT(L, b) {
  const n = b.length;
  const x = new Array(n);
  for (let i = n - 1; i >= 0; i--) {
    let s = b[i];
    for (let k = i + 1; k < n; k++) s -= L[k][i] * x[k];
    x[i] = s / L[i][i];
  }
  return x;
}

// eq-m41-gp: posterior mean and variance at test points (arrays of coordinate arrays).
export function gpPosterior(Xtr, ytr, Xte, ell, sf, sn, mean = 0) {
  const n = Xtr.length;
  const K = Xtr.map((a, i) => Xtr.map((b, j) => rbf(a, b, ell, sf) + (i === j ? sn * sn : 0)));
  const L = cholesky(K);
  const alpha = solveUpperT(L, solveLower(L, ytr.map((y) => y - mean)));
  const mu = [];
  const variance = [];
  for (const x of Xte) {
    const ks = Xtr.map((a) => rbf(x, a, ell, sf));
    let m = mean;
    for (let i = 0; i < n; i++) m += ks[i] * alpha[i];
    const v = solveLower(L, ks);
    let q = 0;
    for (let i = 0; i < n; i++) q += v[i] * v[i];
    mu.push(m);
    variance.push(Math.max(sf * sf - q, 0));
  }
  return { mu, variance };
}

// Standard normal density and distribution (erf by Abramowitz and Stegun 7.1.26, error < 1.5e-7).
export function normPdf(z) {
  return Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);
}
export function normCdf(z) {
  const x = Math.abs(z) / Math.SQRT2;
  const t = 1 / (1 + 0.3275911 * x);
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t) * Math.exp(-x * x);
  return z >= 0 ? 0.5 * (1 + y) : 0.5 * (1 - y);
}

// eq-m41-ei for maximization.
export function expectedImprovement(mu, sigma, best, xi = 0) {
  const d = mu - best - xi;
  if (sigma <= 0) return Math.max(d, 0);
  const z = d / sigma;
  return d * normCdf(z) + sigma * normPdf(z);
}

// Illustrative pace-map similarity on a 60-by-60-mm patch: a main peak at the origin and a weaker decoy.
export const ORIGIN = [42, 18];
export const DECOY = [14, 46];
export function similarity(x, y) {
  const g = (c, s) => Math.exp(-((x - c[0]) ** 2 + (y - c[1]) ** 2) / (2 * s * s));
  return 0.95 * g(ORIGIN, 10) + 0.55 * g(DECOY, 8) - 0.2;
}

// Deterministic pseudo-random generator for the "random pacing" rule.
export function lcg(seed) {
  let s = seed >>> 0;
  return () => {
    s = (1664525 * s + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

// Sequence of paced grid indices: two fixed starts, then EI (or random) choices.
export function pacingSequence(grid, values, nTotal, { ell, sf, sn, rule = "ei", seed = 41 }) {
  const paced = [0, grid.length - 1];
  const rand = lcg(seed);
  while (paced.length < nTotal) {
    const cand = grid.map((_, k) => k).filter((k) => !paced.includes(k));
    if (rule === "random") {
      paced.push(cand[Math.floor(rand() * cand.length)]);
      continue;
    }
    const y = paced.map((k) => values[k]);
    const m = y.reduce((a, b) => a + b, 0) / y.length;
    const best = Math.max(...y);
    const post = gpPosterior(paced.map((k) => grid[k]), y, cand.map((k) => grid[k]), ell, sf, sn, m);
    let arg = 0;
    let top = -Infinity;
    post.mu.forEach((mu, i) => {
      const ei = expectedImprovement(mu, Math.sqrt(post.variance[i]), best);
      if (ei > top) {
        top = ei;
        arg = i;
      }
    });
    paced.push(cand[arg]);
  }
  return paced;
}
