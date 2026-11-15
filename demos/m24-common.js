// m24 · Shared code for the m24 demos, as in labs/python/epml/interpolation.py. MIT License.
// tests/test_m24_demos.py checks these against Python. Times in ms, lengths in mm, speed in mm/ms (= m/s).

// eq-m24-linear
export function linear1d(xd, td, x) {
  if (x <= xd[0]) return td[0];
  if (x >= xd[xd.length - 1]) return td[td.length - 1];
  let k = 1;
  while (xd[k] < x) k++;
  const f = (x - xd[k - 1]) / (xd[k] - xd[k - 1]);
  return td[k - 1] + f * (td[k] - td[k - 1]);
}
export const linearErrorBound = (h, maxSecond) => (h * h * maxSecond) / 8;

// eq-m24-idw
export function idw(points, values, q, p = 2) {
  let sw = 0, swv = 0;
  for (let i = 0; i < points.length; i++) {
    let d2 = 0;
    for (let k = 0; k < q.length; k++) d2 += (q[k] - points[i][k]) ** 2;
    if (d2 < 1e-24) return values[i];
    const w = d2 ** (-p / 2);
    sw += w; swv += w * values[i];
  }
  return swv / sw;
}

// eq-m24-block (apparent speed across a block, and coverage)
export const apparentVelocity = (h, dt) => h / dt;
export const coverageFraction = (density, r) => 1 - Math.exp(-density * Math.PI * r * r);
export const focalTime = (x, y, c = 1, x0 = 0, y0 = 0) => Math.hypot(x - x0, y - y0) / c;

// eq-m24-isochrone: marching squares on a regular grid T[j][i] at (x0 + i dx, y0 + j dy)
export function isolines(T, x0, y0, dx, dy, tau) {
  const segs = [];
  const ny = T.length, nx = T[0].length;
  const cross = (xa, ya, ta, xb, yb, tb) => {
    if ((ta - tau) * (tb - tau) > 0 || ta === tb) return null;
    const f = (tau - ta) / (tb - ta);
    return f < 0 || f > 1 ? null : [xa + f * (xb - xa), ya + f * (yb - ya)];
  };
  for (let j = 0; j < ny - 1; j++) {
    for (let i = 0; i < nx - 1; i++) {
      const xa = x0 + i * dx, ya = y0 + j * dy, xb = xa + dx, yb = ya + dy;
      const c = [
        cross(xa, ya, T[j][i], xb, ya, T[j][i + 1]),
        cross(xb, ya, T[j][i + 1], xb, yb, T[j + 1][i + 1]),
        cross(xb, yb, T[j + 1][i + 1], xa, yb, T[j + 1][i]),
        cross(xa, yb, T[j + 1][i], xa, ya, T[j][i]),
      ].filter((v) => v !== null);
      if (c.length >= 2) segs.push([c[0], c[1]]);
      if (c.length === 4) segs.push([c[2], c[3]]);
    }
  }
  return segs;
}

export function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
