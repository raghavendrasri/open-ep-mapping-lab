// m38-d2 · A remote-monitoring inbox: review time, and what a triage filter gains and loses. MIT License.
import { alertWorkload, filteredAlerts } from "./m38-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A clinic follows many implanted monitors. Each alert needs a person to review it. A triage filter can hide some alerts. " +
        "Left: share of shown alerts that are true (PPV) as the filter removes more false alerts. Right: true alerts lost per month " +
        "as the filter keeps a smaller share of true alerts.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const left = setupCanvas(row, { width: 320, height: 270, label: "PPV of shown alerts versus share of false alerts removed" });
  const right = setupCanvas(row, { width: 320, height: 270, label: "True alerts lost per month versus share of true alerts kept" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const N = addSlider(controls, { id: "m38-d2-n", label: "Patients followed", min: 50, max: 2000, step: 50, value: 500, digits: 0, onInput: draw });
  const rate = addSlider(controls, { id: "m38-d2-rate", label: "Alerts per patient per day", min: 0.01, max: 0.3, step: 0.01, value: 0.1, onInput: draw });
  const ppv = addSlider(controls, { id: "m38-d2-ppv", label: "PPV of raw alerts", min: 0.05, max: 0.9, step: 0.05, value: 0.25, onInput: draw });
  const mins = addSlider(controls, { id: "m38-d2-min", label: "Minutes to review one alert", min: 1, max: 15, step: 1, value: 3, digits: 0, onInput: draw });
  const keep = addSlider(controls, { id: "m38-d2-keep", label: "Filter keeps true alerts", min: 0.8, max: 1, step: 0.005, value: 0.98, digits: 3, onInput: draw });
  const remove = addSlider(controls, { id: "m38-d2-remove", label: "Filter removes false alerts", min: 0, max: 0.99, step: 0.01, value: 0.7, onInput: draw });

  const rs = Array.from({ length: 100 }, (_, i) => i / 100);
  const kts = Array.from({ length: 41 }, (_, i) => 0.8 + i * 0.005);
  function draw() {
    const w = alertWorkload(Number(N.value), Number(rate.value), Number(ppv.value), Number(mins.value));
    const f = filteredAlerts(Number(ppv.value), Number(keep.value), Number(remove.value));
    drawPlot(left, {
      xRange: [0, 1],
      yRange: [0, 1],
      xLabel: "share of false alerts removed",
      yLabel: "PPV of shown alerts",
      series: [{ x: rs, y: rs.map((r) => filteredAlerts(Number(ppv.value), Number(keep.value), r).ppv), color: COLORS.green }],
      markers: [{ x: Number(remove.value), y: f.ppv, color: COLORS.ink, label: "filter" }],
      margin: { l: 52 },
    });
    const lost = kts.map((kt) => w.true * (1 - kt) * 30);
    drawPlot(right, {
      xRange: [0.8, 1],
      yRange: [0, Math.max(1, ...lost) * 1.05],
      xLabel: "share of true alerts kept",
      yLabel: "true alerts lost / month",
      series: [{ x: kts, y: lost, color: COLORS.vermillion }],
      markers: [{ x: Number(keep.value), y: w.true * f.lost * 30, color: COLORS.ink, label: "filter" }],
      margin: { l: 52 },
    });
    readout.textContent =
      `Without a filter: ${w.alerts.toFixed(0)} alerts a day, ${w.false.toFixed(0)} false, ${w.hours.toFixed(1)} hours of review. ` +
      `With the filter: ${(w.alerts * f.shown).toFixed(0)} shown a day (${((w.alerts * f.shown * Number(mins.value)) / 60).toFixed(1)} hours), ` +
      `PPV ${(100 * f.ppv).toFixed(0)}%, and about ${(w.true * f.lost * 30).toFixed(1)} true alerts a month hidden from review.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m38-d2-root");
if (root) mount(root);
