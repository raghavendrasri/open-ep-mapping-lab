// m39-d2 · Overlap (Dice) and centroid distance answer different questions. MIT License.
import { discDice } from "./m39-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A true target region (blue disc) and a predicted region (orange disc). Left: the two discs. Right: their Dice overlap " +
        "as the distance between their centres grows; the marker is the chosen distance.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const left = setupCanvas(row, { width: 300, height: 280, label: "True and predicted discs" });
  const right = setupCanvas(row, { width: 340, height: 280, label: "Dice overlap versus centroid distance" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const R = addSlider(controls, { id: "m39-d2-R", label: "True region radius", min: 1, max: 20, step: 0.5, value: 5, digits: 1, unit: "mm", onInput: draw });
  const r = addSlider(controls, { id: "m39-d2-r", label: "Predicted region radius", min: 1, max: 20, step: 0.5, value: 5, digits: 1, unit: "mm", onInput: draw });
  const d = addSlider(controls, { id: "m39-d2-d", label: "Distance between centres", min: 0, max: 30, step: 0.1, value: 7.3, digits: 1, unit: "mm", onInput: draw });

  const circle = (cx, rad) => {
    const a = Array.from({ length: 121 }, (_, i) => (2 * Math.PI * i) / 120);
    return { x: a.map((t) => cx + rad * Math.cos(t)), y: a.map((t) => rad * Math.sin(t)) };
  };
  function draw() {
    const Rv = Number(R.value);
    const rv = Number(r.value);
    const dv = Number(d.value);
    const span = Math.max(Rv, rv) + dv / 2 + 2;
    const c1 = circle(-dv / 2, Rv);
    const c2 = circle(dv / 2, rv);
    drawPlot(left, {
      xRange: [-span, span],
      yRange: [-span, span],
      xLabel: "x (mm)",
      yLabel: "y (mm)",
      series: [
        { x: c1.x, y: c1.y, color: COLORS.blue, width: 2, label: "true" },
        { x: c2.x, y: c2.y, color: COLORS.vermillion, width: 2, label: "predicted" },
      ],
      markers: [
        { x: -dv / 2, y: 0, color: COLORS.blue },
        { x: dv / 2, y: 0, color: COLORS.vermillion },
      ],
      margin: { l: 46 },
    });
    const ds = Array.from({ length: 151 }, (_, i) => (i * 30) / 150);
    drawPlot(right, {
      xRange: [0, 30],
      yRange: [0, 1],
      xLabel: "distance between centres (mm)",
      yLabel: "Dice overlap",
      series: [{ x: ds, y: ds.map((x) => discDice(Rv, rv, x)), color: COLORS.green }],
      markers: [{ x: dv, y: discDice(Rv, rv, dv), color: COLORS.ink }],
      margin: { l: 50 },
    });
    const dice = discDice(Rv, rv, dv);
    readout.textContent =
      `Centres ${dv.toFixed(1)} mm apart: Dice ${(100 * dice).toFixed(1)}%. ` +
      (dice < 0.2 && dv < 10
        ? "A prediction that looks close by centroid distance can still overlap the target very little when both regions are small."
        : "Dice falls to zero once the centres are more than the sum of the radii apart.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m39-d2-root");
if (root) mount(root);
