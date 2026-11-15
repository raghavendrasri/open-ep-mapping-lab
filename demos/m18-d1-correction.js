// m18-d1 · Correcting impedance coordinates with magnetic reference points (eq-m18-affine, eq-m18-rbf). MIT License.
// Tested in tests/test_m18_demos.py.
import { applyAffine, applyRbf, fitAffine, fitRbf, impedanceCoordinates, rng } from "./m18-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A slice through a chamber (gray grid, the truth). Orange: where an impedance system reports it, with the m17 " +
        "nonlinearity and illustrative per-axis scale errors. Dots: points where a magnetic sensor gave the true " +
        "position as well. Blue: the grid after a smooth correction (Gaussian radial basis functions plus an affine " +
        "part) fitted to those points.",
    ),
  );
  const cv = setupCanvas(root, { width: 460, height: 420, label: "True, reported and corrected grids" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const nS = addSlider(controls, { id: "m18-d1-n", label: "Magnetic reference points", min: 5, max: 120, step: 1, value: 40, digits: 0, onInput: draw });
  const sS = addSlider(controls, { id: "m18-d1-s", label: "Basis-function width", min: 10, max: 60, step: 1, value: 30, digits: 0, unit: "mm", onInput: draw });

  function draw() {
    const n = Number(nS.value), scale = Number(sS.value), R = 45, r = rng(18);
    const cal = [];
    while (cal.length < n) {
      const x = (2 * r() - 1) * R, y = (2 * r() - 1) * R;
      if (x * x + y * y <= R * R) cal.push([x, y]);
    }
    const imp = (p) => impedanceCoordinates([p[0], p[1], 0]).slice(0, 2);
    const u = cal.map(imp);
    const aff = fitAffine(u, cal), rbf = fitRbf(u, cal, scale, 1e-6);
    const series = [];
    let eRaw = 0, eAff = 0, eRbf = 0, cnt = 0;
    const ticks = [-40, -30, -20, -10, 0, 10, 20, 30, 40];
    for (const c of ticks) {
      for (const dir of [0, 1]) {
        const tru = [], ur = [];
        for (let i = 0; i <= 30; i++) {
          const t = -40 + (80 * i) / 30, p = dir ? [c, t] : [t, c];
          if (p[0] * p[0] + p[1] * p[1] > R * R) continue;
          tru.push(p); ur.push(imp(p));
        }
        if (tru.length < 2) continue;
        const ua = applyAffine(aff, ur), ub = applyRbf(rbf, ur);
        tru.forEach((p, i) => {
          eRaw += (ur[i][0] - p[0]) ** 2 + (ur[i][1] - p[1]) ** 2;
          eAff += (ua[i][0] - p[0]) ** 2 + (ua[i][1] - p[1]) ** 2;
          eRbf += (ub[i][0] - p[0]) ** 2 + (ub[i][1] - p[1]) ** 2;
          cnt++;
        });
        series.push({ x: tru.map((p) => p[0]), y: tru.map((p) => p[1]), color: COLORS.gray, width: 1 });
        series.push({ x: ur.map((p) => p[0]), y: ur.map((p) => p[1]), color: COLORS.orange, width: 1.2 });
        series.push({ x: ub.map((p) => p[0]), y: ub.map((p) => p[1]), color: COLORS.blue, width: 1.8 });
      }
    }
    drawPlot(cv, { xRange: [-60, 60], yRange: [-60, 60], xLabel: "x (mm)", yLabel: "y (mm)", series, markers: cal.map(([x, y]) => ({ x, y, color: COLORS.ink })) });
    const f = (e) => Math.sqrt(e / cnt).toFixed(3);
    readout.textContent = `With ${n} reference points, RMS error on the grid: reported ${f(eRaw)} mm, affine correction ${f(eAff)} mm, smooth correction ${f(eRbf)} mm.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m18-d1-root");
if (root) mount(root);
