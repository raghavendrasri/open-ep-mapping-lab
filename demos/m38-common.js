// m38 shared math: consecutive-window rule and alert workload. MIT License.
// Mirrors labs/python/epml/wearables.py; tests/test_m38_demos.py checks that both agree.

// eq-m38-runs: expected runs of >= k positives among n independent windows (probability q each)
export function expectedRuns(n, q, k) {
  if (n < k) return 0;
  return q ** k * (1 + (n - k) * (1 - q));
}

// eq-m38-detect: probability that L windows (probability p each) contain a run of >= k positives
export function detectionProbability(L, p, k) {
  const a = new Array(L + 1).fill(1);
  for (let m = k; m <= L; m++) {
    let s = 0;
    for (let j = 0; j < k; j++) s += p ** j * (1 - p) * a[m - j - 1];
    a[m] = s;
  }
  return 1 - a[L];
}

// eq-m38-workload
export function alertWorkload(nPatients, alertsPerPatientDay, ppv, minutesPerAlert) {
  const alerts = nPatients * alertsPerPatientDay;
  return { alerts, false: alerts * (1 - ppv), true: alerts * ppv, hours: (alerts * minutesPerAlert) / 60 };
}

// eq-m38-filter
export function filteredAlerts(ppv, keepTrue, removeFalse) {
  const shown = keepTrue * ppv + (1 - removeFalse) * (1 - ppv);
  return { ppv: (keepTrue * ppv) / shown, shown, lost: 1 - keepTrue };
}
