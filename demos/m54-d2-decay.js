// m54-d2 · Decay and scan timing for fluorine-18 (eq-m54-decay). MIT License. Tested in tests/test_m54_demos.py.
import { F18_HALF_LIFE_MIN, activity, clockErrorBias } from "./m54-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Fluorine-18 halves every 109.73 minutes. The curve is the fraction of the injected activity left in the " +
        "body (ignoring excretion) against time. SUV divides by the injected activity corrected for this decay, so " +
        "a clock error in the injection or scan time becomes an error in SUV.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 230, label: "Fraction of fluorine-18 activity remaining against time" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const uptake = addSlider(controls, { id: "m54-d2-uptake", label: "Time from injection to scan", min: 30, max: 180, step: 5, value: 60, digits: 0, unit: "min", onInput: draw });
  const err = addSlider(controls, { id: "m54-d2-clock", label: "Clock error", min: -20, max: 20, step: 1, value: 10, digits: 0, unit: "min", onInput: draw });
  const ts = Array.from({ length: 361 }, (_, i) => i);

  function draw() {
    const t = Number(uptake.value);
    const e = Number(err.value);
    drawPlot(cv, {
      xRange: [0, 360],
      yRange: [0, 1.05],
      xLabel: "time since injection (min)",
      yLabel: "activity remaining (fraction)",
      series: [{ x: ts, y: ts.map((v) => activity(1, v)), color: COLORS.blue, label: "fluorine-18" }],
      vlines: [
        { x: F18_HALF_LIFE_MIN, color: COLORS.gray, dash: [2, 3] },
        { x: t, color: COLORS.vermillion, dash: [5, 3] },
      ],
      markers: [{ x: t, y: activity(1, t), color: COLORS.vermillion }],
    });
    const bias = clockErrorBias(e);
    readout.textContent =
      `At ${t} min, ${(100 * activity(1, t)).toFixed(0)}% of the injected activity remains (dotted line: one half-life). ` +
      `A ${Math.abs(e)}-min clock error ${e >= 0 ? "overstates" : "understates"} the elapsed time and biases SUV by ` +
      `${bias >= 0 ? "+" : ""}${(100 * bias).toFixed(1)}%.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m54-d2-root");
if (root) mount(root);
