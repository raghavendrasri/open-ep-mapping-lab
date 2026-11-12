// m49-d2 · Time, distance and shielding: relative dose to a person standing near the patient. MIT License.
// relativeStaffDose is tested against Python (tests/test_m49_demos.py).
import { relativeStaffDose } from "./m49-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Scattered radiation spreads from the patient, so the dose to someone nearby falls with the square of " +
        "distance, rises with time and pulse rate, and halves with each half-value layer of shielding. The curve " +
        "is the dose against distance for the other settings; 1 is the reference (1 m, 10 minutes, no shield, " +
        "15 pulses per second).",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 250, label: "Relative staff dose against distance from the patient" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dist = addSlider(controls, { id: "m49-d2-distance", label: "Distance from the patient", min: 0.5, max: 3, step: 0.1, value: 1, digits: 1, unit: "m", onInput: draw });
  const minutes = addSlider(controls, { id: "m49-d2-minutes", label: "Fluoroscopy time", min: 1, max: 60, step: 1, value: 10, digits: 0, unit: "min", onInput: draw });
  const shield = addSlider(controls, { id: "m49-d2-shield", label: "Shielding (half-value layers)", min: 0, max: 4, step: 0.5, value: 0, digits: 1, onInput: draw });
  const rate = addSlider(controls, { id: "m49-d2-rate", label: "Pulse rate", min: 2, max: 30, step: 1, value: 15, digits: 0, unit: "/s", onInput: draw });

  function draw() {
    const d = Number(dist.value);
    const t = Number(minutes.value);
    const s = Number(shield.value);
    const f = Number(rate.value);
    const xs = Array.from({ length: 111 }, (_, i) => 0.25 + (i * 2.75) / 110);
    const ys = xs.map((x) => relativeStaffDose(x, t, s, f));
    const here = relativeStaffDose(d, t, s, f);
    const yMax = Math.max(1.2, ...ys.filter((_, i) => xs[i] >= 0.5)) * 1.05;
    drawPlot(cv, {
      xRange: [0.25, 3], yRange: [0, yMax], xLabel: "distance from the patient (m)", yLabel: "relative dose",
      series: [
        { x: xs, y: ys, color: COLORS.blue, width: 2.5, label: "dose at these settings" },
        { x: [0.25, 3], y: [1, 1], color: COLORS.gray, width: 1.5, dash: [5, 4], label: "reference" },
      ],
      markers: [{ x: d, y: Math.min(here, yMax), color: COLORS.vermillion, radius: 6, label: "you are here" }],
    });
    readout.textContent =
      `At ${d.toFixed(1)} m for ${t} min, ${s.toFixed(1)} half-value layers of shielding and ${f} pulses per second: ` +
      `${here >= 0.1 ? (100 * here).toFixed(0) : (100 * here).toFixed(1)}% of the reference dose.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m49-d2-root");
if (root) mount(root);
