// m17-d2 · Distortion of a grid by a uniform-field assumption (eq-m17-pair, eq-m17-linear). MIT License.
// Tested in tests/test_m17_demos.py.
import { linearEstimate, patchPairs, potentials } from "./m17-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A square grid in the plane between two orthogonal patch pairs (gray) and where a uniform-field map reports it " +
        "(blue). Patches sit at ±d on each axis of an unbounded homogeneous medium. The grid swells toward the patches " +
        "and bends between them; this is the distortion that field scaling corrects.",
    ),
  );
  const cv = setupCanvas(root, { width: 460, height: 420, label: "True and reported grid" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const wS = addSlider(controls, { id: "m17-d2-w", label: "Grid half-width", min: 20, max: 100, step: 5, value: 60, digits: 0, unit: "mm", onInput: draw });
  const dS = addSlider(controls, { id: "m17-d2-d", label: "Patch half-separation d", min: 120, max: 300, step: 5, value: 200, digits: 0, unit: "mm", onInput: draw });

  function draw() {
    const w = Number(wS.value), d = Number(dS.value), P = patchPairs(d);
    const map = (x, y) => potentials([x, y, 0], P).map((p) => linearEstimate(p, d));
    const series = [];
    let worst = 0;
    const n = 6, ticks = Array.from({ length: n + 1 }, (_, i) => -w + (2 * w * i) / n);
    for (const c of ticks) {
      const tx = [], ty = [], rx = [], ry = [], sx = [], sy = [], qx = [], qy = [];
      for (let i = 0; i <= 40; i++) {
        const t = -w + (2 * w * i) / 40;
        tx.push(c); ty.push(t); sx.push(t); sy.push(c);
        const a = map(c, t), b = map(t, c);
        rx.push(a[0]); ry.push(a[1]); qx.push(b[0]); qy.push(b[1]);
        worst = Math.max(worst, Math.hypot(a[0] - c, a[1] - t));
      }
      series.push({ x: tx, y: ty, color: COLORS.gray, width: 1 }, { x: sx, y: sy, color: COLORS.gray, width: 1 });
      series.push({ x: rx, y: ry, color: COLORS.blue, width: 1.8 }, { x: qx, y: qy, color: COLORS.blue, width: 1.8 });
    }
    const lim = 1.5 * w;
    drawPlot(cv, { xRange: [-lim, lim], yRange: [-lim, lim], xLabel: "x (mm)", yLabel: "y (mm)", series });
    readout.textContent = `Largest position error on the grid: ${worst.toFixed(1)} mm (${((100 * worst) / w).toFixed(0)}% of the half-width).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m17-d2-root");
if (root) mount(root);
