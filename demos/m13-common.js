// m13 · Shared code for the m13 demos, as in labs/python/epml/catheters.py. MIT License.
// tests/test_m13_demos.py checks these against Python. Lengths in mm; forces and readings relative.

// eq-m13-alias: bipolar-type profile across a front at height h, (h/pi)/(x^2 + h^2); transform exp(-|k| h)
export const poissonKernel = (x, h) => h / Math.PI / (x * x + h * h);
export const aliasFraction = (spacing, h) => Math.exp((-2 * Math.PI * h) / spacing);
export const maxSpacing = (h, fraction) => (2 * Math.PI * h) / Math.log(1 / fraction);

// eq-m13-orthogonal
export function orthogonalPair(theta) {
  const ax = Math.abs(Math.cos(theta));
  const ay = Math.abs(Math.sin(theta));
  return { best: Math.max(ax, ay), rss: Math.hypot(ax, ay) };
}

// eq-m13-force: rows (lateral cos phi, lateral sin phi, axial) for each sensor angle (degrees)
export function forceMatrix(anglesDeg, axial = 1, lateral = 1) {
  return anglesDeg.map((d) => {
    const p = (d * Math.PI) / 180;
    return [lateral * Math.cos(p), lateral * Math.sin(p), axial];
  });
}

function inv3(m) {
  const [[a, b, c], [d, e, f], [g, h, i]] = m;
  const A = e * i - f * h, B = -(d * i - f * g), C = d * h - e * g;
  const det = a * A + b * B + c * C;
  return [
    [A / det, -(b * i - c * h) / det, (b * f - c * e) / det],
    [B / det, (a * i - c * g) / det, -(a * f - c * d) / det],
    [C / det, -(a * h - b * g) / det, (a * e - b * d) / det],
  ];
}

// eq-m13-force-noise: sigma^2 (C^T C)^-1
export function forceCovariance(C, sigma) {
  const n = C.length;
  const CtC = [0, 1, 2].map((r) => [0, 1, 2].map((c) => {
    let s = 0;
    for (let k = 0; k < n; k++) s += C[k][r] * C[k][c];
    return s;
  }));
  return inv3(CtC).map((row) => row.map((v) => sigma * sigma * v));
}

// 1-SD ellipse of a 2x2 covariance [[sxx, sxy], [sxy, syy]], as points
export function ellipse(sxx, sxy, syy, n = 120) {
  const tr = sxx + syy, det = sxx * syy - sxy * sxy;
  const l1 = tr / 2 + Math.sqrt(Math.max(tr * tr / 4 - det, 0));
  const l2 = tr / 2 - Math.sqrt(Math.max(tr * tr / 4 - det, 0));
  const ang = 0.5 * Math.atan2(2 * sxy, sxx - syy);
  const x = [], y = [];
  for (let k = 0; k <= n; k++) {
    const t = (2 * Math.PI * k) / n;
    const u = Math.sqrt(l1) * Math.cos(t), v = Math.sqrt(Math.max(l2, 0)) * Math.sin(t);
    x.push(u * Math.cos(ang) - v * Math.sin(ang));
    y.push(u * Math.sin(ang) + v * Math.cos(ang));
  }
  return { x, y };
}
