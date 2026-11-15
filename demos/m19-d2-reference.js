// m19-d2 · When does a reference help? (eq-m19-reference, eq-m19-surrogate). MIT License.
// Tested in tests/test_m19_demos.py.
import { differenceSd, residualSd } from "./m19-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Residual motion of a mapping point, relative to its uncorrected motion, against how well a reference's motion " +
        "correlates with it. Orange: subtract the reference outright. Blue: scale it first by the best regression " +
        "slope. Subtraction only helps above the dashed correlation; regression never hurts.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Residual motion against correlation" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const rS = addSlider(controls, { id: "m19-d2-rho", label: "Correlation ρ", min: 0, max: 1, step: 0.01, value: 0.6, digits: 2, onInput: draw });
  const qS = addSlider(controls, { id: "m19-d2-q", label: "Reference motion ÷ point motion", min: 0.2, max: 2, step: 0.05, value: 1, digits: 2, onInput: draw });

  function draw() {
    const rho = Number(rS.value), q = Number(qS.value);
    const xs = [], ys = [], yr = [];
    for (let r = 0; r <= 1.0001; r += 0.01) { xs.push(r); ys.push(differenceSd(1, q, r)); yr.push(residualSd(1, r)); }
    const thr = Math.min(q / 2, 1);
    drawPlot(cv, {
      xRange: [0, 1], yRange: [0, 2.2], xLabel: "correlation ρ", yLabel: "residual SD ÷ uncorrected SD",
      series: [
        { x: xs, y: ys, color: COLORS.orange, width: 2.5, label: "subtract" },
        { x: xs, y: yr, color: COLORS.blue, width: 2.5, label: "regress" },
        { x: [0, 1], y: [1, 1], color: COLORS.gray, width: 1.2 },
        { x: [thr, thr], y: [0, 2.2], color: COLORS.ink, width: 1.2, dash: [5, 4] },
      ],
      markers: [{ x: rho, y: differenceSd(1, q, rho), color: COLORS.orange }, { x: rho, y: residualSd(1, rho), color: COLORS.blue }],
    });
    readout.textContent =
      `At ρ = ${rho.toFixed(2)}: subtracting leaves ${(100 * differenceSd(1, q, rho)).toFixed(0)}%, regressing ` +
      `${(100 * residualSd(1, rho)).toFixed(0)}%. Subtraction helps only if ρ > ${(q / 2).toFixed(2)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m19-d2-root");
if (root) mount(root);
