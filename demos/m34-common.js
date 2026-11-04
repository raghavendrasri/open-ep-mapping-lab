// Shared math for the m34 demos (mapping-system software architecture). MIT License.
// Mirrors labs/python/epml/systems.py; tests/test_part6_demo_math.py checks that they agree.

// Small seeded random generator (mulberry32), so a demo shows the same picture every time.
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

export const exponential = (rand, rate) => -Math.log(1 - rand()) / rate;

// Erlang(k) service time with mean 1/mu: coefficient of variation 1/sqrt(k).
export function erlang(rand, k, mu) {
  let s = 0;
  for (let i = 0; i < k; i++) s += exponential(rand, k * mu);
  return s;
}

// Single server, first in first out, at most `capacity` items in the system (Infinity = no limit).
// Returns departure times (NaN for dropped items).
export function queueDepartures(arrivals, services, capacity = Infinity) {
  const depart = new Float64Array(arrivals.length);
  const inSystem = []; // departure times of items still in the system, in order
  let lastDepart = -Infinity;
  for (let i = 0; i < arrivals.length; i++) {
    const t = arrivals[i];
    while (inSystem.length && inSystem[0] <= t) inSystem.shift();
    if (inSystem.length >= capacity) {
      depart[i] = NaN;
      continue;
    }
    const start = Math.max(t, lastDepart);
    depart[i] = start + services[i];
    lastDepart = depart[i];
    inSystem.push(depart[i]);
  }
  return depart;
}

// Simulate a stage at load rho (mu = 1, so times are in units of the mean service time).
export function simulateStage({ rho, k, capacity, n = 80000, seed = 34 }) {
  const rand = rng(seed);
  const arrivals = new Float64Array(n);
  const services = new Float64Array(n);
  let t = 0;
  for (let i = 0; i < n; i++) {
    t += exponential(rand, rho);
    arrivals[i] = t;
    services[i] = erlang(rand, k, 1);
  }
  const depart = queueDepartures(arrivals, services, capacity);
  const latency = [];
  let dropped = 0;
  for (let i = Math.floor(n / 10); i < n; i++) { // skip the start-up transient
    if (Number.isNaN(depart[i])) dropped++;
    else latency.push(depart[i] - arrivals[i]);
  }
  return { latency, dropFraction: dropped / (n - Math.floor(n / 10)) };
}

export const mm1MeanTime = (lam, mu) => (lam >= mu ? Infinity : 1 / (mu - lam));

export function percentile(values, q) {
  const s = Float64Array.from(values).sort();
  const i = Math.min(s.length - 1, Math.max(0, Math.round(q * (s.length - 1))));
  return s[i];
}

export const mean = (v) => v.reduce((a, b) => a + b, 0) / v.length;

export const dataRateBps = (n, fs, bits, overhead = 0) => n * fs * bits * (1 + overhead);

// Largest position error for a catheter moving at speed v on a circle of radius r: the timing
// offset (v |dt|) plus the linear-interpolation chord error (h^2 max|x''| / 8, with |x''| = v^2 / r).
export const alignmentErrorBound = (v, dt, h, r) => v * Math.abs(dt) + (h * h * v * v) / (8 * r);
