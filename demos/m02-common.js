// m02 · Shared code for the m02 demos, as in labs/python/epml/volume.py. MIT License.
// Relative units, distances in mm. tests/test_m02_demos.py checks these against Python.

// eq-m02-images
export const reflectionCoefficient = (s1, s2) => (s1 - s2) / (s1 + s2);

// 3-D point source I at (0, 0, -d) in medium 1 (z < 0), interface z = 0, medium 2 above
export function imagePotential3d(I, s1, s2, d, x, y, z) {
  const k = reflectionCoefficient(s1, s2);
  const r = Math.hypot(x, y, z + d);
  if (z <= 0) return (I / (4 * Math.PI * s1)) * (1 / r + k / Math.hypot(x, y, z - d));
  return I / (2 * Math.PI * (s1 + s2) * r);
}

// 2-D line source at (0, -d) in medium 1 (y < 0), up to a constant
export function imagePotential2d(I, s1, s2, d, x, y) {
  const k = reflectionCoefficient(s1, s2);
  const r = Math.hypot(x, y + d);
  if (y <= 0) return -(I / (2 * Math.PI * s1)) * (Math.log(r) + k * Math.log(Math.hypot(x, y - d)));
  return -(I / (Math.PI * (s1 + s2))) * Math.log(r);
}

export const gaussianSource2d = (x, y, I, w) => (I / (2 * Math.PI * w * w)) * Math.exp(-(x * x + y * y) / (2 * w * w));

// eq-m02-fd: flux-conserving 5-point scheme, Dirichlet ring, solved by successive over-relaxation.
// sig, src, phi: Float64Array (n * n, row-major, row 0 at y = -half). phi holds the boundary values on entry.
export function solvePoissonSOR(n, h, sig, src, phi, { omega = 1.9, tol = 1e-10, maxIter = 20000 } = {}) {
  const face = (a, b) => (2 * a * b) / (a + b);
  let iter = 0;
  for (; iter < maxIter; iter++) {
    let change = 0;
    for (let j = 1; j < n - 1; j++) {
      for (let i = 1; i < n - 1; i++) {
        const k = j * n + i;
        const e = face(sig[k], sig[k + 1]);
        const w = face(sig[k], sig[k - 1]);
        const nn = face(sig[k], sig[k + n]);
        const s = face(sig[k], sig[k - n]);
        const target = (e * phi[k + 1] + w * phi[k - 1] + nn * phi[k + n] + s * phi[k - n] + h * h * src[k]) / (e + w + nn + s);
        const delta = omega * (target - phi[k]);
        phi[k] += delta;
        change = Math.max(change, Math.abs(delta));
      }
    }
    if (change < tol) break;
  }
  return iter + 1;
}

// Set up and solve the two-media problem of m02-d2: Gaussian source of width 0.3 mm at (0, -d), interface y = 0.
export function twoMediaProblem(n, half, s1, s2, d) {
  const h = (2 * half) / (n - 1);
  const xs = Array.from({ length: n }, (_, i) => -half + i * h);
  const sig = new Float64Array(n * n);
  const src = new Float64Array(n * n);
  const phi = new Float64Array(n * n);
  const exact = new Float64Array(n * n);
  for (let j = 0; j < n; j++) {
    for (let i = 0; i < n; i++) {
      const k = j * n + i;
      sig[k] = xs[j] <= 0 ? s1 : s2;
      src[k] = gaussianSource2d(xs[i], xs[j] + d, 1, 0.3);
      exact[k] = imagePotential2d(1, s1, s2, d, xs[i], xs[j]);
      const edge = i === 0 || j === 0 || i === n - 1 || j === n - 1;
      phi[k] = edge ? exact[k] : 0;
    }
  }
  const iters = solvePoissonSOR(n, h, sig, src, phi);
  let err = 0;
  for (let j = 0; j < n; j++) {
    for (let i = 0; i < n; i++) {
      if (Math.hypot(xs[i], xs[j] + d) > 2) err = Math.max(err, Math.abs(phi[j * n + i] - exact[j * n + i]));
    }
  }
  return { xs, h, phi, exact, iters, err };
}
