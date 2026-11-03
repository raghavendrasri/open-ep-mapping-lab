// m03-d3 · Spatial transfer functions. MIT License.
import { DEFAULTS, bipolarTransferMag, diskTransfer, heightTransfer, linspace } from "./m03-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";


function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "How strongly each part of the recording passes each spatial frequency k (wavelength 2π/k). " +
        "Height and electrode size are low-pass filters; the bipole, aligned with the wave, is a high-pass filter with nulls. " +
        "Their product is the band of spatial detail a bipolar recording can see.",
    ),
  );
  const plot = setupCanvas(root, { width: 640, height: 280, label: "Spatial transfer functions versus spatial frequency" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const dIn = addSlider(controls, { id: "m03-d3-d", label: "Spacing d", min: 0.5, max: 10, step: 0.5, value: DEFAULTS.d, unit: "mm", digits: 1, onInput: draw });
  const hIn = addSlider(controls, { id: "m03-d3-h", label: "Height h", min: 0.2, max: 5, step: 0.1, value: DEFAULTS.h, unit: "mm", digits: 1, onInput: draw });
  const rIn = addSlider(controls, { id: "m03-d3-re", label: "Electrode radius", min: 0.25, max: 1.75, step: 0.05, value: DEFAULTS.re, unit: "mm", onInput: draw });

  const k = linspace(0, 8, 641);

  function draw() {
    const d = Number(dIn.value);
    const h = Number(hIn.value);
    const re = Number(rIn.value);
    const bip = Array.from(k, (kk) => bipolarTransferMag(kk, d) / 2);
    const hgt = Array.from(k, (kk) => heightTransfer(kk, h));
    const disk = Array.from(k, (kk) => Math.abs(diskTransfer(kk, re)));
    const prod = Array.from(k, (_, i) => bip[i] * hgt[i] * disk[i]);
    let iMax = 0;
    for (let i = 1; i < prod.length; i++) if (prod[i] > prod[iMax]) iMax = i;

    drawPlot(plot, {
      xRange: [0, 8],
      yRange: [0, 1.05],
      xLabel: "spatial frequency k (rad/mm)",
      yLabel: "gain",
      series: [
        { x: k, y: bip, color: COLORS.blue, width: 1.5, label: "bipole |H|/2" },
        { x: k, y: hgt, color: COLORS.vermillion, width: 1.5, dash: [6, 3], label: "height e^(−kh)" },
        { x: k, y: disk, color: COLORS.green, width: 1.5, dash: [2, 3], label: "electrode |2J₁(kr)/(kr)|" },
        { x: k, y: prod, color: COLORS.ink, width: 3, label: "product" },
      ],
    });

    const kPeak = k[iMax];
    readout.textContent =
      `The product peaks at k = ${kPeak.toFixed(2)} rad/mm (wavelength ${(2 * Math.PI / Math.max(kPeak, 1e-9)).toFixed(1)} mm). ` +
      `The bipole's first null is at k = 2π/d = ${(2 * Math.PI / d).toFixed(2)} rad/mm (wavelength ${d.toFixed(1)} mm).`;
  }
  draw();
  // Redraw once the page fonts have loaded, so canvas labels use them too.
  if (document.fonts) document.fonts.ready.then(draw);
}

// Start after every constant above is defined.
const root = document.getElementById("m03-d3-root");
if (root) mount(root);
