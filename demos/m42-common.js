// m42 · One-dimensional radial-basis fits and randomized-prior ensembles. MIT License.
// rbfDesign and ridgeFit mirror labs/python/epml/pinn.py and numpy (tests/test_m42_demos.py).

export function rbfDesign(xs, centres, h) {
  return xs.map((x) => [...centres.map((c) => Math.exp(-0.5 * ((x - c) / h) ** 2)), 1]);
}

function solve(A, b) {
  // Gaussian elimination with partial pivoting (small systems).
  const n = b.length;
  const M = A.map((row, i) => [...row, b[i]]);
  for (let k = 0; k < n; k++) {
    let p = k;
    for (let i = k + 1; i < n; i++) if (Math.abs(M[i][k]) > Math.abs(M[p][k])) p = i;
    [M[k], M[p]] = [M[p], M[k]];
    for (let i = k + 1; i < n; i++) {
      const f = M[i][k] / M[k][k];
      for (let j = k; j <= n; j++) M[i][j] -= f * M[k][j];
    }
  }
  const x = new Array(n).fill(0);
  for (let i = n - 1; i >= 0; i--) {
    let s = M[i][n];
    for (let j = i + 1; j < n; j++) s -= M[i][j] * x[j];
    x[i] = s / M[i][i];
  }
  return x;
}

// Ridge least squares: minimize |Phi a - y|^2 + ridge |a_without_constant|^2.
export function ridgeFit(Phi, y, ridge) {
  const k = Phi[0].length;
  const A = Array.from({ length: k }, (_, i) => Array.from({ length: k }, (_, j) => Phi.reduce((s, row) => s + row[i] * row[j], 0) + (i === j && i < k - 1 ? ridge : 0)));
  const b = Array.from({ length: k }, (_, i) => Phi.reduce((s, row, r) => s + row[i] * y[r], 0));
  return solve(A, b);
}

// Seeded standard normals (mulberry32 + Box-Muller).
export function normals(seed) {
  let a = seed >>> 0;
  const u = () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  return () => Math.sqrt(-2 * Math.log(1 - u())) * Math.cos(2 * Math.PI * u());
}

// Randomized-prior ensemble in one dimension: each member fits (data + noise - prior) and adds its prior back.
export function ensemble1d({ xs, ys, xEval, centres, h, ridge, members, noise, priorScale, seed }) {
  const rnd = normals(seed);
  const Phi = rbfDesign(xs, centres, h);
  const PhiE = rbfDesign(xEval, centres, h);
  const preds = [];
  for (let m = 0; m < members; m++) {
    const w = centres.map(() => priorScale * rnd());
    const prior = (row) => row.slice(0, -1).reduce((s, v, i) => s + v * w[i], 0);
    const target = ys.map((y, i) => y + noise * rnd() - prior(Phi[i]));
    const a = ridgeFit(Phi, target, ridge);
    preds.push(PhiE.map((row) => row.reduce((s, v, i) => s + v * a[i], 0) + prior(row)));
  }
  return preds;
}
