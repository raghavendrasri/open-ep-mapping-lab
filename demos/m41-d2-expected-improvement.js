// m41-d2 · A Gaussian process and expected improvement in one dimension. MIT License.
import { expectedImprovement, gpPosterior } from "./m41-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const XS = [6, 22, 31, 50]; // paced positions along a line (mm), illustrative
const YS = [0.1, 0.45, 0.62, -0.05]; // similarity scores at those positions, illustrative

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Four pacing sites along a 60-mm line with their similarity scores (dots). Top: the Gaussian-process mean with a band of " +
        "two standard deviations. Bottom: expected improvement over the best score so far; the next site is where it peaks.",
    ),
  );
  const top = setupCanvas(root, { width: 640, height: 200, label: "Gaussian-process mean and uncertainty band" });
  const bottom = setupCanvas(root, { width: 640, height: 150, label: "Expected improvement" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const ell = addSlider(controls, { id: "m41-d2-ell", label: "Length scale", min: 2, max: 30, step: 0.5, value: 8, digits: 1, unit: "mm", onInput: draw });
  const sf = addSlider(controls, { id: "m41-d2-sf", label: "Signal scale", min: 0.1, max: 1.0, step: 0.05, value: 0.4, digits: 2, onInput: draw });
  const xi = addSlider(controls, { id: "m41-d2-xi", label: "Required margin ξ", min: 0, max: 0.3, step: 0.01, value: 0, digits: 2, onInput: draw });

  function draw() {
    const xs = Array.from({ length: 241 }, (_, i) => (i * 60) / 240);
    const m = YS.reduce((a, b) => a + b, 0) / YS.length;
    const post = gpPosterior(XS.map((x) => [x]), YS, xs.map((x) => [x]), Number(ell.value), Number(sf.value), 0.01, m);
    const sd = post.variance.map(Math.sqrt);
    const best = Math.max(...YS);
    const ei = post.mu.map((mu, i) => expectedImprovement(mu, sd[i], best, Number(xi.value)));
    let arg = 0;
    ei.forEach((v, i) => {
      if (v > ei[arg]) arg = i;
    });
    drawPlot(top, {
      xRange: [0, 60],
      yRange: [-1, 1.5],
      xLabel: "position (mm)",
      yLabel: "similarity",
      series: [
        { x: xs, y: post.mu, color: COLORS.blue, width: 2, label: "GP mean" },
        { x: xs, y: post.mu.map((v, i) => v + 2 * sd[i]), color: COLORS.sky, width: 1, dash: [4, 3], label: "± 2 SD" },
        { x: xs, y: post.mu.map((v, i) => v - 2 * sd[i]), color: COLORS.sky, width: 1, dash: [4, 3] },
      ],
      markers: XS.map((x, i) => ({ x, y: YS[i], color: COLORS.ink })),
      vlines: [{ x: xs[arg], color: COLORS.vermillion }],
    });
    const eMax = Math.max(...ei, 1e-9);
    drawPlot(bottom, {
      xRange: [0, 60],
      yRange: [0, eMax * 1.15],
      xLabel: "position (mm)",
      yLabel: "EI",
      series: [{ x: xs, y: ei, color: COLORS.vermillion, width: 2 }],
      vlines: [{ x: xs[arg], color: COLORS.vermillion }],
    });
    readout.textContent =
      `Next pacing site at ${xs[arg].toFixed(1)} mm, expected improvement ${ei[arg].toFixed(3)} over the best score ` +
      `${best.toFixed(2)}. Short length scales spread the search; a margin ξ pushes it towards uncertain regions.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m41-d2-root");
if (root) mount(root);
