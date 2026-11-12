// m47-d1 · Quantizing an ECG beat: step size, range and signal-to-quantization-noise ratio. MIT License.
// The quantizer is tested against Python (tests/test_m47_demos.py).
import { beat } from "./m37-common.js";
import { fakeQuant, predictedSqnrDb, qparams, sqnrDb } from "./m47-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const FS = 250;
const T = Array.from({ length: 200 }, (_, i) => -0.3 + i / FS);
const X = T.map((t) => beat(t));
const RANGES = {
  beat: { label: "the beat's own minimum to maximum", lo: Math.min(...X), hi: Math.max(...X) },
  wide: { label: "a fixed ±5 mV range (illustrative)", lo: -5, hi: 5 },
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A synthetic beat (250 samples per second) is stored with b bits: each value is rounded to the nearest of " +
        "2ᵇ levels spread over a chosen range. Top: the beat and its quantized copy. Bottom: the " +
        "signal-to-quantization-noise ratio (SQNR) measured on the beat (dots) and predicted from the step size " +
        "with the uniform-noise model (line). A range much wider than the signal wastes levels.",
    ),
  );
  const top = setupCanvas(root, { width: 640, height: 220, label: "Synthetic beat and its quantized copy, voltage against time" });
  const bottom = setupCanvas(root, { width: 640, height: 200, label: "Measured and predicted SQNR against the number of bits" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const bits = addSlider(controls, { id: "m47-d1-bits", label: "Bits", min: 2, max: 12, step: 1, value: 6, digits: 0, onInput: draw });
  const range = addSelect(controls, {
    id: "m47-d1-range",
    label: "Range",
    options: Object.entries(RANGES).map(([value, r]) => ({ value, label: r.label })),
    value: "beat",
    onChange: draw,
  });

  function draw() {
    const b = Number(bits.value);
    const r = RANGES[range.value];
    const qp = qparams(r.lo, r.hi, b);
    const xq = fakeQuant(X, qp);
    drawPlot(top, {
      xRange: [-0.3, 0.5], yRange: [-0.4, 1.2], xLabel: "time from R peak (s)", yLabel: "mV",
      series: [
        { x: T, y: X, color: COLORS.gray, width: 1.5, label: "beat" },
        { x: T, y: xq, color: COLORS.blue, width: 2, label: `${b}-bit copy` },
      ],
    });
    const bs = Array.from({ length: 15 }, (_, i) => i + 2);
    const meas = bs.map((k) => {
      const p = qparams(r.lo, r.hi, k);
      return sqnrDb(X, fakeQuant(X, p));
    });
    const pred = bs.map((k) => predictedSqnrDb(X, qparams(r.lo, r.hi, k).S));
    drawPlot(bottom, {
      xRange: [2, 16], yRange: [-10, 100], xLabel: "bits", yLabel: "SQNR (dB)", xTicks: 8,
      series: [{ x: bs, y: pred, color: COLORS.orange, width: 2, label: "predicted, S²/12 noise" }],
      markers: [
        ...bs.map((k, i) => ({ x: k, y: Math.min(meas[i], 99), color: COLORS.blue, radius: 3.5 })),
        { x: b, y: Math.min(meas[b - 2], 99), color: COLORS.vermillion, radius: 6, label: "measured (this setting in red)" },
      ],
      legendLeft: true,
    });
    const m = meas[b - 2];
    readout.textContent =
      `${b} bits over ${r.label}: step S = ${(1000 * qp.S).toFixed(1)} µV. ` +
      `Measured SQNR ${Number.isFinite(m) ? m.toFixed(1) : "∞"} dB; predicted from S²/12 ${pred[b - 2].toFixed(1)} dB.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m47-d1-root");
if (root) mount(root);
