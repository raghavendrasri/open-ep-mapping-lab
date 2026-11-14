// m11-d2 · The post-pacing interval and distance from the circuit (eq-m11-ppi). MIT License.
// Tested in tests/test_m11_demos.py.
import { ppiMinusTcl } from "./m11-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Entrainment from a pacing site connected to a reentrant circuit by a path of length d. After pacing stops, the " +
        "last paced wave travels to the circuit, goes once around it and comes back, so the post-pacing interval " +
        "exceeds the tachycardia cycle length by the round trip 2d/CV. On the circuit itself the difference is about zero.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Post-pacing interval minus cycle length against distance from the circuit" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dS = addSlider(controls, { id: "m11-d2-d", label: "Distance from pacing site to circuit", min: 0, max: 40, step: 1, value: 10, digits: 0, unit: "mm", onInput: draw });
  const vS = addSlider(controls, { id: "m11-d2-cv", label: "Conduction velocity along the path", min: 0.2, max: 1.5, step: 0.05, value: 0.5, digits: 2, unit: "m/s", onInput: draw });

  function draw() {
    const d = Number(dS.value);
    const v = Number(vS.value);
    const ds = Array.from({ length: 41 }, (_, i) => i);
    drawPlot(cv, {
      xRange: [0, 40],
      yRange: [0, 400],
      xLabel: "distance from the circuit d (mm)",
      yLabel: "PPI − TCL (ms)",
      series: [{ x: ds, y: ds.map((x) => ppiMinusTcl(x, v)), color: COLORS.blue, width: 2, label: "2d / CV" }],
      markers: [{ x: d, y: ppiMinusTcl(d, v), color: COLORS.vermillion }],
    });
    readout.textContent =
      `d = ${d} mm at ${v.toFixed(2)} m/s: PPI − TCL = ${ppiMinusTcl(d, v).toFixed(0)} ms. ` +
      "Slowing in the circuit during pacing adds to this (lab part E).";
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m11-d2-root");
if (root) mount(root);
