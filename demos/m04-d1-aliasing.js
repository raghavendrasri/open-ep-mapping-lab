// m04-d1 · Sampling and aliasing (eq-m04-sampling). MIT License. Tested in tests/test_m04_demos.py.
import { aliasFrequency } from "./m04-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A sinusoid (gray), the samples a converter takes of it (dots), and the lowest-frequency sinusoid through the " +
        "same samples (orange). Above half the sampling rate the samples cannot tell the two apart: the signal is " +
        "aliased to a lower frequency.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 240, label: "A sinusoid, its samples and its alias" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const freq = addSlider(controls, { id: "m04-d1-freq", label: "Signal frequency", min: 5, max: 1500, step: 5, value: 850, digits: 0, unit: "Hz", onInput: draw });
  const rate = addSlider(controls, { id: "m04-d1-rate", label: "Sampling rate", min: 100, max: 2000, step: 50, value: 1000, digits: 0, unit: "Hz", onInput: draw });
  const T = 20; // ms shown

  function draw() {
    const f = Number(freq.value);
    const fs = Number(rate.value);
    const fa = aliasFrequency(f, fs);
    const tc = Array.from({ length: 2001 }, (_, i) => (T * i) / 2000);
    const ts = [];
    for (let t = 0; t <= T + 1e-9; t += 1000 / fs) ts.push(t);
    drawPlot(cv, {
      xRange: [0, T],
      yRange: [-1.3, 1.8],
      xLabel: "time (ms)",
      yLabel: "signal (relative)",
      series: [
        { x: tc, y: tc.map((t) => Math.cos((2 * Math.PI * f * t) / 1000)), color: COLORS.gray, label: `signal, ${f} Hz` },
        { x: tc, y: tc.map((t) => Math.cos((2 * Math.PI * fa * t) / 1000)), color: COLORS.vermillion, dash: [5, 3], width: 2, label: `alias, ${fa} Hz` },
      ],
      markers: ts.map((t) => ({ x: t, y: Math.cos((2 * Math.PI * f * t) / 1000), color: COLORS.blue })),
    });
    readout.textContent =
      `Signal ${f} Hz sampled at ${fs} Hz (Nyquist frequency ${fs / 2} Hz). ` +
      (f <= fs / 2
        ? "Below the Nyquist frequency: the samples represent it faithfully."
        : `Above it: the samples are identical to those of a ${fa} Hz signal, and no later processing can undo that.`);
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m04-d1-root");
if (root) mount(root);
