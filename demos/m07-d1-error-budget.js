// m07-d1 · The error budget of Tikhonov regularization (eq-m07-error). MIT License. Tested in tests/test_m07_demos.py.
import { WIDTH, dft, expectedError, gain, grid, norm, tissueProfile } from "./m07-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "The expected error of a Tikhonov reconstruction of tissue-level potentials from potentials recorded a height h " +
        "above the tissue, against the regularization parameter lambda. Blue: bias, the detail the filter removes. " +
        "Green: noise passed through the inverse. Orange: their total. Small lambda lets noise through; large lambda " +
        "smooths away the fronts. The dot marks the best lambda.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Relative error against lambda, both on log scales" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const height = addSlider(controls, { id: "m07-d1-height", label: "Electrode height above the tissue", min: 0.25, max: 3, step: 0.05, value: 1, digits: 2, unit: "mm", onInput: draw });
  const noise = addSlider(controls, { id: "m07-d1-noise", label: "Noise (log10 of fraction of the recorded peak)", min: -4, max: -1, step: 0.05, value: -2, digits: 2, onInput: draw });

  const { s, k } = grid();
  const x = tissueProfile(s, WIDTH);
  const X = dft(x);
  const X2 = Array.from(X.re, (v, m) => v * v + X.im[m] * X.im[m]);
  const xn = norm(x);
  const lams = Array.from({ length: 241 }, (_, i) => 10 ** (-6 + i * 0.025));

  function draw() {
    const h = Number(height.value);
    const g = gain(k, h);
    const recorded = tissueProfile(s, WIDTH + h);
    const sigma = 10 ** Number(noise.value) * Math.max(...recorded.map(Math.abs));
    const e = lams.map((lam) => expectedError(X2, g, sigma, lam));
    const lg = (v) => Math.log10(Math.sqrt(v) / xn);
    const lx = lams.map(Math.log10);
    let best = 0;
    e.forEach((v, i) => {
      if (v.total < e[best].total) best = i;
    });
    drawPlot(cv, {
      xRange: [-6, 0],
      yRange: [-3, 1],
      xLabel: "log10 lambda",
      yLabel: "log10 relative RMS error",
      legendLeft: true,
      series: [
        { x: lx, y: e.map((v) => lg(v.bias)), color: COLORS.blue, label: "bias" },
        { x: lx, y: e.map((v) => lg(v.variance)), color: COLORS.green, label: "noise" },
        { x: lx, y: e.map((v) => lg(v.total)), color: COLORS.orange, width: 3, label: "total" },
      ],
      markers: [{ x: lx[best], y: lg(e[best].total), color: COLORS.ink }],
    });
    const eb = e[best];
    readout.textContent =
      `Best lambda about ${lams[best].toExponential(1)}: expected relative error ${(Math.sqrt(eb.total) / xn).toFixed(2)} ` +
      `(bias ${(Math.sqrt(eb.bias) / xn).toFixed(2)}, noise ${(Math.sqrt(eb.variance) / xn).toFixed(2)}). ` +
      "Raise the height or the noise and the best achievable error grows.";
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m07-d1-root");
if (root) mount(root);
