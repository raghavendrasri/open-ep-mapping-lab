// m42-d2 · Ensemble spread grows where there are no data. MIT License.
import { ensemble1d } from "./m42-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const X0 = 8; // mm, origin of activation (illustrative)
const V = 1.0; // m/s = mm/ms
const XS_ALL = [2, 6, 11, 15, 19, 24, 28, 33, 37, 40, 13, 30]; // measurement positions (mm), illustrative
const NOISE_ALL = [0.6, -0.9, 0.3, 1.1, -0.4, 0.2, -1.2, 0.8, -0.1, 0.5, -0.7, 0.9]; // ms, illustrative

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Activation times along a 60-mm line, measured only between 0 and 40 mm (dots). Each ensemble member fits the " +
        "data with fresh noise and its own fixed random prior function. Thin lines: members; thick line: their mean; " +
        "dashed blue lines: two standard deviations either side of the mean. The true map is dotted.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Ensemble of fitted activation times along a line" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const members = addSlider(controls, { id: "m42-d2-members", label: "Ensemble members", min: 2, max: 30, step: 1, value: 10, digits: 0, onInput: draw });
  const prior = addSlider(controls, { id: "m42-d2-prior", label: "Prior scale", min: 0, max: 8, step: 0.5, value: 4, digits: 1, unit: "ms", onInput: draw });
  const npts = addSlider(controls, { id: "m42-d2-n", label: "Measurement points", min: 4, max: 12, step: 1, value: 8, digits: 0, onInput: draw });

  function draw() {
    const n = Number(npts.value);
    const xs = XS_ALL.slice(0, n);
    const ys = xs.map((x, i) => Math.abs(x - X0) / V + NOISE_ALL[i]);
    const xEval = Array.from({ length: 121 }, (_, i) => i * 0.5);
    const centres = Array.from({ length: 13 }, (_, i) => i * 5);
    const preds = ensemble1d({ xs, ys, xEval, centres, h: 5, ridge: 1e-3, members: Number(members.value), noise: 1.0, priorScale: Number(prior.value), seed: 42 });
    const mean = xEval.map((_, j) => preds.reduce((s, p) => s + p[j], 0) / preds.length);
    const sd = xEval.map((_, j) => Math.sqrt(preds.reduce((s, p) => s + (p[j] - mean[j]) ** 2, 0) / Math.max(preds.length - 1, 1)));
    const truth = xEval.map((x) => Math.abs(x - X0) / V);
    const series = preds.slice(0, 30).map((p) => ({ x: xEval, y: p, color: "#b6c8d9", width: 1 }));
    series.push({ x: xEval, y: mean.map((m, j) => m + 2 * sd[j]), color: COLORS.sky, width: 1.5, dash: [4, 3], label: "mean ± 2 SD" });
    series.push({ x: xEval, y: mean.map((m, j) => m - 2 * sd[j]), color: COLORS.sky, width: 1.5, dash: [4, 3] });
    series.push({ x: xEval, y: mean, color: COLORS.blue, width: 2.5, label: "ensemble mean" });
    series.push({ x: xEval, y: truth, color: COLORS.ink, width: 1.5, dash: [2, 3], label: "true" });
    drawPlot(cv, {
      xRange: [0, 60],
      yRange: [-20, 80],
      xLabel: "position (mm)",
      yLabel: "activation time (ms)",
      series,
      markers: xs.map((x, i) => ({ x, y: ys[i], color: COLORS.vermillion })),
      vlines: [{ x: 40, color: COLORS.gray }],
      legendLeft: true,
    });
    const near = sd.filter((_, j) => xEval[j] <= 40).reduce((a, b) => a + b, 0) / xEval.filter((x) => x <= 40).length;
    const far = sd[sd.length - 1];
    readout.textContent =
      `Mean spread where there are data: ${near.toFixed(1)} ms; at 60 mm, 20 mm beyond the last point: ${far.toFixed(1)} ms. ` +
      (Number(prior.value) === 0 ? "With no prior, the spread comes only from the measurement noise." : "The random priors make the members disagree where the data cannot hold them together.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m42-d2-root");
if (root) mount(root);
