// m54-d1 · Why thin myocardium looks dim: a slab of uptake blurred by the scanner (eq-m54-recovery). MIT License.
// Tested in tests/test_m54_demos.py.
import { PET_FWHM_MM, fwhmToSigma, rcMean, rcPeak, slabProfile } from "./m54-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A wall of tissue with uniform uptake, seen through the blur of a PET scanner. Top: the true profile and the " +
        "measured one. Bottom: how much of the true value the maximum and the mean recover, against wall " +
        "thickness. Clinical scanners resolve about 4–7 mm; the heart wall is not much thicker.",
    ),
  );
  const cvProf = setupCanvas(root, { width: 640, height: 200, label: "True and blurred uptake across a wall" });
  const cvRc = setupCanvas(root, { width: 640, height: 200, label: "Recovery coefficients against wall thickness" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const wall = addSlider(controls, { id: "m54-d1-wall", label: "Wall thickness", min: 2, max: 20, step: 0.5, value: 10, digits: 1, unit: "mm", onInput: draw });
  const fwhm = addSlider(controls, { id: "m54-d1-fwhm", label: "Scanner blur (FWHM)", min: 3, max: 10, step: 0.5, value: 5.5, digits: 1, unit: "mm", onInput: draw });
  const xs = Array.from({ length: 401 }, (_, i) => -20 + i * 0.1);
  const ws = Array.from({ length: 291 }, (_, i) => 1 + i * 0.1);

  function draw() {
    const w = Number(wall.value);
    const s = fwhmToSigma(Number(fwhm.value));
    drawPlot(cvProf, {
      xRange: [-20, 20],
      yRange: [0, 1.4],
      xLabel: "position across the wall (mm)",
      yLabel: "uptake (fraction of true)",
      legendLeft: true,
      series: [
        { x: xs, y: xs.map((x) => (Math.abs(x) <= w / 2 ? 1 : 0)), color: COLORS.gray, dash: [5, 4], label: "true" },
        { x: xs, y: xs.map((x) => slabProfile(x, w, s)), color: COLORS.vermillion, label: "measured" },
      ],
    });
    drawPlot(cvRc, {
      xRange: [1, 30],
      yRange: [0, 1.35],
      xLabel: "wall thickness (mm)",
      yLabel: "recovery",
      series: [
        { x: ws, y: ws.map((v) => rcPeak(v, s)), color: COLORS.blue, label: "maximum" },
        { x: ws, y: ws.map((v) => rcMean(v, s)), color: COLORS.green, label: "mean over the wall" },
      ],
      markers: [
        { x: w, y: rcPeak(w, s), color: COLORS.blue },
        { x: w, y: rcMean(w, s), color: COLORS.green },
      ],
    });
    const inRange = Number(fwhm.value) >= PET_FWHM_MM[0] && Number(fwhm.value) <= PET_FWHM_MM[1];
    readout.textContent =
      `Wall ${w.toFixed(1)} mm, blur ${Number(fwhm.value).toFixed(1)} mm FWHM${inRange ? " (within the 4–7 mm reported for clinical scanners)" : ""}. ` +
      `The maximum recovers ${(100 * rcPeak(w, s)).toFixed(0)}% and the mean over the wall ${(100 * rcMean(w, s)).toFixed(0)}% of the true uptake; ` +
      `a true uptake of 6 would read ${(6 * rcMean(w, s)).toFixed(1)} on average.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m54-d1-root");
if (root) mount(root);
