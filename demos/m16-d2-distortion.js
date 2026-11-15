// m16-d2 · Position bias from a nearby conductor (eq-m16-distortion). MIT License.
// Tested in tests/test_m16_demos.py.
import { distortedReadings, generator, linearBias, readings } from "./m16-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Top view of sensor positions 150 mm above an illustrative generator. A small conductor (orange dot) responds to " +
        "each generator coil with an induced dipole that the pose solver does not model. Arrows show the first-order " +
        "position error, magnified ×200, at each grid point. Move the conductor or change its strength.",
    ),
  );
  const cv = setupCanvas(root, { width: 460, height: 420, label: "Position bias vectors in the horizontal plane" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const aS = addSlider(controls, { id: "m16-d2-alpha", label: "Conductor strength (induced moment per field)", min: 0, max: 5000, step: 100, value: 2000, digits: 0, onInput: draw });
  const xS = addSlider(controls, { id: "m16-d2-x", label: "Conductor x", min: -150, max: 150, step: 5, value: 60, digits: 0, unit: "mm", onInput: draw });
  const zS = addSlider(controls, { id: "m16-d2-z", label: "Conductor height", min: 200, max: 400, step: 10, value: 250, digits: 0, unit: "mm", onInput: draw });
  const gen = generator();

  function draw() {
    const alpha = Number(aS.value), c = [Number(xS.value), 0, Number(zS.value)];
    const series = [];
    let worst = 0;
    for (let gx = -80; gx <= 80; gx += 40) {
      for (let gy = -80; gy <= 80; gy += 40) {
        const q = [gx, gy, 150, 0.6, 1.1];
        const v = readings(q, gen), d = distortedReadings(q, gen, c, alpha);
        const b = linearBias(q, gen, d.map((x, k) => x - v[k]));
        worst = Math.max(worst, Math.hypot(b[0], b[1], b[2]));
        series.push({ x: [gx, gx + 200 * b[0]], y: [gy, gy + 200 * b[1]], color: COLORS.blue, width: 2 });
      }
    }
    drawPlot(cv, {
      xRange: [-160, 160], yRange: [-160, 160], xLabel: "x (mm)", yLabel: "y (mm)", series,
      markers: [{ x: c[0], y: c[1], color: COLORS.orange, label: "conductor" }],
    });
    readout.textContent = `Largest position error on the grid: ${worst.toFixed(3)} mm (conductor ${c[2] - 150} mm above the sensor plane).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m16-d2-root");
if (root) mount(root);
