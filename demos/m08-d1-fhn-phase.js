// m08-d1 · Threshold and firing in the FitzHugh-Nagumo model (eq-m08-fhn, eq-m08-hopf). MIT License.
// Tested in tests/test_m08_demos.py.
import { FHN, fhnFixedPoint, fhnHopf, fhnSimulate } from "./m08-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Left: the phase plane of the FitzHugh-Nagumo model, with the voltage-like variable v across and the recovery " +
        "variable w up. Gray: the cubic v-nullcline and the straight w-nullcline; the rest state is where they cross. " +
        "Orange: the path after a brief kick to v. Right: v against time. Small kicks die out; kicks past the threshold " +
        "give a full action potential. A steady current above the Hopf value makes the cell fire on its own.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const phase = setupCanvas(row, { width: 330, height: 280, label: "Phase plane of v and w with nullclines and the trajectory" });
  const trace = setupCanvas(row, { width: 330, height: 280, label: "v against time" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const kick = addSlider(controls, { id: "m08-d1-kick", label: "Kick to v at time 0", min: 0, max: 1.5, step: 0.01, value: 0.8, digits: 2, onInput: draw });
  const cur = addSlider(controls, { id: "m08-d1-current", label: "Steady current I", min: 0, max: 0.6, step: 0.005, value: 0, digits: 3, onInput: draw });
  const IH = fhnHopf();

  function draw() {
    const I = Number(cur.value);
    const k = Number(kick.value);
    const sim = fhnSimulate(150, 0.05, I, k);
    const vs = Array.from({ length: 121 }, (_, i) => -2.5 + i * (5 / 120));
    const [vr, wr] = fhnFixedPoint(I);
    drawPlot(phase, {
      xRange: [-2.5, 2.5],
      yRange: [-1, 2],
      xLabel: "v",
      yLabel: "w",
      series: [
        { x: vs, y: vs.map((v) => v - (v * v * v) / 3 + I), color: COLORS.gray, width: 1.5, label: "dv/dt = 0" },
        { x: vs, y: vs.map((v) => (v + FHN.a) / FHN.b), color: COLORS.gray, dash: [5, 4], width: 1.5, label: "dw/dt = 0" },
        { x: Array.from(sim.v), y: Array.from(sim.w), color: COLORS.vermillion, width: 2, label: "trajectory" },
      ],
      markers: [{ x: vr, y: wr, color: COLORS.ink }],
    });
    drawPlot(trace, {
      xRange: [0, 150],
      yRange: [-2.5, 2.5],
      xLabel: "time (dimensionless)",
      yLabel: "v",
      series: [{ x: Array.from(sim.t), y: Array.from(sim.v), color: COLORS.blue, width: 2 }],
    });
    const late = Array.from(sim.v).slice(Math.floor(sim.v.length * 0.6));
    const osc = Math.max(...late) - Math.min(...late) > 1;
    const fired = Math.max(...sim.v) > 1;
    readout.textContent =
      `Kick ${k.toFixed(2)}: peak v = ${Math.max(...sim.v).toFixed(2)}. ` +
      (I > IH ? `I = ${I.toFixed(3)} is above the Hopf value ${IH.toFixed(3)}: ` : `I = ${I.toFixed(3)} is below the Hopf value ${IH.toFixed(3)}: `) +
      (osc ? "the cell fires repeatedly." : fired ? "one action potential, then rest." : "the kick dies out without an action potential.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m08-d1-root");
if (root) mount(root);
