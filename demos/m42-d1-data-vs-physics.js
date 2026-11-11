// m42-d1 · Data versus physics: fitting an activation map with and without the eikonal term. MIT License.
// Data: demos/m42-d1-data.json, written by tools/make_m42_d1.py from labs/python/epml/pinn.py.
import { COLORS, addReadout, addSlider, drawField, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Activation spreads from a point (orange) across a 60-by-60-mm square. Left: the true map with the measurement " +
        "points (white). Right: the map fitted to those points, from the data alone (weight 0) or with the eikonal " +
        "equation added with the chosen weight.",
    ),
  );
  const narrow = (root.clientWidth || 640) < 520;
  const maps = setupCanvas(root, { width: narrow ? 340 : 640, height: narrow ? 600 : 300, label: "True and fitted activation maps" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  let data = null;
  let nIdx;
  let lIdx;

  function draw() {
    if (!data) return;
    const N = data.N[Number(nIdx.value)];
    const lam = data.lambda[Number(lIdx.value)];
    const fit = data.fits[`${N}_${lam}`];
    for (const [input, text] of [[nIdx, `${N} points`], [lIdx, `${lam}`]]) {
      input.nextSibling.textContent = text; // show the value, not the slider index
      input.setAttribute("aria-valuetext", text);
    }
    const n = data.grid.n;
    const h = data.grid.spacing_mm;
    const pts = data.points.slice(0, N).map(([x, y]) => ({ x, y, color: "#ffffff", radius: 3 }));
    const markers = [...pts, { x: data.source_mm[0], y: data.source_mm[1], color: COLORS.orange, radius: 4.5 }];
    const { ctx, width, height } = maps;
    ctx.clearRect(0, 0, width, height);
    const panels = narrow
      ? [{ x: 0, y: 0, w: width, h: height / 2 }, { x: 0, y: height / 2, w: width, h: height / 2 }]
      : [{ x: 0, y: 0, w: width / 2, h: height }, { x: width / 2, y: 0, w: width / 2, h: height }];
    // The data are stored with x as the slow index (numpy meshgrid, indexing="ij"); drawField wants x fastest.
    const xFast = (f) => f.map((_, k) => f[(k % n) * n + Math.floor(k / n)]);
    const common = { nx: n, ny: n, extent: [-h / 2, (n - 1) * h + h / 2, -h / 2, (n - 1) * h + h / 2], range: [0, 70], unit: "ms" };
    drawField(maps, { ...common, field: xFast(data.truth), panel: panels[0], title: "True map", markers });
    drawField(maps, { ...common, field: xFast(fit.T), panel: panels[1], title: lam === 0 ? "Data only" : `Data + eikonal (weight ${lam})`, markers });
    readout.textContent =
      `${N} points, eikonal weight ${lam}: RMS error over the square ${fit.rmse.toFixed(1)} ms` +
      (lam === 0 ? " (no speed estimate without the physics term)." : `, estimated speed ${fit.speed.toFixed(2)} m/s (true ${data.speed_m_per_s.toFixed(1)}).`);
  }

  fetch(new URL("./m42-d1-data.json", import.meta.url))
    .then((r) => r.json())
    .then((d) => {
      data = d;
      nIdx = addSlider(controls, { id: "m42-d1-n", label: "Measurement points", min: 0, max: d.N.length - 1, step: 1, value: 1, digits: 0, onInput: draw });
      lIdx = addSlider(controls, { id: "m42-d1-lam", label: "Eikonal weight λ", min: 0, max: d.lambda.length - 1, step: 1, value: 3, digits: 0, onInput: draw });
      draw();
      document.fonts?.ready.then(draw);
    })
    .catch(() => {
      readout.textContent = "Could not load the precomputed data (demos/m42-d1-data.json).";
    });
}

const root = document.getElementById("m42-d1-root");
if (root) mount(root);
