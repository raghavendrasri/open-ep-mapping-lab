// m05 · Shared code for the m05 demos, as in labs/python/epml/timefreq.py. MIT License.
// tests/test_m05_demos.py checks these against Python.

// In-place radix-2 FFT (re, im: Float64Array of length 2^k). inverse=true computes the unscaled inverse.
export function fft(re, im, inverse = false) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) {
    let bit = n >> 1;
    for (; j & bit; bit >>= 1) j ^= bit;
    j ^= bit;
    if (i < j) {
      [re[i], re[j]] = [re[j], re[i]];
      [im[i], im[j]] = [im[j], im[i]];
    }
  }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = ((inverse ? 2 : -2) * Math.PI) / len;
    for (let i = 0; i < n; i += len) {
      for (let k = 0; k < len / 2; k++) {
        const c = Math.cos(ang * k);
        const s = Math.sin(ang * k);
        const ar = re[i + k + len / 2] * c - im[i + k + len / 2] * s;
        const ai = re[i + k + len / 2] * s + im[i + k + len / 2] * c;
        re[i + k + len / 2] = re[i + k] - ar;
        im[i + k + len / 2] = im[i + k] - ai;
        re[i + k] += ar;
        im[i + k] += ai;
      }
    }
  }
}

// eq-m05-analytic: analytic signal by the FFT, padded to the next power of two (as scipy.signal.hilbert(x, N)).
export function analytic(x) {
  let n = 1;
  while (n < x.length) n <<= 1;
  const re = new Float64Array(n);
  const im = new Float64Array(n);
  for (let i = 0; i < x.length; i++) re[i] = x[i];
  fft(re, im);
  for (let k = 1; k < n / 2; k++) {
    re[k] *= 2;
    im[k] *= 2;
  }
  for (let k = n / 2 + 1; k < n; k++) {
    re[k] = 0;
    im[k] = 0;
  }
  fft(re, im, true);
  return { re: Array.from(re.slice(0, x.length), (v) => v / n), im: Array.from(im.slice(0, x.length), (v) => v / n) };
}

export function unwrappedPhase(z) {
  const out = new Float64Array(z.re.length);
  let prev = Math.atan2(z.im[0], z.re[0]);
  let acc = prev;
  out[0] = acc;
  for (let i = 1; i < out.length; i++) {
    const p = Math.atan2(z.im[i], z.re[i]);
    let d = p - prev;
    while (d > Math.PI) d -= 2 * Math.PI;
    while (d < -Math.PI) d += 2 * Math.PI;
    acc += d;
    out[i] = acc;
    prev = p;
  }
  return out;
}

// eq-m05-leakage: periodogram (one-sided, density scaling) evaluated directly at the given frequencies.
export function periodogramAt(x, fs, freqs, window = "boxcar") {
  const n = x.length;
  const w = Array.from({ length: n }, (_, i) => (window === "hann" ? 0.5 - 0.5 * Math.cos((2 * Math.PI * i) / n) : 1));
  const s2 = w.reduce((a, v) => a + v * v, 0);
  return freqs.map((f) => {
    let re = 0;
    let im = 0;
    for (let i = 0; i < n; i++) {
      const a = (-2 * Math.PI * f * i) / fs;
      re += x[i] * w[i] * Math.cos(a);
      im += x[i] * w[i] * Math.sin(a);
    }
    return (2 * (re * re + im * im)) / (fs * s2);
  });
}

export const twoTone = (fs, T, f1, f2, a2 = 1, phase = 0.3) =>
  Array.from({ length: Math.round(fs * T) }, (_, i) => Math.cos((2 * Math.PI * f1 * i) / fs) + a2 * Math.cos((2 * Math.PI * f2 * i) / fs + phase));

// Synthetic signals for m05-d2 (width 4 ms biphasic deflections, first activation at half a cycle)
export function makeSignal(kind, fs, T, cycle) {
  const n = Math.round(fs * T);
  const t = Array.from({ length: n }, (_, i) => i / fs);
  const w = 0.004;
  const g = (u) => Math.exp(-0.5 * (u / w) ** 2);
  const times = [];
  for (let tk = cycle / 2; tk < T; tk += cycle) times.push(tk);
  let seed = 12345;
  const rand = () => {
    seed = (1103515245 * seed + 12345) % 2147483648;
    return seed / 2147483648;
  };
  const x = t.map((tt) => {
    if (kind === "sine") return Math.cos((2 * Math.PI * (tt - cycle / 2)) / cycle);
    let v = 0;
    for (const tk of times) {
      v += (-(tt - tk) / w) * g(tt - tk);
      if (kind === "double") v += ((-0.8 * (tt - tk - 0.04)) / w) * g(tt - tk - 0.04);
    }
    if (kind === "noisy") v += 0.15 * Math.sqrt(-2 * Math.log(rand() + 1e-12)) * Math.cos(2 * Math.PI * rand());
    return v;
  });
  return { t, x, activations: times.length };
}
