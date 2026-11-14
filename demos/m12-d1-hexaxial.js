// m12-d1 · Limb leads and the frontal axis (eq-m12-einthoven, eq-m12-augmented, eq-m12-axis). MIT License.
// Tested in tests/test_m12_demos.py.
import { frontalAxis, leadsForDipole } from "./m12-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const NAMES = ["I", "II", "III", "aVR", "aVL", "aVF"];

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Left: a heart vector (orange) at the center of Einthoven's triangle in the frontal plane; the gray lines are the " +
        "six limb-lead axes. Right: the voltage each limb lead records, proportional to the projection of the vector on " +
        "its axis. Turn the vector and watch which leads go positive, negative or flat.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const plane = setupCanvas(row, { width: 330, height: 300, label: "Frontal plane with lead axes and the heart vector" });
  const bars = setupCanvas(row, { width: 330, height: 300, label: "Voltages of the six limb leads" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const angS = addSlider(controls, { id: "m12-d1-angle", label: "Heart vector angle (0 = toward the left arm, +90 = toward the feet)", min: -180, max: 180, step: 1, value: 60, digits: 0, unit: "°", onInput: draw });

  const axes = { I: 0, II: 60, III: 120, aVR: -150, aVL: -30, aVF: 90 };

  function draw() {
    const a = (Number(angS.value) * Math.PI) / 180;
    const p = [Math.cos(a), Math.sin(a), 0];
    const L = leadsForDipole(p);
    const series = Object.entries(axes).map(([k, deg]) => {
      const r = (deg * Math.PI) / 180;
      return { x: [-Math.cos(r), Math.cos(r)], y: [Math.sin(r), -Math.sin(r)], color: COLORS.gray, width: 1 };
    });
    series.push({ x: [0, Math.cos(a)], y: [0, -Math.sin(a)], color: COLORS.vermillion, width: 3, label: "heart vector" });
    drawPlot(plane, { xRange: [-1.2, 1.2], yRange: [-1.2, 1.2], xLabel: "toward the left arm →", yLabel: "up = toward the head", series });
    drawPlot(bars, {
      xRange: [0.3, 6.7],
      yRange: [-0.45, 0.45],
      xLabel: "I, II, III, aVR, aVL, aVF",
      yLabel: "lead voltage (relative)",
      series: NAMES.map((k, i) => ({ x: [i + 1, i + 1], y: [0, L[k]], color: L[k] >= 0 ? COLORS.blue : COLORS.vermillion, width: 14 })),
    });
    const ax = frontalAxis(L.I, L.aVF);
    readout.textContent =
      `Axis from leads I and aVF: ${ax.toFixed(0)}°. ` + NAMES.map((k) => `${k} ${L[k] >= 0 ? "+" : ""}${L[k].toFixed(2)}`).join(", ") +
      `. I + III − II = ${(L.I + L.III - L.II).toFixed(3)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m12-d1-root");
if (root) mount(root);
