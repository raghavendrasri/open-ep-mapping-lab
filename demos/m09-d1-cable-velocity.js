// m09-d1 · Conduction velocity on a cable (eq-m09-cv). MIT License. Tested in tests/test_m09_demos.py.
import { cableCV, msCable } from "./m09-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const LENGTH = 20; // mm

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A Mitchell-Schaeffer cable 20 mm long, stimulated at the left end. Each curve is the voltage along the cable at " +
        "one moment, 4 ms apart. Raise the diffusion coefficient D (conductivity over capacitance) and the wave speeds " +
        "up as its square root. Coarsen the grid and the computed wave slows down: a numerical error, not physiology.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Voltage along the cable at several moments" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dS = addSlider(controls, { id: "m09-d1-d", label: "Diffusion coefficient D (log10, mm²/ms)", min: -1, max: 0, step: 0.02, value: -0.06, digits: 2, onInput: draw });
  const dxS = addSlider(controls, { id: "m09-d1-dx", label: "Grid spacing", min: 0.05, max: 0.6, step: 0.05, value: 0.1, digits: 2, unit: "mm", onInput: draw });
  let ref = null;

  function draw() {
    const D = 10 ** Number(dS.value);
    const dx = Number(dxS.value);
    const n = Math.round(LENGTH / dx);
    if (!ref) ref = cableCV(msCable(200, 0.1, 0.1, 80).act, 0.1);
    const run = msCable(n, dx, D, 40, [4, 8, 12, 16, 20, 24]);
    const x = Array.from({ length: n }, (_, i) => i * dx);
    const colors = [COLORS.blue, COLORS.green, COLORS.orange, COLORS.vermillion, COLORS.gray, COLORS.ink];
    drawPlot(cv, {
      xRange: [0, LENGTH],
      yRange: [-0.05, 1.05],
      xLabel: "position along the cable (mm)",
      yLabel: "v (dimensionless)",
      series: run.snaps.map((s, k) => ({ x, y: s, color: colors[k], width: 1.8, label: `${4 * (k + 1)} ms` })),
      legendLeft: false,
    });
    const v = cableCV(run.act, dx);
    readout.textContent =
      `D = ${D.toFixed(3)} mm²/ms, grid ${dx.toFixed(2)} mm: velocity ${v.toFixed(2)} m/s. ` +
      `Square-root scaling from D = 0.1 at 0.1 mm predicts ${(ref * Math.sqrt(D / 0.1)).toFixed(2)} m/s.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m09-d1-root");
if (root) mount(root);
