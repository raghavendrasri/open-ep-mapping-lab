// m07-d2 · Deblurring one noisy record (eq-m07-continuation, eq-m07-filters, eq-m07-choice). MIT License.
// Tested in tests/test_m07_demos.py.
import { LENGTH, N, WIDTH, filterReal, gain, grid, norm, normals, tikhonov, tissueProfile } from "./m07-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Three activation fronts on the tissue surface (dashed), two of them 3 mm apart. Blue: the potential recorded a " +
        "height h above the tissue, plus noise. Orange: the Tikhonov reconstruction of the tissue-level potential for " +
        "the lambda you choose. Too small a lambda amplifies noise; too large a lambda merges the close fronts.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Tissue-level, recorded and reconstructed potentials" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const lamS = addSlider(controls, { id: "m07-d2-lambda", label: "Regularization (log10 lambda)", min: -5, max: 0, step: 0.05, value: -2, digits: 2, onInput: draw });
  const height = addSlider(controls, { id: "m07-d2-height", label: "Electrode height above the tissue", min: 0.25, max: 3, step: 0.05, value: 1, digits: 2, unit: "mm", onInput: draw });
  const noise = addSlider(controls, { id: "m07-d2-noise", label: "Noise (log10 of fraction of the recorded peak)", min: -4, max: -1, step: 0.05, value: -2, digits: 2, onInput: draw });

  const { s, k } = grid();
  const x = tissueProfile(s, WIDTH);
  const z = normals(N, 7);
  const xn = norm(x);

  function draw() {
    const h = Number(height.value);
    const lam = 10 ** Number(lamS.value);
    const clean = tissueProfile(s, WIDTH + h);
    const sigma = 10 ** Number(noise.value) * Math.max(...clean.map(Math.abs));
    const b = clean.map((v, i) => v + sigma * z[i]);
    const g = gain(k, h);
    const xr = tikhonov(b, g, lam);
    const re = norm(xr.map((v, i) => v - x[i])) / xn;
    const resid = norm(filterReal(xr, g).map((v, i) => v - b[i]));
    const ss = Array.from(s);
    drawPlot(cv, {
      xRange: [0, LENGTH],
      yRange: [-2.5, 2.5],
      xLabel: "position along the tissue (mm)",
      yLabel: "potential (relative)",
      series: [
        { x: ss, y: Array.from(x), color: COLORS.ink, dash: [5, 4], width: 1.5, label: "tissue (truth)" },
        { x: ss, y: Array.from(b), color: COLORS.blue, width: 1.5, label: "recorded" },
        { x: ss, y: Array.from(xr), color: COLORS.vermillion, width: 2, label: "reconstruction" },
      ],
    });
    const ratio = resid / (sigma * Math.sqrt(N));
    readout.textContent =
      `Relative error ${re.toFixed(2)}. Residual ${ratio.toFixed(2)} times the expected noise norm ` +
      `(the discrepancy principle picks the lambda where this is 1).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m07-d2-root");
if (root) mount(root);
