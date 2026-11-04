// Shared math for the m36 demos (from prototype to product). MIT License.
// Mirrors labs/python/epml/product.py; tests/test_part6_demo_math.py checks that they agree.

// log Gamma by the Lanczos approximation (g = 7, 9 terms), accurate to about 1e-15 relative.
const LANCZOS = [0.99999999999980993, 676.5203681218851, -1259.1392167224028, 771.32342877765313,
  -176.61502916214059, 12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
export function logGamma(x) {
  if (x < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * x)) - logGamma(1 - x);
  x -= 1;
  let a = LANCZOS[0];
  const t = x + 7.5;
  for (let i = 1; i < 9; i++) a += LANCZOS[i] / (x + i);
  return 0.5 * Math.log(2 * Math.PI) + (x + 0.5) * Math.log(t) - t + Math.log(a);
}

const logChoose = (n, k) => logGamma(n + 1) - logGamma(k + 1) - logGamma(n - k + 1);

// P(X <= c) for X ~ Binomial(n, p).
export function binomCdf(c, n, p) {
  if (p <= 0) return 1;
  if (p >= 1) return c >= n ? 1 : 0;
  let s = 0;
  for (let k = 0; k <= Math.min(c, n); k++) s += Math.exp(logChoose(n, k) + k * Math.log(p) + (n - k) * Math.log(1 - p));
  return Math.min(1, s);
}

export const successRunN = (R, C) => Math.ceil(Math.log(1 - C) / Math.log(R) - 1e-12);

export function acceptanceN(R, C, c, nMax = 100000) {
  for (let n = c + 1; n <= nMax; n++) if (binomCdf(c, n, 1 - R) <= 1 - C) return n;
  return NaN;
}

// Probability of passing a plan (n, c) when the true reliability is r.
export const passProbability = (n, c, r) => binomCdf(c, n, 1 - r);

export const reliability = (t, rate) => Math.exp(-rate * t);
export const seriesRate = (rates) => rates.reduce((a, b) => a + b, 0);
