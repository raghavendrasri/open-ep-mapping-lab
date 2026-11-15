// m19-d1 · Respiratory gating: duty cycle against residual motion (eq-m19-breathing, eq-m19-gating). MIT License.
// Tested in tests/test_m19_demos.py.
import { breathing, gatingDutyCycle } from "./m19-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A periodic, asymmetric breathing trace (illustrative period 4 s and excursion 12 mm) that spends more time near " +
        "exhale as the shape parameter n grows. Points are accepted only while the heart is within the gating window " +
        "of its end-exhale position (blue). A wider window accepts more of the time but lets more motion through.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Breathing displacement and gated segments" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const wS = addSlider(controls, { id: "m19-d1-w", label: "Gating window", min: 0.5, max: 12, step: 0.5, value: 2, digits: 1, unit: "mm", onInput: draw });
  const nS = addSlider(controls, { id: "m19-d1-n", label: "Shape parameter n", min: 1, max: 4, step: 1, value: 2, digits: 0, onInput: draw });
  const T = 4, b = 12;

  function draw() {
    const w = Number(wS.value), n = Number(nS.value);
    const xs = [], ys = [], gx = [], gy = [];
    const series = [];
    let segx = [], segy = [];
    for (let t = 0; t <= 8.0001; t += 0.01) {
      const z = breathing(t, T, b, n);
      xs.push(t); ys.push(z);
      if (-z <= w) { segx.push(t); segy.push(z); }
      else if (segx.length) { series.push({ x: segx, y: segy, color: COLORS.blue, width: 4 }); segx = []; segy = []; }
    }
    if (segx.length) series.push({ x: segx, y: segy, color: COLORS.blue, width: 4 });
    series.unshift({ x: xs, y: ys, color: COLORS.gray, width: 1.8, label: "displacement" });
    series.push({ x: [0, 8], y: [-w, -w], color: COLORS.vermillion, width: 1.2, dash: [5, 4], label: "window edge" });
    drawPlot(cv, { xRange: [0, 8], yRange: [-13, 1], xLabel: "time (s)", yLabel: "displacement from exhale (mm)", series });
    readout.textContent = `Accepted ${(100 * gatingDutyCycle(w, b, n)).toFixed(0)}% of the time; motion within the window at most ${w.toFixed(1)} mm (of ${b} mm).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m19-d1-root");
if (root) mount(root);
