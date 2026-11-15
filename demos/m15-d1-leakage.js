// m15-d1 · Leakage through isolation capacitance (eq-m15-leakage). MIT License.
// Tested in tests/test_m15_demos.py.
import { SWERDLOW_1999_UA, capacitiveCurrent, maxCapacitance } from "./m15-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Mains-frequency current that can reach a patient through the isolation capacitance of each device connected to " +
        "intracardiac electrodes, if the patient touches ground and all devices see the same mains voltage (worst case: " +
        "the currents add in phase). Dashed lines: the lowest 60-Hz intracardiac currents that caused intermittent " +
        "ventricular capture (20 µA) and fibrillation (49 µA) in 40 patients (Swerdlow et al. 1999).",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Leakage current against isolation capacitance" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const cS = addSlider(controls, { id: "m15-d1-c", label: "Isolation capacitance per device", min: 10, max: 1000, step: 10, value: 200, digits: 0, unit: "pF", onInput: draw });
  const nS = addSlider(controls, { id: "m15-d1-n", label: "Devices connected to the patient", min: 1, max: 6, step: 1, value: 3, digits: 0, onInput: draw });
  const vS = addSlider(controls, { id: "m15-d1-v", label: "Mains voltage (rms)", min: 100, max: 250, step: 5, value: 230, digits: 0, unit: "V", onInput: draw });
  const fS = addSlider(controls, { id: "m15-d1-f", label: "Mains frequency", min: 50, max: 60, step: 10, value: 50, digits: 0, unit: "Hz", onInput: draw });

  function draw() {
    const v = Number(vS.value), f = Number(fS.value), n = Number(nS.value), c = Number(cS.value) * 1e-12;
    const xs = [], ys = [];
    for (let pf = 0; pf <= 1000; pf += 10) { xs.push(pf); ys.push(n * capacitiveCurrent(v, f, pf * 1e-12) * 1e6); }
    const total = n * capacitiveCurrent(v, f, c) * 1e6;
    drawPlot(cv, {
      xRange: [0, 1000], yRange: [0, 200], xLabel: "isolation capacitance per device (pF)", yLabel: "total leakage (µA rms)",
      series: [
        { x: xs, y: ys, color: COLORS.blue, width: 2.5, label: `${n} device${n > 1 ? "s" : ""}` },
        { x: [0, 1000], y: [SWERDLOW_1999_UA.intermittentCapture, SWERDLOW_1999_UA.intermittentCapture], color: COLORS.orange, width: 1.5, dash: [5, 4], label: "20 µA" },
        { x: [0, 1000], y: [SWERDLOW_1999_UA.ventricularFibrillation, SWERDLOW_1999_UA.ventricularFibrillation], color: COLORS.vermillion, width: 1.5, dash: [5, 4], label: "49 µA" },
      ],
      markers: [{ x: Number(cS.value), y: total, color: COLORS.blue }],
    });
    const cmax = maxCapacitance(SWERDLOW_1999_UA.intermittentCapture * 1e-6, v, f) / n;
    readout.textContent =
      `Total leakage ${total.toFixed(1)} µA. To stay below 20 µA with ${n} device${n > 1 ? "s" : ""}, each needs at ` +
      `most ${(cmax * 1e12).toFixed(0)} pF.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m15-d1-root");
if (root) mount(root);
