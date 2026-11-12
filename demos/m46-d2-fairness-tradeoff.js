// m46-d2 · Equal error rates or equal predictive values? With different prevalences, not both.
// MIT License. Closed-form; tested against Python.
import { fprFromPpv, ppv } from "./m46-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "One detector with the same sensitivity (TPR) and false-positive rate (FPR) in two patient groups. The curve " +
        "is the positive predictive value (PPV) against prevalence; the dots are the two groups. With different " +
        "prevalences the PPVs differ, and equalizing PPV would require a different FPR in group B.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Positive predictive value against prevalence for two groups" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const pa = addSlider(controls, { id: "m46-d2-pa", label: "Prevalence, group A", min: 0.01, max: 0.5, step: 0.01, value: 0.05, digits: 2, onInput: draw });
  const pb = addSlider(controls, { id: "m46-d2-pb", label: "Prevalence, group B", min: 0.01, max: 0.5, step: 0.01, value: 0.25, digits: 2, onInput: draw });
  const tpr = addSlider(controls, { id: "m46-d2-tpr", label: "Sensitivity (TPR)", min: 0.5, max: 0.99, step: 0.01, value: 0.9, digits: 2, onInput: draw });
  const fpr = addSlider(controls, { id: "m46-d2-fpr", label: "False-positive rate (FPR)", min: 0.01, max: 0.3, step: 0.01, value: 0.05, digits: 2, onInput: draw });

  function draw() {
    const t = Number(tpr.value);
    const f = Number(fpr.value);
    const a = Number(pa.value);
    const b = Number(pb.value);
    const xs = Array.from({ length: 99 }, (_, i) => 0.005 + (i * 0.495) / 98);
    const ppvA = ppv(a, t, f);
    const ppvB = ppv(b, t, f);
    drawPlot(cv, {
      xRange: [0, 0.5], yRange: [0, 1], xLabel: "prevalence", yLabel: "PPV",
      series: [{ x: xs, y: xs.map((p) => ppv(p, t, f)), color: COLORS.blue, width: 2.5, label: "PPV at this TPR and FPR" }],
      markers: [{ x: a, y: ppvA, color: COLORS.orange, label: "group A" }, { x: b, y: ppvB, color: COLORS.purple, label: "group B" }],
      legendLeft: true,
    });
    const needed = fprFromPpv(b, ppvA, t);
    readout.textContent =
      `PPV is ${(100 * ppvA).toFixed(1)}% in group A and ${(100 * ppvB).toFixed(1)}% in group B with the same TPR ${t.toFixed(2)} and FPR ${f.toFixed(2)}. ` +
      `For group B to have group A's PPV at the same TPR, its FPR would have to be ${needed.toFixed(3)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m46-d2-root");
if (root) mount(root);
