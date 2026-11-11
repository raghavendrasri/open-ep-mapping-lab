// m39-d1 · What graph-convolution layers do to a map. MIT License.
import { applyAhat, gridNeighbors, hopReach, seededNormals } from "./m39-common.js";
import { COLORS, addReadout, addSlider, drawField, el, setupCanvas } from "./plot.js";

const NX = 31;
const H = 2; // mm between grid points
const SIZE = (NX - 1) * H;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A noisy map on a 60-by-60-mm mesh holds a disc of low values. Each graph-convolution layer replaces every point by a " +
        "degree-weighted average of itself and its mesh neighbours. Left: the input. Right: after the chosen number of layers, " +
        "with the points that can influence the centre point marked.",
    ),
  );
  const narrow = (root.clientWidth || 640) < 520;
  const maps = setupCanvas(root, { width: narrow ? 340 : 640, height: narrow ? 600 : 300, label: "Input map and the map after graph-convolution layers" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const layers = addSlider(controls, { id: "m39-d1-layers", label: "Layers", min: 0, max: 12, step: 1, value: 3, digits: 0, onInput: draw });
  const radius = addSlider(controls, { id: "m39-d1-radius", label: "Disc radius", min: 2, max: 20, step: 1, value: 8, digits: 0, unit: "mm", onInput: draw });
  const noise = addSlider(controls, { id: "m39-d1-noise", label: "Noise SD (map units)", min: 0, max: 0.6, step: 0.05, value: 0.3, onInput: draw });

  const neigh = gridNeighbors(NX, NX);
  const z = seededNormals(NX * NX, 39);
  const centre = Math.floor(NX / 2) * NX + Math.floor(NX / 2);

  function draw() {
    const L = Number(layers.value);
    const R = Number(radius.value);
    const sd = Number(noise.value);
    const truth = Array.from({ length: NX * NX }, (_, k) => {
      const x = (k % NX) * H - SIZE / 2;
      const y = Math.floor(k / NX) * H - SIZE / 2;
      return x * x + y * y <= R * R ? 0.2 : 1.0;
    });
    const input = truth.map((t, k) => t + sd * z[k]);
    let out = input;
    for (let l = 0; l < L; l++) out = applyAhat(neigh, out);
    const reach = hopReach(neigh, centre, L);
    const markers = [];
    reach.forEach((r, k) => {
      if (r && L > 0) markers.push({ x: (k % NX) * H, y: Math.floor(k / NX) * H, color: COLORS.vermillion, radius: 1.6 });
    });
    const { ctx, width, height } = maps;
    ctx.clearRect(0, 0, width, height);
    const panels = narrow
      ? [{ x: 0, y: 0, w: width, h: height / 2 }, { x: 0, y: height / 2, w: width, h: height / 2 }]
      : [{ x: 0, y: 0, w: width / 2, h: height }, { x: width / 2, y: 0, w: width / 2, h: height }];
    const common = { nx: NX, ny: NX, extent: [-H / 2, SIZE + H / 2, -H / 2, SIZE + H / 2], range: [-0.2, 1.4], unit: "map units" };
    drawField(maps, { ...common, field: input, panel: panels[0], title: "Input (noisy)" });
    drawField(maps, { ...common, field: out, panel: panels[1], title: `After ${L} layer${L === 1 ? "" : "s"}`, markers });
    const err = (f) => Math.sqrt(f.reduce((s, v, k) => s + (v - truth[k]) ** 2, 0) / f.length);
    const inside = truth.map((t) => t < 0.5);
    const mean = (f, m) => f.filter((_, k) => m[k] === true).reduce((s, v) => s + v, 0) / Math.max(1, m.filter(Boolean).length);
    const contrast = (f) => mean(f, inside.map((v) => !v)) - mean(f, inside);
    readout.textContent =
      `After ${L} layers the centre point depends on ${reach.filter(Boolean).length} points, up to ${L} edges (${L * H} mm along the grid) away. ` +
      `RMS error against the noise-free map: input ${err(input).toFixed(2)}, output ${err(out).toFixed(2)}. ` +
      `Contrast between background and disc: input ${contrast(input).toFixed(2)}, output ${contrast(out).toFixed(2)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m39-d1-root");
if (root) mount(root);
