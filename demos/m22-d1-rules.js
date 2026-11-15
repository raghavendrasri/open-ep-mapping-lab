// m22-d1 · Annotation rules on a modeled bipolar recording (eq-m22-intrinsic, eq-m22-onset). MIT License.
// Tested in tests/test_m22_demos.py.
import { bipolarTrace, onsetTime, peakTime, steepestDownstroke, unipolarTrace } from "./m22-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A planar front at 1.0 m/s crosses a bipole along its axis; the front reaches the bipole midpoint at 0 ms. " +
        "Gray: the two unipolar signals. Blue: the bipolar signal. Markers: each unipolar steepest downstroke, the " +
        "bipolar peak, and the bipolar onset (the first time it reaches a set fraction of its peak). Raise the electrode " +
        "or shrink the spacing and see which annotation moves.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Unipolar and bipolar electrograms with annotation markers" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const hS = addSlider(controls, { id: "m22-d1-h", label: "Electrode height above tissue", min: 0.2, max: 4, step: 0.1, value: 1, digits: 1, unit: "mm", onInput: draw });
  const dS = addSlider(controls, { id: "m22-d1-d", label: "Bipole spacing", min: 0.5, max: 8, step: 0.5, value: 2, digits: 1, unit: "mm", onInput: draw });
  const fS = addSlider(controls, { id: "m22-d1-f", label: "Onset fraction of peak", min: 0.05, max: 0.5, step: 0.05, value: 0.1, digits: 2, onInput: draw });
  const c = 1.0, w = 0.3;

  function draw() {
    const a = w + Number(hS.value), d = Number(dS.value), f = Number(fS.value);
    const t = [];
    for (let x = -15; x <= 15.0001; x += 0.01) t.push(x);
    const u1 = t.map((x) => unipolarTrace(x, c, a, 0.5 * d / c));     // distal: activates later
    const u2 = t.map((x) => unipolarTrace(x, c, a, -0.5 * d / c));    // proximal
    const b = t.map((x) => bipolarTrace(x, c, a, d));
    const s1 = steepestDownstroke(t, u1), s2 = steepestDownstroke(t, u2);
    const pk = peakTime(t, b), on = onsetTime(t, b, f);
    const ymax = Math.max(...b.map(Math.abs)) * 1.15;
    const at = (arr, tt) => arr[Math.round((tt + 15) / 0.01)];
    drawPlot(cv, {
      xRange: [-15, 15], yRange: [-ymax, ymax], xLabel: "time from midpoint activation (ms)", yLabel: "potential (relative)",
      series: [
        { x: t, y: u2, color: COLORS.gray, width: 1.2, dash: [4, 3], label: "proximal unipolar" },
        { x: t, y: u1, color: COLORS.gray, width: 1.2, label: "distal unipolar" },
        { x: t, y: b, color: COLORS.blue, width: 2.2, label: "bipolar" },
        { x: [0, 0], y: [-ymax, ymax], color: COLORS.ink, width: 1, dash: [2, 3] },
      ],
      markers: [
        { x: s2, y: at(u2, s2), color: COLORS.gray, radius: 4 },
        { x: s1, y: at(u1, s1), color: COLORS.gray, radius: 4, label: "steepest downstrokes" },
        { x: pk, y: at(b, pk), color: COLORS.vermillion, radius: 5, label: "bipolar peak" },
        { x: on, y: at(b, on), color: COLORS.green, radius: 5, label: "onset" },
      ],
    });
    const fmt = (v) => (Math.abs(v) < 0.005 ? 0 : v).toFixed(2);
    readout.textContent =
      `Bipolar peak ${fmt(pk)} ms, onset ${fmt(on)} ms; unipolar steepest downstrokes ` +
      `${fmt(s2)} and ${fmt(s1)} ms (relative to the midpoint activation).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m22-d1-root");
if (root) mount(root);
