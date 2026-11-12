// m53-d2 · Real-time MRI: lines, repetition time and frame rate. MIT License.
// eq-m53-frame, tested in tests/test_m53_demos.py.
import { FPS_ACTIVE, FPS_PASSIVE, fps, frameTimeMs } from "./m53-common.js";
import { CORONARY_SPEED } from "./m51-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A real-time image is built line by line, one repetition time (TR) apart, so its frame time is the number " +
        "of lines times TR, divided by any acceleration. The curve is frames per second against lines per frame. " +
        "Reported rates: 4–8 frames/s for passive catheter visualization (shaded) and up to 50/s for active " +
        "tracking of tip coils (dashed). The readout says how far a structure moves during one frame.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 250, label: "Frames per second against lines per frame" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const lines = addSlider(controls, { id: "m53-d2-lines", label: "Lines per frame", min: 16, max: 256, step: 8, value: 64, digits: 0, onInput: draw });
  const tr = addSlider(controls, { id: "m53-d2-tr", label: "Repetition time", min: 2, max: 6, step: 0.1, value: 3, digits: 1, unit: "ms", onInput: draw });
  const accel = addSelect(controls, {
    id: "m53-d2-accel",
    label: "Acceleration",
    options: [1, 2, 4].map((v) => ({ value: String(v), label: v === 1 ? "none" : `${v}×` })),
    value: "1",
    onChange: draw,
  });
  const speed = addSelect(controls, {
    id: "m53-d2-speed",
    label: "Motion",
    options: Object.entries(CORONARY_SPEED).map(([k, v]) => ({ value: k, label: `${v} mm/s, coronary ${k}` })),
    value: "all three arteries",
    onChange: draw,
  });
  const xs = Array.from({ length: 241 }, (_, i) => 16 + i);

  function draw() {
    const n = Number(lines.value);
    const t = Number(tr.value);
    const r = Number(accel.value);
    const ymax = 75;
    const band = [];
    const by = [];
    for (const x of [16, 256, 256, 16, 16]) band.push(x);
    for (const y of [FPS_PASSIVE[0], FPS_PASSIVE[0], FPS_PASSIVE[1], FPS_PASSIVE[1], FPS_PASSIVE[0]]) by.push(y);
    const p = drawPlot(cv, {
      xRange: [16, 256],
      yRange: [0, ymax],
      xLabel: "lines per frame",
      yLabel: "frames per second",
      series: [
        { x: band, y: by, color: COLORS.green, width: 1, label: "4–8 /s passive" },
        { x: [16, 256], y: [FPS_ACTIVE, FPS_ACTIVE], color: COLORS.purple, dash: [6, 4], width: 1.5, label: "50 /s active tracking" },
        { x: xs, y: xs.map((v) => Math.min(ymax * 2, fps(v, t, r))), color: COLORS.blue, label: "this sequence" },
      ],
      markers: [{ x: n, y: Math.min(ymax, fps(n, t, r)), color: COLORS.vermillion }],
    });
    const { ctx } = cv;
    ctx.save();
    ctx.globalAlpha = 0.15;
    ctx.fillStyle = COLORS.green;
    const yTop = p.Y(FPS_PASSIVE[1]);
    ctx.fillRect(p.X(16), yTop, p.X(256) - p.X(16), p.Y(FPS_PASSIVE[0]) - yTop);
    ctx.restore();
    const ft = frameTimeMs(n, t, r);
    const v = CORONARY_SPEED[speed.value];
    readout.textContent =
      `${n} lines × ${t.toFixed(1)} ms${r > 1 ? ` ÷ ${r}` : ""} = ${Math.round(ft)} ms per frame, ` +
      `${fps(n, t, r).toFixed(1)} frames/s. At ${v} mm/s a structure moves ${((v * ft) / 1e3).toFixed(1)} mm during one frame.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m53-d2-root");
if (root) mount(root);
