// m35-d1 · Leakage: splitting records instead of patients. MIT License.
import { clusteredRecords, nearestNeighbourAccuracy } from "./m35-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Synthetic patients, each with one label and several records described by six features. A nearest-neighbour classifier is scored two ways: " +
        "leaving out one record at a time (record-wise) or a whole patient at a time (patient-wise). " +
        "The plot shows both as the patient signature grows.",
    ),
  );
  const plot = setupCanvas(root, { width: 640, height: 230, label: "Record-wise and patient-wise accuracy versus patient signature strength" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const icc = addSlider(controls, { id: "m35-d1-icc", label: "Patient signature (share of variance)", min: 0, max: 0.95, step: 0.05, value: 0.6, onInput: draw });
  const signal = addSlider(controls, { id: "m35-d1-signal", label: "Class signal (SD units)", min: 0, max: 3, step: 0.1, value: 1.0, digits: 1, onInput: draw });
  const per = addSlider(controls, { id: "m35-d1-m", label: "Records per patient", min: 1, max: 20, step: 1, value: 10, digits: 0, onInput: draw });

  const PATIENTS = 30;
  const grid = Array.from({ length: 8 }, (_, i) => i * 0.13);

  function draw() {
    const s = Number(signal.value);
    const m = Number(per.value);
    const r = Number(icc.value);
    const curve = (patientWise) =>
      grid.map((g) => nearestNeighbourAccuracy(clusteredRecords({ patients: PATIENTS, perPatient: m, icc: g, signal: s }), patientWise));
    const recs = clusteredRecords({ patients: PATIENTS, perPatient: m, icc: r, signal: s });
    const accRecord = nearestNeighbourAccuracy(recs, false);
    const accPatient = nearestNeighbourAccuracy(recs, true);
    drawPlot(plot, {
      xRange: [0, 0.95],
      yRange: [0.3, 1.0],
      xLabel: "patient signature (share of variance)",
      yLabel: "accuracy",
      series: [
        { x: grid, y: curve(false), color: COLORS.vermillion, label: "record-wise split" },
        { x: grid, y: curve(true), color: COLORS.blue, label: "patient-wise split" },
      ],
      markers: [
        { x: r, y: accRecord, color: COLORS.vermillion },
        { x: r, y: accPatient, color: COLORS.blue },
      ],
      legendLeft: true,
    });
    readout.textContent =
      `${PATIENTS} patients × ${m} records: record-wise accuracy ${(100 * accRecord).toFixed(0)}%, ` +
      `patient-wise ${(100 * accPatient).toFixed(0)}% (the estimate for new patients). ` +
      `Gap ${(100 * (accRecord - accPatient)).toFixed(0)} points.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m35-d1-root");
if (root) mount(root);
