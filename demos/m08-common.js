// m08 · Shared code for the m08 demos, as in labs/python/epml/membrane.py. MIT License.
// tests/test_m08_demos.py checks these against Python.

export const FHN = { a: 0.7, b: 0.8, eps: 0.08 }; // illustrative
// Mitchell-Schaeffer parameters (ms) as reported by Nieto Ramos et al. 2023, based on Mitchell and Schaeffer 2003
export const MS = { tauIn: 0.3, tauOut: 6, tauOpen: 150, tauClose: 120, vGate: 0.13 };

// eq-m08-fhn
export const fhnRhs = (v, w, I = 0, p = FHN) => [v - (v * v * v) / 3 - w + I, p.eps * (v + p.a - p.b * w)];

// The unique fixed point: root of v - v^3/3 - (v + a)/b + I = 0 by Newton's method from v = -1.5
export function fhnFixedPoint(I = 0, p = FHN) {
  let v = -1.5;
  for (let k = 0; k < 60; k++) {
    const f = v - (v * v * v) / 3 - (v + p.a) / p.b + I;
    const df = 1 - v * v - 1 / p.b;
    v -= f / df;
  }
  return [v, (v + p.a) / p.b];
}

// eq-m08-hopf
export function fhnHopf(p = FHN) {
  const v = -Math.sqrt(1 - p.eps * p.b);
  return (v * v * v) / 3 - v + (v + p.a) / p.b;
}

// RK4 from rest plus a kick on v; returns {t, v, w}
export function fhnSimulate(tEnd, dt = 0.02, I = 0, kick = 0, p = FHN) {
  let [v, w] = fhnFixedPoint(I, p);
  v += kick;
  const n = Math.round(tEnd / dt);
  const t = new Float64Array(n + 1);
  const vs = new Float64Array(n + 1);
  const ws = new Float64Array(n + 1);
  vs[0] = v;
  ws[0] = w;
  for (let i = 0; i < n; i++) {
    const k1 = fhnRhs(v, w, I, p);
    const k2 = fhnRhs(v + (dt / 2) * k1[0], w + (dt / 2) * k1[1], I, p);
    const k3 = fhnRhs(v + (dt / 2) * k2[0], w + (dt / 2) * k2[1], I, p);
    const k4 = fhnRhs(v + dt * k3[0], w + dt * k3[1], I, p);
    v += (dt / 6) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]);
    w += (dt / 6) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
    t[i + 1] = (i + 1) * dt;
    vs[i + 1] = v;
    ws[i + 1] = w;
  }
  return { t, v: vs, w: ws };
}

// eq-m08-ms: one cell by forward Euler with square stimuli (amplitude 0.5 per ms for 1 ms)
export function msCell(tEnd, stimTimes, p = MS, dt = 0.02, amp = 0.5, dur = 1) {
  const n = Math.round(tEnd / dt);
  const t = new Float64Array(n + 1);
  const v = new Float64Array(n + 1);
  const h = new Float64Array(n + 1);
  h[0] = 1;
  for (let i = 0; i < n; i++) {
    const ti = i * dt;
    let stim = 0;
    for (const s of stimTimes) if (ti >= s && ti < s + dur) stim = amp;
    const vi = v[i];
    const hi = h[i];
    const dv = (hi * vi * vi * (1 - vi)) / p.tauIn - vi / p.tauOut;
    const dh = vi < p.vGate ? (1 - hi) / p.tauOpen : -hi / p.tauClose;
    v[i + 1] = vi + dt * (dv + stim);
    h[i + 1] = hi + dt * dh;
    t[i + 1] = (i + 1) * dt;
  }
  return { t, v, h };
}

// Upstroke time, APD and preceding diastolic interval of each beat, measured at a crossing level
export function apds(t, v, level) {
  const up = [];
  const down = [];
  for (let i = 0; i < v.length - 1; i++) {
    if (v[i] < level && v[i + 1] >= level) up.push(i);
    if (v[i] >= level && v[i + 1] < level) down.push(i);
  }
  const rows = [];
  for (const u of up) {
    const d = down.find((x) => x > u);
    if (d === undefined) break;
    const prev = down.filter((x) => x < u);
    rows.push([t[u], t[d] - t[u], prev.length ? t[u] - t[prev[prev.length - 1]] : NaN]);
  }
  return rows;
}

// eq-m08-apd
export function msApdClosed(di, p = MS) {
  const hm = (4 * p.tauIn) / p.tauOut;
  const h0 = 1 - (1 - hm) * Math.exp(-di / p.tauOpen);
  return p.tauClose * Math.log(h0 / hm);
}

// S1-S2: four beats at s1, then S2; returns [s2, DI, APD] (NaN when S2 does not capture)
export function s1s2(s2, p = MS, s1 = 500, nS1 = 4) {
  const times = [];
  for (let k = 0; k < nS1; k++) times.push(k * s1);
  times.push((nS1 - 1) * s1 + s2);
  const run = msCell(times[times.length - 1] + 600, times, p);
  const rows = apds(run.t, run.v, p.vGate);
  if (rows.length !== nS1 + 1) return { row: [s2, NaN, NaN], run };
  const last = rows[rows.length - 1];
  return { row: [s2, last[2], last[1]], run };
}
