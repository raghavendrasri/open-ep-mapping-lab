// m14-d1 · A common-mode rejection budget (eq-m14-diffamp, eq-m14-inamp, eq-m14-imbalance). MIT License.
// Tested in tests/test_m14_demos.py.
import { combinedCmrr, imbalanceCmrr, toDb, worstCaseCmrr } from "./m14-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "How much common-mode voltage leaks into the recorded difference. Gray: the amplifier, an input stage of gain G1 " +
        "followed by a gain-10 difference stage with resistor tolerance as set. Orange: the electrode impedance mismatch " +
        "into the amplifier's common-mode input impedance. Blue: both together, worst case. Higher is better; the weaker " +
        "path sets the total.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "CMRR against electrode impedance mismatch" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dzS = addSlider(controls, { id: "m14-d1-dz", label: "Electrode impedance mismatch", min: 0.5, max: 50, step: 0.5, value: 10, digits: 1, unit: "kΩ", onInput: draw });
  const zS = addSlider(controls, { id: "m14-d1-zcm", label: "Common-mode input impedance, log₁₀ (Ω)", min: 6, max: 11, step: 0.1, value: 8, digits: 1, onInput: draw });
  const tS = addSlider(controls, { id: "m14-d1-tol", label: "Resistor tolerance", min: 0.01, max: 1, step: 0.01, value: 0.1, digits: 2, unit: "%", onInput: draw });
  const gS = addSlider(controls, { id: "m14-d1-g1", label: "Input-stage gain G1", min: 1, max: 100, step: 1, value: 10, digits: 0, onInput: draw });

  function draw() {
    const zcm = 10 ** Number(zS.value), tol = Number(tS.value) / 100, g1 = Number(gS.value);
    const amp = g1 * worstCaseCmrr(10, tol);
    const xs = [], yAmp = [], yImb = [], yTot = [];
    for (let dz = 0.5; dz <= 50.0001; dz += 0.5) {
      xs.push(dz);
      const imb = imbalanceCmrr(dz * 1e3, zcm);
      yAmp.push(toDb(amp)); yImb.push(toDb(imb)); yTot.push(toDb(combinedCmrr(amp, imb)));
    }
    const dz = Number(dzS.value);
    const imb = imbalanceCmrr(dz * 1e3, zcm), tot = combinedCmrr(amp, imb);
    drawPlot(cv, {
      xRange: [0, 50], yRange: [40, 140], xLabel: "electrode impedance mismatch (kΩ)", yLabel: "CMRR (dB)",
      series: [
        { x: xs, y: yAmp, color: COLORS.gray, width: 2, label: "amplifier" },
        { x: xs, y: yImb, color: COLORS.orange, width: 2, label: "electrode mismatch" },
        { x: xs, y: yTot, color: COLORS.blue, width: 3, label: "total" },
      ],
      markers: [{ x: dz, y: toDb(tot), color: COLORS.blue }],
    });
    readout.textContent =
      `At ${dz.toFixed(1)} kΩ mismatch: amplifier ${toDb(amp).toFixed(0)} dB, mismatch ${toDb(imb).toFixed(0)} dB, ` +
      `total ${toDb(tot).toFixed(0)} dB, so 1 V of common mode leaks as ${(1e6 / tot).toFixed(1)} µV.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m14-d1-root");
if (root) mount(root);
