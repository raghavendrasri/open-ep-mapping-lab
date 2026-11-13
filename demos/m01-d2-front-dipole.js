// m01-d2 · A wavefront is a moving line of dipoles (eq-m01-core, eq-m01-front-dipole). MIT License.
// Tested in tests/test_m01_demos.py.
import { frontIm, frontPotential, frontVm, lineDipole } from "./m01-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Top: the transmembrane voltage across an arctangent front and the membrane current it drives (source ahead, " +
        "sink behind), both scaled to a peak of one. Bottom: the potential at an electrode a height h above the " +
        "tissue as the front passes, and the potential of an infinitely thin front, a line of dipoles, at the same " +
        "height. Relative units; distance s is from the front, positive where it has not arrived.",
    ),
  );
  const cvTop = setupCanvas(root, { width: 640, height: 200, label: "Voltage and membrane current across the front" });
  const cvBot = setupCanvas(root, { width: 640, height: 220, label: "Electrode potential against distance from the front" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const width = addSlider(controls, { id: "m01-d2-width", label: "Front width w", min: 0.05, max: 3, step: 0.05, value: 0.3, digits: 2, unit: "mm", onInput: draw });
  const height = addSlider(controls, { id: "m01-d2-height", label: "Electrode height h", min: 0.2, max: 5, step: 0.1, value: 1, digits: 1, unit: "mm", onInput: draw });
  const xs = Array.from({ length: 801 }, (_, i) => -10 + (20 * i) / 800);

  function draw() {
    const w = Number(width.value);
    const h = Number(height.value);
    const imPeak = frontIm(w / Math.sqrt(3), w);
    drawPlot(cvTop, {
      xRange: [-10, 10],
      yRange: [-1.2, 1.6],
      xLabel: "distance from the front s (mm)",
      yLabel: "relative units",
      legendLeft: true,
      series: [
        { x: xs, y: xs.map((s) => frontVm(s, w)), color: COLORS.blue, width: 2, label: "V_m / dV" },
        { x: xs, y: xs.map((s) => frontIm(s, w) / imPeak), color: COLORS.vermillion, width: 2, label: "membrane current (outward +)" },
      ],
    });
    const thin = xs.map((s) => lineDipole(1, 1, s, h));
    const real = xs.map((s) => frontPotential(s, w, h));
    const top = Math.max(...thin.map(Math.abs));
    drawPlot(cvBot, {
      xRange: [-10, 10],
      yRange: [-1.15 * top, 1.6 * top],
      xLabel: "distance from the front s (mm)",
      yLabel: "potential (relative)",
      legendLeft: true,
      series: [
        { x: xs, y: thin, color: COLORS.gray, dash: [5, 4], label: "thin front (line of dipoles) at height h" },
        { x: xs, y: real, color: COLORS.green, width: 2, label: "front of width w at height h" },
      ],
    });
    const A = 1 / (2 * Math.PI);
    readout.textContent =
      `Front width ${w.toFixed(2)} mm, height ${h.toFixed(1)} mm. The front's dipole moment is beta dV = 1.00 for ` +
      `every width; widening it is the same as raising the electrode by w. Peak-to-peak potential ` +
      `${(A / (w + h)).toFixed(3)}, against ${(A / h).toFixed(3)} for an infinitely thin front at the same height.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m01-d2-root");
if (root) mount(root);
