// m36-d3 · Reliability of a series system. MIT License.
import { reliability, seriesRate } from "./m36-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const NAMES = ["Part A", "Part B", "Part C"];
const COLS = [COLORS.sky, COLORS.green, COLORS.purple];

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Three parts in series, each with a constant failure rate. The system survives only if every part does, " +
        "so its failure rate is the sum. Curves show the probability of surviving to each time.",
    ),
  );
  const plot = setupCanvas(root, { width: 640, height: 260, label: "Survival probability versus time for each part and the system" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const rates = NAMES.map((name, i) =>
    addSlider(controls, {
      id: `m36-d3-l${i}`,
      label: `${name} failure rate`,
      min: 0.1,
      max: 10,
      step: 0.1,
      value: [1, 0.5, 2][i],
      digits: 1,
      unit: "per 10⁴ h",
      onInput: draw,
    }),
  );
  const mission = addSlider(controls, { id: "m36-d3-t", label: "Mission time", min: 100, max: 20000, step: 100, value: 2000, digits: 0, unit: "h", onInput: draw });

  function draw() {
    const lam = rates.map((s) => Number(s.value) / 1e4); // per hour
    const lamSys = seriesRate(lam);
    const tMax = 20000;
    const ts = Array.from({ length: 201 }, (_, i) => (tMax * i) / 200);
    const tm = Number(mission.value);
    drawPlot(plot, {
      xRange: [0, tMax],
      yRange: [0, 1],
      xLabel: "time (h)",
      yLabel: "probability of surviving",
      series: [
        ...lam.map((l, i) => ({ x: ts, y: ts.map((t) => reliability(t, l)), color: COLS[i], label: NAMES[i] })),
        { x: ts, y: ts.map((t) => reliability(t, lamSys)), color: COLORS.ink, width: 2.5, label: "system" },
      ],
      vlines: [{ x: tm, color: COLORS.gray, label: "mission time" }],
    });
    const worst = lam.indexOf(Math.max(...lam));
    readout.textContent =
      `System failure rate ${(lamSys * 1e4).toFixed(1)} per 10⁴ h, MTBF ${Math.round(1 / lamSys)} h. ` +
      `Probability of surviving ${tm} h: ${reliability(tm, lamSys).toFixed(3)}. ` +
      `${NAMES[worst]} contributes ${((100 * lam[worst]) / lamSys).toFixed(0)}% of the failure rate.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m36-d3-root");
if (root) mount(root);
