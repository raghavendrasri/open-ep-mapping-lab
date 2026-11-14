// m10-d1 · The restitution map and alternans (eq-m10-restitution, eq-m10-alternans). MIT License.
// Tested in tests/test_m10_demos.py.
import { fixedPoint, iterateMap, restitution, restitutionSlope } from "./m10-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Gray: the restitution curve of the m08 cell model, action potential duration against the diastolic interval " +
        "before it. Blue: the pacing line APD = CL − DI for the cycle length you choose. They cross at the steady " +
        "state. Orange: successive beats after a 5-ms disturbance, drawn as a staircase between the two lines. Where " +
        "the curve is steeper than the line (slope above 1), the staircase spirals outward: alternans.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const web = setupCanvas(row, { width: 330, height: 300, label: "Restitution curve, pacing line and cobweb of successive beats" });
  const beats = setupCanvas(row, { width: 330, height: 300, label: "Action potential duration of successive beats" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const clS = addSlider(controls, { id: "m10-d1-cl", label: "Pacing cycle length", min: 140, max: 320, step: 1, value: 200, digits: 0, unit: "ms", onInput: draw });

  function draw() {
    const cl = Number(clS.value);
    const [apd, di] = fixedPoint(cl);
    const seq = iterateMap(cl, (Number.isFinite(apd) ? apd : 100) + 5, 14);
    const dis = Array.from({ length: 151 }, (_, i) => 0.5 + i * 2);
    const wx = [];
    const wy = [];
    for (let k = 0; k < seq.length - 1 && Number.isFinite(seq[k + 1]); k++) {
      const d = cl - seq[k];
      wx.push(d, d);
      wy.push(seq[k], seq[k + 1]);
    }
    drawPlot(web, {
      xRange: [0, 300],
      yRange: [0, 220],
      xLabel: "diastolic interval (ms)",
      yLabel: "APD (ms)",
      series: [
        { x: dis, y: dis.map((d) => restitution(d)), color: COLORS.gray, width: 2, label: "restitution" },
        { x: [0, cl], y: [cl, 0], color: COLORS.blue, width: 1.5, label: "APD = CL − DI" },
        { x: wx, y: wy, color: COLORS.vermillion, width: 1.5, label: "beats" },
      ],
      markers: Number.isFinite(apd) ? [{ x: di, y: apd, color: COLORS.ink }] : [],
    });
    drawPlot(beats, {
      xRange: [0, 14],
      yRange: [0, 220],
      xLabel: "beat number",
      yLabel: "APD (ms)",
      series: [{ x: seq.map((_, k) => k), y: seq, color: COLORS.vermillion, width: 2 }],
    });
    const slope = restitutionSlope(di);
    const blocked = seq.some((v) => !Number.isFinite(v));
    readout.textContent = Number.isFinite(apd)
      ? `CL ${cl} ms: steady APD ${apd.toFixed(1)} ms, DI ${di.toFixed(1)} ms, restitution slope ${slope.toFixed(2)}. ` +
        (slope < 1 ? "The disturbance dies out." : blocked ? "Alternans grows until a beat is blocked." : "Alternans grows.")
      : `CL ${cl} ms is too short for a steady 1:1 response.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m10-d1-root");
if (root) mount(root);
