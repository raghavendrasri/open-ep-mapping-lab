// m20-d2 · Reconstructing a chamber outline from catheter positions (eq-m20-hull, eq-m20-closing). MIT License.
// Tested in tests/test_m20_demos.py.
import { boundaryPoints, hullMask, reconstruct, surfaceStats, truthMask, wallSamples } from "./m20-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A slice through an illustrative chamber with a concave notch and a vein-like stub (gray). Dots: catheter " +
        "positions within 2 mm of the wall. Orange: their convex hull, which bridges the notch. Blue: inflate every point " +
        "by r, fill the enclosed hole, shrink back by r. Too small an r leaves gaps; too large an r rounds off detail.",
    ),
  );
  const cv = setupCanvas(root, { width: 460, height: 420, label: "Chamber outline and two reconstructions" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const nS = addSlider(controls, { id: "m20-d2-n", label: "Catheter positions", min: 20, max: 400, step: 10, value: 160, digits: 0, onInput: draw });
  const rS = addSlider(controls, { id: "m20-d2-r", label: "Inflation radius r", min: 2, max: 10, step: 1, value: 5, digits: 0, unit: "mm", onInput: draw });
  const T = truthMask(), TB = boundaryPoints(T);

  function draw() {
    const n = Number(nS.value), r = Number(rS.value);
    const P = wallSamples(n, 2, 20);
    const H = hullMask(P), R = reconstruct(P, r);
    const sh = surfaceStats(H, T), sr = surfaceStats(R, T);
    const toMarkers = (B, color) => B.map(([x, y]) => ({ x, y, color, radius: 1.4 }));
    drawPlot(cv, {
      xRange: [-50, 50], yRange: [-50, 50], xLabel: "x (mm)", yLabel: "y (mm)",
      series: [
        { x: [], y: [], color: COLORS.gray, width: 2, label: "true wall" },
        { x: [], y: [], color: COLORS.orange, width: 2, label: "convex hull" },
        { x: [], y: [], color: COLORS.blue, width: 2, label: "inflate–fill–shrink" },
      ],
      markers: [...toMarkers(TB, COLORS.gray), ...toMarkers(boundaryPoints(H), COLORS.orange), ...toMarkers(boundaryPoints(R), COLORS.blue),
        ...P.map(([x, y]) => ({ x, y, color: COLORS.ink, radius: 2 }))],
    });
    const f = (s) => (Number.isFinite(s.hausdorff) ? `largest ${s.hausdorff.toFixed(1)} mm, mean ${s.mean.toFixed(2)} mm` : "no closed surface");
    readout.textContent = `Distance to the true wall. Hull: ${f(sh)}. Inflate–fill–shrink, r = ${r} mm: ${f(sr)}. (${n} positions.)`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m20-d2-root");
if (root) mount(root);
