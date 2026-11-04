// m35-d3 · Calibration: reliability diagram and Brier score. MIT License.
import { brier, randn, rng, sigmoid } from "./m35-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const N = 6000;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Synthetic outcomes whose true probability is known. The model's predictions are distorted so that " +
        "logit P(y = 1) = α + β logit p̂. The reliability diagram bins the predictions and plots the observed frequency in each bin.",
    ),
  );
  const plot = setupCanvas(root, { width: 640, height: 300, label: "Reliability diagram: observed frequency versus predicted probability" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const beta = addSlider(controls, { id: "m35-d3-beta", label: "Calibration slope β", min: 0.3, max: 2, step: 0.05, value: 0.6, onInput: draw });
  const alpha = addSlider(controls, { id: "m35-d3-alpha", label: "Calibration intercept α", min: -1.5, max: 1.5, step: 0.05, value: 0, onInput: draw });

  const rand = rng(353);
  const z = Float64Array.from({ length: N }, () => 1.5 * randn(rand)); // true logits
  const u = Float64Array.from({ length: N }, () => rand());
  const y = Array.from(z, (zz, i) => (u[i] < sigmoid(zz) ? 1 : 0));

  function draw() {
    const b = Number(beta.value);
    const a = Number(alpha.value);
    const p = Array.from(z, (zz) => sigmoid((zz - a) / b)); // so that z = a + b logit(p)
    const bins = 10;
    const sumP = new Array(bins).fill(0);
    const sumY = new Array(bins).fill(0);
    const cnt = new Array(bins).fill(0);
    p.forEach((pp, i) => {
      const k = Math.min(bins - 1, Math.floor(pp * bins));
      sumP[k] += pp;
      sumY[k] += y[i];
      cnt[k]++;
    });
    const xs = [];
    const ys = [];
    for (let k = 0; k < bins; k++) if (cnt[k] >= 20) {
      xs.push(sumP[k] / cnt[k]);
      ys.push(sumY[k] / cnt[k]);
    }
    const ideal = Array.from(z, sigmoid);
    drawPlot(plot, {
      xRange: [0, 1],
      yRange: [0, 1],
      xLabel: "predicted probability p̂",
      yLabel: "observed frequency",
      series: [
        { x: [0, 1], y: [0, 1], color: COLORS.gray, dash: [4, 4], label: "perfect calibration" },
        { x: xs, y: ys, color: COLORS.vermillion, label: "this model (bins of 0.1)" },
      ],
      markers: xs.map((x, i) => ({ x, y: ys[i], color: COLORS.vermillion })),
      legendLeft: true,
    });
    readout.textContent =
      `Slope ${b.toFixed(2)}, intercept ${a.toFixed(2)}: Brier score ${brier(p, y).toFixed(4)} ` +
      `(${brier(ideal, y).toFixed(4)} with the true probabilities). ` +
      (b < 1 ? "Predictions are too extreme." : b > 1 ? "Predictions are too timid." : "Slope 1.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m35-d3-root");
if (root) mount(root);
