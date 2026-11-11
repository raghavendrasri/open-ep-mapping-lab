// m45-d1 · Silent drift: a deployed model meets a shifted population, and a CUSUM alarm fires.
// MIT License. Live simulation with a fixed seed; the recursion is tested against Python.
import { cusum, normals } from "./m45-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const DAYS = 120;
const SHIFT_DAY = 60;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Each day the deployed model scores a batch of recordings; the dots are the day's mean score, standardized " +
        "against the validation period (mean 0, standard deviation 1). From day 61 the population changes and the mean " +
        "moves by the chosen shift. The lower panel is the CUSUM statistic; an alarm is raised when it crosses the " +
        "threshold h. No labels are needed, only scores.",
    ),
  );
  const top = setupCanvas(root, { width: 640, height: 200, label: "Daily mean model score, standardized, with the day the population changed" });
  const bottom = setupCanvas(root, { width: 640, height: 200, label: "CUSUM statistic with the alarm threshold" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const shift = addSlider(controls, { id: "m45-d1-shift", label: "Shift after day 60", min: 0, max: 2, step: 0.1, value: 0.8, digits: 1, unit: "SD", onInput: draw });
  const k = addSlider(controls, { id: "m45-d1-k", label: "Allowance k", min: 0, max: 1.5, step: 0.05, value: 0.5, digits: 2, unit: "SD", onInput: draw });
  const h = addSlider(controls, { id: "m45-d1-h", label: "Threshold h", min: 1, max: 15, step: 0.5, value: 5, digits: 1, onInput: draw });
  const noise = normals(DAYS, 2024);

  function draw() {
    const d = Number(shift.value);
    const x = noise.map((z, t) => z + (t >= SHIFT_DAY ? d : 0));
    const { S, alarm } = cusum(x, 0, Number(k.value), Number(h.value));
    const days = x.map((_, t) => t + 1);
    drawPlot(top, {
      xRange: [1, DAYS], yRange: [-4, 5], xLabel: "day", yLabel: "mean score (SD units)",
      series: [], markers: x.map((v, t) => ({ x: t + 1, y: v, color: t >= SHIFT_DAY ? COLORS.vermillion : COLORS.blue, radius: 3 })),
      vlines: [{ x: SHIFT_DAY + 0.5, color: COLORS.gray, label: "population changes" }],
    });
    const yMax = Math.max(Number(h.value) * 1.6, ...S) * 1.05;
    drawPlot(bottom, {
      xRange: [1, DAYS], yRange: [0, yMax], xLabel: "day", yLabel: "CUSUM S",
      series: [
        { x: days, y: S, color: COLORS.blue, width: 2, label: "S" },
        { x: [1, DAYS], y: [Number(h.value), Number(h.value)], color: COLORS.vermillion, width: 1.5, dash: [5, 4], label: "threshold h" },
      ],
      vlines: alarm === null ? [] : [{ x: alarm + 1, color: COLORS.green, label: "alarm" }],
      legendLeft: true,
    });
    if (alarm === null) readout.textContent = `No alarm in ${DAYS} days.` + (d > 0 ? " The shift went undetected: lower h or k." : "");
    else if (alarm < SHIFT_DAY) readout.textContent = `False alarm on day ${alarm + 1}, before the population changed. Raise h to make false alarms rarer.`;
    else readout.textContent = `Alarm on day ${alarm + 1}, ${alarm + 1 - SHIFT_DAY} days after the population changed (shift ${d.toFixed(1)} SD, k = ${Number(k.value).toFixed(2)}, h = ${Number(h.value).toFixed(1)}).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m45-d1-root");
if (root) mount(root);
