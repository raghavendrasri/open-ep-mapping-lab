// m25-d2 · Velocity from one clique of electrodes (eq-m25-omnipolar). MIT License.
// Tested in tests/test_m25_demos.py.
import { cliqueVelocity } from "./m25-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A plane wave at 1.0 m/s crosses a cross-shaped clique: a center electrode gives the time derivative of the " +
        "potential, and four electrodes at ±d/2 give its gradient by differences. Their ratio estimates the velocity " +
        "without any activation times. With the true gradient the estimate is exact; with a finite clique it reads " +
        "fast, more so for wider spacing or an electrode closer to the tissue.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Estimated over true speed against clique spacing" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const hS = addSlider(controls, { id: "m25-d2-h", label: "Electrode height above tissue", min: 0.2, max: 4, step: 0.1, value: 1, digits: 1, unit: "mm", onInput: draw });
  const tS = addSlider(controls, { id: "m25-d2-th", label: "Propagation angle to the clique axis", min: 0, max: 45, step: 1, value: 20, digits: 0, unit: "°", onInput: draw });
  const dS = addSlider(controls, { id: "m25-d2-d", label: "Clique spacing", min: 0.2, max: 6, step: 0.1, value: 2, digits: 1, unit: "mm", onInput: draw });
  const c = 1.0, w = 0.3;

  function draw() {
    const a = w + Number(hS.value), th = (Number(tS.value) * Math.PI) / 180, d0 = Number(dS.value);
    const ds = [], ratio = [];
    for (let d = 0.2; d <= 6.0001; d += 0.05) {
      const v = cliqueVelocity(c, th, a, d);
      ds.push(d); ratio.push(Math.hypot(v[0], v[1]) / c);
    }
    const v0 = cliqueVelocity(c, th, a, d0);
    const r0 = Math.hypot(v0[0], v0[1]) / c;
    const angErr = ((Math.atan2(v0[1], v0[0]) - th) * 180) / Math.PI;
    const ymax = Math.max(2, Math.max(...ratio) * 1.1);
    drawPlot(cv, {
      xRange: [0, 6], yRange: [0, ymax], xLabel: "clique spacing d (mm)", yLabel: "estimated / true speed",
      series: [
        { x: ds, y: ratio, color: COLORS.blue, width: 2.2, label: "clique estimate" },
        { x: [0, 6], y: [1, 1], color: COLORS.gray, width: 1.2, dash: [5, 4], label: "true" },
      ],
      markers: [{ x: d0, y: r0, color: COLORS.vermillion, radius: 5 }],
    });
    readout.textContent = `At ${d0.toFixed(1)} mm: speed reads ${r0.toFixed(3)} times the truth; direction off by ${angErr.toFixed(2)}°.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m25-d2-root");
if (root) mount(root);
