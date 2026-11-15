// m23-d1 · Bipolar amplitude against wavefront direction (eq-m23-amplitude, eq-m23-direction). MIT License.
// Tested in tests/test_m23_demos.py.
import { bipolarPp, pairAndField } from "./m23-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A planar front crosses healthy tissue at an angle to the catheter. Gray: one bipole. Orange: the larger of two " +
        "orthogonal bipoles. Blue: the largest peak-to-peak over all projections of the pair (an orientation-free " +
        "amplitude). All are relative to a bipole aligned with propagation. The dashed line is a threshold as a " +
        "fraction of that aligned amplitude.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Peak-to-peak amplitude against wavefront angle" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dS = addSlider(controls, { id: "m23-d1-d", label: "Bipole spacing", min: 0.5, max: 6, step: 0.5, value: 2, digits: 1, unit: "mm", onInput: draw });
  const hS = addSlider(controls, { id: "m23-d1-h", label: "Electrode height above tissue", min: 0.2, max: 4, step: 0.1, value: 1, digits: 1, unit: "mm", onInput: draw });
  const qS = addSlider(controls, { id: "m23-d1-q", label: "Threshold (fraction of aligned)", min: 0.1, max: 0.9, step: 0.01, value: 0.33, digits: 2, onInput: draw });
  const w = 0.3;

  function draw() {
    const d = Number(dS.value), a = w + Number(hS.value), q = Number(qS.value);
    const ref = bipolarPp(a, d, 0);
    const ang = [], single = [], pair = [], field = [];
    for (let deg = 0; deg <= 180; deg += 2) {
      const r = pairAndField(a, d, (deg * Math.PI) / 180);
      ang.push(deg); single.push(r.single / ref); pair.push(r.pair / ref); field.push(r.field / ref);
    }
    const frac = (arr) => (100 * arr.filter((v) => v < q).length) / arr.length;
    const ymax = Math.max(1.9, 1.6 * Math.max(...field));
    drawPlot(cv, {
      xRange: [0, 180], yRange: [0, ymax], xLabel: "angle between bipole and propagation (degrees)", yLabel: "amplitude / aligned bipole",
      series: [
        { x: ang, y: single, color: COLORS.gray, width: 2, label: "one bipole" },
        { x: ang, y: pair, color: COLORS.orange, width: 2, label: "larger of a pair" },
        { x: ang, y: field, color: COLORS.blue, width: 2.4, label: "largest projection" },
        { x: [0, 180], y: [q, q], color: COLORS.vermillion, width: 1.2, dash: [6, 4], label: "threshold" },
      ],
    });
    readout.textContent =
      `Below the threshold for ${frac(single).toFixed(1)}% of directions with one bipole, ${frac(pair).toFixed(1)}% with ` +
      `the larger of a pair, ${frac(field).toFixed(1)}% with the largest projection. Aligned bipole: ${(ref * a).toFixed(3)} of the unipolar peak-to-peak.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m23-d1-root");
if (root) mount(root);
