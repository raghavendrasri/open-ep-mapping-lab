// m49-d1 · A shadow of the heart: a projected chest phantom with a catheter, and quantum noise. MIT License.
// Line integrals are exact for the ellipsoid phantom; noise uses a normal approximation to Poisson counts.
import { normals } from "./m45-common.js";
import { chestPhantom, chord, cnr, deltaMu, lineIntegral } from "./m49-common.js";
import { COLORS, addReadout, addSelect, addSlider, el, setupCanvas } from "./plot.js";

const X0 = -90;
const Z0 = -80;
const NX = 200; // 1-mm pixels, x from -90 to 110 mm
const NZ = 150; // z from -80 to 70 mm
const TARGETS = {
  heart: { label: "heart (blood against soft tissue)", part: "heart", x: 45, z: 40 },
  electrode: { label: "catheter electrode (platinum in blood)", part: "electrode 3", x: 20, z: 0 },
  spine: { label: "spine (cortical bone against soft tissue)", part: "spine", x: 0, z: -60 },
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A front-to-back X-ray projection of a chest phantom: soft tissue, a blood-filled heart, a bone spine and a " +
        "catheter with four platinum electrodes inside the heart. Darker means more attenuation. Each pixel " +
        "counts photons, so fewer photons (less dose) means more noise. Pick a structure to see its contrast and " +
        "contrast-to-noise ratio (CNR).",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Simulated fluoroscopy image of a chest phantom with a catheter, with noise set by the dose" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dose = addSlider(controls, { id: "m49-d1-dose", label: "Photons per pixel (log10)", min: 1, max: 6, step: 0.1, value: 4.5, digits: 1, onInput: draw });
  const target = addSelect(controls, {
    id: "m49-d1-target",
    label: "Structure",
    options: Object.entries(TARGETS).map(([value, t]) => ({ value, label: t.label })),
    value: "heart",
    onChange: draw,
  });
  const phantom = chestPhantom();
  const L = new Float64Array(NX * NZ);
  for (let j = 0; j < NZ; j++) for (let i = 0; i < NX; i++) L[j * NX + i] = lineIntegral(phantom, X0 + i + 0.5, Z0 + j + 0.5);
  const z = normals(NX * NZ, 49);
  const off = document.createElement("canvas");
  off.width = NX;
  off.height = NZ;
  const octx = off.getContext("2d");

  function draw() {
    const N = 10 ** Number(dose.value);
    const img = octx.createImageData(NX, NZ);
    const lmin = 4.2;
    const lmax = 7.2;
    for (let k = 0; k < NX * NZ; k++) {
      const mean = N * Math.exp(-L[k]);
      const counts = Math.max(0.5, mean + Math.sqrt(mean) * z[k]);
      const shown = Math.min(Math.max(-Math.log(counts / N), lmin), lmax);
      const g = Math.round(255 * (1 - (shown - lmin) / (lmax - lmin)));
      // image rows run head (top) to foot: row j = NZ - 1 - zIndex
      const row = NZ - 1 - Math.floor(k / NX);
      const p = 4 * (row * NX + (k % NX));
      img.data[p] = img.data[p + 1] = img.data[p + 2] = g;
      img.data[p + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    const s = 1.8;
    const left = (width - NX * s) / 2;
    const top = 10;
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(off, left, top, NX * s, NZ * s);
    ctx.strokeStyle = "#8c959f";
    ctx.strokeRect(left, top, NX * s, NZ * s);
    const t = TARGETS[target.value];
    const part = phantom.find((p) => p.name === t.part);
    const px = left + (t.x - X0) * s;
    const pz = top + (NZ - (t.z - Z0)) * s;
    ctx.strokeStyle = COLORS.vermillion;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(px, pz, 9, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.fillStyle = COLORS.ink;
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText("head", left + NX * s + 6, top);
    ctx.fillText("foot", left + NX * s + 6, top + NZ * s - 14);
    ctx.fillText("20 mm", left + 4, top + NZ * s + 6);
    ctx.fillRect(left + 50, top + NZ * s + 12, 20 * s, 2);
    const Lpix = lineIntegral(phantom, t.x, t.z);
    const without = Lpix - deltaMu(part) * chord(part, t.x, t.z);
    const contrast = 1 - Math.exp(-(Lpix - without));
    const nBg = N * Math.exp(-without);
    const r = cnr(contrast, nBg);
    const factor = (3 / Math.max(r, 1e-9)) ** 2;
    readout.textContent =
      `${Math.round(N).toLocaleString("en-US")} photons per pixel. ${t.label[0].toUpperCase()}${t.label.slice(1)}: ` +
      `contrast ${(100 * contrast).toFixed(contrast < 0.1 ? 2 : 1)}%, CNR ${r.toFixed(r < 10 ? 2 : 0)}. ` +
      (r >= 3 ? "Above CNR 3 at this dose." : `Reaching CNR 3 would need ${factor < 10 ? factor.toFixed(1) : Math.round(factor).toLocaleString("en-US")} times this dose.`);
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m49-d1-root");
if (root) mount(root);
