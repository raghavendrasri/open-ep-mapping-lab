// m12 · Shared code for the m12 demos, as in labs/python/epml/ecg.py. MIT License.
// tests/test_m12_demos.py checks these against Python. Coordinates: x left, y inferior, z anterior; unit sphere.

const C30 = Math.cos(Math.PI / 6);
export const LIMBS = { R: [-C30, -0.5, 0], L: [C30, -0.5, 0], F: [0, 1, 0] };

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => Math.sqrt(dot(a, a));

// eq-m12-sphere: centric dipole, surface potential 3 p . rhat / (4 pi sigma R^2), sigma = R = 1
export const centricSurface = (p, rhat) => (3 * dot(rhat, p)) / (4 * Math.PI);

// eq-m12-series: point source at r0 inside the unit sphere, surface potential at x (l >= 1 terms)
export function sourceSurface(current, r0, x, lmax = 120) {
  const a = norm(r0);
  if (a === 0) return 0;
  const c = dot(r0, x) / a;
  let p0 = 1;
  let p1 = c;
  let sum = 3 * a * p1;
  let al = a;
  for (let l = 1; l < lmax; l++) {
    const p2 = ((2 * l + 1) * c * p1 - l * p0) / (l + 1);
    al *= a;
    sum += ((2 * (l + 1) + 1) / (l + 1)) * al * p2;
    p0 = p1;
    p1 = p2;
  }
  return (current / (4 * Math.PI)) * sum;
}

// Dipole as a source-sink pair h apart
export function dipoleSurface(p, r0, x, h = 1e-4) {
  const m = norm(p);
  if (m === 0) return 0;
  const u = p.map((v) => v / m);
  const plus = r0.map((v, i) => v + (u[i] * h) / 2);
  const minus = r0.map((v, i) => v - (u[i] * h) / 2);
  return sourceSurface(m / h, plus, x) - sourceSurface(m / h, minus, x);
}

// eq-m12-einthoven, eq-m12-augmented
export function limbLeads(r, l, f) {
  return { I: l - r, II: f - r, III: f - l, aVR: r - (l + f) / 2, aVL: l - (r + f) / 2, aVF: f - (r + l) / 2 };
}

// Limb leads for a dipole at r0 (centric closed form when r0 is the center)
export function leadsForDipole(p, r0 = [0, 0, 0]) {
  const centric = r0.every((v) => v === 0);
  const phi = {};
  for (const k of ["R", "L", "F"]) phi[k] = centric ? centricSurface(p, LIMBS[k]) : dipoleSurface(p, r0, LIMBS[k]);
  return limbLeads(phi.R, phi.L, phi.F);
}

// eq-m12-axis (degrees, 0 = lead I, +90 = inferior)
export const frontalAxis = (leadI, aVF) => (Math.atan2((2 * aVF) / Math.sqrt(3), leadI) * 180) / Math.PI;

// eq-m12-lead: lead vector of electrodes a minus b for a dipole at r0
export function leadVector(a, b, r0 = [0, 0, 0]) {
  const centric = r0.every((v) => v === 0);
  return [0, 1, 2].map((k) => {
    const e = [0, 0, 0];
    e[k] = 1;
    return centric ? centricSurface(e, a) - centricSurface(e, b) : dipoleSurface(e, r0, a) - dipoleSurface(e, r0, b);
  });
}
