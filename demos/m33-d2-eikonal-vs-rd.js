// m33-d2 · Eikonal vs reaction-diffusion: precomputed activation maps on a 2D sheet. MIT License.
// Data: demos/m33-d2-data.json, written by tools/make_m33_d2.py from the course's own models.
import { bestOffset } from "./m33-common.js";
import { addReadout, addSelect, addSlider, diverging, drawField, el, setupCanvas } from "./plot.js";

function percentile(values, q) {
  const s = values.slice().sort((a, b) => a - b);
  const pos = (s.length - 1) * q;
  const lo = Math.floor(pos);
  return s[lo] + (s[Math.min(lo + 1, s.length - 1)] - s[lo]) * (pos - lo);
}

async function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "The same sheet activated two ways: by a reaction–diffusion (monodomain) model, and by the eikonal model with " +
        "speeds set to the reaction–diffusion model's planar conduction velocities. Colors are activation times in " +
        "2-ms bands. The difference map subtracts the eikonal times, after removing the best constant offset.",
    ),
  );
  const narrow = root.clientWidth > 0 && root.clientWidth < 520; // stack the two maps on phones
  const canvas = setupCanvas(root, { width: narrow ? 340 : 640, height: narrow ? 600 : 300, label: "Activation maps from reaction-diffusion and eikonal models, or their difference" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  let data;
  try {
    const res = await fetch(new URL("./m33-d2-data.json", import.meta.url));
    data = await res.json();
  } catch (err) {
    readout.textContent = "Could not load the precomputed data (demos/m33-d2-data.json).";
    return;
  }
  const n = data.grid.n;
  const step = data.grid.spacing_mm;
  const size = (n - 1) * step;

  const scenario = addSelect(controls, {
    id: "m33-d2-scenario",
    label: "Scenario",
    options: Object.entries(data.scenarios).map(([key, s]) => ({ value: key, label: s.label })),
    value: "isthmus",
    onChange: draw,
  });
  const view = addSelect(controls, {
    id: "m33-d2-view",
    label: "Right panel",
    options: [{ value: "eikonal", label: "Eikonal model" }, { value: "diff", label: "Difference (RD − eikonal)" }],
    value: "diff",
    onChange: draw,
  });
  const band = addSlider(controls, { id: "m33-d2-band", label: "Band width", min: 1, max: 5, step: 1, value: 2, unit: "ms", digits: 0, onInput: draw });

  function draw() {
    const s = data.scenarios[scenario.value];
    const rd = s.rd;
    const ek = s.eikonal;
    const both = rd.map((v, i) => v !== null && ek[i] !== null);
    const off = bestOffset(ek.filter((_, i) => both[i]), rd.filter((_, i) => both[i]));
    const diff = rd.map((v, i) => (both[i] ? v - (ek[i] + off) : null));
    const vals = rd.filter((v) => v !== null);
    const range = [0, Math.max(...vals)];
    const { ctx, width, height } = canvas;
    ctx.clearRect(0, 0, width, height);
    const panels = narrow
      ? [{ x: 0, y: 0, w: width, h: height / 2 }, { x: 0, y: height / 2, w: width, h: height / 2 }]
      : [{ x: 0, y: 0, w: width / 2, h: height }, { x: width / 2, y: 0, w: width / 2, h: height }];
    const common = { nx: n, ny: n, extent: [0, size, 0, size], mask: s.scar, band: Number(band.value) };
    drawField(canvas, { ...common, field: rd, range, unit: "ms", panel: panels[0], title: "Reaction–diffusion" });
    if (view.value === "eikonal") {
      const shifted = ek.map((v) => (v === null ? null : v + off));
      drawField(canvas, { ...common, field: shifted, range, unit: "ms", panel: panels[1], title: "Eikonal (offset removed)" });
    } else {
      drawField(canvas, { ...common, band: null, field: diff, range: [-3, 3], signed: true, colormap: diverging, unit: "ms", panel: panels[1], title: "Difference" });
    }
    const abs = diff.filter((v) => v !== null).map(Math.abs);
    const mean = abs.reduce((a, b) => a + b, 0) / abs.length;
    readout.textContent =
      `${s.label}: best offset ${off.toFixed(2)} ms; after removing it, |difference| averages ${mean.toFixed(2)} ms, ` +
      `95th percentile ${percentile(abs, 0.95).toFixed(2)} ms, maximum ${Math.max(...abs).toFixed(2)} ms. ` +
      `Positive (vermillion) means reaction–diffusion activates later than the eikonal model. ` +
      `Activation maps are drawn in ${band.value}-ms bands.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m33-d2-root");
if (root) mount(root);
