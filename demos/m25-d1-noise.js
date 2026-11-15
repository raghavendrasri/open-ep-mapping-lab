// m25-d1 · How timing noise becomes speed noise (eq-m25-pair, eq-m25-triangle, eq-m25-planefit). MIT License.
// Tested in tests/test_m25_demos.py.
import { diskFitSd, pairRelativeError } from "./m25-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Relative error (SD) of a conduction-speed estimate when every activation time carries independent timing " +
        "error. Blue: two points along the propagation direction, or an equilateral triangle, a given distance apart. " +
        "Orange: a least-squares plane fitted to several points spread over a disk of that radius. Fast conduction " +
        "and close points make speed estimates noisy.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Relative speed error against point spacing" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const sS = addSlider(controls, { id: "m25-d1-s", label: "Timing error (SD)", min: 0.1, max: 3, step: 0.1, value: 1, digits: 1, unit: "ms", onInput: draw });
  const cS = addSlider(controls, { id: "m25-d1-c", label: "Conduction speed", min: 0.2, max: 2, step: 0.1, value: 1, digits: 1, unit: "m/s", onInput: draw });
  const nS = addSlider(controls, { id: "m25-d1-n", label: "Points in the plane fit", min: 5, max: 60, step: 1, value: 20, digits: 0, onInput: draw });

  function draw() {
    const s = Number(sS.value), c = Number(cS.value), n = Number(nS.value);
    const hs = [], pair = [], fit = [];
    for (let h = 1; h <= 20.0001; h += 0.1) {
      hs.push(h);
      pair.push(Math.min(100, 100 * pairRelativeError(s, c, h)));
      fit.push(Math.min(100, 100 * c * diskFitSd(s, n, h)));
    }
    drawPlot(cv, {
      xRange: [1, 20], yRange: [0, 100], xLabel: "spacing or fit radius (mm)", yLabel: "relative speed error (%)",
      series: [
        { x: hs, y: pair, color: COLORS.blue, width: 2.2, label: "two points or a triangle" },
        { x: hs, y: fit, color: COLORS.orange, width: 2.2, label: `plane fit, ${n} points` },
        { x: [4, 4], y: [0, 100], color: COLORS.gray, width: 1, dash: [3, 3] },
      ],
    });
    readout.textContent =
      `At 4 mm: ${(100 * pairRelativeError(s, c, 4)).toFixed(1)}% for two points or a triangle, ` +
      `${(100 * c * diskFitSd(s, n, 4)).toFixed(1)}% for a plane fit to ${n} points (values above about 30% are only indicative).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m25-d1-root");
if (root) mount(root);
