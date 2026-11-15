// m24-d2 · Isochrones from sparse points by inverse-distance weighting (eq-m24-idw, eq-m24-isochrone). MIT License.
// Tested in tests/test_m24_demos.py.
import { focalTime, idw, isolines, rng } from "./m24-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A focal activation spreads at 1.0 m/s from a point in a 40 × 40 mm patch. Gray: true isochrones (lines of equal " +
        "activation time), evenly spaced. Blue: isochrones of a map interpolated from randomly placed points by " +
        "inverse-distance weighting. Few points or a high power give rings around single points (bull's-eyes) and " +
        "uneven spacing that a reader could mistake for changes in conduction.",
    ),
  );
  const cv = setupCanvas(root, { width: 520, height: 460, label: "True and interpolated isochrones on a square patch" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const nS = addSlider(controls, { id: "m24-d2-n", label: "Number of points", min: 10, max: 300, step: 5, value: 60, digits: 0, onInput: draw });
  const pS = addSlider(controls, { id: "m24-d2-p", label: "IDW power", min: 1, max: 4, step: 0.5, value: 2, digits: 1, onInput: draw });
  const sS = addSlider(controls, { id: "m24-d2-step", label: "Isochrone step", min: 4, max: 16, step: 1, value: 8, digits: 0, unit: "ms", onInput: draw });
  const c = 1.0, W = 40, x0 = 12, y0 = 15, G = 61;

  function draw() {
    const n = Number(nS.value), p = Number(pS.value), step = Number(sS.value);
    const r = rng(24);
    const pts = [], vals = [];
    for (let i = 0; i < n; i++) { const q = [W * r(), W * r()]; pts.push(q); vals.push(focalTime(q[0], q[1], c, x0, y0)); }
    const dx = W / (G - 1);
    const Tt = [], Ti = [];
    let se = 0;
    for (let j = 0; j < G; j++) {
      const rt = [], ri = [];
      for (let i = 0; i < G; i++) {
        const x = i * dx, y = j * dx;
        const t = focalTime(x, y, c, x0, y0), e = idw(pts, vals, [x, y], p);
        rt.push(t); ri.push(e); se += (e - t) ** 2;
      }
      Tt.push(rt); Ti.push(ri);
    }
    const series = [];
    let firstT = true, firstI = true;
    for (let tau = step; tau < 45; tau += step) {
      for (const s of isolines(Tt, 0, 0, dx, dx, tau)) {
        series.push({ x: [s[0][0], s[1][0]], y: [s[0][1], s[1][1]], color: COLORS.gray, width: 1.2, dash: [4, 3], label: firstT ? "true isochrones" : undefined });
        firstT = false;
      }
      for (const s of isolines(Ti, 0, 0, dx, dx, tau)) {
        series.push({ x: [s[0][0], s[1][0]], y: [s[0][1], s[1][1]], color: COLORS.blue, width: 1.8, label: firstI ? "interpolated" : undefined });
        firstI = false;
      }
    }
    drawPlot(cv, {
      xRange: [0, W], yRange: [0, W], xLabel: "x (mm)", yLabel: "y (mm)", series,
      markers: pts.map((q) => ({ x: q[0], y: q[1], color: COLORS.ink, radius: 2 })).concat([{ x: x0, y: y0, color: COLORS.vermillion, radius: 5, label: "source" }]),
    });
    readout.textContent = `${n} points: RMS error of the interpolated map ${Math.sqrt(se / (G * G)).toFixed(2)} ms; ` +
      `true isochrones ${(c * step).toFixed(1)} mm apart.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m24-d2-root");
if (root) mount(root);
