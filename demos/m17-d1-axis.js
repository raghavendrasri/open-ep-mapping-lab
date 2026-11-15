// m17-d1 · Nonlinearity of a patch-pair field along its axis (eq-m17-axis). MIT License.
// Tested in tests/test_m17_demos.py.
import { axisPotential, linearEstimate } from "./m17-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Two skin patches at ±d drive a current through a homogeneous medium. A system that assumes a uniform field turns " +
        "the potential into position with the slope at the center. Blue: the position it reports along the patches' " +
        "axis; gray: the truth. The field is stronger toward the patches, so positions there are stretched.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Reported against true position along the axis" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dS = addSlider(controls, { id: "m17-d1-d", label: "Patch half-separation d", min: 120, max: 300, step: 5, value: 200, digits: 0, unit: "mm", onInput: draw });
  const xS = addSlider(controls, { id: "m17-d1-x", label: "Probe position", min: 0, max: 100, step: 1, value: 50, digits: 0, unit: "mm", onInput: draw });

  function draw() {
    const d = Number(dS.value), xp = Number(xS.value);
    const xs = [], ys = [];
    for (let x = -100; x <= 100.0001; x += 1) { xs.push(x); ys.push(linearEstimate(axisPotential(x, d), d)); }
    const rep = linearEstimate(axisPotential(xp, d), d);
    drawPlot(cv, {
      xRange: [-100, 100], yRange: [-140, 140], xLabel: "true position along the axis (mm)", yLabel: "reported position (mm)",
      series: [
        { x: [-100, 100], y: [-100, 100], color: COLORS.gray, width: 1.5, label: "truth" },
        { x: xs, y: ys, color: COLORS.blue, width: 2.5, label: "uniform-field estimate" },
      ],
      markers: [{ x: xp, y: rep, color: COLORS.vermillion }],
    });
    readout.textContent =
      `At ${xp} mm the system reports ${rep.toFixed(1)} mm: ${(rep - xp).toFixed(1)} mm too far, ` +
      `${((100 * xp * xp) / (d * d - xp * xp)).toFixed(1)}% stretch (x²/(d² − x²)).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m17-d1-root");
if (root) mount(root);
