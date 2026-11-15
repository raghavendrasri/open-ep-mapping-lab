// m21-d2 · Threshold segmentation of a contrast-filled chamber (eq-m21-threshold, eq-m21-dice). MIT License.
// Tested in tests/test_m21_demos.py.
import { gaussianDice, mixtureHistogram, otsuFromHistogram } from "./m21-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Intensities of tissue (around 100) and contrast-filled blood (adjustable) in an illustrative image, each with " +
        "Gaussian noise, weighted by how much of the image each fills. Gray: the two populations. Blue: the Dice overlap " +
        "of a threshold segmentation with the true blood pool, against threshold. Dashed: Otsu's threshold, which " +
        "maximizes the between-class variance without knowing the truth.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Intensity distributions and Dice against threshold" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const mS = addSlider(controls, { id: "m21-d2-mu1", label: "Blood intensity", min: 150, max: 450, step: 10, value: 350, digits: 0, onInput: draw });
  const sS = addSlider(controls, { id: "m21-d2-sigma", label: "Noise SD", min: 10, max: 120, step: 5, value: 50, digits: 0, onInput: draw });
  const pS = addSlider(controls, { id: "m21-d2-p", label: "Blood fraction of the image", min: 0.05, max: 0.5, step: 0.01, value: 0.2, digits: 2, onInput: draw });

  function draw() {
    const mu0 = 100, mu1 = Number(mS.value), sigma = Number(sS.value), p = Number(pS.value);
    const { hist, centers } = mixtureHistogram(mu0, mu1, sigma, p);
    const t = otsuFromHistogram(hist, centers);
    const xs = [], d0 = [], d1 = [], dc = [];
    let best = 0, bestT = 0;
    for (let x = -100; x <= 700; x += 2) {
      xs.push(x);
      const g = (m) => Math.exp(-0.5 * ((x - m) / sigma) ** 2) / (sigma * Math.sqrt(2 * Math.PI));
      d0.push((1 - p) * g(mu0) * sigma * 2.5); d1.push(p * g(mu1) * sigma * 2.5);
      const dd = gaussianDice(x, mu0, mu1, sigma, p);
      dc.push(dd);
      if (dd > best) { best = dd; bestT = x; }
    }
    drawPlot(cv, {
      xRange: [-100, 700], yRange: [0, 1.05], xLabel: "intensity (relative)", yLabel: "Dice; scaled density",
      series: [
        { x: xs, y: d0, color: COLORS.gray, width: 1.5, label: "tissue" },
        { x: xs, y: d1, color: COLORS.vermillion, width: 1.5, label: "blood" },
        { x: xs, y: dc, color: COLORS.blue, width: 2.5, label: "Dice" },
        { x: [t, t], y: [0, 1.05], color: COLORS.ink, width: 1.5, dash: [5, 4] },
      ],
    });
    readout.textContent = `Otsu threshold ${t.toFixed(0)}, Dice ${gaussianDice(t, mu0, mu1, sigma, p).toFixed(3)}; best possible Dice ${best.toFixed(3)} at ${bestT}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m21-d2-root");
if (root) mount(root);
