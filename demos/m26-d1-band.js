// m26-d1 · A probabilistic activation profile (eq-m26-gp). MIT License.
// Tested in tests/test_m26_demos.py.
import { gauss, gpPosterior, rng } from "./m26-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Activation along a 60-mm line from a focal source 5 mm off the line, at 1.0 m/s (gray). Points are recorded at " +
        "random places with annotation error (dots). A Gaussian process interpolates them (blue) and gives a band of " +
        "about ±2 SD (dashed), narrow near points and wide in gaps. A good map shows where it is unsure.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Activation time along a line with a Gaussian-process band" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const nS = addSlider(controls, { id: "m26-d1-n", label: "Number of points", min: 3, max: 40, step: 1, value: 10, digits: 0, onInput: draw });
  const sS = addSlider(controls, { id: "m26-d1-s", label: "Per-point error (SD)", min: 0.2, max: 5, step: 0.1, value: 1, digits: 1, unit: "ms", onInput: draw });
  const lS = addSlider(controls, { id: "m26-d1-l", label: "Kernel length scale", min: 2, max: 20, step: 0.5, value: 8, digits: 1, unit: "mm", onInput: draw });
  const c = 1.0, L = 60, s2 = 400;
  const truth = (x) => Math.hypot(x - 20, 5) / c;

  function draw() {
    const n = Number(nS.value), sa = Number(sS.value), ell = Number(lS.value);
    const r = rng(26);
    const X = [], y = [];
    for (let i = 0; i < n; i++) { const x = L * r(); X.push(x); y.push(truth(x) + sa * gauss(r)); }
    const mean = y.reduce((s, v) => s + v, 0) / n;
    const xs = [];
    for (let x = 0; x <= L + 1e-9; x += 0.25) xs.push(x);
    const [mu, vr] = gpPosterior(X, y, xs, ell, s2, sa, mean);
    const up = mu.map((m, i) => m + 1.96 * Math.sqrt(vr[i])), lo = mu.map((m, i) => m - 1.96 * Math.sqrt(vr[i]));
    const tt = xs.map(truth);
    const inside = tt.filter((t, i) => t >= lo[i] && t <= up[i]).length / tt.length;
    const maxSd = Math.max(...vr.map(Math.sqrt));
    drawPlot(cv, {
      xRange: [0, L], yRange: [-20, 80], xLabel: "position along the line (mm)", yLabel: "activation time (ms)",
      series: [
        { x: xs, y: tt, color: COLORS.gray, width: 1.5, dash: [5, 4], label: "truth" },
        { x: xs, y: mu, color: COLORS.blue, width: 2.2, label: "GP mean" },
        { x: xs, y: up, color: COLORS.sky, width: 1.2, dash: [4, 3], label: "±1.96 SD" },
        { x: xs, y: lo, color: COLORS.sky, width: 1.2, dash: [4, 3] },
      ],
      markers: X.map((x, i) => ({ x, y: y[i], color: COLORS.ink, radius: 3 })),
    });
    readout.textContent = `${n} points: truth inside the band along ${(100 * inside).toFixed(1)}% of the line; largest SD ${maxSd.toFixed(2)} ms.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m26-d1-root");
if (root) mount(root);
