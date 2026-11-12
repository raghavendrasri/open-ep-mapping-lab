// m50-d2 · Frequency, depth and frame rate: what an ICE image can reach and how often it refreshes. MIT License.
// The formulas are tested against Python (tests/test_m50_demos.py).
import { axialResolutionMm, frameRate, maxDepthCm, roundTripLossDb, wavelengthMm } from "./m50-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const BUDGET_DB = 60; // illustrative signal budget
const CYCLES = 2; // illustrative pulse length

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Higher frequency gives finer depth resolution but loses signal faster on the way out and back. The " +
        "curve is the round-trip loss against depth for the chosen frequency and tissue attenuation; where it " +
        "crosses the signal budget (dashed) echoes become too weak. Deeper images and more lines per frame also " +
        "lower the frame rate, because each line must wait for its deepest echo.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 250, label: "Round-trip loss in decibels against depth" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const freq = addSlider(controls, { id: "m50-d2-freq", label: "Frequency", min: 5, max: 10, step: 0.5, value: 7.5, digits: 1, unit: "MHz", onInput: draw });
  const depth = addSlider(controls, { id: "m50-d2-depth", label: "Image depth", min: 2, max: 15, step: 0.5, value: 8, digits: 1, unit: "cm", onInput: draw });
  const lines = addSlider(controls, { id: "m50-d2-lines", label: "Lines per frame", min: 32, max: 256, step: 8, value: 96, digits: 0, onInput: draw });
  const tissue = addSelect(controls, {
    id: "m50-d2-tissue",
    label: "Attenuation",
    options: [
      { value: "0.52", label: "0.52 dB/(cm·MHz), across fibers" },
      { value: "1.88", label: "1.88 dB/(cm·MHz), along fibers" },
    ],
    value: "0.52",
    onChange: draw,
  });

  function draw() {
    const f = Number(freq.value);
    const D = Number(depth.value);
    const N = Number(lines.value);
    const a = Number(tissue.value);
    const zs = Array.from({ length: 151 }, (_, i) => i * 0.1);
    const loss = zs.map((z) => roundTripLossDb(a, f, z));
    const zMax = maxDepthCm(BUDGET_DB, a, f);
    drawPlot(cv, {
      xRange: [0, 15], yRange: [0, 150], xLabel: "depth (cm)", yLabel: "round-trip loss (dB)", xTicks: 4,
      series: [
        { x: zs, y: loss, color: COLORS.blue, width: 2.5, label: `${f.toFixed(1)} MHz` },
        { x: [0, 15], y: [BUDGET_DB, BUDGET_DB], color: COLORS.gray, width: 1.5, dash: [5, 4], label: "signal budget (illustrative)" },
      ],
      vlines: [{ x: D, color: COLORS.vermillion, label: "image depth" }],
      legendLeft: true,
    });
    readout.textContent =
      `Wavelength ${wavelengthMm(f).toFixed(3)} mm; axial resolution ${axialResolutionMm(f, CYCLES).toFixed(2)} mm ` +
      `for a ${CYCLES}-cycle pulse. Loss at ${D.toFixed(1)} cm: ${roundTripLossDb(a, f, D).toFixed(0)} dB; the budget ` +
      `lasts to ${zMax.toFixed(1)} cm. Frame rate with ${N} lines: ${frameRate(D / 100, N).toFixed(0)} frames per second.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m50-d2-root");
if (root) mount(root);
