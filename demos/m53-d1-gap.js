// m53-d1 · Can the scan see the gap? A lesion line with a gap, blurred by the scanner. MIT License.
// Exact for a straight band and a Gaussian blur (eq-m53-gap); tested in tests/test_m53_demos.py.
import { bandGapImage, bandPeak, fwhmToSigma, gapCenter, minVisibleGap } from "./m53-common.js";
import { COLORS, addReadout, addSlider, drawField, drawPlot, el, setupCanvas } from "./plot.js";

const HALF = 8;
const N = 121;
const gray = (t) => {
  const g = Math.round(255 * Math.min(1, Math.max(0, t)));
  return [g, g, g];
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A straight ablation line (bright) with a gap in it. Left: the line as made. Right: the same line seen " +
        "through the scanner's blur. Below: the signal along the line. A gap counts as visible when its center " +
        "falls below half the full contrast (dotted line). Narrow gaps fill in; a thin line also loses contrast.",
    ),
  );
  const cvImg = setupCanvas(root, { width: 640, height: 230, label: "A lesion line with a gap, before and after blur" });
  const cvPlot = setupCanvas(root, { width: 640, height: 180, label: "Signal along the center of the lesion line" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const gap = addSlider(controls, { id: "m53-d1-gap", label: "Gap width", min: 0.2, max: 6, step: 0.1, value: 1.5, digits: 1, unit: "mm", onInput: draw });
  const res = addSlider(controls, { id: "m53-d1-blur", label: "Blur (FWHM)", min: 0.5, max: 4, step: 0.1, value: 1.5, digits: 1, unit: "mm", onInput: draw });
  const band = addSlider(controls, { id: "m53-d1-band", label: "Line width", min: 1, max: 8, step: 0.5, value: 4, digits: 1, unit: "mm", onInput: draw });
  const axis = Array.from({ length: N }, (_, i) => -HALF + (2 * HALF * i) / (N - 1));
  const xs = Array.from({ length: 321 }, (_, i) => -HALF + (2 * HALF * i) / 320);

  function draw() {
    const g = Number(gap.value);
    const w = Number(band.value);
    const sigma = fwhmToSigma(Number(res.value));
    const made = [];
    const seen = [];
    for (const y of axis) for (const x of axis) {
      made.push(Math.abs(y) <= w / 2 && Math.abs(x) > g / 2 ? 1 : 0);
      seen.push(bandGapImage(x, y, w, g, sigma));
    }
    const { ctx, width, height } = cvImg;
    ctx.clearRect(0, 0, width, height);
    const common = { nx: N, ny: N, extent: [-HALF, HALF, -HALF, HALF], range: [0, 1], colormap: gray, xLabel: "along the line (mm)", yLabel: "across (mm)" };
    drawField(cvImg, { ...common, field: made, panel: { x: 0, y: 0, w: 320, h: height }, title: "As made" });
    drawField(cvImg, { ...common, field: seen, panel: { x: 320, y: 0, w: 320, h: height }, title: "Seen through the blur" });
    drawPlot(cvPlot, {
      xRange: [-HALF, HALF],
      yRange: [0, 1.35],
      xLabel: "along the line (mm)",
      yLabel: "signal",
      legendLeft: true,
      series: [
        { x: xs, y: xs.map((x) => (Math.abs(x) > g / 2 ? 1 : 0)), color: COLORS.gray, dash: [5, 4], label: "as made" },
        { x: xs, y: xs.map((x) => bandGapImage(x, 0, w, g, sigma)), color: COLORS.vermillion, label: "seen" },
        { x: [-HALF, HALF], y: [0.5, 0.5], color: COLORS.ink, dash: [2, 3], width: 1 },
      ],
    });
    const c = gapCenter(w, g, sigma);
    const gmin = minVisibleGap(w, sigma);
    readout.textContent =
      `Line ${bandPeak(w, sigma).toFixed(2)} of full contrast; gap center ${c.toFixed(2)}. ` +
      (Number.isFinite(gmin)
        ? `${c < 0.5 ? "The gap is visible" : "The gap is hidden"}: the smallest visible gap at this blur and line width is ${gmin.toFixed(2)} mm.`
        : "The line itself stays below half contrast, so neither it nor its gaps can be thresholded.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m53-d1-root");
if (root) mount(root);
