// Shared math for the m35 demos (machine learning in EP mapping). MIT License.
// Mirrors labs/python/epml/ml.py; tests/test_part6_demo_math.py checks that they agree.
import { rng } from "./m34-common.js";

export { rng };

// Standard normal draws (Box-Muller).
export function randn(rand) {
  const u = 1 - rand();
  const v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

// Error function (Abramowitz and Stegun 7.1.26, absolute error below 1.5e-7) and normal CDF.
export function erf(x) {
  const s = Math.sign(x);
  const a = Math.abs(x);
  const t = 1 / (1 + 0.3275911 * a);
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-a * a);
  return s * y;
}
export const normCdf = (z) => 0.5 * (1 + erf(z / Math.SQRT2));

export function predictiveValues(se, sp, prev) {
  const ppv = (se * prev) / (se * prev + (1 - sp) * (1 - prev));
  const npv = (sp * (1 - prev)) / (sp * (1 - prev) + (1 - se) * prev);
  return { ppv, npv };
}

// Equal-variance binormal scores: negatives ~ N(0, 1), positives ~ N(d, 1).
export const binormalSe = (t, d) => 1 - normCdf(t - d);
export const binormalSp = (t) => normCdf(t);
export const binormalAuc = (d) => normCdf(d / Math.SQRT2);

export const sigmoid = (z) => 1 / (1 + Math.exp(-z));
export const logit = (p) => Math.log(p / (1 - p));

export function brier(p, y) {
  let s = 0;
  for (let i = 0; i < p.length; i++) s += (p[i] - y[i]) ** 2;
  return s / p.length;
}

// Patients with a label each. Every record has DIMS features: a patient "signature" (a share icc
// of the variance, the same for all records of that patient), independent noise, and a class
// signal of strength `signal` along the first feature.
export const DIMS = 6;
export function clusteredRecords({ patients, perPatient, icc, signal, seed = 35 }) {
  const rand = rng(seed);
  const recs = [];
  for (let p = 0; p < patients; p++) {
    const y = p % 2;
    const u = Array.from({ length: DIMS }, () => randn(rand) * Math.sqrt(icc));
    for (let r = 0; r < perPatient; r++) {
      const x = u.map((ui) => ui + randn(rand) * Math.sqrt(1 - icc));
      x[0] += signal * y;
      recs.push({ patient: p, y, x });
    }
  }
  return recs;
}

// Accuracy of a 1-nearest-neighbour classifier, leaving out either the record itself
// (record-wise) or every record of the same patient (patient-wise).
export function nearestNeighbourAccuracy(recs, patientWise) {
  let correct = 0;
  for (let i = 0; i < recs.length; i++) {
    let best = Infinity;
    let label = 0;
    for (let j = 0; j < recs.length; j++) {
      if (j === i || (patientWise && recs[j].patient === recs[i].patient)) continue;
      let d = 0;
      for (let k = 0; k < recs[i].x.length; k++) d += (recs[i].x[k] - recs[j].x[k]) ** 2;
      if (d < best) {
        best = d;
        label = recs[j].y;
      }
    }
    if (label === recs[i].y) correct++;
  }
  return correct / recs.length;
}
