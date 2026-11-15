// m16-d1 · Position precision against distance from the field generator (eq-m16-crlb, eq-m16-sensitivity). MIT License.
// Tested in tests/test_m16_demos.py.
import { generator, positionSd } from "./m16-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Predicted RMS position error of a single-coil sensor above the center of an illustrative generator (three coil " +
        "trios on a 150 mm circle), against height, on log axes. The gray line has slope 4. Far from the coils the error " +
        "grows at least as the fourth power of distance, because the field falls as the cube; near them it grows more slowly.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Position error against height above the generator" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const nS = addSlider(controls, { id: "m16-d1-noise", label: "Reading noise, log₁₀ (relative)", min: -5, max: -2, step: 0.1, value: -4, digits: 1, onInput: draw });
  const tS = addSlider(controls, { id: "m16-d1-tilt", label: "Sensor tilt from vertical", min: 0, max: 90, step: 5, value: 35, digits: 0, unit: "°", onInput: draw });
  const gen = generator();

  function draw() {
    const sigma = 10 ** Number(nS.value), tilt = (Number(tS.value) * Math.PI) / 180;
    const xs = [], ys = [];
    for (let lz = 2; lz <= 2.8001; lz += 0.02) {
      xs.push(lz);
      ys.push(Math.log10(positionSd([0, 0, 10 ** lz, Math.max(tilt, 1e-3), 1.1], gen, sigma)));
    }
    const ref = ys[0];
    drawPlot(cv, {
      xRange: [2, 2.8], yRange: [-3, 4], xLabel: "log₁₀ height above the generator (mm)", yLabel: "log₁₀ RMS position error (mm)",
      series: [
        { x: xs, y: ys, color: COLORS.blue, width: 2.5, label: "predicted error" },
        { x: [2, 2.8], y: [ref, ref + 4 * 0.8], color: COLORS.gray, width: 1.5, dash: [5, 4], label: "slope 4" },
      ],
    });
    const at = (z) => positionSd([0, 0, z, Math.max(tilt, 1e-3), 1.1], gen, sigma);
    readout.textContent = `RMS position error: ${at(150).toFixed(2)} mm at 150 mm, ${at(300).toFixed(2)} mm at 300 mm (×${(at(300) / at(150)).toFixed(0)}).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m16-d1-root");
if (root) mount(root);
