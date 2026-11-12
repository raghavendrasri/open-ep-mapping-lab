// m48-d1 · Thin walls and blur across modalities (eq-m51-wall, read at published resolutions). MIT License.
// Tested in tests/test_m48_demos.py.
import {
  LA_WALL_MM,
  RESOLUTION_MM,
  fwhmThickness,
  fwhmToSigma,
  slabPeak,
  slabProfile,
  thresholdThickness,
} from "./m48-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A wall of unit contrast between two equal backgrounds, seen through a Gaussian blur. Top: the true and " +
        "blurred profiles, with a fixed threshold at half the contrast and the half of the blurred peak. Bottom: " +
        "the thickness each reading reports against the true thickness. Pick a published resolution or set your " +
        "own; the dotted lines mark the thinnest and the mean left atrial wall in one CT study.",
    ),
  );
  const cvProf = setupCanvas(root, { width: 640, height: 210, label: "True and blurred profiles across a wall" });
  const cvRead = setupCanvas(root, { width: 640, height: 230, label: "Thickness read from the image against true thickness" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const wall = addSlider(controls, { id: "m48-d1-wall", label: "True wall thickness", min: 0.2, max: 6, step: 0.05, value: LA_WALL_MM.min, digits: 2, unit: "mm", onInput: draw });
  const fwhm = addSlider(controls, {
    id: "m48-d1-fwhm",
    label: "Blur (FWHM)",
    min: 0.2,
    max: 8,
    step: 0.02,
    value: 1.5,
    digits: 2,
    unit: "mm",
    onInput: () => {
      preset.value = RESOLUTION_MM.some((r) => r.fwhm === Number(fwhm.value)) ? String(Number(fwhm.value)) : "custom";
      draw();
    },
  });
  const preset = addSelect(controls, {
    id: "m48-d1-preset",
    label: "Published resolution",
    options: [...RESOLUTION_MM.map((r) => ({ value: String(r.fwhm), label: r.label })), { value: "custom", label: "custom" }],
    value: "1.5",
    onChange: () => {
      if (preset.value === "custom") return;
      fwhm.value = preset.value;
      fwhm.dispatchEvent(new Event("input"));
    },
  });
  const ws = Array.from({ length: 581 }, (_, i) => 0.2 + i * 0.01);

  function draw() {
    const w = Number(wall.value);
    const G = Number(fwhm.value);
    const s = fwhmToSigma(G);
    const half = 3 + Math.max(w, 2 * G);
    const xs = Array.from({ length: 601 }, (_, i) => -half + (2 * half * i) / 600);
    const peak = slabPeak(w, s);
    drawPlot(cvProf, {
      xRange: [-half, half],
      yRange: [0, 1.35],
      xLabel: "position across the wall (mm)",
      yLabel: "signal (fraction of contrast)",
      legendLeft: true,
      series: [
        { x: xs, y: xs.map((x) => (Math.abs(x) <= w / 2 ? 1 : 0)), color: COLORS.gray, dash: [5, 4], label: "true wall" },
        { x: xs, y: xs.map((x) => slabProfile(x, w, s)), color: COLORS.vermillion, width: 2, label: "blurred" },
        { x: [-half, half], y: [0.5, 0.5], color: COLORS.blue, dash: [2, 3], label: "half the contrast" },
        { x: [-half, half], y: [peak / 2, peak / 2], color: COLORS.green, dash: [6, 3], label: "half the blurred peak" },
      ],
    });
    drawPlot(cvRead, {
      xRange: [0, 6],
      yRange: [0, 1.45 * Math.max(6, fwhmThickness(6, s))],
      xLabel: "true wall thickness (mm)",
      yLabel: "read thickness (mm)",
      legendLeft: true,
      series: [
        { x: [0, 6], y: [0, 6], color: COLORS.gray, dash: [5, 4], label: "true" },
        { x: ws, y: ws.map((v) => fwhmThickness(v, s)), color: COLORS.green, width: 2, label: "width at half the blurred peak" },
        { x: ws, y: ws.map((v) => thresholdThickness(v, s)), color: COLORS.blue, width: 2, label: "fixed half-contrast threshold" },
      ],
      vlines: [
        { x: LA_WALL_MM.min, color: COLORS.gray, dash: [1, 3] },
        { x: LA_WALL_MM.mean, color: COLORS.gray, dash: [1, 3] },
      ],
      markers: [
        { x: w, y: fwhmThickness(w, s), color: COLORS.green },
        { x: w, y: thresholdThickness(w, s), color: COLORS.blue },
      ],
    });
    const thr = thresholdThickness(w, s);
    readout.textContent =
      `Wall ${w.toFixed(2)} mm, blur ${G.toFixed(2)} mm FWHM (sigma ${s.toFixed(2)} mm). The blurred wall peaks at ` +
      `${(100 * peak).toFixed(0)}% of its contrast. Read at half the blurred peak it measures ${fwhmThickness(w, s).toFixed(2)} mm` +
      `${w < G ? " (never less than the blur itself)" : ""}; a fixed half-contrast threshold ` +
      `${thr > 0 ? `reads ${thr.toFixed(2)} mm` : "misses the wall entirely"}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m48-d1-root");
if (root) mount(root);
