// m01-d1 · How fast potentials fall: point source, dipole and double layer (eq-m01-point, eq-m01-dipole,
// eq-m01-double-layer). MIT License. Tested in tests/test_m01_demos.py.
import { diskSolidAngleAxis, dipoleAxis, doubleLayerPotential, falloffSlope, pointPotential } from "./m01-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Potential against distance on log-log axes, in relative units: a point source of unit current, a dipole of " +
        "unit moment, and a disk-shaped double layer of unit strength seen along its axis. Slopes of -1 and -2 mean " +
        "falloff as one over distance and one over distance squared. Change the disk radius and move the marker.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 280, label: "Log potential against log distance" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const dist = addSlider(controls, { id: "m01-d1-dist", label: "Marker distance (log10 of mm)", min: -1, max: 2, step: 0.01, value: 0.5, digits: 2, onInput: draw });
  const radius = addSlider(controls, { id: "m01-d1-radius", label: "Disk radius", min: 0.5, max: 10, step: 0.1, value: 3, digits: 1, unit: "mm", onInput: draw });
  const lr = Array.from({ length: 301 }, (_, i) => -1 + (3 * i) / 300);

  function draw() {
    const R = Number(radius.value);
    const r0 = 10 ** Number(dist.value);
    const mono = (r) => pointPotential(1, 1, r);
    const dip = (r) => dipoleAxis(1, 1, r);
    const disk = (r) => doubleLayerPotential(1, 1, diskSolidAngleAxis(R, r));
    const L = (f) => lr.map((v) => Math.log10(Math.abs(f(10 ** v))));
    drawPlot(cv, {
      xRange: [-1, 2],
      yRange: [-6, 1.5],
      xLabel: "log10 distance (mm)",
      yLabel: "log10 potential (relative)",
      series: [
        { x: lr, y: L(mono), color: COLORS.blue, width: 2, label: "point source (slope -1)" },
        { x: lr, y: L(dip), color: COLORS.vermillion, width: 2, label: "dipole (slope -2)" },
        { x: lr, y: L(disk), color: COLORS.green, width: 2, label: `double-layer disk, R = ${R.toFixed(1)} mm` },
      ],
      vlines: [{ x: Math.log10(r0), color: COLORS.gray, dash: [3, 3] }],
      markers: [
        { x: Math.log10(r0), y: Math.log10(mono(r0)), color: COLORS.blue },
        { x: Math.log10(r0), y: Math.log10(dip(r0)), color: COLORS.vermillion },
        { x: Math.log10(r0), y: Math.log10(disk(r0)), color: COLORS.green },
      ],
    });
    readout.textContent =
      `At ${r0.toFixed(2)} mm: local slopes are ${falloffSlope(mono, r0).toFixed(2)} (point source), ` +
      `${falloffSlope(dip, r0).toFixed(2)} (dipole) and ${falloffSlope(disk, r0).toFixed(2)} (disk). ` +
      `The disk subtends ${(diskSolidAngleAxis(R, r0) / (4 * Math.PI)).toFixed(3)} of the full sphere: ` +
      `${r0 < R ? "close up it looks like an infinite sheet and its potential barely changes" : "far away it looks like one dipole of moment tau times its area"}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m01-d1-root");
if (root) mount(root);
