// m34-d2 · Data rate and storage. MIT License.
import { dataRateBps } from "./m34-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const fmtBytes = (b) => (b >= 1e9 ? `${(b / 1e9).toFixed(2)} GB` : b >= 1e6 ? `${(b / 1e6).toFixed(1)} MB` : `${(b / 1e3).toFixed(1)} kB`);

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Raw data rate R = N f_s b, the buffer needed to ride out a stall, and storage over a session. " +
        "The curve shows storage against session length for the current settings; the dot marks the chosen length.",
    ),
  );
  const plot = setupCanvas(root, { width: 640, height: 220, label: "Raw storage versus session length" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const n = addSlider(controls, { id: "m34-d2-n", label: "Channels N", min: 1, max: 256, step: 1, value: 8, digits: 0, onInput: draw });
  const fs = addSlider(controls, { id: "m34-d2-fs", label: "Sampling rate f_s", min: 250, max: 4000, step: 250, value: 1000, digits: 0, unit: "Hz", onInput: draw });
  const b = addSlider(controls, { id: "m34-d2-b", label: "Bits per sample b", min: 8, max: 32, step: 1, value: 14, digits: 0, onInput: draw });
  const minutes = addSlider(controls, { id: "m34-d2-t", label: "Session length", min: 5, max: 240, step: 5, value: 60, digits: 0, unit: "min", onInput: draw });
  const stall = addSlider(controls, { id: "m34-d2-stall", label: "Longest consumer stall", min: 10, max: 2000, step: 10, value: 100, digits: 0, unit: "ms", onInput: draw });

  function draw() {
    const rate = dataRateBps(Number(n.value), Number(fs.value), Number(b.value)); // bit/s
    const bytesPerS = rate / 8;
    const tMin = Number(minutes.value);
    const xs = Array.from({ length: 49 }, (_, i) => i * 5);
    const ys = xs.map((m) => (bytesPerS * 60 * m) / 1e9);
    const yMax = Math.max(0.01, ys[ys.length - 1] * 1.05);
    drawPlot(plot, {
      xRange: [0, 240],
      yRange: [0, yMax],
      xLabel: "session length (min)",
      yLabel: "raw storage (GB)",
      series: [{ x: xs, y: ys, color: COLORS.blue }],
      markers: [{ x: tMin, y: (bytesPerS * 60 * tMin) / 1e9, color: COLORS.vermillion, label: "chosen session" }],
      legendLeft: true,
    });
    const buffer = (bytesPerS * Number(stall.value)) / 1000;
    readout.textContent =
      `Data rate ${(rate / 1e3).toFixed(1)} kbit/s (${fmtBytes(bytesPerS)} per second). ` +
      `Buffer for a ${stall.value} ms stall: ${fmtBytes(buffer)}. Raw storage for ${tMin} min: ${fmtBytes(bytesPerS * 60 * tMin)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m34-d2-root");
if (root) mount(root);
