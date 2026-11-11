// m40 · Closed forms shared by the m40 demos. MIT License.
// Each function mirrors labs/python/epml/imaging.py and is tested against it (tests/test_m40_demos.py).

// eq-m40-sphere: Dice of concentric spheres of radii R and R + delta.
export function sphereDice(R, delta) {
  const r2 = R + delta;
  return (2 * Math.min(R, r2) ** 3) / (R ** 3 + r2 ** 3);
}

// Two-dimensional counterpart: concentric discs (also a vein seen along its axis).
export function discDice(R, delta) {
  const r2 = R + delta;
  return (2 * Math.min(R, r2) ** 2) / (R ** 2 + r2 ** 2);
}

// eq-m40-slab: a wall of thickness t shifted by delta along its normal.
export function slabDice(t, delta) {
  return Math.min(1, Math.max(0, 1 - Math.abs(delta) / t));
}

// eq-m40-offset, first order: 1 - |delta| S / (2 V).
export function offsetDiceFirstOrder(delta, area, volume) {
  return 1 - (Math.abs(delta) * area) / (2 * volume);
}

// m40-d1: Dice, Hausdorff distance, ASSD and NSD for a true disc (radius R), a concentric predicted
// disc (radius R + delta) and an optional island (radius rho, nearest edge `gap` beyond the outer
// main contour). Distances between contours, weighted by arc length; midpoint rule with n points.
export function circleIslandMetrics(R, delta, rho, gap, tau, n = 3600) {
  const Rp = R + delta;
  const ad = Math.abs(delta);
  const dice = (2 * Math.min(R, Rp) ** 2) / (R ** 2 + Rp ** 2 + rho ** 2);
  const lenMain = 2 * Math.PI * Rp;
  const lenT = 2 * Math.PI * R;
  const lenIsl = rho > 0 ? 2 * Math.PI * rho : 0;
  const c = R + Math.max(delta, 0) + gap + rho;
  let hd = ad;
  let sumIsl = 0;
  let inIsl = 0;
  let sumT = 0;
  let inT = 0;
  for (let i = 0; i < n; i++) {
    const p = ((i + 0.5) * 2 * Math.PI) / n;
    let dT = ad;
    if (rho > 0) {
      const dI = Math.hypot(c + rho * Math.cos(p), rho * Math.sin(p)) - R;
      sumIsl += dI;
      inIsl += dI <= tau ? 1 : 0;
      hd = Math.max(hd, dI);
      dT = Math.min(ad, Math.hypot(R * Math.cos(p) - c, R * Math.sin(p)) - rho);
    }
    sumT += dT;
    inT += dT <= tau ? 1 : 0;
    hd = Math.max(hd, dT);
  }
  const total = lenMain + lenIsl + lenT;
  const assd = (lenMain * ad + (rho > 0 ? (lenIsl * sumIsl) / n : 0) + (lenT * sumT) / n) / total;
  const nsd = (lenMain * (ad <= tau ? 1 : 0) + (rho > 0 ? (lenIsl * inIsl) / n : 0) + (lenT * inT) / n) / total;
  return { dice, hd, assd, nsd, islandCentre: c };
}
