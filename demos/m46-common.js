// m46 · Shared code for the m46 demos, as in labs/python/epml/trust.py. MIT License.
// tests/test_m46_demos.py checks these functions against Python.

// eq-m46-conformal: the ceil((n + 1)(1 - alpha))-th smallest score (Infinity if beyond n).
export function conformalQuantile(scores, alpha) {
  const s = [...scores].sort((a, b) => a - b);
  const k = Math.ceil((s.length + 1) * (1 - alpha));
  return k > s.length ? Infinity : s[k - 1];
}

// Prediction sets {k : 1 - p_k <= q}; byClass uses one threshold per true class.
export function conformalSets(Pcal, ycal, Ptest, alpha, byClass = false) {
  const K = Pcal[0].length;
  const scores = Pcal.map((p, i) => 1 - p[ycal[i]]);
  const qs = byClass
    ? Array.from({ length: K }, (_, k) => conformalQuantile(scores.filter((_, i) => ycal[i] === k), alpha))
    : Array(K).fill(conformalQuantile(scores, alpha));
  return Ptest.map((p) => p.map((v, k) => 1 - v <= qs[k]));
}

// PPV from prevalence, TPR and FPR, and eq-m46-fpr: the FPR that gives a chosen PPV.
export function ppv(prev, tpr, fpr) {
  return (tpr * prev) / (tpr * prev + fpr * (1 - prev));
}

export function fprFromPpv(prev, ppvValue, tpr) {
  return (prev / (1 - prev)) * ((1 - ppvValue) / ppvValue) * tpr;
}
