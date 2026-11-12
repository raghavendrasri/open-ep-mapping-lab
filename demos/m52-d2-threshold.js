// m52-d2 · Fibrosis depends on the threshold: a synthetic, unwrapped left atrial wall with known fibrotic patches,
// "scanned" twice, and the burden each published threshold finds. MIT License. Data: demos/m52-d2-wall.json
// (tools/make_m52_d2.py); formulas tested in tests/test_m52_demos.py.
import { burden, dice, thresholdFor } from "./m52-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const CATEGORY = {
  tp: [213, 94, 0], // found and true: vermillion
  fp: [230, 159, 0], // found, not true: orange
  fn: [86, 180, 233], // true, missed: sky blue
};

async function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A synthetic left atrial wall, cut open and laid flat, with fibrotic patches whose extent we know (15% of " +
        "the wall; columns go around the atrium, rows up its wall). Intensities are divided by the blood-pool mean " +
        "(image intensity ratio, IIR). Left: the wall. " +
        "Right: what a threshold calls fibrosis, against the truth. Choose a published threshold or set your own, " +
        "and compare the burden it reports with the truth and with a repeat scan of the same wall.",
    ),
  );
  const data = await (await fetch(new URL("./m52-d2-wall.json", import.meta.url))).json();
  const { nx, ny, wall, repeat, truth } = data;
  const cvMap = setupCanvas(root, { width: 640, height: 200, label: "Unwrapped atrial wall: intensity ratio and the pixels above the threshold" });
  const cvHist = setupCanvas(root, { width: 640, height: 180, label: "Histogram of wall intensity ratios with the threshold" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const th = addSlider(controls, { id: "m52-d2-threshold", label: "IIR threshold", min: 0.8, max: 2.0, step: 0.01, value: 1.2, digits: 2, onInput: () => { method.value = "custom"; draw(); } });
  const options = data.methods.map((m, i) => ({ value: String(i), label: m.label }));
  options.push({ value: "custom", label: "custom (slider)" });
  const method = addSelect(controls, { id: "m52-d2-method", label: "Method", options, value: "1", onChange: () => { if (method.value !== "custom") setFromMethod(); draw(); } });

  function setFromMethod() {
    const m = data.methods[Number(method.value)];
    const t = thresholdFor(m, wall, data.bloodSd);
    th.value = String(Math.min(2, Math.max(0.8, t)));
    const text = Number(th.value).toFixed(2);
    th.nextSibling.textContent = text;
    th.setAttribute("aria-valuetext", text);
  }

  // histogram of the wall, fixed bins
  const bins = 60;
  const lo = 0.2;
  const hi = 2.2;
  const counts = new Array(bins).fill(0);
  for (const v of wall) {
    const k = Math.floor(((v - lo) / (hi - lo)) * bins);
    if (k >= 0 && k < bins) counts[k] += 1;
  }
  const hx = [];
  const hy = [];
  counts.forEach((c, k) => {
    const a = lo + ((hi - lo) * k) / bins;
    const b = lo + ((hi - lo) * (k + 1)) / bins;
    const y = c / wall.length;
    hx.push(a, a, b, b);
    hy.push(0, y, y, 0);
  });
  const ymax = Math.max(...hy) * 1.15;
  const truthBurden = truth.reduce((a, b) => a + b, 0) / truth.length;

  function drawMap(ctx, x0, w, h, color) {
    const cw = w / nx;
    const ch = (h - 28) / ny;
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const c = color(j * nx + i);
        ctx.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`;
        ctx.fillRect(x0 + i * cw, 20 + (ny - 1 - j) * ch, cw + 0.5, ch + 0.5);
      }
    }
    ctx.strokeStyle = "#8c959f";
    ctx.strokeRect(x0, 20, w, h - 28);
  }

  function draw() {
    const m = method.value === "custom" ? null : data.methods[Number(method.value)];
    const t1 = m ? thresholdFor(m, wall, data.bloodSd) : Number(th.value);
    const t2 = m ? thresholdFor(m, repeat, data.bloodSdRepeat) : Number(th.value);
    const found = wall.map((v) => v > t1);
    const found2 = repeat.map((v) => v > t2);
    const { ctx, width, height } = cvMap;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    const w = 300;
    drawMap(ctx, 10, w, height, (k) => {
      const g = Math.round(255 * Math.min(1, Math.max(0, (wall[k] - 0.3) / 1.7)));
      return [g, g, g];
    });
    drawMap(ctx, 330, w, height, (k) => {
      if (found[k] && truth[k]) return CATEGORY.tp;
      if (found[k]) return CATEGORY.fp;
      if (truth[k]) return CATEGORY.fn;
      return [235, 237, 240];
    });
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.fillStyle = COLORS.ink;
    ctx.textBaseline = "top";
    ctx.fillText("Wall IIR (dark 0.3, bright 2.0)", 10, 3);
    ctx.fillText("Found and true · found only · missed", 330, 3);
    drawPlot(cvHist, {
      xRange: [lo, hi],
      yRange: [0, ymax],
      xLabel: "wall intensity ratio (IIR)",
      yLabel: "fraction of wall",
      series: [{ x: hx, y: hy, color: COLORS.blue, width: 1.5 }],
      vlines: [{ x: t1, color: COLORS.vermillion, dash: [4, 3], label: "threshold" }],
    });
    readout.textContent =
      `Threshold IIR ${t1.toFixed(2)}${m && m.kind !== "iir" ? ` (from ${m.kind === "sd" ? "the blood pool" : "Otsu"})` : ""}. ` +
      `Burden ${(100 * burden(wall, t1)).toFixed(1)}% against a true ${(100 * truthBurden).toFixed(0)}%. ` +
      `Overlap with the truth (Dice) ${dice(found, truth).toFixed(2)}; with a repeat scan ${dice(found, found2).toFixed(2)}.`;
  }
  setFromMethod();
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m52-d2-root");
if (root) mount(root);
