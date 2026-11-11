// m37 shared math: receptive field, synthetic beat, screening yield, prior shift. MIT License.
// Mirrors labs/python/epml/aiecg.py; tests/test_m37_demos.py checks that both agree.

// eq-m37-receptive-field: r = 1 + sum_l (k_l - 1) prod_{j<l} s_j
export function receptiveField(kernels, strides) {
  let r = 1;
  let jump = 1;
  kernels.forEach((k, i) => {
    r += (k - 1) * jump;
    jump *= strides[i];
  });
  return r;
}

// Gaussian waves of one beat: [name, time from R (s), amplitude (mV), width (s)]. Illustrative values.
export const WAVES = [
  ["P", -0.17, 0.12, 0.025],
  ["Q", -0.03, -0.1, 0.01],
  ["R", 0.0, 1.0, 0.012],
  ["S", 0.03, -0.2, 0.012],
  ["T", 0.25, 0.3, 0.05],
];

export function beat(t, scale = 1, pWave = true) {
  let v = 0;
  for (const [name, t0, a, b] of WAVES) {
    if (name === "P" && !pWave) continue;
    v += scale * a * Math.exp(-((t - t0) ** 2) / (2 * b * b));
  }
  return v;
}

// A noise-free regular rhythm: R peaks every 60/hr seconds, the first at `first` seconds.
export function regularEcg(fs, duration, hr, first = 0.4, pWave = true) {
  const n = Math.round(duration * fs);
  const rr = 60 / hr;
  const x = new Array(n).fill(0);
  for (let tr = first - rr; tr < duration + rr; tr += rr) {
    for (let i = 0; i < n; i++) x[i] += beat(i / fs - tr, 1, pWave);
  }
  return x;
}

// eq-m37-yield
export function screeningYield(n, prevalence, se, sp) {
  const tp = n * prevalence * se;
  const fp = n * (1 - prevalence) * (1 - sp);
  return { tp, fp, flagged: tp + fp, perCase: tp > 0 ? (tp + fp) / tp : Infinity };
}

// eq-m37-prior-shift
export function priorShift(p, prevTrain, prevNew) {
  const a = (prevNew / prevTrain) * p;
  const b = ((1 - prevNew) / (1 - prevTrain)) * (1 - p);
  return a / (a + b);
}
