// m50 · Shared code for the m50 demos, as in labs/python/epml/ice.py. MIT License.
// tests/test_m50_demos.py checks these functions against Python.

export const C_ASSUMED = 1540; // m/s, the speed of sound scanners assume (Zhang et al. 2026)

// eq-m50-axial: wavelength and half the spatial pulse length, in mm (f in MHz).
export function wavelengthMm(fMHz, c = C_ASSUMED) {
  return (c / (fMHz * 1e6)) * 1e3;
}

export function axialResolutionMm(fMHz, cycles, c = C_ASSUMED) {
  return (cycles * wavelengthMm(fMHz, c)) / 2;
}

// eq-m50-attenuation: round-trip loss 2 alpha f z (dB) and the depth that uses a budget (cm).
export function roundTripLossDb(alpha, fMHz, depthCm) {
  return 2 * alpha * fMHz * depthCm;
}

export function maxDepthCm(budgetDb, alpha, fMHz) {
  return budgetDb / (2 * alpha * fMHz);
}

// eq-m50-steer: array factor of n elements, pitch d in wavelengths, steered to theta0 (radians).
export function arrayFactor(thetas, n, pitchOverLambda, steer) {
  const s0 = Math.sin(steer);
  return thetas.map((th) => {
    const psi = 2 * Math.PI * pitchOverLambda * (Math.sin(th) - s0);
    let re = 0;
    let im = 0;
    for (let k = 0; k < n; k++) {
      re += Math.cos(k * psi);
      im += Math.sin(k * psi);
    }
    return Math.hypot(re, im) / n;
  });
}

export function gratingLobesDeg(pitchOverLambda, steer) {
  const out = [];
  const mMax = Math.ceil(2 * pitchOverLambda) + 1;
  for (let m = -mMax; m <= mMax; m++) {
    if (m === 0) continue;
    const s = Math.sin(steer) + m / pitchOverLambda;
    if (Math.abs(s) <= 1) out.push((Math.asin(s) * 180) / Math.PI);
  }
  return out.sort((a, b) => a - b);
}

export function firstNullOffset(n, pitchOverLambda) {
  return 1 / (n * pitchOverLambda);
}

// eq-m50-frame-rate: c / (2 D N), D in meters.
export function frameRate(depthM, nLines, c = C_ASSUMED) {
  return c / (2 * depthM * nLines);
}
