// m14-d2 · Noise against source resistance (eq-m14-noise). MIT License.
// Tested in tests/test_m14_demos.py.
import { optimalSourceResistance, thermalDensity, totalDensity } from "./m14-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Input-referred noise density against the source (electrode) resistance, on log scales. Gray: the source's own " +
        "thermal noise at 37 °C. Green: the amplifier's voltage noise. Orange: its current noise flowing through the " +
        "source. Blue: all three in quadrature. Small electrodes have high resistance (m13), which moves you to the right.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Noise density against source resistance" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const rS = addSlider(controls, { id: "m14-d2-rs", label: "Source resistance, log₁₀ (Ω)", min: 2, max: 7, step: 0.05, value: 3.5, digits: 2, onInput: draw });
  const eS = addSlider(controls, { id: "m14-d2-en", label: "Amplifier voltage noise", min: 1, max: 50, step: 1, value: 10, digits: 0, unit: "nV/√Hz", onInput: draw });
  const iS = addSlider(controls, { id: "m14-d2-in", label: "Amplifier current noise, log₁₀ (A/√Hz)", min: -15, max: -11, step: 0.1, value: -13, digits: 1, onInput: draw });
  const bS = addSlider(controls, { id: "m14-d2-bw", label: "Bandwidth", min: 100, max: 2000, step: 50, value: 500, digits: 0, unit: "Hz", onInput: draw });

  function draw() {
    const en = Number(eS.value) * 1e-9, inn = 10 ** Number(iS.value), bw = Number(bS.value);
    const lg = (v) => Math.log10(v * 1e9);    // plot log10 of nV/sqrt(Hz)
    const xs = [], th = [], ev = [], iv = [], tot = [];
    for (let lr = 2; lr <= 7.0001; lr += 0.025) {
      const r = 10 ** lr;
      xs.push(lr); th.push(lg(thermalDensity(r))); ev.push(lg(en)); iv.push(lg(inn * r)); tot.push(lg(totalDensity(r, en, inn)));
    }
    const lr = Number(rS.value), r = 10 ** lr, d = totalDensity(r, en, inn);
    drawPlot(cv, {
      xRange: [2, 7], yRange: [-1, 4], xLabel: "log₁₀ source resistance (Ω)", yLabel: "log₁₀ noise density (nV/√Hz)",
      series: [
        { x: xs, y: th, color: COLORS.gray, width: 2, label: "thermal" },
        { x: xs, y: ev, color: COLORS.green, width: 2, label: "amplifier voltage" },
        { x: xs, y: iv, color: COLORS.orange, width: 2, label: "current × source" },
        { x: xs, y: tot, color: COLORS.blue, width: 3, label: "total" },
      ],
      markers: [{ x: lr, y: lg(d), color: COLORS.blue }],
    });
    readout.textContent =
      `At ${r < 1e4 ? r.toFixed(0) + " Ω" : (r / 1e3).toFixed(0) + " kΩ"}: total ${(d * 1e9).toFixed(1)} nV/√Hz, ` +
      `${(d * Math.sqrt(bw) * 1e6).toFixed(2)} µV rms over ${bw} Hz. Lowest noise factor at ` +
      `${(optimalSourceResistance(en, inn) / 1e3).toFixed(1)} kΩ.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m14-d2-root");
if (root) mount(root);
