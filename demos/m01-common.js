// m01 · Shared code for the m01 demos, as in labs/python/epml/sources.py. MIT License.
// Relative units: sigma = 1, beta = 1, dV = 1, distances in mm. tests/test_m01_demos.py checks these against Python.

// eq-m01-point: phi = I / (4 pi sigma r)
export const pointPotential = (I, sigma, r) => I / (4 * Math.PI * sigma * r);

// eq-m01-dipole on the dipole's axis: phi = p / (4 pi sigma r^2)
export const dipoleAxis = (p, sigma, r) => p / (4 * Math.PI * sigma * r * r);

// eq-m01-double-layer on the axis of a disk of radius R at height z > 0
export const diskSolidAngleAxis = (R, z) => 2 * Math.PI * (1 - z / Math.sqrt(z * z + R * R));
export const doubleLayerPotential = (tau, sigma, omega) => (tau * omega) / (4 * Math.PI * sigma);

// local slope of log|phi| against log r, by a centered difference in log r
export function falloffSlope(f, r, h = 1e-4) {
  const a = Math.log(Math.abs(f(r * Math.exp(-h))));
  const b = Math.log(Math.abs(f(r * Math.exp(h))));
  return (b - a) / (2 * h);
}

// the m03 arctangent front and its membrane current (eq-m01-core)
export const frontVm = (s, w) => 0.5 - Math.atan(s / w) / Math.PI;
export const frontIm = (s, w) => (2 * w * s) / (Math.PI * (s * s + w * w) ** 2);

// eq-m01-front-dipole: a line of dipoles (moment p per unit length) seen from height h
export const lineDipole = (p, sigma, s, h) => (p * s) / (2 * Math.PI * sigma * (s * s + h * h));

// the m03 closed form: a front of width w at height h is a line dipole at height w + h
export const frontPotential = (s, w, h) => lineDipole(1, 1, s, w + h);
