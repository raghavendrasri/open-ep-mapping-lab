// m33-d1 · Calibrate a twin: fit regional speeds to sparse activation times. MIT License.
import { blockRegions, calibrate, eikonalGrid, gridTriangles, kfoldRmse, randn, rng } from "./m33-common.js";
import { COLORS, addButton, addReadout, addSelect, addSlider, drawField, drawPlot, el, setupCanvas } from "./plot.js";

const SIZE = 30; // mm
const H = 1; // mm grid spacing
const NX = SIZE / H + 1;
const V_FAST = 1.0; // m/s = mm/ms, normal-voltage tissue (Heil et al. 2023)
const V_SLOW = 0.6; // m/s, low-voltage areas (Heil et al. 2023)
const SLOW = { x: 18, y: 15, r: 7 }; // hidden slow region, mm
const OFFSET = 20; // ms, unknown to the fit
const SOURCE = 15 * NX; // pacing at the middle of the left edge
const K_OPTIONS = [1, 2, 3, 4]; // blocks per side

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A 30 × 30 mm sheet hides a slow region inside normal tissue. Activation is measured at random points, with " +
        "noise and an unknown timing offset. The twin is an eikonal model with one speed per square region; its speeds " +
        "and offset are fitted to the points. Compare the fitted speed map with the truth, and the error on the fitted " +
        "points with the error on held-out points.",
    ),
  );
  const narrow = root.clientWidth > 0 && root.clientWidth < 520; // stack the two maps on phones
  const maps = setupCanvas(root, { width: narrow ? 340 : 640, height: narrow ? 600 : 300, label: "Two maps of conduction speed: the hidden truth with measured points, and the fitted twin" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const buttons = el("div", "demo-buttons");
  root.appendChild(buttons);
  const readout = addReadout(root);
  const chart = setupCanvas(root, { width: 640, height: 220, label: "Fitting error and held-out error against the number of regions" });

  const nPts = addSlider(controls, { id: "m33-d1-points", label: "Measured points", min: 20, max: 200, step: 10, value: 60, digits: 0, onInput: schedule });
  const noise = addSlider(controls, { id: "m33-d1-noise", label: "Annotation noise (SD)", min: 0, max: 4, step: 0.5, value: 1, unit: "ms", digits: 1, onInput: schedule });
  const kSel = addSelect(controls, {
    id: "m33-d1-regions",
    label: "Regions in the twin",
    options: K_OPTIONS.map((k) => ({ value: k, label: `${k * k} (${k} × ${k})` })),
    value: 3,
    onChange: schedule,
  });
  let seed = 3301;
  addButton(buttons, { label: "New random points", onClick: () => { seed += 1; schedule(); } });
  const compareBtn = addButton(buttons, { label: "Compare region counts", onClick: compare });

  const tris = gridTriangles(NX, NX);
  const grid = { nx: NX, ny: NX, h: H, tris };
  const centroid = tris.map((t) => [t.reduce((a, v) => a + (v % NX) * H, 0) / 3, t.reduce((a, v) => a + Math.floor(v / NX) * H, 0) / 3]);
  const truthSpeed = centroid.map(([x, y]) => ((x - SLOW.x) ** 2 + (y - SLOW.y) ** 2 <= SLOW.r ** 2 ? V_SLOW : V_FAST));
  const truthT = eikonalGrid(NX, NX, H, tris, truthSpeed, [SOURCE]);
  const cells = (NX - 1) * (NX - 1);
  const cellOf = (perTri) => Array.from({ length: cells }, (_, c) => perTri[2 * c]); // first triangle of each cell

  let data;
  let timer;
  let history = [];

  function sample() {
    const rand = rng(seed);
    const idx = Array.from({ length: NX * NX }, (_, i) => i).filter((i) => i !== SOURCE);
    for (let i = idx.length - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [idx[i], idx[j]] = [idx[j], idx[i]];
    }
    const pts = idx.slice(0, Number(nPts.value));
    const sd = Number(noise.value);
    const meas = pts.map((p) => truthT[p] + OFFSET + sd * randn(rand));
    return { pts, meas };
  }

  function fitK(k, { withCv }) {
    const region = blockRegions(tris, NX, H, SIZE, k);
    const fit = calibrate(grid, region, k * k, SOURCE, data.pts, data.meas);
    const cv = withCv ? kfoldRmse(grid, region, k * k, SOURCE, data.pts, data.meas, 5, seed, fit) : null;
    const counts = new Array(k * k).fill(0);
    for (const p of data.pts) {
      const i = Math.min(k - 1, Math.floor(((p % NX) * H / SIZE) * k));
      const j = Math.min(k - 1, Math.floor((Math.floor(p / NX) * H / SIZE) * k));
      counts[j * k + i]++;
    }
    return { k, region, fit, cv, counts };
  }

  function drawMaps(res) {
    const { ctx, width, height } = maps;
    ctx.clearRect(0, 0, width, height);
    const panels = narrow
      ? [{ x: 0, y: 0, w: width, h: height / 2 }, { x: 0, y: height / 2, w: width, h: height / 2 }]
      : [{ x: 0, y: 0, w: width / 2, h: height }, { x: width / 2, y: 0, w: width / 2, h: height }];
    const markers = data.pts.map((p) => ({ x: (p % NX) * H, y: Math.floor(p / NX) * H, color: COLORS.ink, radius: 2.2 }));
    const common = { nx: NX - 1, ny: NX - 1, extent: [0, SIZE, 0, SIZE], range: [0.4, 1.4], unit: "m/s" };
    drawField(maps, { ...common, field: cellOf(truthSpeed), panel: panels[0], title: "Truth and measured points", markers });
    const fitted = res.region.map((r) => (res.counts[r] > 0 ? res.fit.speeds[r] : null));
    drawField(maps, { ...common, field: cellOf(fitted), panel: panels[1], title: `Twin, ${res.k * res.k} region${res.k > 1 ? "s" : ""}` });
  }

  function drawChart() {
    const ks = history.map((h) => h.k * h.k);
    const maxY = Math.max(1, ...history.flatMap((h) => [h.fit.rmse, h.cv ?? 0])) * 1.15;
    drawPlot(chart, {
      xRange: [0, 17],
      yRange: [0, maxY],
      xLabel: "regions in the twin",
      yLabel: "RMSE (ms)",
      series: history.length > 1
        ? [
          { x: ks, y: history.map((h) => h.fit.rmse), color: COLORS.blue, label: "on fitted points" },
          { x: ks, y: history.map((h) => h.cv), color: COLORS.vermillion, label: "on held-out points (5-fold)" },
        ]
        : [],
      markers: history.flatMap((h) => [
        { x: h.k * h.k, y: h.fit.rmse, color: COLORS.blue },
        { x: h.k * h.k, y: h.cv, color: COLORS.vermillion },
      ]),
    });
  }

  function describe(res) {
    const empty = res.counts.filter((c) => c === 0).length;
    const sp = res.fit.speeds.filter((_, r) => res.counts[r] > 0);
    const text =
      `${res.k * res.k} region${res.k > 1 ? "s" : ""}: fitted speeds ${Math.min(...sp).toFixed(2)}–${Math.max(...sp).toFixed(2)} m/s ` +
      `(truth 0.60 and 1.00); offset ${res.fit.offset.toFixed(1)} ms (truth ${OFFSET}); error on fitted points ` +
      `${res.fit.rmse.toFixed(2)} ms` + (res.cv !== null ? `, on held-out points ${res.cv.toFixed(2)} ms.` : ".") +
      (empty ? ` ${empty} region${empty > 1 ? "s have" : " has"} no points inside, so ${empty > 1 ? "their speeds are" : "its speed is"} constrained only indirectly (gray).` : "");
    readout.textContent = text;
  }

  function run() {
    data = sample();
    const res = fitK(Number(kSel.value), { withCv: true });
    drawMaps(res);
    describe(res);
    history = history.filter((h) => h.k !== res.k && h.seed === seed && h.n === data.pts.length && h.sd === Number(noise.value));
    history.push({ ...res, seed, n: data.pts.length, sd: Number(noise.value) });
    history.sort((a, b) => a.k - b.k);
    drawChart();
  }

  function schedule() {
    clearTimeout(timer);
    readout.textContent = "Fitting…";
    timer = setTimeout(run, 120);
  }

  function compare() {
    compareBtn.disabled = true;
    const todo = K_OPTIONS.filter((k) => !history.some((h) => h.k === k));
    const step = () => {
      const k = todo.shift();
      if (k === undefined) {
        compareBtn.disabled = false;
        readout.textContent =
          "Region counts compared on the same points. " +
          history.map((h) => `${h.k * h.k}: ${h.fit.rmse.toFixed(2)} / ${h.cv.toFixed(2)} ms`).join("; ") +
          " (error on fitted / held-out points).";
        return;
      }
      readout.textContent = `Fitting ${k * k} regions…`;
      setTimeout(() => {
        const res = fitK(k, { withCv: true });
        history.push({ ...res, seed, n: data.pts.length, sd: Number(noise.value) });
        history.sort((a, b) => a.k - b.k);
        drawChart();
        step();
      }, 20);
    };
    step();
  }

  run();
  document.fonts?.ready.then(() => {
    const res = history.find((h) => h.k === Number(kSel.value));
    if (res) drawMaps(res);
    drawChart();
  });
}

const root = document.getElementById("m33-d1-root");
if (root) mount(root);
