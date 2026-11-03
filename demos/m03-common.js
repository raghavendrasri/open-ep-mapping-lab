// m03 model functions for the browser demos. MIT License.
//
// These mirror labs/python/epml/electrograms.py, and tests/test_m03_demo_math.py checks that the
// two give the same numbers. Units: mm, ms, conduction velocity in mm/ms (= m/s).
// No DOM access here, so Node can import this file in tests.

// Default parameters, each with its source (see the Assumptions lists in m03).
export const DEFAULTS = {
  c: 1.0, // m/s, anterior left atrial wall, normal-voltage areas [heil2023]
  h: 1.0, // mm, electrode-to-tissue distance used in [riccio2021]
  d: 2.0, // mm, bipole spacing of a 2-5-2 mm decapolar catheter [iafdb]
  re: 0.5, // mm, disk radius for a 1-mm electrode [anter2015], treated as a 1-mm-diameter disk
  w: 0.3, // mm, front width: TODO(source), see m03 Assumptions
};

export function linspace(a, b, n) {
  const out = new Float64Array(n);
  const step = (b - a) / (n - 1);
  for (let i = 0; i < n; i++) out[i] = a + i * step;
  return out;
}

// Unipolar potential U(s) = A s / (s^2 + a^2), a = w + h (eq-m03-unipolar-closed).
export function unipolar(s, a, A = 1) {
  return (A * s) / (s * s + a * a);
}

// dU/ds = A (a^2 - s^2) / (s^2 + a^2)^2.
export function unipolarDs(s, a, A = 1) {
  const q = s * s + a * a;
  return (A * (a * a - s * s)) / (q * q);
}

// Normalized transmembrane voltage across the arctangent front, 0 (rest) to 1 (activated).
export function frontVm(s, w) {
  return 0.5 - Math.atan(s / w) / Math.PI;
}

// Bipolar signal U(s + delta) - U(s - delta), delta = (d/2) cos(theta) (eq-m03-bipolar-planar).
export function bipolarPlanar(s, d, theta, a, A = 1) {
  const delta = 0.5 * d * Math.cos(theta);
  return unipolar(s + delta, a, A) - unipolar(s - delta, a, A);
}

// |H_bip(k)| = 2 |sin(k d cos(theta) / 2)| (eq-m03-bipolar-transfer).
export function bipolarTransferMag(k, d, theta = 0) {
  return 2 * Math.abs(Math.sin(0.5 * k * d * Math.cos(theta)));
}

// exp(-|k| h) (eq-m03-height-filter).
export function heightTransfer(k, h) {
  return Math.exp(-Math.abs(k) * h);
}

// Bessel J1 from its integral form, J1(x) = (1/pi) * integral_0^pi cos(tau - x sin tau) dtau,
// by Simpson's rule. Accurate to about 1e-10 for |x| < 30, which covers the demos.
export function besselJ1(x) {
  const n = 400; // even
  const h = Math.PI / n;
  let sum = 0;
  for (let i = 0; i <= n; i++) {
    const tau = i * h;
    const f = Math.cos(tau - x * Math.sin(tau));
    sum += (i === 0 || i === n ? 1 : i % 2 ? 4 : 2) * f;
  }
  return (sum * h) / 3 / Math.PI;
}

// 2 J1(|k| r) / (|k| r) (eq-m03-disk-average).
export function diskTransfer(k, r) {
  const x = Math.abs(k) * r;
  return x < 1e-9 ? 1 : (2 * besselJ1(x)) / x;
}

// Peak-to-peak of an array.
export function ptp(arr) {
  let lo = Infinity;
  let hi = -Infinity;
  for (const v of arr) {
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  return hi - lo;
}

// Least-squares field from clique bipoles (eq-m03-clique-field): E = -(D D^T)^-1 D b.
// positions: [[x, y], ...]; signals: array of Float64Array, one per electrode; pairs: [[i, j], ...].
// Returns {ex, ey} as Float64Arrays.
export function cliqueField(positions, signals, pairs) {
  let m00 = 0, m01 = 0, m11 = 0;
  const cols = pairs.map(([i, j]) => [positions[j][0] - positions[i][0], positions[j][1] - positions[i][1]]);
  for (const [dx, dy] of cols) {
    m00 += dx * dx;
    m01 += dx * dy;
    m11 += dy * dy;
  }
  const det = m00 * m11 - m01 * m01;
  const n = signals[0].length;
  const ex = new Float64Array(n);
  const ey = new Float64Array(n);
  for (let t = 0; t < n; t++) {
    let r0 = 0, r1 = 0;
    pairs.forEach(([i, j], p) => {
      const b = signals[j][t] - signals[i][t];
      r0 += cols[p][0] * b;
      r1 += cols[p][1] * b;
    });
    ex[t] = -(m11 * r0 - m01 * r1) / det;
    ey[t] = -(-m01 * r0 + m00 * r1) / det;
  }
  return { ex, ey };
}

// Principal axis of the field loop: unit vector of largest extent (sign arbitrary).
export function loopDirection(ex, ey) {
  let sxx = 0, sxy = 0, syy = 0;
  for (let t = 0; t < ex.length; t++) {
    sxx += ex[t] * ex[t];
    sxy += ex[t] * ey[t];
    syy += ey[t] * ey[t];
  }
  const angle = 0.5 * Math.atan2(2 * sxy, sxx - syy);
  return [Math.cos(angle), Math.sin(angle)];
}

// Omnipolar signal v = -d * E . omega (eq-m03-omnipole).
export function omnipolar(ex, ey, d, omega) {
  const out = new Float64Array(ex.length);
  for (let t = 0; t < ex.length; t++) out[t] = -d * (ex[t] * omega[0] + ey[t] * omega[1]);
  return out;
}

// Unipolar signals at electrodes for a plane wave along unit vector n, front through the origin at t = 0.
export function planeWaveSignals(positions, n, times, c, a, A = 1) {
  return positions.map(([x, y]) => {
    const out = new Float64Array(times.length);
    const proj = x * n[0] + y * n[1];
    for (let t = 0; t < times.length; t++) out[t] = unipolar(proj - c * times[t], a, A);
    return out;
  });
}

// Square clique centered at the origin, with all six bipoles.
export function squareClique(d) {
  const h = d / 2;
  return {
    positions: [[-h, -h], [h, -h], [-h, h], [h, h]],
    pairs: [[0, 1], [2, 3], [0, 2], [1, 3], [0, 3], [1, 2]],
  };
}
