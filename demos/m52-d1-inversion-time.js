// m52-d1 · Choosing the inversion time: recovery after an inversion pulse for myocardium, infarct scar and blood,
// 10 minutes after gadolinium. MIT License. Formulas tested in tests/test_m52_demos.py.
import { T1_BLOOD_ILLUSTRATIVE, T1_POST, bestTiSigned, lgeSignal, nullTime } from "./m52-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const TISSUES = [
  { key: "myocardium", label: "myocardium (379 ms)", t1: T1_POST.myocardium, color: COLORS.blue },
  { key: "scar", label: "infarct scar (238 ms)", t1: T1_POST.infarct, color: COLORS.vermillion },
  { key: "blood", label: "blood (249 ms, illustrative)", t1: T1_BLOOD_ILLUSTRATIVE, color: COLORS.gray, dash: [6, 4] },
];

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "After an inversion pulse each tissue recovers at its own rate, set by its T1. Gadolinium shortens T1 most " +
        "where there is most extracellular space, such as scar. Pick the inversion time (TI) at which the image " +
        "is read: at the myocardial null, healthy muscle is black and scar is bright. Magnitude images show only " +
        "the size of the signal; phase-sensitive images keep its sign. Dotted lines: the chosen TI (black) and the " +
        "myocardial null (blue).",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Signal against inversion time for myocardium, scar and blood" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const ti = addSlider(controls, { id: "m52-d1-ti", label: "Inversion time", min: 50, max: 700, step: 5, value: 265, digits: 0, unit: "ms", onInput: draw });
  const recon = addSelect(controls, {
    id: "m52-d1-recon",
    label: "Reconstruction",
    options: [
      { value: "magnitude", label: "magnitude (sign lost)" },
      { value: "signed", label: "phase-sensitive (sign kept)" },
    ],
    value: "magnitude",
    onChange: draw,
  });
  const xs = Array.from({ length: 351 }, (_, i) => 2 * i);

  function draw() {
    const T = Number(ti.value);
    const mag = recon.value === "magnitude";
    const series = TISSUES.map((t) => ({
      x: xs,
      y: xs.map((v) => lgeSignal(v, t.t1, mag)),
      color: t.color,
      dash: t.dash,
      label: t.label,
    }));
    const tNull = nullTime(T1_POST.myocardium);
    drawPlot(cv, {
      xRange: [0, 700],
      yRange: mag ? [0, 1.35] : [-1.05, 1.75],
      xLabel: "inversion time TI (ms)",
      yLabel: mag ? "signal |Mz| / M0" : "signal Mz / M0",
      series,
      vlines: [
        { x: T, color: COLORS.ink, dash: [2, 3] },
        { x: tNull, color: COLORS.blue, dash: [1, 4] },
      ],
    });
    const s = Object.fromEntries(TISSUES.map((t) => [t.key, lgeSignal(T, t.t1, mag)]));
    const f = (v) => v.toFixed(2);
    readout.textContent =
      `TI ${T} ms (${mag ? "magnitude" : "phase-sensitive"}). Myocardium ${f(s.myocardium)}, scar ${f(s.scar)}, ` +
      `blood ${f(s.blood)}. Scar minus myocardium ${f(s.scar - s.myocardium)}; scar minus blood ` +
      `${f(s.scar - s.blood)}. Null at ${Math.round(tNull)} ms; the signed scar-myocardium difference peaks at ` +
      `${Math.round(bestTiSigned(T1_POST.myocardium, T1_POST.infarct))} ms.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m52-d1-root");
if (root) mount(root);
