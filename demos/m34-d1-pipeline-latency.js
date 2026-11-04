// m34-d1 · Pipeline latency near full load. MIT License.
import { mean, mm1MeanTime, percentile, simulateStage } from "./m34-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "One processing stage with random arrivals, simulated item by item. Top: how long items spend in the stage, " +
        "in units of the mean service time. Bottom: mean time in the stage against load, with the M/M/1 formula.",
    ),
  );
  const top = setupCanvas(root, { width: 640, height: 200, label: "Histogram of latency through one stage" });
  const bottom = setupCanvas(root, { width: 640, height: 200, label: "Mean latency versus load, simulation and M/M/1 formula" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const rho = addSlider(controls, { id: "m34-d1-rho", label: "Load ρ = λ/μ", min: 0.1, max: 0.98, step: 0.02, value: 0.7, onInput: draw });
  const k = addSlider(controls, { id: "m34-d1-k", label: "Service regularity k (1 = random)", min: 1, max: 16, step: 1, value: 1, digits: 0, onInput: draw });
  const cap = addSlider(controls, { id: "m34-d1-cap", label: "Buffer capacity (items)", min: 1, max: 60, step: 1, value: 60, digits: 0, onInput: draw });

  const rhoCurve = Array.from({ length: 90 }, (_, i) => 0.05 + i * 0.01);
  const mm1Curve = rhoCurve.map((r) => mm1MeanTime(r, 1));

  function draw() {
    const r = Number(rho.value);
    const kv = Number(k.value);
    const capacity = Number(cap.value);
    const { latency, dropFraction } = simulateStage({ rho: r, k: kv, capacity });
    const xMax = 30;
    const bins = 60;
    const counts = new Array(bins).fill(0);
    for (const l of latency) counts[Math.min(bins - 1, Math.floor((l / xMax) * bins))]++;
    const xs = [];
    const ys = [];
    counts.forEach((c, i) => {
      const y = c / latency.length / (xMax / bins);
      xs.push((i * xMax) / bins, ((i + 1) * xMax) / bins);
      ys.push(y, y);
    });
    const m = mean(latency);
    const p99 = percentile(latency, 0.99);
    drawPlot(top, {
      xRange: [0, xMax],
      yRange: [0, Math.max(0.2, Math.max(...ys) * 1.1)],
      xLabel: "time in stage (mean service times)",
      yLabel: "density",
      series: [{ x: xs, y: ys, color: COLORS.blue, label: "simulated latency" }],
      vlines: [
        { x: Math.min(m, xMax), color: COLORS.ink, label: "mean" },
        { x: Math.min(p99, xMax), color: COLORS.vermillion, label: "99th percentile" },
      ],
    });
    drawPlot(bottom, {
      xRange: [0, 1],
      yRange: [0, 30],
      xLabel: "load ρ",
      yLabel: "mean time in stage",
      series: [{ x: rhoCurve, y: mm1Curve.map((v) => Math.min(v, 40)), color: COLORS.gray, dash: [5, 4], label: "M/M/1: 1/(1 − ρ)" }],
      markers: [{ x: r, y: Math.min(m, 30), color: COLORS.vermillion, label: "this simulation" }],
      legendLeft: true,
    });
    const formula = capacity >= 60 && kv === 1 ? ` (M/M/1 formula: ${mm1MeanTime(r, 1).toFixed(1)})` : "";
    readout.textContent =
      `Load ${r.toFixed(2)}: mean time in stage ${m.toFixed(1)} service times${formula}; ` +
      `99th percentile ${p99.toFixed(1)}; dropped ${(100 * dropFraction).toFixed(1)}% of items.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m34-d1-root");
if (root) mount(root);
