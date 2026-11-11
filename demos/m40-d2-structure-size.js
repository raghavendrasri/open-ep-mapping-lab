// m40-d2 · The same boundary error costs more Dice on thin structures. MIT License.
import { discDice, offsetDiceFirstOrder, slabDice, sphereDice } from "./m40-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Dice after a uniform boundary error for three shapes: a sphere (a blood pool), a long cylinder (a vein) and a wall " +
        "shifted along its normal. Curves are exact; the markers show the chosen error.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Dice versus boundary error for a sphere, a cylinder and a wall" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const delta = addSlider(controls, { id: "m40-d2-delta", label: "Boundary error", min: 0, max: 3, step: 0.05, value: 1, digits: 2, unit: "mm", onInput: draw });
  const R = addSlider(controls, { id: "m40-d2-R", label: "Sphere radius (blood pool)", min: 10, max: 40, step: 1, value: 25, digits: 0, unit: "mm", onInput: draw });
  const r = addSlider(controls, { id: "m40-d2-r", label: "Cylinder radius (vein)", min: 2, max: 10, step: 0.5, value: 5, digits: 1, unit: "mm", onInput: draw });
  const t = addSlider(controls, { id: "m40-d2-t", label: "Wall thickness", min: 0.5, max: 3.5, step: 0.01, value: 1.89, digits: 2, unit: "mm", onInput: draw });

  function draw() {
    const d = Number(delta.value);
    const Rv = Number(R.value);
    const rv = Number(r.value);
    const tv = Number(t.value);
    const xs = Array.from({ length: 121 }, (_, i) => (i * 3) / 120);
    drawPlot(cv, {
      xRange: [0, 3],
      yRange: [0, 1.2],
      xLabel: "boundary error (mm)",
      yLabel: "Dice (0 to 1)",
      series: [
        { x: xs, y: xs.map((x) => sphereDice(Rv, x)), color: COLORS.blue, width: 2, label: `sphere, R = ${Rv} mm` },
        { x: xs, y: xs.map((x) => discDice(rv, x)), color: COLORS.green, width: 2, label: `cylinder, r = ${rv} mm` },
        { x: xs, y: xs.map((x) => slabDice(tv, x)), color: COLORS.vermillion, width: 2, label: `wall, t = ${tv.toFixed(2)} mm` },
      ],
      markers: [
        { x: d, y: sphereDice(Rv, d), color: COLORS.blue },
        { x: d, y: discDice(rv, d), color: COLORS.green },
        { x: d, y: slabDice(tv, d), color: COLORS.vermillion },
      ],
      vlines: [{ x: d, color: COLORS.gray }],
    });
    const lin = offsetDiceFirstOrder(d, 4 * Math.PI * Rv ** 2, (4 / 3) * Math.PI * Rv ** 3); // S and V of the sphere
    readout.textContent =
      `A ${d.toFixed(2)} mm error gives Dice ${sphereDice(Rv, d).toFixed(3)} for the sphere (first-order estimate ` +
      `${lin.toFixed(3)}), ${discDice(rv, d).toFixed(3)} for the cylinder and ${slabDice(tv, d).toFixed(3)} for the wall.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m40-d2-root");
if (root) mount(root);
