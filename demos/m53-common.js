// m53 · Shared code for the m53 demos, as in labs/python/epml/lesion.py. MIT License.
// tests/test_m53_demos.py checks these functions against Python.
import { erf } from "./m35-common.js";

export const FPS_PASSIVE = [4, 8]; // frames/s, passive catheter visualization (Tampakis et al. 2023)
export const FPS_ACTIVE = 50; // frames/s, active tracking, upper value (Tampakis et al. 2023)

export function fwhmToSigma(fwhm) {
  return fwhm / (2 * Math.sqrt(2 * Math.LN2));
}

function box(u, width, sigma) {
  const r = Math.SQRT2 * sigma;
  return 0.5 * (erf((u + width / 2) / r) - erf((u - width / 2) / r));
}

// eq-m53-gap
export function bandGapImage(x, y, bandWidth, gapWidth, sigma) {
  return box(y, bandWidth, sigma) * (1 - box(x, gapWidth, sigma));
}

export function bandPeak(bandWidth, sigma) {
  return erf(bandWidth / (2 * Math.SQRT2 * sigma));
}

export function gapCenter(bandWidth, gapWidth, sigma) {
  return bandPeak(bandWidth, sigma) * (1 - erf(gapWidth / (2 * Math.SQRT2 * sigma)));
}

export function erfinv(y) {
  let lo = -6;
  let hi = 6;
  for (let k = 0; k < 80; k++) {
    const mid = (lo + hi) / 2;
    if (erf(mid) < y) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

export function minVisibleGap(bandWidth, sigma, threshold = 0.5) {
  const peak = bandPeak(bandWidth, sigma);
  if (peak <= threshold) return Infinity;
  return 2 * Math.SQRT2 * sigma * erfinv(1 - threshold / peak);
}

// eq-m53-frame
export function frameTimeMs(nLines, trMs, acceleration = 1) {
  return (nLines * trMs) / acceleration;
}

export function fps(nLines, trMs, acceleration = 1) {
  return 1e3 / frameTimeMs(nLines, trMs, acceleration);
}
