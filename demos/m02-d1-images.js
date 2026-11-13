// m02-d1 · A source below an interface: the method of images (eq-m02-interface, eq-m02-images). MIT License.
// Tested in tests/test_m02_demos.py.
import { imagePotential3d, reflectionCoefficient } from "./m02-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A unit point source a depth d below a flat interface. Medium 1 (with the source) has conductivity 1; medium 2 " +
        "above has the conductivity you choose. Top: the potential along the vertical line through the source. " +
        "Bottom: the potential along a line 1 mm above the interface, where an electrode would sit. Dashed lines show " +
        "the same source in medium 1 everywhere.",
    ),
  );
  const cvV = setupCanvas(root, { width: 640, height: 210, label: "Potential along the vertical through the source" });
  const cvH = setupCanvas(root, { width: 640, height: 210, label: "Potential 1 mm above the interface" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const ratio = addSlider(controls, { id: "m02-d1-ratio", label: "Conductivity of medium 2 (log10 of sigma2/sigma1)", min: -2, max: 1, step: 0.05, value: 0.5, digits: 2, onInput: draw });
  const depth = addSlider(controls, { id: "m02-d1-depth", label: "Source depth d", min: 0.5, max: 5, step: 0.1, value: 2, digits: 1, unit: "mm", onInput: draw });
  const zs = Array.from({ length: 601 }, (_, i) => -8 + (14 * i) / 600);
  const xs = Array.from({ length: 401 }, (_, i) => -10 + (20 * i) / 400);

  function draw() {
    const s2 = 10 ** Number(ratio.value);
    const d = Number(depth.value);
    const keep = zs.filter((z) => Math.abs(z + d) > 0.35);
    const vTwo = keep.map((z) => imagePotential3d(1, 1, s2, d, 0, 0, z));
    const vOne = keep.map((z) => imagePotential3d(1, 1, 1, d, 0, 0, z));
    const top = 1.4 * Math.max(...vTwo, ...vOne);
    drawPlot(cvV, {
      xRange: [-8, 6],
      yRange: [0, top],
      xLabel: "height z (mm); interface at 0, source at -d",
      yLabel: "potential (relative)",
      series: [
        { x: keep, y: vOne, color: COLORS.gray, dash: [5, 4], label: "medium 1 everywhere" },
        { x: keep, y: vTwo, color: COLORS.blue, width: 2, label: "two media" },
      ],
      vlines: [{ x: 0, color: COLORS.ink, dash: [2, 2] }],
    });
    const hTwo = xs.map((x) => imagePotential3d(1, 1, s2, d, x, 0, 1));
    const hOne = xs.map((x) => imagePotential3d(1, 1, 1, d, x, 0, 1));
    drawPlot(cvH, {
      xRange: [-10, 10],
      yRange: [0, 1.35 * Math.max(...hTwo, ...hOne)],
      xLabel: "lateral position x (mm), 1 mm above the interface",
      yLabel: "potential (relative)",
      series: [
        { x: xs, y: hOne, color: COLORS.gray, dash: [5, 4], label: "medium 1 everywhere" },
        { x: xs, y: hTwo, color: COLORS.vermillion, width: 2, label: "two media" },
      ],
    });
    const k = reflectionCoefficient(1, s2);
    readout.textContent =
      `sigma2/sigma1 = ${s2.toFixed(2)}, reflection coefficient k = ${k.toFixed(2)}. Above the interface the potential is ` +
      `${(2 / (1 + s2)).toFixed(2)} times what the same source would give in medium 1 alone` +
      `${s2 < 0.05 ? " (an almost insulating medium 2 nearly doubles it)" : s2 > 1 ? " (a better-conducting medium 2 shunts current and lowers it)" : ""}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m02-d1-root");
if (root) mount(root);
