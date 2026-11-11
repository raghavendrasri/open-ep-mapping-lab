// m44-d2 · Error compounding: why long agent chains need checks and a human reviewer. MIT License.
import { chainSuccess, checkedChain, escapedErrors } from "./m44-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const N_TASKS = 100;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Probability that an agent completes a task correctly, against the number of steps in the task. Each step " +
        "succeeds independently with probability p. With a check, a failed step is caught with probability c and " +
        "retried once, and the retry succeeds with probability p. A human reviewer then catches a share r of the " +
        "wrong outputs that remain.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Task success against number of steps, with and without a checking step" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const p = addSlider(controls, { id: "m44-d2-p", label: "Step success p", min: 0.8, max: 1, step: 0.01, value: 0.95, digits: 2, onInput: draw });
  const n = addSlider(controls, { id: "m44-d2-n", label: "Steps n", min: 1, max: 40, step: 1, value: 10, digits: 0, onInput: draw });
  const c = addSlider(controls, { id: "m44-d2-c", label: "Check catches c", min: 0, max: 1, step: 0.05, value: 0.8, digits: 2, onInput: draw });
  const r = addSlider(controls, { id: "m44-d2-r", label: "Reviewer catches r", min: 0, max: 1, step: 0.05, value: 0.5, digits: 2, onInput: draw });

  function draw() {
    const pv = Number(p.value);
    const nv = Number(n.value);
    const cv_ = Number(c.value);
    const rv = Number(r.value);
    const ns = Array.from({ length: 40 }, (_, i) => i + 1);
    drawPlot(cv, {
      xRange: [1, 40],
      yRange: [0, 1.05],
      xLabel: "steps in the task, n",
      yLabel: "task success (probability)",
      series: [
        { x: ns, y: ns.map((k) => checkedChain(pv, cv_, k, pv)), color: COLORS.green, width: 2.5, label: "with a check and one retry" },
        { x: ns, y: ns.map((k) => chainSuccess(pv, k)), color: COLORS.vermillion, width: 2.5, label: "no check" },
      ],
      vlines: [{ x: nv, color: COLORS.gray }],
      markers: [
        { x: nv, y: chainSuccess(pv, nv), color: COLORS.vermillion },
        { x: nv, y: checkedChain(pv, cv_, nv, pv), color: COLORS.green },
      ],
    });
    const plain = chainSuccess(pv, nv);
    const checked = checkedChain(pv, cv_, nv, pv);
    readout.textContent =
      `${nv} steps at p = ${pv.toFixed(2)}: ${(100 * plain).toFixed(1)}% of tasks succeed without a check, ` +
      `${(100 * checked).toFixed(1)}% with one. Of ${N_TASKS} tasks, about ${escapedErrors(N_TASKS, plain, rv).toFixed(1)} ` +
      `wrong outputs get past the reviewer without the check, ${escapedErrors(N_TASKS, checked, rv).toFixed(1)} with it.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m44-d2-root");
if (root) mount(root);
