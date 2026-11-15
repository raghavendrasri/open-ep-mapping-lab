// m18-d2 · Frequency dependence of tissue impedance (eq-m18-dielectric). MIT License.
// Tested in tests/test_m18_demos.py.
import { ILLUSTRATIVE_TISSUES, conductivityMagnitude, impedancePhaseDeg } from "./m18-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Impedance phase against frequency for two illustrative tissues with one relaxation each: a 'blood-like' one " +
        "with high conductivity and little polarization, and a 'wall-like' one with lower conductivity and strong " +
        "polarization. Their difference is small at low frequency and large near the relaxation, which is why measuring " +
        "at several frequencies can tell tissues apart. The parameters are illustrative, not measured.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Impedance phase against frequency" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const fS = addSlider(controls, { id: "m18-d2-f", label: "Frequency, log₁₀ (Hz)", min: 2, max: 7, step: 0.05, value: 5, digits: 2, onInput: draw });
  const B = ILLUSTRATIVE_TISSUES["blood-like"], W = ILLUSTRATIVE_TISSUES["wall-like"];

  function draw() {
    const lf = Number(fS.value), f = 10 ** lf;
    const xs = [], yb = [], yw = [];
    for (let x = 2; x <= 7.0001; x += 0.02) { xs.push(x); yb.push(impedancePhaseDeg(10 ** x, B)); yw.push(impedancePhaseDeg(10 ** x, W)); }
    drawPlot(cv, {
      xRange: [2, 7], yRange: [-25, 1], xLabel: "log₁₀ frequency (Hz)", yLabel: "impedance phase (degrees)",
      series: [
        { x: xs, y: yb, color: COLORS.vermillion, width: 2.5, label: "blood-like" },
        { x: xs, y: yw, color: COLORS.blue, width: 2.5, label: "wall-like" },
        { x: [lf, lf], y: [-25, 1], color: COLORS.gray, width: 1.2, dash: [5, 4] },
      ],
    });
    const pb = impedancePhaseDeg(f, B), pw = impedancePhaseDeg(f, W);
    readout.textContent =
      `At ${f < 1e3 ? f.toFixed(0) + " Hz" : (f / 1e3).toFixed(1) + " kHz"}: phase ${pb.toFixed(2)}° and ${pw.toFixed(2)}°; ` +
      `conductivity magnitude ratio ${(conductivityMagnitude(f, B) / conductivityMagnitude(f, W)).toFixed(2)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m18-d2-root");
if (root) mount(root);
