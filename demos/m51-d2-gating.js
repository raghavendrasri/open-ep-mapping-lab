// m51-d2 · Motion and the gating window: a vessel cross-section that moves at constant speed while the scanner
// collects a half-scan. MIT License. Formulas tested in tests/test_m51_demos.py.
import { CORONARY_SPEED, smearedDisk, temporalWindow } from "./m51-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawField, drawPlot, el, setupCanvas } from "./plot.js";

const HALF = 9; // mm, half the field shown
const NF = 91;
const gray = (t) => {
  const g = Math.round(255 * Math.min(1, Math.max(0, t)));
  return [g, g, g];
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A half-scan collects about half a rotation of data; a scanner with two X-ray tubes needs about a quarter. " +
        "A vessel that moves during that window is smeared along its path. The left image is the vessel at rest, " +
        "the right one averaged over the window; the plot shows the profile along the direction of motion. " +
        "Speeds are published averages for coronary arteries.",
    ),
  );
  const cvImg = setupCanvas(root, { width: 640, height: 230, label: "A vessel cross-section at rest and smeared by motion during the gating window" });
  const cvPlot = setupCanvas(root, { width: 640, height: 190, label: "Brightness profile along the direction of motion, at rest and smeared" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const rot = addSlider(controls, { id: "m51-d2-rotation", label: "Rotation time", min: 0.25, max: 0.5, step: 0.01, value: 0.33, digits: 2, unit: "s", onInput: draw });
  const diam = addSlider(controls, { id: "m51-d2-diameter", label: "Vessel diameter", min: 1, max: 5, step: 0.5, value: 3, digits: 1, unit: "mm", onInput: draw });
  const sources = addSelect(controls, {
    id: "m51-d2-sources",
    label: "X-ray sources",
    options: [
      { value: "1", label: "one (window ≈ rotation / 2)" },
      { value: "2", label: "two (window ≈ rotation / 4)" },
    ],
    value: "1",
    onChange: draw,
  });
  const speed = addSelect(controls, {
    id: "m51-d2-speed",
    label: "Speed",
    options: Object.entries(CORONARY_SPEED).map(([k, v]) => ({ value: k, label: `${v} mm/s, ${k}` })),
    value: "all three arteries",
    onChange: draw,
  });

  const axis = Array.from({ length: NF }, (_, i) => -HALF + (2 * HALF * i) / (NF - 1));
  const xs = Array.from({ length: 361 }, (_, i) => -HALF + (2 * HALF * i) / 360);

  function draw() {
    const D = Number(diam.value);
    const win = temporalWindow(Number(rot.value), Number(sources.value));
    const v = CORONARY_SPEED[speed.value];
    const b = v * win;
    const still = [];
    const moving = [];
    for (const yy of axis) for (const xx of axis) {
      still.push(smearedDisk(xx, yy, D, 0));
      moving.push(smearedDisk(xx, yy, D, b));
    }
    const { ctx, width, height } = cvImg;
    ctx.clearRect(0, 0, width, height);
    const common = { nx: NF, ny: NF, extent: [-HALF, HALF, -HALF, HALF], range: [0, 1], colormap: gray };
    drawField(cvImg, { ...common, field: still, panel: { x: 0, y: 0, w: 320, h: height }, title: "At rest" });
    drawField(cvImg, { ...common, field: moving, panel: { x: 320, y: 0, w: 320, h: height }, title: `Moving ${b.toFixed(1)} mm during the window →` });
    drawPlot(cvPlot, {
      xRange: [-HALF, HALF],
      yRange: [0, 1.05],
      xLabel: "position along the motion (mm)",
      yLabel: "brightness",
      legendLeft: true,
      series: [
        { x: xs, y: xs.map((t) => smearedDisk(t, 0, D, 0)), color: COLORS.gray, dash: [5, 4], label: "at rest" },
        { x: xs, y: xs.map((t) => smearedDisk(t, 0, D, b)), color: COLORS.vermillion, label: "smeared" },
      ],
    });
    const peak = Math.min(1, b > 0 ? D / b : 1);
    readout.textContent =
      `Window ${Math.round(win * 1000)} ms. At ${v} mm/s the vessel moves ${b.toFixed(1)} mm during it, so a ` +
      `${D.toFixed(1)}-mm vessel looks ${(D + b).toFixed(1)} mm long and its peak brightness falls to ${Math.round(100 * peak)}%.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m51-d2-root");
if (root) mount(root);
