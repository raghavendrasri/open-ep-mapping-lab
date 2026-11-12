// m51 · Shared code for the m51 demos, as in labs/python/epml/ct.py. MIT License.
// tests/test_m51_demos.py checks these functions against Python.
import { MATERIALS, muPerMm as tissueMu } from "./m49-common.js";

// Mass attenuation coefficients (cm^2/g) at 60 keV, NIST SRD 126 (Hubbell and Seltzer).
export const WATER_MASS_ATT = 0.2059; // water, liquid, density 1.000 g/cm^3
export const IODINE_MASS_ATT = 7.579;

export function muPerMm(material) {
  if (material === "water") return WATER_MASS_ATT / 10;
  if (material === "air") return 0;
  if (!(material in MATERIALS)) throw new Error(`unknown material ${material}`);
  return tissueMu(material);
}

// eq-m51-hu (air taken as 0).
export function hounsfield(mu) {
  const mw = muPerMm("water");
  return (1000 * (mu - mw)) / mw;
}

// eq-m51-iodine: blood plus c mg/mL of iodine.
export function bloodWithIodineMu(c) {
  return muPerMm("blood") + (c * 1e-3 * IODINE_MASS_ATT) / 10;
}

// The thorax slice of epml.ct.thorax_phantom: [x0, y0, a, b, phi (deg), delta-mu (1/mm)], sizes illustrative.
export function thoraxPhantom(contrast = 10) {
  const tissue = muPerMm("soft tissue");
  const fat = muPerMm("adipose");
  const bone = muPerMm("cortical bone");
  const blood = bloodWithIodineMu(contrast);
  return [
    [0, 0, 150, 110, 0, tissue],
    [-88, 10, 46, 72, 0, -tissue],
    [92, 10, 46, 72, 0, -tissue],
    [5, -5, 40, 72, 0, fat - tissue],
    [10, 20, 34, 26, 30, tissue - fat],
    [14, 24, 21, 14, 30, blood - tissue],
    [0, -32, 24.5, 14.5, 0, tissue - fat],
    [0, -32, 22, 12, 0, blood - tissue],
    [-22, -58, 10, 10, 0, blood - fat],
    [10, -56, 7, 6, 0, tissue - fat],
    [0, -92, 16, 13, 0, bone - tissue],
  ];
}

// The phantom sampled at pixel centers: n x n over fov mm, row-major with row 0 at the bottom (y = -fov/2).
export function raster(phantom, n, fov) {
  const img = new Float64Array(n * n);
  const x = Array.from({ length: n }, (_, i) => (i - (n - 1) / 2) * (fov / n));
  for (const [x0, y0, a, b, phi, v] of phantom) {
    const c = Math.cos((phi * Math.PI) / 180);
    const s = Math.sin((phi * Math.PI) / 180);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const u = (x[i] - x0) * c + (x[j] - y0) * s;
        const w = -(x[i] - x0) * s + (x[j] - y0) * c;
        if ((u / a) ** 2 + (w / b) ** 2 <= 1) img[j * n + i] += v;
      }
    }
  }
  return { img, x };
}

export function angles(n) {
  return Array.from({ length: n }, (_, k) => (k * Math.PI) / n);
}

export function detectorAxis(fov, n) {
  const ds = fov / n;
  const half = Math.ceil((fov * Math.SQRT2) / 2 / ds);
  return Array.from({ length: 2 * half + 1 }, (_, k) => (k - half) * ds);
}

// eq-m51-radon: exact projections of the ellipses. Returns rows (one Float64Array per angle).
export function radonEllipses(phantom, thetas, s) {
  return thetas.map((th) => {
    const row = new Float64Array(s.length);
    for (const [x0, y0, a, b, phi, v] of phantom) {
      const d = th - (phi * Math.PI) / 180;
      const r2 = (a * Math.cos(d)) ** 2 + (b * Math.sin(d)) ** 2;
      const s0 = x0 * Math.cos(th) + y0 * Math.sin(th);
      for (let j = 0; j < s.length; j++) {
        const q = r2 - (s[j] - s0) ** 2;
        if (q > 0) row[j] += (v * 2 * a * b * Math.sqrt(q)) / r2;
      }
    }
    return row;
  });
}

// eq-m51-ramlak: h[n] for n = -nHalf..nHalf.
export function ramlakKernel(nHalf, ds) {
  const h = new Float64Array(2 * nHalf + 1);
  for (let n = -nHalf; n <= nHalf; n++) {
    if (n === 0) h[n + nHalf] = 1 / (4 * ds * ds);
    else if (n % 2 !== 0) h[n + nHalf] = -1 / (Math.PI ** 2 * n * n * ds * ds);
  }
  return h;
}

export function rampFilter(rows, ds) {
  const n = rows[0].length;
  const h = ramlakKernel(n - 1, ds);
  return rows.map((p) => {
    const out = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      let acc = 0;
      for (let j = 0; j < n; j++) acc += p[j] * h[i - j + n - 1];
      out[i] = acc * ds;
    }
    return out;
  });
}

// eq-m51-fbp: back-projection with linear interpolation, row-major output (row 0 at the bottom).
export function backproject(rows, thetas, s, x) {
  const n = x.length;
  const img = new Float64Array(n * n);
  const s0 = s[0];
  const ds = s[1] - s[0];
  const ns = s.length;
  thetas.forEach((th, k) => {
    const c = Math.cos(th);
    const sn = Math.sin(th);
    const p = rows[k];
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const u = (x[i] * c + x[j] * sn - s0) / ds;
        const i0 = Math.floor(u);
        if (i0 < 0 || i0 >= ns - 1) continue;
        const f = u - i0;
        img[j * n + i] += p[i0] * (1 - f) + p[i0 + 1] * f;
      }
    }
  });
  const scale = Math.PI / thetas.length;
  for (let k = 0; k < img.length; k++) img[k] *= scale;
  return img;
}

export function fbp(rows, thetas, s, x, filtered = true) {
  return backproject(filtered ? rampFilter(rows, s[1] - s[0]) : rows, thetas, s, x);
}

// eq-m51-gating and eq-m51-smear.
export function temporalWindow(rotationS, sources = 1) {
  return rotationS / (2 * sources);
}

export function smearedDisk(x, y, diameter, blur) {
  const c2 = (diameter / 2) ** 2 - y * y;
  if (c2 <= 0) return 0;
  const c = Math.sqrt(c2);
  if (blur <= 0) return Math.abs(x) <= c ? 1 : 0;
  const lo = Math.max(x - blur / 2, -c);
  const hi = Math.min(x + blur / 2, c);
  return Math.max(0, hi - lo) / blur;
}

// In-plane coronary artery speed (mm/s) by electron-beam CT in 25 patients, Achenbach et al. 2000.
export const CORONARY_SPEED = {
  "left anterior descending": 22.4,
  "slowest phase (48% of the cycle)": 27.9,
  "all three arteries": 46.6,
  "left circumflex": 48.4,
  "right coronary": 69.5,
};
