// m11 · Shared code for the m11 demos, as in labs/python/epml/epstudy.py. MIT License.
// tests/test_m11_demos.py checks these against Python.

// Rabbit anterograde AV nodal values (Reid et al. 2003); tau is illustrative
export const AVN = { nctMin: 57, nctMax: 150, erp: 91, tau: 100 };

// eq-m11-avnode: nodal conduction time after a recovery time rt; NaN (block) below the nodal refractory period
export function nodalTime(rt, p = AVN) {
  if (rt < p.erp) return NaN;
  return p.nctMin + (p.nctMax - p.nctMin) * Math.exp(-(rt - p.erp) / p.tau);
}

// Atrial beats every cl ms; nodal time per beat (NaN when blocked)
export function avSequence(cl, n = 40, p = AVN) {
  const out = [];
  let lastOut = -Infinity;
  for (let k = 0; k < n; k++) {
    const tIn = k * cl;
    const nct = Number.isFinite(lastOut) ? nodalTime(tIn - lastOut, p) : p.nctMin;
    if (Number.isFinite(nct)) lastOut = tIn + nct;
    out.push(nct);
  }
  return out;
}

// Repeating pattern (atrial, conducted) per cycle of the steady sequence
export function conductionRatio(seq) {
  const blocked = [];
  seq.forEach((v, i) => {
    if (!Number.isFinite(v)) blocked.push(i);
  });
  if (blocked.length === 0) return [1, 1];
  if (blocked.length < 3) return null;
  const last = blocked.slice(-4);
  const diffs = last.slice(1).map((v, i) => v - last[i]).sort((a, b) => a - b);
  const period = diffs[Math.floor(diffs.length / 2)];
  return [period, period - 1];
}

// eq-m11-ppi
export const ppiMinusTcl = (d, cv) => (2 * d) / cv;
