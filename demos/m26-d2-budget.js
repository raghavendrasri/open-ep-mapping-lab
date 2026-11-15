// m26-d2 · Per-point error budget and map uncertainty against distance (eq-m26-budget, eq-m26-gp, eq-m26-density).
// MIT License. Tested in tests/test_m26_demos.py.
import { errorBudget, nnDistanceMean, singlePointVariance } from "./m26-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Each mapped point carries annotation, reference and position errors; a position error becomes a time error " +
        "of distance over conduction speed. Together they set the per-point error (black). The map's uncertainty " +
        "(blue), counting only the nearest point, starts there and grows with distance to it. The dotted line marks " +
        "the mean distance to the nearest point at the chosen point density.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Error components and map uncertainty against distance to the nearest point" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const aS = addSlider(controls, { id: "m26-d2-a", label: "Annotation error (SD)", min: 0.2, max: 5, step: 0.1, value: 1, digits: 1, unit: "ms", onInput: draw });
  const rS = addSlider(controls, { id: "m26-d2-r", label: "Reference error (SD)", min: 0, max: 5, step: 0.1, value: 2, digits: 1, unit: "ms", onInput: draw });
  const xS = addSlider(controls, { id: "m26-d2-x", label: "Position error (SD)", min: 0, max: 5, step: 0.1, value: 2, digits: 1, unit: "mm", onInput: draw });
  const dS = addSlider(controls, { id: "m26-d2-rho", label: "Point density", min: 0.25, max: 4, step: 0.05, value: 1, digits: 2, unit: "/cm²", onInput: draw });
  const c = 1.0, ell = 8, s2 = 400;

  function draw() {
    const sa = Number(aS.value), sr = Number(rS.value), sx = Number(xS.value), rho = Number(dS.value) / 100;
    const sn = errorBudget(sa, sr, sx, c);
    const ds = [], map = [];
    for (let d = 0; d <= 20.0001; d += 0.1) { ds.push(d); map.push(Math.sqrt(singlePointVariance(d, ell, s2, sn))); }
    const dnn = nnDistanceMean(rho);
    const at = Math.sqrt(singlePointVariance(dnn, ell, s2, sn));
    const flat = (v) => [v, v];
    const ymax = Math.max(12, Math.max(...map.filter((_, i) => ds[i] <= 12)) * 1.2);
    drawPlot(cv, {
      xRange: [0, 20], yRange: [0, ymax], xLabel: "distance to the nearest mapped point (mm)", yLabel: "SD (ms)",
      series: [
        { x: [0, 20], y: flat(sa), color: COLORS.orange, width: 1.2, dash: [4, 3], label: "annotation" },
        { x: [0, 20], y: flat(sr), color: COLORS.purple, width: 1.2, dash: [4, 3], label: "reference" },
        { x: [0, 20], y: flat(sx / c), color: COLORS.green, width: 1.2, dash: [4, 3], label: "position" },
        { x: [0, 20], y: flat(sn), color: COLORS.ink, width: 1.6, label: "per point" },
        { x: ds, y: map, color: COLORS.blue, width: 2.4, label: "map" },
        { x: [dnn, dnn], y: [0, ymax], color: COLORS.gray, width: 1, dash: [2, 3] },
      ],
    });
    readout.textContent = `Per-point error ${sn.toFixed(2)} ms; at the mean nearest-point distance ` +
      `(${dnn.toFixed(1)} mm for ${Number(dS.value).toFixed(2)} points/cm²), that one point alone gives an SD of ${at.toFixed(2)} ms; other nearby points lower it.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m26-d2-root");
if (root) mount(root);
