// m09-d2 · Spread from a point in anisotropic tissue (eq-m09-anisotropy). MIT License.
// Tested in tests/test_m09_demos.py.
import { raySpeed } from "./m09-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const CV_L = 1.0; // m/s along fibers, as reported for normal-voltage left atrium

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Isochrones every 5 ms around a point stimulus in uniform tissue whose fibers run at the angle you choose. The " +
        "wave is fastest along the fibers, so the isochrones are ellipses. The dashed line is a row of mapping points " +
        "along the horizontal axis: the speed you would measure there depends on the fiber angle.",
    ),
  );
  const cv = setupCanvas(root, { width: 420, height: 400, label: "Elliptical isochrones around a point stimulus" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const angS = addSlider(controls, { id: "m09-d2-angle", label: "Fiber angle", min: 0, max: 180, step: 5, value: 30, digits: 0, unit: "°", onInput: draw });
  const ratS = addSlider(controls, { id: "m09-d2-ratio", label: "Longitudinal / transverse velocity", min: 1, max: 4, step: 0.1, value: 3, digits: 1, onInput: draw });

  function draw() {
    const a = (Number(angS.value) * Math.PI) / 180;
    const cvT = CV_L / Number(ratS.value);
    const series = [];
    for (let t = 5; t <= 25; t += 5) {
      const xs = [], ys = [];
      for (let k = 0; k <= 120; k++) {
        const phi = (2 * Math.PI * k) / 120;
        const xl = CV_L * t * Math.cos(phi), xt = cvT * t * Math.sin(phi);
        xs.push(Math.cos(a) * xl - Math.sin(a) * xt);
        ys.push(Math.sin(a) * xl + Math.cos(a) * xt);
      }
      series.push({ x: xs, y: ys, color: COLORS.blue, width: 1.5, label: t === 5 ? "isochrones, 5 ms apart" : undefined });
    }
    series.push({ x: [-30, 30], y: [0, 0], color: COLORS.vermillion, dash: [5, 4], width: 1.5, label: "mapping line" });
    series.push({ x: [-30 * Math.cos(a), 30 * Math.cos(a)], y: [-30 * Math.sin(a), 30 * Math.sin(a)], color: COLORS.gray, width: 1, label: "fiber direction" });
    drawPlot(cv, { xRange: [-30, 30], yRange: [-28, 28], xLabel: "x (mm)", yLabel: "y (mm)", series });
    const along = raySpeed(a, CV_L, cvT);
    readout.textContent =
      `Along the fibers ${CV_L.toFixed(2)} m/s, across ${cvT.toFixed(2)} m/s. ` +
      `Measured along the horizontal line: ${along.toFixed(2)} m/s.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m09-d2-root");
if (root) mount(root);
