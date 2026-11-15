// m13-d1 · Electrode spacing against height above the tissue (eq-m13-alias). MIT License.
// Tested in tests/test_m13_demos.py.
import { aliasFraction, maxSpacing, poissonKernel } from "./m13-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Left: the sharpest signal a planar front can make across its width, seen from a height h above the activated " +
        "layer (gray), sampled by electrodes at the chosen spacing (dots) and joined by straight lines (blue). Right: " +
        "its spatial spectrum exp(−kh); the dashed line is the spatial Nyquist limit π/spacing. Energy beyond it is lost " +
        "or aliased.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const cvL = setupCanvas(row, { width: 390, height: 260, label: "Signal across a front, true and sampled" });
  const cvR = setupCanvas(row, { width: 300, height: 260, label: "Spatial spectrum and the Nyquist limit" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dS = addSlider(controls, { id: "m13-d1-spacing", label: "Electrode spacing", min: 0.5, max: 6, step: 0.1, value: 2, digits: 1, unit: "mm", onInput: draw });
  const hS = addSlider(controls, { id: "m13-d1-height", label: "Height above the activated layer", min: 0.3, max: 3, step: 0.1, value: 1, digits: 1, unit: "mm", onInput: draw });
  const oS = addSlider(controls, { id: "m13-d1-offset", label: "Grid offset (fraction of spacing)", min: 0, max: 1, step: 0.05, value: 0.5, digits: 2, onInput: draw });

  function draw() {
    const D = Number(dS.value), h = Number(hS.value), off = Number(oS.value) * D;
    const peak = poissonKernel(0, h);
    const xs = [], ys = [];
    for (let x = -10; x <= 10.0001; x += 0.05) { xs.push(x); ys.push(poissonKernel(x, h) / peak); }
    const sx = [], sy = [];
    for (let m = -Math.ceil(12 / D); m <= Math.ceil(12 / D); m++) {
      const x = m * D + off;
      if (x >= -10 && x <= 10) { sx.push(x); sy.push(poissonKernel(x, h) / peak); }
    }
    drawPlot(cvL, {
      xRange: [-10, 10], yRange: [0, 1.05], xLabel: "distance across the front (mm)", yLabel: "signal (relative to peak)",
      series: [
        { x: xs, y: ys, color: COLORS.gray, width: 2, label: "true" },
        { x: sx, y: sy, color: COLORS.blue, width: 2, label: "sampled, joined" },
      ],
      markers: sx.map((x, i) => ({ x, y: sy[i], color: COLORS.blue })),
    });
    const kx = [], ky = [];
    for (let k = 0; k <= 8.0001; k += 0.04) { kx.push(k); ky.push(Math.exp(-k * h)); }
    drawPlot(cvR, {
      xRange: [0, 8], yRange: [0, 1.05], xLabel: "spatial frequency k (rad/mm)", yLabel: "amplitude exp(−kh)",
      series: [
        { x: kx, y: ky, color: COLORS.vermillion, width: 2 },
        { x: [Math.PI / D, Math.PI / D], y: [0, 1.05], color: COLORS.ink, width: 1.5, dash: [5, 4] },
      ],
    });
    const best = Math.max(...sy);
    readout.textContent =
      `Energy above Nyquist: ${(100 * aliasFraction(D, h)).toFixed(2)}%. Highest sample: ${(100 * best).toFixed(0)}% of the ` +
      `true peak. Spacing for 1% at this height: ${maxSpacing(h, 0.01).toFixed(2)} mm.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m13-d1-root");
if (root) mount(root);
