// m16 · Shared code for the m16 demos, as in labs/python/epml/magnetic.py. MIT License.
// tests/test_m16_demos.py checks these against Python. Lengths in mm; fields in relative units (mu0/4pi = 1).

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];

// eq-m16-dipole
export function dipoleField(m, r) {
  const d = Math.hypot(r[0], r[1], r[2]);
  const rh = [r[0] / d, r[1] / d, r[2] / d];
  const k = 3 * dot(m, rh);
  return [(k * rh[0] - m[0]) / d ** 3, (k * rh[1] - m[1]) / d ** 3, (k * rh[2] - m[2]) / d ** 3];
}

export function generator(radius = 150, moment = 1e6, nSites = 3) {
  const out = [];
  for (let k = 0; k < nSites; k++) {
    const a = (2 * Math.PI * k) / nSites;
    const s = [radius * Math.cos(a), radius * Math.sin(a), 0];
    for (let j = 0; j < 3; j++) { const m = [0, 0, 0]; m[j] = moment; out.push([s, m]); }
  }
  return out;
}

export const axisFromAngles = (t, p) => [Math.sin(t) * Math.cos(p), Math.sin(t) * Math.sin(p), Math.cos(t)];

// eq-m16-coupling: readings n . B_k(p) of a single-coil sensor; params (x, y, z, theta, phi)
export function readings(q, gen) {
  const p = [q[0], q[1], q[2]], n = axisFromAngles(q[3], q[4]);
  return gen.map(([s, m]) => dot(n, dipoleField(m, sub(p, s))));
}

// eq-m16-distortion: a conductor at c responds to each coil with an induced dipole alpha B_k(c)
export function distortedReadings(q, gen, c, alpha) {
  const p = [q[0], q[1], q[2]], n = axisFromAngles(q[3], q[4]);
  return gen.map(([s, m]) => {
    const bc = dipoleField(m, sub(c, s));
    const mq = [alpha * bc[0], alpha * bc[1], alpha * bc[2]];
    return dot(n, add(dipoleField(m, sub(p, s)), dipoleField(mq, sub(p, c))));
  });
}

export function jacobian(q, gen, h = 1e-4) {
  const K = gen.length, J = Array.from({ length: K }, () => new Array(5).fill(0));
  for (let j = 0; j < 5; j++) {
    const qp = q.slice(), qm = q.slice();
    qp[j] += h; qm[j] -= h;
    const a = readings(qp, gen), b = readings(qm, gen);
    for (let k = 0; k < K; k++) J[k][j] = (a[k] - b[k]) / (2 * h);
  }
  return J;
}

function invert(A) {
  const n = A.length, M = A.map((row, i) => [...row, ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0))]);
  for (let c = 0; c < n; c++) {
    let piv = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[piv][c])) piv = r;
    [M[c], M[piv]] = [M[piv], M[c]];
    const d = M[c][c];
    for (let j = 0; j < 2 * n; j++) M[c][j] /= d;
    for (let r = 0; r < n; r++) if (r !== c) { const f = M[r][c]; for (let j = 0; j < 2 * n; j++) M[r][j] -= f * M[c][j]; }
  }
  return M.map((row) => row.slice(n));
}

const normal = (J) => [0, 1, 2, 3, 4].map((a) => [0, 1, 2, 3, 4].map((b) => J.reduce((s, row) => s + row[a] * row[b], 0)));

// eq-m16-crlb
export function crlb(q, gen, sigma) {
  return invert(normal(jacobian(q, gen))).map((row) => row.map((v) => sigma * sigma * v));
}
export const positionSd = (q, gen, sigma) => { const C = crlb(q, gen, sigma); return Math.sqrt(C[0][0] + C[1][1] + C[2][2]); };

// first-order bias (J^T J)^-1 J^T dv
export function linearBias(q, gen, dv) {
  const J = jacobian(q, gen), Ni = invert(normal(J));
  const g = [0, 1, 2, 3, 4].map((a) => J.reduce((s, row, k) => s + row[a] * dv[k], 0));
  return Ni.map((row) => row.reduce((s, v, j) => s + v * g[j], 0));
}
