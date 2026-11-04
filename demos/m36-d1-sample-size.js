// m36-d1 · Verification sample size and the operating characteristic. MIT License.
import { acceptanceN, passProbability } from "./m36-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Choose the reliability to demonstrate, the confidence and how many failures the plan allows. " +
        "The curve is the plan's operating characteristic: the probability of passing for each true reliability. " +
        "The dot is the design point: a device that is only as good as the target passes with probability at most 1 − C.",
    ),
  );
  const plot = setupCanvas(root, { width: 640, height: 260, label: "Probability of passing the test plan versus true reliability" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const R = addSlider(controls, { id: "m36-d1-r", label: "Reliability to show R", min: 0.8, max: 0.995, step: 0.005, value: 0.95, digits: 3, onInput: draw });
  const C = addSlider(controls, { id: "m36-d1-c", label: "Confidence C", min: 0.8, max: 0.99, step: 0.01, value: 0.95, onInput: draw });
  const c = addSlider(controls, { id: "m36-d1-f", label: "Failures allowed c", min: 0, max: 5, step: 1, value: 0, digits: 0, onInput: draw });

  function draw() {
    const r = Number(R.value);
    const conf = Number(C.value);
    const cv = Number(c.value);
    const n = acceptanceN(r, conf, cv);
    const lo = Math.max(0.5, 1 - 4 * (1 - r));
    const xs = Array.from({ length: 201 }, (_, i) => lo + ((1 - lo) * i) / 200);
    drawPlot(plot, {
      xRange: [lo, 1],
      yRange: [0, 1],
      xLabel: "true reliability",
      yLabel: "probability of passing",
      series: [{ x: xs, y: xs.map((x) => passProbability(n, cv, x)), color: COLORS.blue, label: `plan: n = ${n}, c = ${cv}` }],
      markers: [{ x: r, y: passProbability(n, cv, r), color: COLORS.vermillion, label: "design point" }],
      vlines: [{ x: r, color: COLORS.gray }],
      legendLeft: true,
    });
    readout.textContent =
      `Test ${n} units with at most ${cv} failure${cv === 1 ? "" : "s"}. If the true reliability were only ${r.toFixed(3)}, ` +
      `the plan would pass with probability ${passProbability(n, cv, r).toFixed(3)} (≤ ${(1 - conf).toFixed(2)}).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m36-d1-root");
if (root) mount(root);
