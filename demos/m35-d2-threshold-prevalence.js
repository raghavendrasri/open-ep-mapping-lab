// m35-d2 · Threshold, prevalence and predictive values. MIT License.
import { binormalAuc, binormalSe, binormalSp, predictiveValues } from "./m35-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Scores of negative cases follow N(0, 1) and of positive cases N(d, 1). Left: the ROC curve and the operating " +
        "point for the chosen threshold. Right: positive and negative predictive values as prevalence changes, at that threshold.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const roc = setupCanvas(row, { width: 320, height: 280, label: "ROC curve with the operating point" });
  const pv = setupCanvas(row, { width: 320, height: 280, label: "Predictive values versus prevalence" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const d = addSlider(controls, { id: "m35-d2-d", label: "Class separation d (SD units)", min: 0, max: 4, step: 0.1, value: 1.5, digits: 1, onInput: draw });
  const t = addSlider(controls, { id: "m35-d2-t", label: "Decision threshold", min: -2, max: 5, step: 0.05, value: 0.75, onInput: draw });
  const prev = addSlider(controls, { id: "m35-d2-prev", label: "Prevalence π", min: 0.01, max: 0.9, step: 0.01, value: 0.1, onInput: draw });

  const ts = Array.from({ length: 241 }, (_, i) => -6 + i * 0.05);
  const prevs = Array.from({ length: 90 }, (_, i) => 0.01 + i * 0.01);

  function draw() {
    const dv = Number(d.value);
    const tv = Number(t.value);
    const pi = Number(prev.value);
    const se = binormalSe(tv, dv);
    const sp = binormalSp(tv);
    drawPlot(roc, {
      xRange: [0, 1],
      yRange: [0, 1],
      xLabel: "1 − specificity",
      yLabel: "sensitivity",
      series: [
        { x: ts.map((x) => 1 - binormalSp(x)), y: ts.map((x) => binormalSe(x, dv)), color: COLORS.blue },
        { x: [0, 1], y: [0, 1], color: COLORS.gray, dash: [4, 4] },
      ],
      markers: [{ x: 1 - sp, y: se, color: COLORS.vermillion, label: "threshold" }],
      margin: { l: 48 },
    });
    const curves = prevs.map((p) => predictiveValues(se, sp, p));
    drawPlot(pv, {
      xRange: [0, 0.9],
      yRange: [0, 1],
      xLabel: "prevalence π",
      yLabel: "predictive value",
      series: [
        { x: prevs, y: curves.map((c) => c.ppv), color: COLORS.vermillion, label: "PPV" },
        { x: prevs, y: curves.map((c) => c.npv), color: COLORS.blue, label: "NPV" },
      ],
      vlines: [{ x: pi, color: COLORS.gray }],
      margin: { l: 48 },
    });
    const { ppv, npv } = predictiveValues(se, sp, pi);
    readout.textContent =
      `AUC ${binormalAuc(dv).toFixed(3)}. At this threshold: sensitivity ${(100 * se).toFixed(0)}%, ` +
      `specificity ${(100 * sp).toFixed(0)}%. At prevalence ${(100 * pi).toFixed(0)}%: PPV ${(100 * ppv).toFixed(0)}%, NPV ${(100 * npv).toFixed(0)}%.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m35-d2-root");
if (root) mount(root);
