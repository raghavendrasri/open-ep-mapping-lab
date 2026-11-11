// m37-d2 · Screening yield and probabilities at a new prevalence. MIT License.
import { priorShift, screeningYield } from "./m37-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Left: for every 1,000 people screened, how many are flagged, and how many of those truly have the condition, as " +
        "prevalence changes. Right: a model's probability learned at one prevalence, corrected for use at another.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const left = setupCanvas(row, { width: 320, height: 280, label: "Flagged and true positives per 1000 screened versus prevalence" });
  const right = setupCanvas(row, { width: 320, height: 280, label: "Model probability before and after prevalence correction" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const se = addSlider(controls, { id: "m37-d2-se", label: "Sensitivity", min: 0.5, max: 1, step: 0.01, value: 0.8, onInput: draw });
  const sp = addSlider(controls, { id: "m37-d2-sp", label: "Specificity", min: 0.5, max: 1, step: 0.005, value: 0.9, digits: 3, onInput: draw });
  const prev = addSlider(controls, { id: "m37-d2-prev", label: "Prevalence where used", min: 0.005, max: 0.3, step: 0.005, value: 0.02, digits: 3, onInput: draw });
  const prevTrain = addSlider(controls, { id: "m37-d2-train", label: "Prevalence in training data", min: 0.05, max: 0.95, step: 0.05, value: 0.5, onInput: draw });

  const prevs = Array.from({ length: 60 }, (_, i) => 0.005 + i * 0.005);
  const ps = Array.from({ length: 101 }, (_, i) => i / 100);

  function draw() {
    const s1 = Number(se.value);
    const s2 = Number(sp.value);
    const pi = Number(prev.value);
    const pt = Number(prevTrain.value);
    const ys = prevs.map((p) => screeningYield(1000, p, s1, s2));
    const ymax = Math.max(...ys.map((y) => y.flagged)) * 1.05;
    drawPlot(left, {
      xRange: [0, 0.3],
      yRange: [0, ymax],
      xLabel: "prevalence",
      yLabel: "people per 1000 screened",
      series: [
        { x: prevs, y: ys.map((y) => y.flagged), color: COLORS.vermillion, label: "flagged" },
        { x: prevs, y: ys.map((y) => y.tp), color: COLORS.blue, label: "true positives" },
      ],
      vlines: [{ x: pi, color: COLORS.gray }],
      margin: { l: 52 },
    });
    drawPlot(right, {
      xRange: [0, 1],
      yRange: [0, 1],
      xLabel: "probability at training prevalence",
      yLabel: "probability where used",
      series: [
        { x: ps, y: ps.map((p) => priorShift(p, pt, pi)), color: COLORS.green, label: "corrected" },
        { x: [0, 1], y: [0, 1], color: COLORS.gray, dash: [4, 4] },
      ],
      margin: { l: 62 },
    });
    const y = screeningYield(1000, pi, s1, s2);
    readout.textContent =
      `Per 1,000 screened at prevalence ${(100 * pi).toFixed(1)}%: ${y.flagged.toFixed(0)} flagged, ${y.tp.toFixed(1)} true cases found, ` +
      `${y.fp.toFixed(0)} false alarms; about ${y.perCase.toFixed(1)} flags per true case. ` +
      `A probability of 0.50 learned at ${(100 * pt).toFixed(0)}% prevalence means ${priorShift(0.5, pt, pi).toFixed(3)} here.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m37-d2-root");
if (root) mount(root);
