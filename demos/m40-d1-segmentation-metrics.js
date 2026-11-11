// m40-d1 · Overlap and distance metrics for a predicted region with a boundary error and a stray island.
// MIT License.
import { circleIslandMetrics } from "./m40-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A true region (blue circle) and a prediction (orange): a concentric outline with a boundary error, plus an optional " +
        "stray island. Left: the outlines. Right: Dice and normalized surface Dice (NSD) as the boundary error changes, with " +
        "the island as set; the markers show the chosen error.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const left = setupCanvas(row, { width: 300, height: 280, label: "True outline, predicted outline and island" });
  const right = setupCanvas(row, { width: 340, height: 280, label: "Dice and NSD versus boundary error" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const delta = addSlider(controls, { id: "m40-d1-delta", label: "Boundary error (+ grows, − shrinks)", min: -4, max: 4, step: 0.1, value: 1, digits: 1, unit: "mm", onInput: draw });
  const rho = addSlider(controls, { id: "m40-d1-rho", label: "Island radius (0 = none)", min: 0, max: 6, step: 0.5, value: 2, digits: 1, unit: "mm", onInput: draw });
  const gap = addSlider(controls, { id: "m40-d1-gap", label: "Island gap", min: 1, max: 40, step: 0.5, value: 15, digits: 1, unit: "mm", onInput: draw });
  const R = addSlider(controls, { id: "m40-d1-R", label: "True region radius", min: 5, max: 30, step: 0.5, value: 20, digits: 1, unit: "mm", onInput: draw });
  const tau = addSlider(controls, { id: "m40-d1-tau", label: "NSD tolerance τ", min: 0.5, max: 8, step: 0.5, value: 4, digits: 1, unit: "mm", onInput: draw });

  const circle = (cx, rad) => {
    const a = Array.from({ length: 145 }, (_, i) => (2 * Math.PI * i) / 144);
    return { x: a.map((t) => cx + rad * Math.cos(t)), y: a.map((t) => rad * Math.sin(t)) };
  };
  function draw() {
    const Rv = Number(R.value);
    const dv = Number(delta.value);
    const rv = Number(rho.value);
    const gv = Number(gap.value);
    const tv = Number(tau.value);
    const m = circleIslandMetrics(Rv, dv, rv, gv, tv);
    const right_edge = rv > 0 ? m.islandCentre + rv : Rv + Math.max(dv, 0);
    const span = Math.max(right_edge, Rv + 4) + 2;
    const t = circle(0, Rv);
    const p = circle(0, Rv + dv);
    const series = [
      { x: t.x, y: t.y, color: COLORS.blue, width: 2, label: "true" },
      { x: p.x, y: p.y, color: COLORS.vermillion, width: 2, label: "predicted" },
    ];
    if (rv > 0) {
      const isl = circle(m.islandCentre, rv);
      series.push({ x: isl.x, y: isl.y, color: COLORS.vermillion, width: 2 });
    }
    drawPlot(left, { xRange: [-span, span], yRange: [-span, span], xLabel: "x (mm)", yLabel: "y (mm)", series, margin: { l: 46 } });
    const ds = Array.from({ length: 81 }, (_, i) => -4 + (i * 8) / 80);
    const curves = ds.map((x) => circleIslandMetrics(Rv, x, rv, gv, tv, 720));
    drawPlot(right, {
      xRange: [-4, 4],
      yRange: [0, 1.2],
      xLabel: "boundary error (mm)",
      yLabel: "score (0 to 1)",
      legendLeft: true,
      series: [
        { x: ds, y: curves.map((c) => c.dice), color: COLORS.green, width: 2, label: "Dice" },
        { x: ds, y: curves.map((c) => c.nsd), color: COLORS.purple, width: 2, dash: [5, 4], label: `NSD (τ = ${tv} mm)` },
      ],
      markers: [
        { x: dv, y: m.dice, color: COLORS.green },
        { x: dv, y: m.nsd, color: COLORS.purple },
      ],
      margin: { l: 50 },
    });
    readout.textContent =
      `Dice ${m.dice.toFixed(3)}, NSD at ${tv} mm ${m.nsd.toFixed(3)}, Hausdorff distance ${m.hd.toFixed(1)} mm, ` +
      `average symmetric surface distance ${m.assd.toFixed(2)} mm. ` +
      (rv > 0 && m.hd > 2 * Math.abs(dv) + 1
        ? "The island sets the Hausdorff distance while Dice hardly moves."
        : "Without a distant island, the Hausdorff distance equals the boundary error.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m40-d1-root");
if (root) mount(root);
