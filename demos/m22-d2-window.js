// m22-d2 · Window of interest on a macroreentrant circuit (eq-m22-woi). MIT License.
// Tested in tests/test_m22_demos.py.
import { ringActivation, windowLat } from "./m22-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "An idealized reentry: activation travels once around a circuit every cycle at constant speed. Each site " +
        "activates once per cycle, so its time after the reference is defined only up to whole cycles. The window of " +
        "interest picks one copy. Gray: activation times over two cycles. Blue: the times the window assigns. Where " +
        "the window wraps, the earliest and latest sites meet. A window shorter than the cycle leaves sites out.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Assigned local activation time around the circuit" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const sS = addSlider(controls, { id: "m22-d2-start", label: "Window start", min: -300, max: 0, step: 5, value: -150, digits: 0, unit: "ms", onInput: draw });
  const wS = addSlider(controls, { id: "m22-d2-width", label: "Window width", min: 50, max: 400, step: 5, value: 250, digits: 0, unit: "ms", onInput: draw });
  const cS = addSlider(controls, { id: "m22-d2-cl", label: "Cycle length", min: 150, max: 400, step: 5, value: 250, digits: 0, unit: "ms", onInput: draw });
  const L = 100, tStart = -120;

  function draw() {
    const w0 = Number(sS.value), W = Number(wS.value), T = Number(cS.value);
    const series = [];
    for (const k of [-1, 0, 1]) {
      const xs = [], ys = [];
      for (let p = 0; p <= L; p += 0.5) { xs.push(p); ys.push(ringActivation(p, L, T, tStart) + k * T); }
      series.push({ x: xs, y: ys, color: COLORS.gray, width: 1, dash: [4, 3], label: k === 0 ? "activation (any cycle)" : undefined });
    }
    let segx = [], segy = [], prev = NaN, covered = 0, n = 0, jumpAt = null;
    const push = () => { if (segx.length) series.push({ x: segx, y: segy, color: COLORS.blue, width: 3, label: series.some((s) => s.label === "assigned LAT") ? undefined : "assigned LAT" }); segx = []; segy = []; };
    for (let p = 0; p < L; p += 0.25) {
      const v = windowLat(ringActivation(p, L, T, tStart), w0, W, T);
      n++;
      if (Number.isNaN(v)) { push(); prev = NaN; continue; }
      covered++;
      if (!Number.isNaN(prev) && Math.abs(v - prev) > T / 2) { push(); jumpAt = p; }
      segx.push(p); segy.push(v); prev = v;
    }
    push();
    series.push({ x: [0, L], y: [w0, w0], color: COLORS.vermillion, width: 1.2, dash: [6, 4], label: "window" });
    series.push({ x: [0, L], y: [w0 + W, w0 + W], color: COLORS.vermillion, width: 1.2, dash: [6, 4] });
    drawPlot(cv, { xRange: [0, L], yRange: [-420, 420], xLabel: "position around the circuit (% of its length)", yLabel: "time after reference (ms)", series });
    const pct = (100 * covered) / n;
    readout.textContent =
      `Window ${w0} to ${w0 + W} ms: ${pct.toFixed(1)}% of the circuit annotated` +
      (jumpAt !== null ? `; earliest meets latest at ${jumpAt.toFixed(1)}% of the circuit.` : "; no wrap inside the annotated part.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m22-d2-root");
if (root) mount(root);
