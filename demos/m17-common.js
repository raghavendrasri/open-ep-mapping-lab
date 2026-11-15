// m17 · Shared code for the m17 demos, as in labs/python/epml/impedance.py. MIT License.
// tests/test_m17_demos.py checks these against Python. Lengths in mm; potentials relative, k = I/(4 pi sigma) = 1.

const dist = (r, a) => Math.hypot(r[0] - a[0], r[1] - a[1], r[2] - a[2]);

// eq-m17-pair
export const pairPotential = (r, a, b, k = 1) => k * (1 / dist(r, a) - 1 / dist(r, b));
export const patchPairs = (d) => [[[d, 0, 0], [-d, 0, 0]], [[0, d, 0], [0, -d, 0]], [[0, 0, d], [0, 0, -d]]];
export const potentials = (r, pairs, k = 1) => pairs.map(([a, b]) => pairPotential(r, a, b, k));
// eq-m17-axis
export const axisPotential = (x, d, k = 1) => (2 * k * x) / (d * d - x * x);
export const centerField = (d, k = 1) => (2 * k) / (d * d);
// eq-m17-linear: phi / E0 on each axis
export const linearEstimate = (phi, d, k = 1) => phi / centerField(d, k);
