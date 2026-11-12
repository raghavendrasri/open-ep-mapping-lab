// m49 · Shared code for the m49 demos, as in labs/python/epml/fluoro.py. MIT License.
// tests/test_m49_demos.py checks these functions against Python.

// Mass attenuation coefficient (cm^2/g) at 60 keV and density (g/cm^3), NIST SRD 126 (Hubbell and Seltzer).
export const MATERIALS = {
  "soft tissue": [0.2048, 1.06],
  blood: [0.2057, 1.06],
  adipose: [0.1974, 0.95],
  "cortical bone": [0.3148, 1.92],
  platinum: [4.339, 21.45],
};

export function muPerMm(material) {
  const [mass, rho] = MATERIALS[material];
  return (mass * rho) / 10;
}

// The chest phantom of epml.fluoro.chest_phantom (sizes in mm, illustrative).
export function chestPhantom(nElectrodes = 4, spacing = 5, electrodeLength = 2, electrodeRadius = 1.2) {
  const parts = [
    { name: "body", centre: [0, 0, 0], axes: [160, 110, 200], material: "soft tissue", parent: null },
    { name: "heart", centre: [15, -10, 10], axes: [55, 45, 60], material: "blood", parent: "soft tissue" },
    { name: "spine", centre: [0, 75, 0], axes: [18, 18, 190], material: "cortical bone", parent: "soft tissue" },
  ];
  for (let k = 0; k < nElectrodes; k++) {
    parts.push({
      name: `electrode ${k + 1}`,
      centre: [20, -10, -10 + k * spacing],
      axes: [electrodeRadius, electrodeRadius, electrodeLength / 2],
      material: "platinum",
      parent: "blood",
    });
  }
  return parts;
}

export function deltaMu(part) {
  return muPerMm(part.material) - (part.parent ? muPerMm(part.parent) : 0);
}

// Chord length of a ray parallel to y through (x, z).
export function chord(part, x, z) {
  const [a, b, c] = part.axes;
  const q = 1 - ((x - part.centre[0]) / a) ** 2 - ((z - part.centre[2]) / c) ** 2;
  return q > 0 ? 2 * b * Math.sqrt(q) : 0;
}

// eq-m49-beer: exact line integral of mu along y.
export function lineIntegral(phantom, x, z) {
  return phantom.reduce((s, p) => s + deltaMu(p) * chord(p, x, z), 0);
}

// eq-m49-contrast and eq-m49-cnr.
export function subjectContrast(muObject, muBackground, thickness) {
  return 1 - Math.exp(-(muObject - muBackground) * thickness);
}

export function cnr(contrast, photons) {
  return contrast * Math.sqrt(photons);
}

// eq-m49-staff, relative to the reference (1 m, 10 min, no shield, 15 pulses per second, dose per pulse 1).
export function relativeStaffDose(distanceM, minutes, shieldHvl = 0, pulseRate = 15, dosePerPulse = 1) {
  const h = (d, t, s, f, q) => (f * q * t * 2 ** -s) / (d * d);
  return h(distanceM, minutes, shieldHvl, pulseRate, dosePerPulse) / h(1, 10, 0, 15, 1);
}
