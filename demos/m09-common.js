// m09 · Shared code for the m09 demos, as in labs/python/epml/propagation.py. MIT License.
// tests/test_m09_demos.py checks these against Python.

// Mitchell-Schaeffer parameters (ms) as reported by Nieto Ramos et al. 2023, based on Mitchell and Schaeffer 2003
export const MS = { tauIn: 0.3, tauOut: 6, tauOpen: 150, tauClose: 120, vGate: 0.13 };

// 1D cable, no-flux ends, stimulus on the first 0.5 mm for 1 ms. Returns activation times (first upward crossing of
// 0.5, interpolated; NaN if never) and voltage snapshots at the requested times.
export function msCable(n, dx, D, tEnd, snapTimes = [], p = MS) {
  const dt = Math.min(0.005, (0.2 * dx * dx) / D);
  let v = new Float64Array(n);
  let h = new Float64Array(n).fill(1);
  const act = new Float64Array(n).fill(NaN);
  const nStim = Math.max(3, Math.round(0.5 / dx));
  const snaps = [];
  let next = 0;
  const steps = Math.round(tEnd / dt);
  for (let k = 0; k < steps; k++) {
    const t = k * dt;
    if (next < snapTimes.length && t >= snapTimes[next]) {
      snaps.push(Array.from(v));
      next++;
    }
    const vn = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const left = i > 0 ? v[i - 1] : v[i + 1];
      const right = i < n - 1 ? v[i + 1] : v[i - 1];
      const lap = (left - 2 * v[i] + right) / (dx * dx);
      const vi = v[i];
      const dv = (h[i] * vi * vi * (1 - vi)) / p.tauIn - vi / p.tauOut;
      const stim = t < 1 && i < nStim ? 1 : 0;
      vn[i] = vi + dt * (D * lap + dv + stim);
      h[i] += dt * (vi < p.vGate ? (1 - h[i]) / p.tauOpen : -h[i] / p.tauClose);
      if (Number.isNaN(act[i]) && vi < 0.5 && vn[i] >= 0.5) act[i] = t + (dt * (0.5 - vi)) / (vn[i] - vi);
    }
    v = vn;
  }
  return { act, snaps };
}

// Least-squares slope of activation time against position over the middle third: conduction velocity (mm/ms)
export function cableCV(act, dx) {
  const n = act.length;
  let sx = 0, st = 0, sxx = 0, sxt = 0, m = 0;
  for (let i = 0; i < n; i++) {
    const x = i * dx;
    if (x > (n * dx) / 3 && x < (2 * n * dx) / 3 && Number.isFinite(act[i])) {
      sx += x; st += act[i]; sxx += x * x; sxt += x * act[i]; m++;
    }
  }
  const slope = (m * sxt - sx * st) / (m * sxx - sx * sx);
  return 1 / slope;
}

// eq-m09-anisotropy: far-field activation time from a point, fibers at angle (radians)
export function pointActivation(x, y, cvL, cvT, angle = 0) {
  const c = Math.cos(angle), s = Math.sin(angle);
  const xl = c * x + s * y, xt = -s * x + c * y;
  return Math.sqrt((xl * xl) / (cvL * cvL) + (xt * xt) / (cvT * cvT));
}

// Apparent speed along a ray at angle theta to the fibers
export const raySpeed = (theta, cvL, cvT) =>
  (cvL * cvT) / Math.sqrt(cvT * cvT * Math.cos(theta) ** 2 + cvL * cvL * Math.sin(theta) ** 2);
