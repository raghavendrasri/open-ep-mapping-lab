// m21-d1 · Iterative closest point from different starting rotations (eq-m21-icp). MIT License.
// Tested in tests/test_m21_demos.py.
import { applyRt, icp2, outline } from "./m21-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Gray: an image-derived outline of a chamber with a vein-like bump. Orange: 60 mapped points of the same wall, " +
        "rotated and shifted as they arrive. Blue: the mapped points after iterative closest point (closest-point " +
        "matching, then a least-squares rotation, repeated). From small rotations ICP finds the truth; from large ones it " +
        "can settle into a wrong fit whose surface distance is still small.",
    ),
  );
  const cv = setupCanvas(root, { width: 460, height: 400, label: "Outline, mapped points and their registration" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const aS = addSlider(controls, { id: "m21-d1-angle", label: "Starting rotation", min: 0, max: 180, step: 5, value: 40, digits: 0, unit: "°", onInput: draw });
  const kS = addSlider(controls, { id: "m21-d1-iters", label: "ICP iterations", min: 0, max: 60, step: 1, value: 30, digits: 0, onInput: draw });
  const target = outline(400), truth = outline(60);

  function draw() {
    const a = (Number(aS.value) * Math.PI) / 180, k = Number(kS.value);
    const Rs = [[Math.cos(a), -Math.sin(a)], [Math.sin(a), Math.cos(a)]];
    const src = applyRt(Rs, [6, -4], truth);
    const { R, t, hist } = icp2(src, target, k);
    const reg = applyRt(R, t, src);
    const close = (P) => ({ x: [...P.map((p) => p[0]), P[0][0]], y: [...P.map((p) => p[1]), P[0][1]] });
    const err = Math.sqrt(reg.reduce((s, p, i) => s + (p[0] - truth[i][0]) ** 2 + (p[1] - truth[i][1]) ** 2, 0) / reg.length);
    drawPlot(cv, {
      xRange: [-50, 50], yRange: [-45, 45], xLabel: "x (mm)", yLabel: "y (mm)",
      series: [
        { ...close(target), color: COLORS.gray, width: 2, label: "image outline" },
        { ...close(src), color: COLORS.orange, width: 1.2, dash: [4, 3], label: "mapped, as acquired" },
        { ...close(reg), color: COLORS.blue, width: 2, label: "after ICP" },
      ],
    });
    readout.textContent =
      `After ${k} iterations: RMS surface distance ${Math.sqrt(hist[hist.length - 1]).toFixed(2)} mm, ` +
      `RMS error against the true positions ${err.toFixed(2)} mm.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m21-d1-root");
if (root) mount(root);
