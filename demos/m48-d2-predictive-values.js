// m48-d2 · What a positive imaging test means: predictive values against prevalence (eq-m35-ppv, eq-m48-lr).
// MIT License. Tested in tests/test_m48_demos.py.
import { ROMERO2013, likelihoodRatios, predictiveValues } from "./m48-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const PROTOCOLS = {
  standard: { label: "CT, pooled (Se 96%, Sp 92%)", ...ROMERO2013.standard },
  delayed: { label: "CT with delayed imaging, pooled (Se 100%, Sp 99%)", ...ROMERO2013.delayed },
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Positive and negative predictive values of an imaging test against the prevalence of what it looks for. " +
        "The presets are the pooled accuracy of CT for left atrial appendage thrombus against TEE in one " +
        "meta-analysis; the dots are the pooled predictive values that meta-analysis reported at its 8.9% " +
        "prevalence. Move the sensitivity or specificity to try another test.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Predictive values against prevalence" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const prev = addSlider(controls, { id: "m48-d2-prev", label: "Prevalence", min: 0.5, max: 50, step: 0.1, value: 8.9, digits: 1, unit: "%", onInput: draw });
  const custom = () => {
    protocol.value = "custom";
    draw();
  };
  const se = addSlider(controls, { id: "m48-d2-se", label: "Sensitivity", min: 50, max: 100, step: 0.5, value: 96, digits: 1, unit: "%", onInput: custom });
  const sp = addSlider(controls, { id: "m48-d2-sp", label: "Specificity", min: 50, max: 99.9, step: 0.1, value: 92, digits: 1, unit: "%", onInput: custom });
  const protocol = addSelect(controls, {
    id: "m48-d2-protocol",
    label: "Test",
    options: [
      { value: "standard", label: PROTOCOLS.standard.label },
      { value: "delayed", label: PROTOCOLS.delayed.label },
      { value: "custom", label: "custom" },
    ],
    value: "standard",
    onChange: () => {
      const p = PROTOCOLS[protocol.value];
      if (!p) return;
      se.value = String(100 * p.se);
      sp.value = String(Math.min(99.9, 100 * p.sp));
      se.dispatchEvent(new Event("input"));
      sp.dispatchEvent(new Event("input"));
      protocol.value = Object.keys(PROTOCOLS).find((k) => PROTOCOLS[k] === p);
      draw();
    },
  });
  const xs = Array.from({ length: 500 }, (_, i) => 0.001 + (i * 0.499) / 499);

  function draw() {
    const S = Number(se.value) / 100;
    const P = Number(sp.value) / 100;
    const pi = Number(prev.value) / 100;
    const curves = xs.map((x) => predictiveValues(S, P, x));
    const now = predictiveValues(S, P, pi);
    const lr = likelihoodRatios(S, P);
    const ref = PROTOCOLS[protocol.value];
    const markers = [
      { x: 100 * pi, y: 100 * now.ppv, color: COLORS.vermillion },
      { x: 100 * pi, y: 100 * now.npv, color: COLORS.blue },
    ];
    if (ref) {
      markers.push({ x: 100 * ROMERO2013.prevalence, y: 100 * ref.ppv, color: COLORS.ink, label: "pooled values reported" });
      markers.push({ x: 100 * ROMERO2013.prevalence, y: 100 * ref.npv, color: COLORS.ink });
    }
    drawPlot(cv, {
      xRange: [0, 50],
      yRange: [0, 135],
      xLabel: "prevalence (%)",
      yLabel: "predictive value (%)",
      series: [
        { x: xs.map((x) => 100 * x), y: curves.map((c) => 100 * c.ppv), color: COLORS.vermillion, width: 2, label: "positive predictive value" },
        { x: xs.map((x) => 100 * x), y: curves.map((c) => 100 * c.npv), color: COLORS.blue, width: 2, label: "negative predictive value" },
      ],
      vlines: [{ x: 100 * pi, color: COLORS.gray, dash: [3, 3] }],
      markers,
    });
    const fmt = (v) => (Number.isFinite(v) ? v.toFixed(v < 1 ? 3 : 1) : "infinite");
    let text =
      `Sensitivity ${(100 * S).toFixed(1)}%, specificity ${(100 * P).toFixed(1)}%, prevalence ${(100 * pi).toFixed(1)}%: ` +
      `a positive result is right ${(100 * now.ppv).toFixed(0)}% of the time and a negative one ${(100 * now.npv).toFixed(1)}% of the time. ` +
      `LR+ ${fmt(lr.pos)}, LR− ${fmt(lr.neg)}.`;
    if (ref) text += ` The meta-analysis reported pooled values of ${(100 * ref.ppv).toFixed(0)}% and ${(100 * ref.npv).toFixed(0)}%, pooled study by study.`;
    readout.textContent = text;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m48-d2-root");
if (root) mount(root);
