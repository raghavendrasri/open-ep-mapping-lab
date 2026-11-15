// m20 · Shared code for the m20 demos, as in labs/python/epml/geometry.py (2D). MIT License.
// tests/test_m20_demos.py checks these against Python. Lengths in mm; grids have 1 mm pixels on [-50, 50]^2.

export const AX = Array.from({ length: 101 }, (_, i) => -50 + i);
const N = AX.length;

// the illustrative chamber (z = 0 slice): disk of radius 25, minus a notch disk, plus a stub along -x
export function inside(x, y) {
  const disk = Math.hypot(x, y) <= 25 && !(Math.hypot(x - 34, y) < 12);
  const stub = x >= -45 && x <= -20 && Math.abs(y) <= 6;
  return disk || stub;
}
export function truthMask() {
  const m = new Uint8Array(N * N);
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) m[i * N + j] = inside(AX[i], AX[j]) ? 1 : 0;
  return m;
}

export function pointsMask(points) {
  const m = new Uint8Array(N * N);
  for (const [x, y] of points) {
    const i = Math.min(Math.max(Math.round(x + 50), 0), N - 1), j = Math.min(Math.max(Math.round(y + 50), 0), N - 1);
    m[i * N + j] = 1;
  }
  return m;
}

function disk(r) {
  const R = Math.ceil(r), out = [];
  for (let a = -R; a <= R; a++) for (let b = -R; b <= R; b++) if (a * a + b * b <= r * r) out.push([a, b]);
  return out;
}
function dilate(m, r) {
  const o = new Uint8Array(N * N), d = disk(r);
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    if (!m[i * N + j]) continue;
    for (const [a, b] of d) { const p = i + a, q = j + b; if (p >= 0 && p < N && q >= 0 && q < N) o[p * N + q] = 1; }
  }
  return o;
}
function erode(m, r) {
  const o = new Uint8Array(N * N), d = disk(r);
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    let ok = 1;
    for (const [a, b] of d) { const p = i + a, q = j + b; if (p < 0 || p >= N || q < 0 || q >= N || !m[p * N + q]) { ok = 0; break; } }
    o[i * N + j] = ok;
  }
  return o;
}
function fillHoles(m) {
  const outside = new Uint8Array(N * N), stack = [];
  for (let k = 0; k < N; k++) for (const [i, j] of [[0, k], [N - 1, k], [k, 0], [k, N - 1]]) if (!m[i * N + j] && !outside[i * N + j]) { outside[i * N + j] = 1; stack.push([i, j]); }
  while (stack.length) {
    const [i, j] = stack.pop();
    for (const [p, q] of [[i + 1, j], [i - 1, j], [i, j + 1], [i, j - 1]]) {
      if (p < 0 || p >= N || q < 0 || q >= N) continue;
      const k = p * N + q;
      if (!m[k] && !outside[k]) { outside[k] = 1; stack.push([p, q]); }
    }
  }
  return outside.map((v) => 1 - v);
}
// eq-m20-closing: inflate by r, fill holes, shrink by r
export function reconstruct(points, r, close = true) {
  let m = fillHoles(dilate(pointsMask(points), r));
  return close ? erode(m, r) : m;
}

// eq-m20-hull: monotone-chain convex hull and its pixel mask
export function convexHull(points) {
  const p = points.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [], upper = [];
  for (const q of p) { while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop(); lower.push(q); }
  for (const q of p.slice().reverse()) { while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop(); upper.push(q); }
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}
export function hullMask(points) {
  const h = convexHull(points), m = new Uint8Array(N * N);
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    let ok = 1;
    for (let k = 0; k < h.length; k++) {
      const a = h[k], b = h[(k + 1) % h.length];
      if ((b[0] - a[0]) * (AX[j] - a[1]) - (b[1] - a[1]) * (AX[i] - a[0]) < -1e-9) { ok = 0; break; }
    }
    m[i * N + j] = ok;
  }
  return m;
}

// eq-m20-distance on pixel boundaries (4-neighbor erosion)
export function boundaryPoints(m) {
  const out = [];
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    if (!m[i * N + j]) continue;
    const edge = i === 0 || j === 0 || i === N - 1 || j === N - 1 || !m[(i + 1) * N + j] || !m[(i - 1) * N + j] || !m[i * N + j + 1] || !m[i * N + j - 1];
    if (edge) out.push([AX[i], AX[j]]);
  }
  return out;
}
export function surfaceStats(a, b) {
  const A = boundaryPoints(a), B = boundaryPoints(b);
  if (!A.length || !B.length) return { hausdorff: Infinity, mean: Infinity };
  const nearest = (P, Q) => P.map(([x, y]) => Math.sqrt(Math.min(...Q.map(([u, v]) => (x - u) ** 2 + (y - v) ** 2))));
  const d1 = nearest(A, B), d2 = nearest(B, A);
  return { hausdorff: Math.max(...d1, ...d2), mean: (d1.reduce((s, v) => s + v, 0) + d2.reduce((s, v) => s + v, 0)) / (d1.length + d2.length) };
}

// eq-m20-smoothing on a closed polygon
export function umbrellaStep(P, lam) {
  const n = P.length;
  return P.map(([x, y], i) => {
    const a = P[(i - 1 + n) % n], b = P[(i + 1) % n];
    return [x + lam * ((a[0] + b[0]) / 2 - x), y + lam * ((a[1] + b[1]) / 2 - y)];
  });
}
export const polygonFactor = (n, lam, mu = null) => {
  const a = 1 - Math.cos((2 * Math.PI) / n);
  return mu === null ? 1 - lam * a : (1 - lam * a) * (1 - mu * a);
};

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

// catheter positions near the wall: random boundary pixels moved inward by up to `depth` mm
export function wallSamples(n, depth, seed) {
  const T = truthMask(), B = boundaryPoints(T), r = rng(seed), out = [];
  while (out.length < n) {
    const [bx, by] = B[Math.floor(r() * B.length)];
    const ang = 2 * Math.PI * r(), rad = depth * Math.sqrt(r());
    const x = bx + rad * Math.cos(ang), y = by + rad * Math.sin(ang);
    if (inside(x, y)) out.push([x, y]);
  }
  return out;
}
