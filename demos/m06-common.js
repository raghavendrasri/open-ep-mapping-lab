// m06 · Shared code for the m06 demos, as in labs/python/epml/meshes.py. MIT License.
// tests/test_m06_demos.py checks these against Python.

// eq-m06-geodesic: shortest edge path over straight-line distance on an equilateral triangular lattice
export function latticePathRatio(theta) {
  const p = Math.PI / 3;
  const th = ((theta % p) + p) % p;
  return (Math.sin(th) + Math.sin(p - th)) / Math.sin(p);
}

// The two lattice steps that make the shortest path to a point at distance r and angle theta:
// a steps along direction k*60 deg, then b along (k+1)*60 deg.
export function latticePath(r, theta) {
  const p = Math.PI / 3;
  const k = Math.floor((((theta % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) / p);
  const th = theta - k * p;
  const b = (r * Math.sin(th)) / Math.sin(p);
  const a = (r * Math.sin(p - th)) / Math.sin(p);
  return { k, a, b };
}

// eq-m06-cotan: weight of an interior edge from its two opposite angles
export const edgeCotanWeight = (alpha, beta) => 0.5 * (1 / Math.tan(alpha) + 1 / Math.tan(beta));
