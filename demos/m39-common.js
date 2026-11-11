// m39 shared math: graph convolution on a grid mesh, hop reach, disc overlap. MIT License.
// Mirrors labs/python/epml/graphs.py; tests/test_m39_demos.py checks that both agree.
import { gridTriangles } from "./m33-common.js";

// Neighbour lists of a triangulated nx-by-ny grid (same triangles as epml.mapping.plane_mesh).
export function gridNeighbors(nx, ny) {
  const sets = Array.from({ length: nx * ny }, () => new Set());
  for (const [a, b, c] of gridTriangles(nx, ny)) {
    sets[a].add(b); sets[a].add(c);
    sets[b].add(a); sets[b].add(c);
    sets[c].add(a); sets[c].add(b);
  }
  return sets.map((s) => Array.from(s).sort((u, v) => u - v));
}

// eq-m39-gcn without weights: (A_hat f)_i = sum over j in N(i) and i of f_j / sqrt(d_i d_j), d = degree + 1
export function applyAhat(neigh, f) {
  const d = neigh.map((n) => n.length + 1);
  return f.map((fi, i) => {
    let s = fi / d[i];
    for (const j of neigh[i]) s += f[j] / Math.sqrt(d[i] * d[j]);
    return s;
  });
}

export function hopReach(neigh, start, layers) {
  let reach = new Array(neigh.length).fill(false);
  reach[start] = true;
  for (let l = 0; l < layers; l++) {
    const next = reach.slice();
    reach.forEach((r, i) => {
      if (r) for (const j of neigh[i]) next[j] = true;
    });
    reach = next;
  }
  return reach;
}

// eq-m39-lens
export function lensArea(R, r, d) {
  if (d >= R + r) return 0;
  if (d <= Math.abs(R - r)) return Math.PI * Math.min(R, r) ** 2;
  const a = r * r * Math.acos((d * d + r * r - R * R) / (2 * d * r));
  const b = R * R * Math.acos((d * d + R * R - r * r) / (2 * d * R));
  const c = 0.5 * Math.sqrt((-d + r + R) * (d + r - R) * (d - r + R) * (d + r + R));
  return a + b - c;
}

export function discDice(R, r, d) {
  return (2 * lensArea(R, r, d)) / (Math.PI * (R * R + r * r));
}

// Deterministic pseudo-random normals (for the demo's noise pattern only).
export function seededNormals(n, seed = 1) {
  let s = seed >>> 0;
  const u = () => {
    s = (1664525 * s + 1013904223) >>> 0;
    return (s + 0.5) / 4294967296;
  };
  return Array.from({ length: n }, () => Math.sqrt(-2 * Math.log(u())) * Math.cos(2 * Math.PI * u()));
}
