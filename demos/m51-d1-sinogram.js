// m51-d1 · From sinogram to slice: exact projections of a thorax phantom, then back-projection with and without
// the ramp filter, with optional quantum noise. MIT License. Formulas tested in tests/test_m51_demos.py.
import { normals } from "./m45-common.js";
import { angles, detectorAxis, fbp, hounsfield, radonEllipses, raster, thoraxPhantom } from "./m51-common.js";
import { addReadout, addSelect, addSlider, drawField, el, setupCanvas } from "./plot.js";

const N = 160; // 2-mm pixels
const FOV = 320; // mm
const WINDOW = [-200, 600]; // display window, HU
const gray = (t) => {
  const g = Math.round(255 * Math.min(1, Math.max(0, t)));
  return [g, g, g];
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Left: the sinogram, one row of line integrals per projection angle, computed exactly for a synthetic " +
        "thorax slice (body, lungs, mediastinal fat, heart, contrast-filled left atrium and aorta, esophagus, " +
        "spine). Right: the slice rebuilt from those rows. Without the ramp filter, back-projection gives a " +
        "blurred image; with it, the Hounsfield units come back. Few angles leave streaks, and fewer photons " +
        "per ray (less dose) add noise.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Sinogram of a thorax phantom and the slice reconstructed from it" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const nAng = addSlider(controls, { id: "m51-d1-angles", label: "Projection angles", min: 6, max: 180, step: 6, value: 60, digits: 0, onInput: draw });
  const filter = addSelect(controls, {
    id: "m51-d1-filter",
    label: "Filter",
    options: [
      { value: "ramp", label: "ramp (filtered back-projection)" },
      { value: "none", label: "none (plain back-projection)" },
    ],
    value: "ramp",
    onChange: draw,
  });
  const noise = addSelect(controls, {
    id: "m51-d1-noise",
    label: "Photons per ray",
    options: [
      { value: "0", label: "no noise" },
      { value: "1e5", label: "100,000" },
      { value: "1e4", label: "10,000" },
      { value: "1e3", label: "1,000" },
    ],
    value: "0",
    onChange: draw,
  });

  const phantom = thoraxPhantom();
  const { img: truth, x } = raster(phantom, N, FOV);
  const truthHu = Array.from(truth, hounsfield);
  const body = Array.from(truth, (v) => v > 0.01);
  const s = detectorAxis(FOV, N);
  const z = normals(180 * s.length, 51);
  const ia = (xmm) => Math.round(xmm / (FOV / N) + (N - 1) / 2);
  const laIndex = ia(-32) * N + ia(0);

  function draw() {
    const K = Number(nAng.value);
    const th = angles(K);
    const N0 = Number(noise.value);
    let rows = radonEllipses(phantom, th, s);
    if (N0 > 0) {
      rows = rows.map((row, k) =>
        row.map((p, j) => {
          const mean = N0 * Math.exp(-p);
          const counts = Math.max(1, mean + Math.sqrt(mean) * z[k * s.length + j]);
          return -Math.log(counts / N0);
        }),
      );
    }
    const filtered = filter.value === "ramp";
    const rec = fbp(rows, th, s, x, filtered);
    // plain back-projection is not in Hounsfield units: scale it to the body's mean for display only
    let shown;
    if (filtered) shown = Array.from(rec, hounsfield);
    else {
      let a = 0;
      let b = 0;
      for (let k = 0; k < rec.length; k++) if (body[k]) {
        a += rec[k];
        b += truth[k];
      }
      shown = Array.from(rec, (v) => hounsfield((v * b) / a));
    }
    const sino = [];
    let pmax = 0;
    for (const row of rows) for (const v of row) {
      sino.push(v);
      pmax = Math.max(pmax, v);
    }
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    drawField(cv, {
      nx: s.length, ny: K, field: sino, extent: [s[0], s[s.length - 1], 0, 180], range: [0, pmax],
      panel: { x: 0, y: 0, w: 320, h: height }, title: "Sinogram", colormap: gray,
      xLabel: "detector position s (mm)", yLabel: "angle θ (degrees)", unit: "∫μ ds",
    });
    drawField(cv, {
      nx: N, ny: N, field: shown, extent: [-FOV / 2, FOV / 2, -FOV / 2, FOV / 2], range: WINDOW,
      panel: { x: 320, y: 0, w: 320, h: height }, title: filtered ? "Slice, filtered back-projection" : "Slice, plain back-projection",
      colormap: gray, xLabel: "x (mm), patient's left →", yLabel: "y (mm), front ↑", unit: "HU",
    });
    const err = [];
    for (let k = 0; k < shown.length; k++) if (body[k]) err.push(Math.abs(shown[k] - truthHu[k]));
    err.sort((p, q) => p - q);
    const med = err[Math.floor(err.length / 2)];
    readout.textContent =
      `${K} angles over 180°, ${filtered ? "ramp filter" : "no filter (display rescaled)"}, ` +
      `${N0 > 0 ? `${N0.toLocaleString("en-US")} photons per ray` : "no noise"}. ` +
      `Median error inside the body: ${Math.round(med)} HU. Left atrium center: ${Math.round(shown[laIndex])} HU ` +
      `(true ${Math.round(truthHu[laIndex])} HU).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m51-d1-root");
if (root) mount(root);
