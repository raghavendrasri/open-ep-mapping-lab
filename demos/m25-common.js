// m25 · Shared code for the m25 demos, as in labs/python/epml/velocity.py. MIT License.
// tests/test_m25_demos.py checks these against Python. Times in ms, lengths in mm, speeds in mm/ms (= m/s).

// eq-m25-pair
export const pairRelativeError = (sigmaT, c, h) => (Math.SQRT2 * sigmaT * c) / h;
// eq-m25-triangle: an equilateral triangle of side h gives isotropic gradient SD sqrt(2) sigma / h per component
export const equilateralGradientSd = (sigmaT, h) => (Math.SQRT2 * sigmaT) / h;
// eq-m25-planefit
export const diskFitSd = (sigmaT, n, radius) => (2 * sigmaT) / (radius * Math.sqrt(n));

// eq-m25-omnipolar
export const unipolar = (s, a, A = 1) => (A * s) / (s * s + a * a);
const phi = (x, y, t, c, theta, a) => unipolar(Math.cos(theta) * x + Math.sin(theta) * y - c * t, a);
export function cliqueVelocity(c, theta, a, d, t = 0, dt = 1e-4) {
  const h = 0.5 * d;
  const gx = (phi(h, 0, t, c, theta, a) - phi(-h, 0, t, c, theta, a)) / d;
  const gy = (phi(0, h, t, c, theta, a) - phi(0, -h, t, c, theta, a)) / d;
  const pt = (phi(0, 0, t + dt, c, theta, a) - phi(0, 0, t - dt, c, theta, a)) / (2 * dt);
  const g2 = gx * gx + gy * gy;
  return [(-pt * gx) / g2, (-pt * gy) / g2];
}
export const cliqueSpeedRatioAxis = (d, a) => 1 + (0.5 * d) ** 2 / (a * a);
