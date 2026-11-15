// m24-d1 · Interpolating across a line of block (eq-m24-linear, eq-m24-idw, eq-m24-block). MIT License.
// Tested in tests/test_m24_demos.py.
import { idw, linear1d } from "./m24-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Activation along a 60-mm line at 1.0 m/s, with a line of block at 30 mm: tissue beyond it is reached later, by " +
        "a detour. Gray: true activation time. Dots: sampled points. Blue: linear interpolation, which turns the jump " +
        "into a steep ramp that looks like very slow conduction. Orange: inverse-distance weighting, which flattens " +
        "around every point.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Activation time along a line with a block, sampled and interpolated" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const hS = addSlider(controls, { id: "m24-d1-h", label: "Point spacing", min: 1, max: 10, step: 0.5, value: 4, digits: 1, unit: "mm", onInput: draw });
  const dS = addSlider(controls, { id: "m24-d1-dt", label: "Detour delay at the block", min: 10, max: 120, step: 5, value: 60, digits: 0, unit: "ms", onInput: draw });
  const pS = addSlider(controls, { id: "m24-d1-p", label: "IDW power", min: 1, max: 4, step: 0.5, value: 2, digits: 1, onInput: draw });
  const c = 1.0, L = 60, xb = 30;

  function draw() {
    const h = Number(hS.value), dT = Number(dS.value), p = Number(pS.value);
    const truth = (x) => x / c + (x > xb ? dT : 0);
    const xd = [], td = [];
    for (let x = h / 2; x <= L; x += h) { xd.push(x); td.push(truth(x)); }
    const xs = [], tt = [], tl = [], ti = [];
    for (let x = 0; x <= L + 1e-9; x += 0.1) {
      xs.push(x); tt.push(truth(x)); tl.push(linear1d(xd, td, x)); ti.push(idw(xd.map((v) => [v]), td, [x], p));
    }
    // gap between the two points that straddle the block
    let k = 0;
    while (xd[k + 1] <= xb) k++;
    const gap = xd[k + 1] - xd[k];
    const vLin = gap / (td[k + 1] - td[k]);
    let maxSlope = 0;
    for (let i = 1; i < xs.length; i++) maxSlope = Math.max(maxSlope, (ti[i] - ti[i - 1]) / (xs[i] - xs[i - 1]));
    const top = L / c + dT + 45;
    drawPlot(cv, {
      xRange: [0, L], yRange: [0, top], xLabel: "position along the line (mm)", yLabel: "activation time (ms)",
      series: [
        { x: xs, y: tt, color: COLORS.gray, width: 1.5, dash: [5, 4], label: "truth" },
        { x: xs, y: tl, color: COLORS.blue, width: 2.2, label: "linear" },
        { x: xs, y: ti, color: COLORS.orange, width: 2, label: "IDW" },
        { x: [xb, xb], y: [0, top], color: COLORS.vermillion, width: 1.2, dash: [2, 3], label: "block" },
      ],
      markers: xd.map((x, i) => ({ x, y: td[i], color: COLORS.ink, radius: 3 })),
    });
    readout.textContent =
      `Across the block, linear interpolation reads ${vLin.toFixed(3)} m/s over ${gap.toFixed(1)} mm, though nothing ` +
      `conducts there; IDW's steepest slope reads ${(1 / maxSlope).toFixed(3)} m/s.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m24-d1-root");
if (root) mount(root);
