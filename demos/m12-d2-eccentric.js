// m12-d2 · An off-center heart distorts the lead vectors (eq-m12-series, eq-m12-lead). MIT License.
// Tested in tests/test_m12_demos.py.
import { LIMBS, frontalAxis, leadVector, leadsForDipole } from "./m12-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Lead vectors of leads I, II and III in a homogeneous spherical torso, drawn from the origin. Gray: heart at the " +
        "center, Einthoven's equilateral triangle. Colored: heart moved toward the left or the feet. The readout applies " +
        "the textbook axis formula, which assumes the gray triangle, to a heart vector pointing at 60°.",
    ),
  );
  const cv = setupCanvas(root, { width: 420, height: 360, label: "Frontal components of the limb-lead vectors" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const xS = addSlider(controls, { id: "m12-d2-x", label: "Heart offset toward the left (fraction of torso radius)", min: 0, max: 0.5, step: 0.01, value: 0.3, digits: 2, onInput: draw });
  const yS = addSlider(controls, { id: "m12-d2-y", label: "Heart offset toward the feet (fraction of torso radius)", min: -0.3, max: 0.3, step: 0.01, value: 0, digits: 2, onInput: draw });

  const pairs = { I: ["L", "R"], II: ["F", "R"], III: ["F", "L"] };
  const colors = { I: COLORS.blue, II: COLORS.green, III: COLORS.vermillion };

  function draw() {
    const r0 = [Number(xS.value), Number(yS.value), 0];
    const series = [];
    for (const [k, [a, b]] of Object.entries(pairs)) {
      const ideal = leadVector(LIMBS[a], LIMBS[b]);
      const real = leadVector(LIMBS[a], LIMBS[b], r0);
      series.push({ x: [0, ideal[0]], y: [0, -ideal[1]], color: COLORS.gray, width: 1.5 });
      series.push({ x: [0, real[0]], y: [0, -real[1]], color: colors[k], width: 3, label: `lead ${k}` });
    }
    drawPlot(cv, { xRange: [-0.7, 0.7], yRange: [-0.7, 0.5], xLabel: "toward the left arm →", yLabel: "up = toward the head", series });
    const p = [Math.cos(Math.PI / 3), Math.sin(Math.PI / 3), 0];
    const L = leadsForDipole(p, r0);
    readout.textContent = `Heart vector at 60°: the axis formula gives ${frontalAxis(L.I, L.aVF).toFixed(0)}°.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m12-d2-root");
if (root) mount(root);
