// m08-d2 · S1-S2 restitution in the Mitchell-Schaeffer model (eq-m08-ms, eq-m08-apd). MIT License.
// Tested in tests/test_m08_demos.py.
import { MS, msApdClosed, s1s2 } from "./m08-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const S2_GRID = [230, 240, 250, 260, 280, 300, 330, 360, 400, 450, 500, 600];

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Left: the last of four paced beats 500 ms apart (S1) and a premature beat (S2) in the Mitchell-Schaeffer model. " +
        "Right: restitution, the duration of the S2 action potential against the diastolic interval before it. Dots: " +
        "simulated beats; line: the closed-form estimate of when the excited state disappears. Shortening the gate's " +
        "closing time constant shortens every action potential.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const ap = setupCanvas(row, { width: 330, height: 280, label: "Voltage of the last S1 beat and the S2 beat" });
  const rest = setupCanvas(row, { width: 330, height: 280, label: "Action potential duration against diastolic interval" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const s2S = addSlider(controls, { id: "m08-d2-s2", label: "S1-S2 interval", min: 220, max: 600, step: 5, value: 300, digits: 0, unit: "ms", onInput: draw });
  const tcS = addSlider(controls, { id: "m08-d2-tauclose", label: "Gate closing time constant", min: 70, max: 160, step: 5, value: 120, digits: 0, unit: "ms", onInput: () => { grid = null; draw(); } });
  let grid = null;

  function draw() {
    const p = { ...MS, tauClose: Number(tcS.value) };
    if (!grid) grid = S2_GRID.map((s2) => s1s2(s2, p).row).filter((r) => Number.isFinite(r[2]));
    const s2 = Number(s2S.value);
    const { row: r, run } = s1s2(s2, p);
    const t0 = 1500 - 50;
    const idx = [];
    for (let i = 0; i < run.t.length; i += 5) if (run.t[i] >= t0) idx.push(i);
    drawPlot(ap, {
      xRange: [-50, 1100],
      yRange: [-0.05, 1.05],
      xLabel: "time after the last S1 (ms)",
      yLabel: "v (dimensionless)",
      series: [{ x: idx.map((i) => run.t[i] - 1500), y: idx.map((i) => run.v[i]), color: COLORS.blue, width: 2 }],
      vlines: [{ x: s2, color: COLORS.gray }],
    });
    const dis = Array.from({ length: 120 }, (_, i) => 1 + i * 4);
    drawPlot(rest, {
      xRange: [0, 400],
      yRange: [0, 300],
      xLabel: "diastolic interval (ms)",
      yLabel: "APD of S2 (ms)",
      series: [{ x: dis, y: dis.map((d) => msApdClosed(d, p)), color: COLORS.gray, width: 1.5, label: "closed form" }],
      markers: grid
        .map((g) => ({ x: g[1], y: g[2], color: COLORS.blue }))
        .concat(Number.isFinite(r[2]) ? [{ x: r[1], y: r[2], color: COLORS.vermillion }] : []),
    });
    readout.textContent = Number.isFinite(r[2])
      ? `S2 at ${s2} ms: diastolic interval ${r[1].toFixed(0)} ms, APD ${r[2].toFixed(0)} ms (closed form ${msApdClosed(r[1], p).toFixed(0)} ms, the time the excited state disappears).`
      : `S2 at ${s2} ms falls inside the refractory period: no action potential.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m08-d2-root");
if (root) mount(root);
