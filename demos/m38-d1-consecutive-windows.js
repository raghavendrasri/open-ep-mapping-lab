// m38-d1 · Requiring k irregular windows in a row: false notifications against missed episodes. MIT License.
import { detectionProbability, expectedRuns } from "./m38-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A wearable judges each window of pulse data as irregular or not, and notifies only after k irregular windows in a row. " +
        "Left: expected false notifications per day in regular rhythm. Right: chance of catching an AF episode of the chosen length. " +
        "Both against k; the marker is the chosen k.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const left = setupCanvas(row, { width: 320, height: 270, label: "False notifications per day versus k" });
  const right = setupCanvas(row, { width: 320, height: 270, label: "Probability of catching an AF episode versus k" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const k = addSlider(controls, { id: "m38-d1-k", label: "Windows in a row, k", min: 1, max: 15, step: 1, value: 4, digits: 0, onInput: draw });
  const q = addSlider(controls, { id: "m38-d1-q", label: "False irregular window rate, q", min: 0.005, max: 0.3, step: 0.005, value: 0.05, digits: 3, onInput: draw });
  const p = addSlider(controls, { id: "m38-d1-p", label: "Irregular window rate in AF, p", min: 0.3, max: 0.99, step: 0.01, value: 0.8, onInput: draw });
  const win = addSlider(controls, { id: "m38-d1-win", label: "Window length", min: 1, max: 15, step: 1, value: 5, digits: 0, unit: "min", onInput: draw });
  const ep = addSlider(controls, { id: "m38-d1-ep", label: "AF episode length", min: 5, max: 240, step: 5, value: 30, digits: 0, unit: "min", onInput: draw });

  const ks = Array.from({ length: 15 }, (_, i) => i + 1);
  function draw() {
    const kv = Number(k.value);
    const qv = Number(q.value);
    const pv = Number(p.value);
    const n = Math.floor(1440 / Number(win.value));
    const L = Math.floor(Number(ep.value) / Number(win.value));
    const falseDay = ks.map((kk) => expectedRuns(n, qv, kk));
    const catchP = ks.map((kk) => detectionProbability(L, pv, kk));
    const floor = 1e-4;
    drawPlot(left, {
      xRange: [1, 15],
      yRange: [Math.log10(floor), Math.log10(Math.max(1, ...falseDay)) + 0.2],
      xLabel: "k (windows in a row)",
      yLabel: "log10 false notifications / day",
      series: [{ x: ks, y: falseDay.map((v) => Math.log10(Math.max(v, floor))), color: COLORS.vermillion }],
      markers: [{ x: kv, y: Math.log10(Math.max(expectedRuns(n, qv, kv), floor)), color: COLORS.ink, label: "chosen k" }],
      margin: { l: 56 },
    });
    drawPlot(right, {
      xRange: [1, 15],
      yRange: [0, 1],
      xLabel: "k (windows in a row)",
      yLabel: "P(episode caught)",
      series: [{ x: ks, y: catchP, color: COLORS.blue }],
      markers: [{ x: kv, y: detectionProbability(L, pv, kv), color: COLORS.ink, label: "chosen k" }],
      margin: { l: 52 },
    });
    const fd = expectedRuns(n, qv, kv);
    readout.textContent =
      `${n} windows a day. With k = ${kv}: about ${fd < 0.01 ? fd.toExponential(1) : fd.toFixed(2)} false notifications a day ` +
      `(${(fd * 365).toFixed(fd * 365 < 10 ? 1 : 0)} a year), and a ${(100 * detectionProbability(L, pv, kv)).toFixed(0)}% chance ` +
      `of catching a ${ep.value}-minute AF episode (${L} windows).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m38-d1-root");
if (root) mount(root);
