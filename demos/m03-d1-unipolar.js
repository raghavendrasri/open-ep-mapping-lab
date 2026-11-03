// m03-d1 · A wavefront passing one electrode. MIT License.
import { DEFAULTS, frontVm, linspace, unipolar, unipolarDs } from "./m03-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";


function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Top: transmembrane voltage at the tissue under the electrode, rising as the front arrives at time 0. " +
        "Bottom: the unipolar electrogram at the electrode. The dot marks the steepest downstroke; the dashed line marks true activation.",
    ),
  );
  const top = setupCanvas(root, { width: 640, height: 150, label: "Transmembrane voltage under the electrode versus time" });
  const bottom = setupCanvas(root, { width: 640, height: 230, label: "Unipolar electrogram versus time" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const h = addSlider(controls, { id: "m03-d1-h", label: "Electrode height h", min: 0.2, max: 5, step: 0.1, value: DEFAULTS.h, unit: "mm", digits: 1, onInput: draw });
  const c = addSlider(controls, { id: "m03-d1-c", label: "Conduction velocity c", min: 0.2, max: 2, step: 0.05, value: DEFAULTS.c, unit: "m/s", onInput: draw });
  const w = addSlider(controls, { id: "m03-d1-w", label: "Front width w", min: 0.1, max: 2, step: 0.05, value: DEFAULTS.w, unit: "mm", onInput: draw });

  const t = linspace(-15, 15, 601);
  const aRef = DEFAULTS.w + DEFAULTS.h;
  const refPtp = 1 / aRef; // peak-to-peak at defaults (A = 1)
  const refSlope = DEFAULTS.c / (aRef * aRef);

  function draw() {
    const hv = Number(h.value);
    const cv = Number(c.value);
    const wv = Number(w.value);
    const a = wv + hv;
    const vm = Array.from(t, (tt) => frontVm(-cv * tt, wv));
    const u = Array.from(t, (tt) => unipolar(-cv * tt, a));
    const dudt = Array.from(t, (tt) => -cv * unipolarDs(-cv * tt, a));
    let iMin = 0;
    for (let i = 1; i < dudt.length; i++) if (dudt[i] < dudt[iMin]) iMin = i;

    drawPlot(top, {
      xRange: [-15, 15],
      yRange: [-0.05, 1.05],
      xLabel: "time (ms)",
      yLabel: "Vm (normalized)",
      yTicks: 2,
      series: [{ x: t, y: vm, color: COLORS.gray }],
      vlines: [{ x: 0, color: COLORS.gray, label: "activation" }],
      margin: { b: 36 },
    });
    drawPlot(bottom, {
      xRange: [-15, 15],
      yRange: [-1, 1],
      xLabel: "time (ms)",
      yLabel: "U (relative units)",
      series: [{ x: t, y: u, color: COLORS.blue, label: "unipolar electrogram" }],
      markers: [{ x: t[iMin], y: u[iMin], color: COLORS.vermillion, label: "steepest downstroke" }],
      vlines: [{ x: 0, color: COLORS.gray }],
    });

    const ptpRel = 1 / a / refPtp;
    const slopeRel = cv / (a * a) / refSlope;
    readout.textContent =
      `Peak-to-peak: ${ptpRel.toFixed(2)} × the default. ` +
      `Steepest downstroke: ${slopeRel.toFixed(2)} × the default, at ${t[iMin].toFixed(2)} ms ` +
      `(true activation at 0 ms). a = w + h = ${a.toFixed(2)} mm.`;
  }
  draw();
}

// Start after every constant above is defined.
const root = document.getElementById("m03-d1-root");
if (root) mount(root);
