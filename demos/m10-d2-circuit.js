// m10-d2 · Wavelength and the excitable gap in a reentrant circuit (eq-m10-wavelength, eq-m10-circuit). MIT License.
// Tested in tests/test_m10_demos.py.
import { circuit } from "./m10-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A wave circulating around a fixed circuit, drawn as a ring. Orange: the wavelength, the stretch of tissue that " +
        "is still refractory behind the front (velocity times refractory period). Green: the excitable gap ahead of " +
        "the front. If the wavelength is longer than the circuit, the front runs into its own tail and reentry stops.",
    ),
  );
  const cv = setupCanvas(root, { width: 380, height: 360, label: "A ring with the refractory wavelength and the excitable gap" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const lS = addSlider(controls, { id: "m10-d2-length", label: "Circuit length", min: 40, max: 300, step: 5, value: 200, digits: 0, unit: "mm", onInput: draw });
  const vS = addSlider(controls, { id: "m10-d2-cv", label: "Conduction velocity", min: 0.2, max: 1.5, step: 0.05, value: 0.8, digits: 2, unit: "m/s", onInput: draw });
  const eS = addSlider(controls, { id: "m10-d2-erp", label: "Refractory period", min: 80, max: 300, step: 5, value: 150, digits: 0, unit: "ms", onInput: draw });

  function arc(r, a0, a1) {
    const n = Math.max(2, Math.ceil(Math.abs(a1 - a0) / 0.03));
    const xs = [];
    const ys = [];
    for (let k = 0; k <= n; k++) {
      const a = a0 + ((a1 - a0) * k) / n;
      xs.push(r * Math.cos(a));
      ys.push(r * Math.sin(a));
    }
    return { xs, ys };
  }

  function draw() {
    const L = Number(lS.value);
    const c = circuit(L, Number(vS.value), Number(eS.value));
    const frac = Math.min(c.wavelength / L, 1);
    const head = Math.PI / 2;
    const tail = head - 2 * Math.PI * frac;
    const refr = arc(1, tail, head);
    const gap = arc(1, head, tail + 2 * Math.PI);
    const series = [{ x: refr.xs, y: refr.ys, color: COLORS.vermillion, width: 8, label: "wavelength (refractory)" }];
    if (frac < 1) series.push({ x: gap.xs, y: gap.ys, color: COLORS.green, width: 8, label: "excitable gap" });
    drawPlot(cv, {
      xRange: [-1.5, 1.5],
      yRange: [-1.4, 1.4],
      xLabel: "",
      yLabel: "",
      series,
      markers: [{ x: Math.cos(head), y: Math.sin(head), color: COLORS.ink, label: "front" }],
    });
    readout.textContent = c.sustained
      ? `Wavelength ${c.wavelength.toFixed(0)} mm in a ${L} mm circuit: reentry can continue with cycle length ` +
        `${c.cycleLength.toFixed(0)} ms and an excitable gap of ${c.gapMm.toFixed(0)} mm (${c.gapMs.toFixed(0)} ms).`
      : `Wavelength ${c.wavelength.toFixed(0)} mm is longer than the ${L} mm circuit: the front meets refractory tissue and reentry stops.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m10-d2-root");
if (root) mount(root);
