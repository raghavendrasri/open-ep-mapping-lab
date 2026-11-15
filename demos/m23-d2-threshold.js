// m23-d2 · Voltage cutoffs, two tissue populations and contact (eq-m23-threshold, eq-m23-amplitude). MIT License.
// Tested in tests/test_m23_demos.py.
import { bipolarPp, thresholdRates } from "./m23-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Illustrative bipolar voltages of scar (orange) and healthy tissue (blue), each log-normal, on a log scale. A " +
        "point is labeled low voltage if it reads below the cutoff. Lifting the electrode shrinks every reading, which " +
        "moves healthy tissue toward the cutoff.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Voltage distributions of scar and healthy tissue with a cutoff" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const cS = addSlider(controls, { id: "m23-d2-cut", label: "Cutoff", min: 0.1, max: 3, step: 0.05, value: 1.5, digits: 2, unit: "mV", onInput: draw });
  const hS = addSlider(controls, { id: "m23-d2-h", label: "Extra electrode height", min: 0, max: 3, step: 0.1, value: 0, digits: 1, unit: "mm", onInput: draw });
  const sS = addSlider(controls, { id: "m23-d2-sd", label: "Spread (SD of ln V)", min: 0.3, max: 1.2, step: 0.05, value: 0.7, digits: 2, onInput: draw });
  const medScar = 0.2, medNormal = 2.5, a = 1.3;

  function draw() {
    const cut = Number(cS.value), extra = Number(hS.value), sd = Number(sS.value);
    const f = bipolarPp(a + extra, 2.0) / bipolarPp(a, 2.0);   // a 2-mm bipole, aligned
    const ms = medScar * f, mn = medNormal * f;
    const xs = [], ys = [], yn = [];
    const pdf = (x, med) => { const z = (x * Math.LN10 - Math.log(med)) / sd; return Math.exp(-0.5 * z * z) / (sd * Math.sqrt(2 * Math.PI)); };
    for (let x = -2.5; x <= 1.5001; x += 0.01) { xs.push(x); ys.push(pdf(x, ms)); yn.push(pdf(x, mn)); }
    const lc = Math.log10(cut);
    const ymax = Math.max(...ys, ...yn) * 1.15;
    drawPlot(cv, {
      xRange: [-2.5, 1.5], yRange: [0, ymax], xLabel: "log10 of bipolar voltage (mV)", yLabel: "density (per unit ln V)",
      series: [
        { x: xs, y: ys, color: COLORS.orange, width: 2, label: "scar" },
        { x: xs, y: yn, color: COLORS.blue, width: 2, label: "healthy" },
        { x: [lc, lc], y: [0, ymax], color: COLORS.vermillion, width: 1.5, dash: [6, 4], label: "cutoff" },
      ],
    });
    const [sens, spec] = thresholdRates(cut, ms, mn, sd, sd);
    readout.textContent =
      `Cutoff ${cut.toFixed(2)} mV: ${(100 * sens).toFixed(1)}% of scar and ${(100 * (1 - spec)).toFixed(1)}% of healthy ` +
      `tissue read below it; readings scaled by ${f.toFixed(2)} for the extra height.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m23-d2-root");
if (root) mount(root);
