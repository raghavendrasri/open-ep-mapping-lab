// m05-d2 · Hilbert phase: one turn per activation? (eq-m05-analytic). MIT License. Tested in tests/test_m05_demos.py.
import { analytic, makeSignal, unwrappedPhase } from "./m05-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const FS = 1000;
const T = 4;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Top: a 4-second synthetic signal with one activation per cycle. Bottom: the unwrapped phase of its analytic " +
        "signal, in turns, against the number of activations so far (dashed). For a sinusoid the phase turns once per " +
        "cycle. For electrogram-like signals it may not: an extra deflection or noise adds turns.",
    ),
  );
  const cvX = setupCanvas(root, { width: 640, height: 180, label: "Signal" });
  const cvP = setupCanvas(root, { width: 640, height: 200, label: "Phase turns against activations" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const cycle = addSlider(controls, { id: "m05-d2-cycle", label: "Cycle length", min: 120, max: 300, step: 5, value: 180, digits: 0, unit: "ms", onInput: draw });
  const kind = addSelect(controls, {
    id: "m05-d2-kind",
    label: "Signal",
    options: [
      { value: "sine", label: "sinusoid" },
      { value: "single", label: "one biphasic deflection per cycle" },
      { value: "double", label: "two deflections per cycle (double potential)" },
      { value: "noisy", label: "one deflection per cycle plus noise" },
    ],
    value: "double",
    onChange: draw,
  });

  function draw() {
    const cl = Number(cycle.value) / 1000;
    const { t, x, activations } = makeSignal(kind.value, FS, T, cl);
    const mean = x.reduce((a, v) => a + v, 0) / x.length;
    const ph = unwrappedPhase(analytic(x.map((v) => v - mean)));
    const turns = Array.from(ph, (v) => (v - ph[0]) / (2 * Math.PI));
    const acts = t.map((tt) => Math.max(0, Math.floor((tt - cl / 2) / cl) + 1));
    const top = Math.max(...x.map(Math.abs));
    drawPlot(cvX, { xRange: [0, T], yRange: [-1.2 * top, 1.2 * top], xLabel: "time (s)", yLabel: "signal", series: [{ x: t, y: x, color: COLORS.gray }] });
    drawPlot(cvP, {
      xRange: [0, T],
      yRange: [0, Math.max(turns[turns.length - 1], activations) * 1.25 + 1],
      xLabel: "time (s)",
      yLabel: "count",
      legendLeft: true,
      series: [
        { x: t, y: turns, color: COLORS.vermillion, width: 2, label: "phase turns" },
        { x: t, y: acts, color: COLORS.ink, dash: [5, 4], label: "activations" },
      ],
    });
    const total = turns[turns.length - 1];
    readout.textContent =
      `${activations} activations in ${T} s; the analytic-signal phase made ${total.toFixed(1)} turns. ` +
      (Math.abs(total - activations) < 1.5 ? "Phase and activations agree." : "They disagree: phase turns are not activations for this signal.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m05-d2-root");
if (root) mount(root);
