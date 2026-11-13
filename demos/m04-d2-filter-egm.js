// m04-d2 · What the recording chain does to a unipolar electrogram (eq-m04-highpass, eq-m04-butterworth,
// eq-m04-delay). MIT License. Tested in tests/test_m04_demos.py.
import { chain, steepestDownstroke, unipolarEgm } from "./m04-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const FS = 20000; // Hz, a fine "analog" reference
const PRESETS = {
  "0.5-500": { hp: 0.5, lp: 500 },
  "30-500": { hp: 30, lp: 500 },
  "100-off": { hp: 100, lp: 10000 },
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "The m03 unipolar electrogram (front passing at 0 ms, 1 m/s, front width 0.3 mm, electrode 1 mm away) before " +
        "(gray) and after a second-order Butterworth high-pass and low-pass (green). The dotted lines mark the true " +
        "activation time and the steepest downstroke of the filtered signal. Presets are the bands used in one " +
        "clinical mapping study.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 250, label: "Unipolar electrogram before and after filtering" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const hp = addSlider(controls, { id: "m04-d2-hp", label: "High-pass cutoff (log10 of Hz)", min: -0.3, max: 2.4, step: 0.001, value: Math.log10(30), digits: 2, onInput: () => { preset.value = "custom"; draw(); } });
  const lp = addSlider(controls, { id: "m04-d2-lp", label: "Low-pass cutoff", min: 100, max: 10000, step: 50, value: 500, digits: 0, unit: "Hz", onInput: () => { preset.value = "custom"; draw(); } });
  const mode = addSelect(controls, { id: "m04-d2-mode", label: "Filtering", options: [{ value: "causal", label: "causal (as recorded live)" }, { value: "zero", label: "zero-phase (forward and backward, offline)" }], value: "causal", onChange: draw });
  const preset = addSelect(controls, {
    id: "m04-d2-preset",
    label: "Band",
    options: [
      { value: "30-500", label: "30-500 Hz (bipolar band in one study)" },
      { value: "0.5-500", label: "0.5-500 Hz (minimally filtered unipolar)" },
      { value: "100-off", label: "100 Hz high-pass (high-pass unipolar)" },
      { value: "custom", label: "custom" },
    ],
    value: "30-500",
    onChange: () => {
      const p = PRESETS[preset.value];
      if (!p) return;
      hp.value = String(Math.log10(p.hp));
      lp.value = String(p.lp);
      hp.dispatchEvent(new Event("input"));
      lp.dispatchEvent(new Event("input"));
      preset.value = Object.keys(PRESETS).find((k) => PRESETS[k] === p);
      draw();
    },
  });
  const t = Array.from({ length: 4000 }, (_, i) => -100 + (i * 1000) / FS);
  const x = t.map((v) => unipolarEgm(v));

  function draw() {
    const f1 = 10 ** Number(hp.value);
    const f2 = Number(lp.value);
    const zero = mode.value === "zero";
    const y = chain(x, FS, { hp: f1, lp: f2, zeroPhase: zero });
    const keep = t.map((v, i) => [v, i]).filter(([v]) => v >= -15 && v <= 15).map(([, i]) => i);
    const tt = keep.map((i) => t[i]);
    const lat = steepestDownstroke(t, Array.from(y));
    const ptp = (a) => Math.max(...a) - Math.min(...a);
    drawPlot(cv, {
      xRange: [-15, 15],
      yRange: [-0.6, 0.8],
      xLabel: "time (ms); the front passes the electrode at 0",
      yLabel: "potential (relative)",
      series: [
        { x: tt, y: keep.map((i) => x[i]), color: COLORS.gray, label: "unfiltered" },
        { x: tt, y: keep.map((i) => y[i]), color: COLORS.green, width: 2, label: `filtered ${f1.toFixed(1)}-${f2 >= FS / 2 ? "no low-pass" : f2 + " Hz"}` },
      ],
      vlines: [
        { x: 0, color: COLORS.ink, dash: [2, 3] },
        { x: lat, color: COLORS.green, dash: [2, 3] },
      ],
    });
    readout.textContent =
      `High-pass ${f1.toFixed(1)} Hz, low-pass ${f2 >= FS / 2 ? "off" : f2 + " Hz"}, ${zero ? "zero-phase" : "causal"}. ` +
      `Peak-to-peak ${(ptp(keep.map((i) => y[i])) / ptp(keep.map((i) => x[i]))).toFixed(2)} of the unfiltered signal; ` +
      `steepest downstroke at ${lat >= 0 ? "+" : ""}${lat.toFixed(2)} ms (true activation 0 ms).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m04-d2-root");
if (root) mount(root);
