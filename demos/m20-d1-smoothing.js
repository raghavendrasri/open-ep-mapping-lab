// m20-d1 · Laplacian against Taubin smoothing (eq-m20-smoothing). MIT License.
// Tested in tests/test_m20_demos.py.
import { polygonFactor, rng, umbrellaStep } from "./m20-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A noisy closed outline of 64 vertices around a 20 mm circle (gray), smoothed by repeatedly moving each vertex " +
        "toward the mean of its two neighbors (orange, Laplacian) or by alternating a shrinking and an inflating step " +
        "(blue, Taubin). Both remove the noise; only Laplacian smoothing also shrinks the shape.",
    ),
  );
  const cv = setupCanvas(root, { width: 440, height: 420, label: "Noisy outline and two smoothed versions" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const kS = addSlider(controls, { id: "m20-d1-k", label: "Smoothing iterations", min: 0, max: 200, step: 5, value: 40, digits: 0, onInput: draw });
  const lS = addSlider(controls, { id: "m20-d1-lam", label: "Step size λ (Taubin μ = −λ − 0.03)", min: 0.1, max: 0.9, step: 0.05, value: 0.5, digits: 2, onInput: draw });
  const n = 64, r0 = rng(20);
  const P0 = Array.from({ length: n }, (_, i) => {
    const t = (2 * Math.PI * i) / n, rr = 20 + 1.5 * (2 * r0() - 1);
    return [rr * Math.cos(t), rr * Math.sin(t)];
  });

  function draw() {
    const k = Number(kS.value), lam = Number(lS.value), mu = -lam - 0.03;
    let L = P0, T = P0;
    for (let i = 0; i < k; i++) { L = umbrellaStep(L, lam); T = umbrellaStep(umbrellaStep(T, lam), mu); }
    const close = (P) => ({ x: [...P.map((p) => p[0]), P[0][0]], y: [...P.map((p) => p[1]), P[0][1]] });
    const meanR = (P) => P.reduce((s, [x, y]) => s + Math.hypot(x, y), 0) / P.length;
    drawPlot(cv, {
      xRange: [-26, 26], yRange: [-26, 26], xLabel: "x (mm)", yLabel: "y (mm)",
      series: [
        { ...close(P0), color: COLORS.gray, width: 1.2, label: "noisy" },
        { ...close(L), color: COLORS.orange, width: 2.2, label: "Laplacian" },
        { ...close(T), color: COLORS.blue, width: 2.2, label: "Taubin" },
      ],
    });
    readout.textContent =
      `After ${k} iterations: mean radius ${meanR(L).toFixed(2)} mm (Laplacian) and ${meanR(T).toFixed(2)} mm (Taubin), from ` +
      `${meanR(P0).toFixed(2)} mm. Per step a regular 64-gon keeps ${polygonFactor(n, lam).toFixed(4)} and ${polygonFactor(n, lam, mu).toFixed(4)} of its radius.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m20-d1-root");
if (root) mount(root);
