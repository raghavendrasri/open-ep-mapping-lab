// m45-d2 · How many patients does a diagnostic-accuracy study need? MIT License.
import { nForSensitivity, nForSpecificity } from "./m45-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Patients to enrol so that the 95% confidence intervals for sensitivity and specificity have a chosen " +
        "half-width, against the prevalence of the condition in the study population (log scale). Sensitivity is " +
        "estimated only on patients who have the condition, so rare conditions need many patients.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Patients needed against prevalence for sensitivity and specificity" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const se = addSlider(controls, { id: "m45-d2-se", label: "Expected sensitivity", min: 0.6, max: 0.99, step: 0.01, value: 0.9, digits: 2, onInput: draw });
  const sp = addSlider(controls, { id: "m45-d2-sp", label: "Expected specificity", min: 0.6, max: 0.99, step: 0.01, value: 0.9, digits: 2, onInput: draw });
  const d = addSlider(controls, { id: "m45-d2-d", label: "Half-width d", min: 0.02, max: 0.1, step: 0.01, value: 0.05, digits: 2, onInput: draw });
  const prev = addSlider(controls, { id: "m45-d2-prev", label: "Prevalence", min: 0.01, max: 0.5, step: 0.01, value: 0.1, digits: 2, onInput: draw });

  function draw() {
    const ps = Array.from({ length: 50 }, (_, i) => 0.01 + (i * 0.49) / 49);
    const ns = ps.map((p) => nForSensitivity(Number(se.value), Number(d.value), p));
    const nsp = ps.map((p) => nForSpecificity(Number(sp.value), Number(d.value), p));
    const pv = Number(prev.value);
    const a = nForSensitivity(Number(se.value), Number(d.value), pv);
    const b = nForSpecificity(Number(sp.value), Number(d.value), pv);
    drawPlot(cv, {
      xRange: [0, 0.5], yRange: [1, 5], xLabel: "prevalence", yLabel: "log10 patients needed",
      series: [
        { x: ps, y: ns.map(Math.log10), color: COLORS.blue, width: 2.5, label: "for sensitivity" },
        { x: ps, y: nsp.map(Math.log10), color: COLORS.green, width: 2.5, label: "for specificity" },
      ],
      markers: [{ x: pv, y: Math.log10(a), color: COLORS.blue }, { x: pv, y: Math.log10(b), color: COLORS.green }],
      vlines: [{ x: pv, color: COLORS.gray }],
    });
    readout.textContent =
      `At prevalence ${pv.toFixed(2)}, ±${Number(d.value).toFixed(2)} on a sensitivity near ${Number(se.value).toFixed(2)} needs ${a} patients ` +
      `(${Math.ceil(a * pv)} with the condition); ±${Number(d.value).toFixed(2)} on a specificity near ${Number(sp.value).toFixed(2)} needs ${b}. ` +
      `Enrol the larger number: ${Math.max(a, b)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m45-d2-root");
if (root) mount(root);
