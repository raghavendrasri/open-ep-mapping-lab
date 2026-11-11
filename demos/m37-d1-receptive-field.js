// m37-d1 · How much of the ECG does one output of a convolutional network see? MIT License.
import { receptiveField, regularEcg } from "./m37-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A stack of convolution layers slides over a synthetic, noise-free ECG. The orange stretch is the receptive field: " +
        "the input samples that one output of the last layer depends on. Change the layers, kernel width, stride, sampling " +
        "rate and heart rate, and see how many beats one output can compare.",
    ),
  );
  const canvas = setupCanvas(root, { width: 660, height: 230, label: "Synthetic ECG with the receptive field of one network output highlighted" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const layers = addSlider(controls, { id: "m37-d1-layers", label: "Layers", min: 1, max: 10, step: 1, value: 4, digits: 0, onInput: draw });
  const width = addSlider(controls, { id: "m37-d1-k", label: "Kernel width k (samples)", min: 3, max: 31, step: 2, value: 9, digits: 0, onInput: draw });
  const stride = addSlider(controls, { id: "m37-d1-s", label: "Stride of layers 2 and up", min: 1, max: 3, step: 1, value: 2, digits: 0, onInput: draw });
  const hr = addSlider(controls, { id: "m37-d1-hr", label: "Heart rate", min: 40, max: 150, step: 5, value: 70, digits: 0, unit: "bpm", onInput: draw });
  const fsSel = addSelect(controls, {
    id: "m37-d1-fs",
    label: "Sampling rate",
    options: [
      { value: 100, label: "100 Hz" },
      { value: 300, label: "300 Hz" },
      { value: 500, label: "500 Hz" },
    ],
    value: 100,
    onChange: draw,
  });

  const duration = 6;
  function draw() {
    const L = Number(layers.value);
    const k = Number(width.value);
    const s = Number(stride.value);
    const fs = Number(fsSel.value);
    const rate = Number(hr.value);
    const kernels = Array(L).fill(k);
    const strides = Array.from({ length: L }, (_, i) => (i === 0 ? 1 : s));
    const r = receptiveField(kernels, strides);
    const seconds = r / fs;
    const x = regularEcg(fs, duration, rate);
    const t = x.map((_, i) => i / fs);
    const start = 1.0;
    const stop = Math.min(duration, start + seconds);
    const i0 = Math.round(start * fs);
    const i1 = Math.min(x.length, Math.round(stop * fs));
    drawPlot(canvas, {
      xRange: [0, duration],
      yRange: [-0.5, 1.2],
      xLabel: "time (s)",
      yLabel: "ECG (mV)",
      series: [
        { x: t, y: x, color: COLORS.gray, width: 1.2 },
        { x: t.slice(i0, i1), y: x.slice(i0, i1), color: COLORS.vermillion, width: 2.4, label: "receptive field" },
      ],
      vlines: [
        { x: start, color: COLORS.vermillion },
        { x: stop, color: COLORS.vermillion },
      ],
    });
    const beats = (seconds * rate) / 60;
    readout.textContent =
      `Receptive field ${r} samples = ${seconds.toFixed(2)} s at ${fs} Hz, about ${beats.toFixed(1)} RR intervals at ${rate} bpm. ` +
      (beats < 2
        ? "One output cannot see two RR intervals, so on its own it cannot judge whether the rhythm is irregular; only later pooling can."
        : "One output spans at least two RR intervals, so it can compare successive beats.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m37-d1-root");
if (root) mount(root);
