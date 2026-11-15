// m15-d2 · Filtering RF ablation energy before the amplifier (eq-m15-rf-filter). MIT License.
// Tested in tests/test_m15_demos.py.
import { lowpassAttenuation, orderNeeded } from "./m15-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Butterworth low-pass responses of orders 1 to 4 on log axes, with the RF ablation frequency (dashed) and the " +
        "attenuation needed to bring the RF at the recording input down to the allowed residual (dotted). Where a curve " +
        "passes below the dotted line at the dashed line, that order is enough.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Low-pass attenuation against frequency" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const fS = addSlider(controls, { id: "m15-d2-f", label: "RF frequency", min: 300, max: 1000, step: 10, value: 500, digits: 0, unit: "kHz", onInput: draw });
  const cS = addSlider(controls, { id: "m15-d2-fc", label: "Filter corner", min: 100, max: 5000, step: 100, value: 500, digits: 0, unit: "Hz", onInput: draw });
  const aS = addSlider(controls, { id: "m15-d2-a", label: "RF amplitude at the input", min: 0.1, max: 50, step: 0.1, value: 10, digits: 1, unit: "V", onInput: draw });
  const rS = addSlider(controls, { id: "m15-d2-r", label: "Allowed residual", min: 0.1, max: 10, step: 0.1, value: 1, digits: 1, unit: "µV", onInput: draw });

  function draw() {
    const f = Number(fS.value) * 1e3, fc = Number(cS.value), amp = Number(aS.value), allowed = Number(rS.value) * 1e-6;
    const colors = [COLORS.gray, COLORS.green, COLORS.blue, COLORS.orange];
    const series = [];
    for (let n = 1; n <= 4; n++) {
      const xs = [], ys = [];
      for (let lf = 1; lf <= 6.0001; lf += 0.02) { xs.push(lf); ys.push(20 * Math.log10(lowpassAttenuation(10 ** lf, fc, n))); }
      series.push({ x: xs, y: ys, color: colors[n - 1], width: 2, label: `order ${n}` });
    }
    const need = 20 * Math.log10(allowed / amp);
    series.push({ x: [Math.log10(f), Math.log10(f)], y: [-200, 0], color: COLORS.ink, width: 1.5, dash: [5, 4] });
    series.push({ x: [1, 6], y: [need, need], color: COLORS.vermillion, width: 1.5, dash: [2, 3] });
    drawPlot(cv, { xRange: [1, 6], yRange: [-200, 10], xLabel: "log₁₀ frequency (Hz)", yLabel: "gain (dB)", series });
    const n = orderNeeded(amp, allowed, f, fc);
    readout.textContent =
      `Needed: ${(-need).toFixed(0)} dB at ${(f / 1e3).toFixed(0)} kHz. Smallest Butterworth order: ${n} ` +
      `(order ${n} gives ${(-20 * Math.log10(lowpassAttenuation(f, fc, n))).toFixed(0)} dB).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m15-d2-root");
if (root) mount(root);
