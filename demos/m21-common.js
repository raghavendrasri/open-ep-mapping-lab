// m21 · Shared code for the m21 demos, as in labs/python/epml/registration.py. MIT License.
// tests/test_m21_demos.py checks these against Python. Lengths in mm; intensities relative.

// standard normal CDF (Abramowitz–Stegun 7.1.26 via erf), accurate to about 1e-7
function erf(x) {
  const s = Math.sign(x), a = Math.abs(x), t = 1 / (1 + 0.3275911 * a);
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-a * a);
  return s * y;
}
export const ndtr = (z) => 0.5 * (1 + erf(z / Math.SQRT2));

// eq-m21-threshold: between-class variance for every split of a histogram
export function betweenClassVariance(hist, centers) {
  const tot = hist.reduce((s, v) => s + v, 0), out = [];
  let w0 = 0, m = 0;
  const mt = hist.reduce((s, v, i) => s + (v / tot) * centers[i], 0);
  for (let i = 0; i < hist.length; i++) {
    w0 += hist[i] / tot; m += (hist[i] / tot) * centers[i];
    const w1 = 1 - w0;
    out.push(w0 > 0 && w1 > 0 ? w0 * w1 * (m / w0 - (mt - m) / w1) ** 2 : 0);
  }
  return out;
}
export function otsuFromHistogram(hist, centers) {
  const sb = betweenClassVariance(hist, centers);
  let k = 0;
  for (let i = 1; i < sb.length; i++) if (sb[i] > sb[k]) k = i;
  return 0.5 * (centers[k] + centers[k + 1]);
}
// eq-m21-dice: expected Dice of a threshold for two Gaussian classes
export function gaussianDice(t, mu0, mu1, sigma, p) {
  const tp = p * (1 - ndtr((t - mu1) / sigma)), fp = (1 - p) * (1 - ndtr((t - mu0) / sigma)), fn = p * ndtr((t - mu1) / sigma);
  return (2 * tp) / (2 * tp + fp + fn);
}
export function mixtureHistogram(mu0, mu1, sigma, p, bins = 512) {
  const lo = mu0 - 5 * sigma, hi = mu1 + 5 * sigma, w = (hi - lo) / bins, hist = [], centers = [];
  for (let i = 0; i < bins; i++) {
    const a = lo + i * w, b = a + w;
    centers.push(a + w / 2);
    hist.push((1 - p) * (ndtr((b - mu0) / sigma) - ndtr((a - mu0) / sigma)) + p * (ndtr((b - mu1) / sigma) - ndtr((a - mu1) / sigma)));
  }
  return { hist, centers };
}

// eq-m21-procrustes in 2D: least-squares rotation angle and translation
export function procrustes2(P, Q) {
  const n = P.length;
  const mp = [P.reduce((s, p) => s + p[0], 0) / n, P.reduce((s, p) => s + p[1], 0) / n];
  const mq = [Q.reduce((s, p) => s + p[0], 0) / n, Q.reduce((s, p) => s + p[1], 0) / n];
  let cr = 0, dt = 0;
  for (let i = 0; i < n; i++) {
    const x = [P[i][0] - mp[0], P[i][1] - mp[1]], y = [Q[i][0] - mq[0], Q[i][1] - mq[1]];
    cr += x[0] * y[1] - x[1] * y[0]; dt += x[0] * y[0] + x[1] * y[1];
  }
  const a = Math.atan2(cr, dt), c = Math.cos(a), s = Math.sin(a);
  return { angle: a, R: [[c, -s], [s, c]], t: [mq[0] - (c * mp[0] - s * mp[1]), mq[1] - (s * mp[0] + c * mp[1])] };
}
export const applyRt = (R, t, P) => P.map(([x, y]) => [R[0][0] * x + R[0][1] * y + t[0], R[1][0] * x + R[1][1] * y + t[1]]);

// eq-m21-icp in 2D (brute-force nearest neighbors)
export function icp2(source, target, iters) {
  let R = [[1, 0], [0, 1]], t = [0, 0];
  const hist = [];
  for (let k = 0; k <= iters; k++) {
    const moved = applyRt(R, t, source);
    const match = moved.map(([x, y]) => {
      let best = 0, bd = Infinity;
      target.forEach(([u, v], j) => { const d = (x - u) ** 2 + (y - v) ** 2; if (d < bd) { bd = d; best = j; } });
      return [best, bd];
    });
    hist.push(match.reduce((s, m) => s + m[1], 0) / match.length);
    if (k === iters) break;
    const fit = procrustes2(source, match.map((m) => target[m[0]]));
    R = fit.R; t = fit.t;
  }
  return { R, t, hist };
}

// an asymmetric chamber-like outline: an ellipse with a vein-like bump
export function outline(n) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const th = (2 * Math.PI * i) / n;
    const bump = 8 * Math.exp(-(((th - 0.6 + Math.PI) % (2 * Math.PI) - Math.PI) ** 2) / 0.05);
    out.push([(30 + bump) * Math.cos(th), (20 + bump) * Math.sin(th)]);
  }
  return out;
}
