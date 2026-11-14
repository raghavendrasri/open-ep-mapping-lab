// m11-d1 · AV nodal conduction and Wenckebach periodicity (eq-m11-avnode, eq-m11-wenckebach). MIT License.
// Tested in tests/test_m11_demos.py.
import { AVN, avSequence, conductionRatio, nodalTime } from "./m11-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Left: the AV nodal recovery curve, nodal conduction time against the time since the node last conducted. " +
        "Right: nodal conduction time for successive atrial paced beats at the cycle length you choose; red marks are " +
        "blocked beats. Shorten the cycle length below the Wenckebach point and conduction times lengthen beat by beat " +
        "until one is blocked.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const rec = setupCanvas(row, { width: 330, height: 280, label: "AV nodal recovery curve" });
  const seqc = setupCanvas(row, { width: 330, height: 280, label: "Nodal conduction time per paced beat" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const clS = addSlider(controls, { id: "m11-d1-cl", label: "Atrial pacing cycle length", min: 140, max: 400, step: 1, value: 220, digits: 0, unit: "ms", onInput: draw });

  // split a sequence into runs of conducted beats, so lines do not bridge blocked beats
  function segments(xs, ys) {
    const out = [];
    let cur = { x: [], y: [] };
    ys.forEach((v, i) => {
      if (Number.isFinite(v)) {
        cur.x.push(xs[i]);
        cur.y.push(v);
      } else if (cur.x.length) {
        out.push(cur);
        cur = { x: [], y: [] };
      }
    });
    if (cur.x.length) out.push(cur);
    return out.length ? out : [{ x: [], y: [] }];
  }

  function draw() {
    const cl = Number(clS.value);
    const rts = Array.from({ length: 120 }, (_, i) => AVN.erp + i * 3);
    drawPlot(rec, {
      xRange: [0, 450],
      yRange: [0, 170],
      xLabel: "recovery time (ms)",
      yLabel: "nodal conduction time (ms)",
      series: [{ x: rts, y: rts.map((r) => nodalTime(r)), color: COLORS.blue, width: 2 }],
      vlines: [{ x: AVN.erp, color: COLORS.gray, label: "nodal ERP" }],
    });
    const seq = avSequence(cl, 40).slice(16);
    const beats = seq.map((_, i) => i + 1);
    drawPlot(seqc, {
      xRange: [0, 25],
      yRange: [0, 170],
      xLabel: "paced beat",
      yLabel: "nodal conduction time (ms)",
      series: segments(beats, seq).map((g) => ({ x: g.x, y: g.y, color: COLORS.blue, width: 1.5 })),
      markers: seq
        .map((v, i) => (Number.isFinite(v) ? { x: beats[i], y: v, color: COLORS.blue } : { x: beats[i], y: 5, color: COLORS.vermillion }))
        .slice(0, 24),
    });
    const r = conductionRatio(avSequence(cl, 80));
    readout.textContent = r
      ? `At ${cl} ms: ${r[0]}:${r[1]} conduction` + (r[0] === 1 ? ` (Wenckebach point ${AVN.erp + AVN.nctMax} ms).` : ", with conduction times lengthening before each blocked beat.")
      : `At ${cl} ms: irregular pattern.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m11-d1-root");
if (root) mount(root);
