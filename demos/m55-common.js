// m55 · Shared code for the m55 demos, as in labs/python/epml/capstone.py. MIT License.
// tests/test_m55_demos.py checks these functions against Python.

// Illustrative landmark layouts (mm), as epml.capstone.fiducial_layout.
export function fiducialLayout(kind, n = 6, radius = 25) {
  const pts = [];
  for (let k = 0; k < n; k++) {
    if (kind === "spread") {
      const a = (2 * Math.PI * k) / n;
      pts.push([radius * Math.cos(a), radius * Math.sin(a), 8 * Math.cos(3 * a)]);
    } else if (kind === "clustered") {
      const a = ((-30 + (60 * k) / Math.max(n - 1, 1)) * Math.PI) / 180;
      pts.push([radius * Math.cos(a), radius * Math.sin(a), 6 * Math.sin(2 * a + 0.5)]);
    } else if (kind === "nearly collinear") {
      const x = n === 1 ? 0 : -radius + (2 * radius * k) / (n - 1);
      pts.push([x, 2 * Math.sin(1.3 * k), 2 * Math.cos(0.7 * k)]);
    } else throw new Error(`unknown layout ${kind}`);
  }
  return pts;
}

// Eigenvectors of a symmetric 3x3 matrix by Jacobi rotations; returns columns as arrays.
export function eigSym3(A) {
  const a = A.map((r) => r.slice());
  const v = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
  for (let sweep = 0; sweep < 50; sweep++) {
    let off = 0;
    for (let p = 0; p < 3; p++) for (let q = p + 1; q < 3; q++) off += a[p][q] ** 2;
    if (off < 1e-22) break;
    for (let p = 0; p < 3; p++) {
      for (let q = p + 1; q < 3; q++) {
        if (Math.abs(a[p][q]) < 1e-300) continue;
        const theta = (a[q][q] - a[p][p]) / (2 * a[p][q]);
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1));
        const c = 1 / Math.sqrt(t * t + 1);
        const s = t * c;
        for (let k = 0; k < 3; k++) {
          const akp = a[k][p];
          const akq = a[k][q];
          a[k][p] = c * akp - s * akq;
          a[k][q] = s * akp + c * akq;
        }
        for (let k = 0; k < 3; k++) {
          const apk = a[p][k];
          const aqk = a[q][k];
          a[p][k] = c * apk - s * aqk;
          a[q][k] = s * apk + c * aqk;
        }
        for (let k = 0; k < 3; k++) {
          const vkp = v[k][p];
          const vkq = v[k][q];
          v[k][p] = c * vkp - s * vkq;
          v[k][q] = s * vkp + c * vkq;
        }
      }
    }
  }
  return [0, 1, 2].map((j) => [v[0][j], v[1][j], v[2][j]]);
}

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

// eq-m55-tre: predicted RMS TRE at each target.
export function predictedTre(fiducials, targets, fleRms) {
  const n = fiducials.length;
  const c = [0, 1, 2].map((k) => fiducials.reduce((s, p) => s + p[k], 0) / n);
  const F = fiducials.map((p) => p.map((v, k) => v - c[k]));
  const M = [0, 1, 2].map((i) => [0, 1, 2].map((j) => F.reduce((s, p) => s + p[i] * p[j], 0)));
  const axes = eigSym3(M);
  const f2 = axes.map((e) => F.reduce((s, p) => s + dot(p, p) - dot(p, e) ** 2, 0) / n);
  return targets.map((t) => {
    const r = t.map((v, k) => v - c[k]);
    let total = 1;
    axes.forEach((e, k) => {
      total += (dot(r, r) - dot(r, e) ** 2) / f2[k] / 3;
    });
    return Math.sqrt((fleRms * fleRms * total) / n);
  });
}

export function predictedFre(n, fleRms) {
  return Math.sqrt((1 - 2 / n) * fleRms * fleRms);
}

// eq-m55-projection
export function rotateZ(p, angleDeg) {
  const a = (angleDeg * Math.PI) / 180;
  return [Math.cos(a) * p[0] - Math.sin(a) * p[1], Math.sin(a) * p[0] + Math.cos(a) * p[1], p[2]];
}

export function project(p, sod = 750, sid = 1100, angleDeg = 0) {
  const q = rotateZ(p, -angleDeg);
  const m = sid / (sod + q[1]);
  return { u: m * q[0], v: m * q[2], m };
}

export function visibleError(e, angleDeg = 0) {
  const q = rotateZ(e, -angleDeg);
  return { seen: Math.hypot(q[0], q[2]), hidden: Math.abs(q[1]) };
}

export function ellipsoidWireframe(semi, center = [0, 0, 0], nLat = 7, nLon = 8, m = 73) {
  const [a, b, c] = semi;
  const ts = Array.from({ length: m }, (_, i) => (2 * Math.PI * i) / (m - 1));
  const lines = [];
  for (let i = 1; i <= nLat; i++) {
    const phi = -Math.PI / 2 + (Math.PI * i) / (nLat + 1);
    lines.push(ts.map((t) => [a * Math.cos(phi) * Math.cos(t) + center[0], b * Math.cos(phi) * Math.sin(t) + center[1], c * Math.sin(phi) + center[2]]));
  }
  for (let j = 0; j < nLon; j++) {
    const lam = (Math.PI * j) / nLon;
    lines.push(ts.map((t) => [a * Math.cos(t) * Math.cos(lam) + center[0], b * Math.cos(t) * Math.sin(lam) + center[1], c * Math.sin(t) + center[2]]));
  }
  return lines;
}
