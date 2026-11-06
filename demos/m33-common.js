// Shared math for the m33 demos: eikonal on a triangulated grid, closed-form offset, regional
// calibration and cross-validation. Mirrors labs/python/epml/mapping.py and twin.py; the tests run
// this file in Node and compare. MIT License.
import { randn, rng } from "./m35-common.js";

export { randn, rng };

// Triangles of an nx-by-ny grid with alternating diagonals, in the same order as
// epml.mapping.plane_mesh. Vertex k = j * nx + i sits at (i h, j h).
export function gridTriangles(nx, ny) {
  const tris = [];
  for (let j = 0; j < ny - 1; j++) {
    for (let i = 0; i < nx - 1; i++) {
      const a = j * nx + i;
      const b = a + 1;
      const c = (j + 1) * nx + i + 1;
      const d = (j + 1) * nx + i;
      if ((i + j) % 2 === 0) tris.push([a, b, c], [a, c, d]);
      else tris.push([a, b, d], [b, c, d]);
    }
  }
  return tris;
}

// Earliest arrival at C from a front crossing edge AB with linear time on AB (speed v).
function update(ax, ay, bx, by, cx, cy, Ta, Tb, v) {
  const ex = bx - ax;
  const ey = by - ay;
  const ux = cx - ax;
  const uy = cy - ay;
  const wx = cx - bx;
  const wy = cy - by;
  const da = Ta + Math.sqrt(ux * ux + uy * uy) / v;
  const db = Tb + Math.sqrt(wx * wx + wy * wy) / v;
  let best = da < db ? da : db;
  if (Ta !== Infinity && Tb !== Infinity) {
    const L = Math.sqrt(ex * ex + ey * ey);
    const along = (ux * ex + uy * ey) / L;
    const px = ux - (along * ex) / L;
    const py = uy - (along * ey) / L;
    const h = Math.sqrt(px * px + py * py);
    const k = (v * (Tb - Ta)) / L;
    if (k > -1 && k < 1) {
      const w = (k * h) / Math.sqrt(1 - k * k);
      const s = (along - w) / L;
      if (s >= 0 && s <= 1) {
        const cand = Ta + s * (Tb - Ta) + Math.sqrt(w * w + h * h) / v;
        if (cand < best) best = cand;
      }
    }
  }
  return best;
}

// Sweep orders for fast sweeping: cells visited row by row and column by column in each of the four
// diagonal directions, so a front travelling any way is propagated in few passes.
const ORDER_CACHE = new Map();
function sweepOrders(nx, ny) {
  const key = `${nx}x${ny}`;
  if (!ORDER_CACHE.has(key)) {
    const orders = [];
    for (const [di, dj] of [[1, 1], [-1, 1], [-1, -1], [1, -1]]) {
      const list = [];
      for (let jj = 0; jj < ny - 1; jj++) {
        const j = dj > 0 ? jj : ny - 2 - jj;
        for (let ii = 0; ii < nx - 1; ii++) {
          const i = di > 0 ? ii : nx - 2 - ii;
          const cell = j * (nx - 1) + i;
          list.push(2 * cell, 2 * cell + 1);
        }
      }
      orders.push(Int32Array.from(list));
    }
    ORDER_CACHE.set(key, orders);
  }
  return ORDER_CACHE.get(key);
}

// eq-m30-eikonal on the grid: speed per triangle (0 = no conduction), sources at time t0.
// Same local update and fixed point as epml.mapping.eikonal; visited in fast-sweeping order.
export function eikonalGrid(nx, ny, h, tris, speed, sources, t0 = 0, tol = 1e-10, maxIter = 2000) {
  const n = nx * ny;
  const T = new Float64Array(n).fill(Infinity);
  for (const s of sources) T[s] = t0;
  const X = new Float64Array(n);
  const Y = new Float64Array(n);
  for (let k = 0; k < n; k++) {
    X[k] = (k % nx) * h;
    Y[k] = Math.floor(k / nx) * h;
  }
  const m = tris.length;
  const A = new Int32Array(m);
  const B = new Int32Array(m);
  const C = new Int32Array(m);
  for (let q = 0; q < m; q++) {
    A[q] = tris[q][0];
    B[q] = tris[q][1];
    C[q] = tris[q][2];
  }
  const orders = sweepOrders(nx, ny);
  const relax = (a, b, c, v) => {
    const Ta = T[a];
    const Tb = T[b];
    if (Ta === Infinity && Tb === Infinity) return 0;
    const cand = update(X[a], Y[a], X[b], Y[b], X[c], Y[c], Ta, Tb, v);
    const old = T[c];
    if (cand < old) {
      T[c] = cand;
      return old === Infinity ? Infinity : old - cand;
    }
    return 0;
  };
  for (let it = 0; it < maxIter; it++) {
    let change = 0;
    const order = orders[it % 4];
    for (let q = 0; q < order.length; q++) {
      const t = order[q];
      const v = speed[t];
      if (!(v > 0)) continue;
      const a = A[t];
      const b = B[t];
      const c = C[t];
      const d1 = relax(a, b, c, v);
      const d2 = relax(b, c, a, v);
      const d3 = relax(c, a, b, v);
      if (d1 > change) change = d1;
      if (d2 > change) change = d2;
      if (d3 > change) change = d3;
    }
    if (change <= tol && it >= 3) break;
  }
  return T;
}

// eq-m33-offset: the timing offset that minimizes the squared misfit.
export function bestOffset(tSim, tMeas) {
  let s = 0;
  for (let i = 0; i < tSim.length; i++) s += tMeas[i] - tSim[i];
  return s / tSim.length;
}

// Region index of each triangle for a k-by-k block layout over a square of side `size`.
export function blockRegions(tris, nx, h, size, k) {
  return tris.map((tri) => {
    const cx = tri.reduce((acc, v) => acc + (v % nx) * h, 0) / 3;
    const cy = tri.reduce((acc, v) => acc + Math.floor(v / nx) * h, 0) / 3;
    const bi = Math.min(k - 1, Math.floor((cx / size) * k));
    const bj = Math.min(k - 1, Math.floor((cy / size) * k));
    return bj * k + bi;
  });
}

function solve(A, b) {
  // Gaussian elimination with partial pivoting on a small dense system.
  const n = b.length;
  const M = A.map((row, i) => [...row, b[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[p][c])) p = r;
    [M[c], M[p]] = [M[p], M[c]];
    for (let r = c + 1; r < n; r++) {
      const f = M[r][c] / M[c][c];
      for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k];
    }
  }
  const x = new Array(n).fill(0);
  for (let r = n - 1; r >= 0; r--) {
    let s = M[r][n];
    for (let k = r + 1; k < n; k++) s -= M[r][k] * x[k];
    x[r] = s / M[r][r];
  }
  return x;
}

// Fit one speed per region to measured times at vertex indices `pts` (eq-m33-offset inside).
// Levenberg-Marquardt on log speeds with a forward-difference Jacobian, kept within bounds.
export function calibrate(grid, region, nRegions, source, pts, tMeas, { vInit = 0.8, bounds = [0.1, 3], iters = 25, start } = {}) {
  const { nx, ny, h, tris } = grid;
  const lo = Math.log(bounds[0]);
  const hi = Math.log(bounds[1]);
  const clamp = (x) => Math.min(hi, Math.max(lo, x));
  let theta = start ? start.map((v) => Math.log(v)) : new Array(nRegions).fill(Math.log(vInit));
  const predict = (th) => {
    const sp = region.map((r) => Math.exp(th[r]));
    const T = eikonalGrid(nx, ny, h, tris, sp, [source]);
    return pts.map((p) => T[p]);
  };
  const resid = (ts) => {
    const off = bestOffset(ts, tMeas);
    return ts.map((t, i) => t + off - tMeas[i]);
  };
  const cost = (r) => r.reduce((a, b) => a + b * b, 0);
  let ts = predict(theta);
  let r = resid(ts);
  let c = cost(r);
  let mu = 1e-2;
  const step = 1e-3;
  for (let it = 0; it < iters; it++) {
    const J = theta.map((_, k) => {
      const th = theta.slice();
      th[k] = th[k] + step;
      const rk = resid(predict(th));
      return rk.map((v, i) => (v - r[i]) / step);
    }); // J[k][i]
    const n = theta.length;
    const JTJ = Array.from({ length: n }, (_, a) => Array.from({ length: n }, (_, b) => J[a].reduce((s, v, i) => s + v * J[b][i], 0)));
    const JTr = J.map((col) => col.reduce((s, v, i) => s + v * r[i], 0));
    let improved = false;
    for (let tries = 0; tries < 8 && !improved; tries++) {
      const A = JTJ.map((row, a) => row.map((v, b) => (a === b ? v + mu * (v + 1e-9) + 1e-12 : v)));
      const delta = solve(A, JTr.map((v) => -v));
      const cand = theta.map((t, k) => clamp(t + delta[k]));
      const tsC = predict(cand);
      const rC = resid(tsC);
      const cC = cost(rC);
      if (cC < c) {
        const rel = (c - cC) / Math.max(c, 1e-12);
        theta = cand;
        ts = tsC;
        r = rC;
        c = cC;
        mu = Math.max(mu / 3, 1e-6);
        improved = true;
        if (rel < 1e-9) it = iters;
      } else mu *= 4;
    }
    if (!improved) break;
  }
  return { speeds: theta.map(Math.exp), offset: bestOffset(ts, tMeas), rmse: Math.sqrt(c / pts.length) };
}

// eq-m33-holdout: k-fold cross-validated RMSE for the regional twin (folds from a seeded shuffle).
export function kfoldRmse(grid, region, nRegions, source, pts, tMeas, k, seed, fullFit) {
  const rand = rng(seed);
  const idx = pts.map((_, i) => i);
  for (let i = idx.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [idx[i], idx[j]] = [idx[j], idx[i]];
  }
  let sq = 0;
  for (let f = 0; f < k; f++) {
    const test = idx.filter((_, i) => i % k === f);
    const train = idx.filter((_, i) => i % k !== f);
    const fit = calibrate(grid, region, nRegions, source, train.map((i) => pts[i]), train.map((i) => tMeas[i]),
      { start: fullFit?.speeds, iters: 12 });
    const sp = region.map((rg) => fit.speeds[rg]);
    const T = eikonalGrid(grid.nx, grid.ny, grid.h, grid.tris, sp, [source]);
    for (const i of test) sq += (T[pts[i]] + fit.offset - tMeas[i]) ** 2;
  }
  return Math.sqrt(sq / pts.length);
}
