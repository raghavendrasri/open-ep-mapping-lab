// m50-d1 · Steering a phased array: main lobe, side lobes and grating lobes. MIT License.
// arrayFactor and gratingLobesDeg are tested against Python (tests/test_m50_demos.py).
import { arrayFactor, firstNullOffset, gratingLobesDeg, wavelengthMm } from "./m50-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "An ICE catheter steers its beam by firing its elements with small delays. The curve is how strongly the " +
        "array sends (and receives) in each direction, in decibels, for the chosen steering angle, element spacing " +
        "and number of elements. When the spacing exceeds half a wavelength, false copies of the beam (grating " +
        "lobes) appear: echoes from those directions would be drawn in the wrong place.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 250, label: "Array factor in decibels against angle" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const steer = addSlider(controls, { id: "m50-d1-steer", label: "Steering angle", min: -60, max: 60, step: 1, value: 20, digits: 0, unit: "°", onInput: draw });
  const pitch = addSlider(controls, { id: "m50-d1-pitch", label: "Element spacing (wavelengths)", min: 0.25, max: 1.5, step: 0.05, value: 0.5, digits: 2, onInput: draw });
  const nEl = addSelect(controls, {
    id: "m50-d1-n",
    label: "Number of elements",
    options: [16, 32, 64, 128].map((v) => ({ value: String(v), label: String(v) })),
    value: "64",
    onChange: draw,
  });
  const deg = Array.from({ length: 1441 }, (_, i) => -90 + i * 0.125);
  const rad = deg.map((d) => (d * Math.PI) / 180);

  function draw() {
    const s = (Number(steer.value) * Math.PI) / 180;
    const d = Number(pitch.value);
    const n = Number(nEl.value);
    const af = arrayFactor(rad, n, d, s).map((v) => Math.max(-50, 20 * Math.log10(Math.max(v, 1e-6))));
    const lobes = gratingLobesDeg(d, s);
    drawPlot(cv, {
      xRange: [-90, 90], yRange: [-50, 3], xLabel: "angle from the catheter's forward direction (°)", yLabel: "dB",
      xTicks: 7,
      series: [{ x: deg, y: af, color: COLORS.blue, width: 1.8, label: "array factor" }],
      vlines: [
        { x: Number(steer.value), color: COLORS.green, label: "steering angle" },
        ...lobes.map((g, i) => ({ x: g, color: COLORS.vermillion, label: i === 0 ? "grating lobe" : undefined })),
      ],
    });
    const null1 = Math.asin(Math.min(1, Math.sin(s) + firstNullOffset(n, d))) - s;
    readout.textContent =
      `Spacing ${d.toFixed(2)} wavelengths (${(d * wavelengthMm(7.5)).toFixed(3)} mm at 7.5 MHz), ${n} elements, steered to ` +
      `${Number(steer.value)}°. First null ${((null1 * 180) / Math.PI).toFixed(1)}° from the main lobe. ` +
      (lobes.length ? `Grating lobes at ${lobes.map((g) => g.toFixed(1) + "°").join(", ")}.` : "No grating lobes.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m50-d1-root");
if (root) mount(root);
