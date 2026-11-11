// m41-d1 · Active pace-mapping with a Gaussian process and expected improvement. MIT License.
import { DECOY, ORIGIN, expectedImprovement, gpPosterior, pacingSequence, similarity } from "./m41-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawField, el, setupCanvas } from "./plot.js";

const NX = 31;
const H = 2; // mm
const GRID = Array.from({ length: NX * NX }, (_, k) => [(k % NX) * H, Math.floor(k / NX) * H]);
const VALUES = GRID.map(([x, y]) => similarity(x, y));
const SF = 0.5;
const SN = 0.01;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A 60-by-60-mm patch of heart surface with an unknown origin. Each pacing site gives a similarity score between the " +
        "paced and the target ECG. Left: the Gaussian-process estimate of that score after the paced sites so far (white dots), " +
        "with the true origin (orange) and the next suggested site (blue). Right: expected improvement, which picks the next site.",
    ),
  );
  const narrow = (root.clientWidth || 640) < 520;
  const maps = setupCanvas(root, { width: narrow ? 340 : 640, height: narrow ? 600 : 300, label: "Estimated similarity and expected improvement" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const n = addSlider(controls, { id: "m41-d1-n", label: "Pacing sites so far", min: 2, max: 16, step: 1, value: 5, digits: 0, onInput: draw });
  const ell = addSlider(controls, { id: "m41-d1-ell", label: "GP length scale", min: 4, max: 30, step: 1, value: 12, digits: 0, unit: "mm", onInput: recompute });
  const rule = addSelect(controls, {
    id: "m41-d1-rule",
    label: "Next-site rule",
    options: [{ value: "ei", label: "Expected improvement" }, { value: "random", label: "Random" }],
    value: "ei",
    onChange: recompute,
  });

  let seq = [];
  function recompute() {
    seq = pacingSequence(GRID, VALUES, 17, { ell: Number(ell.value), sf: SF, sn: SN, rule: rule.value });
    draw();
  }
  function draw() {
    const k = Number(n.value);
    const paced = seq.slice(0, k);
    const y = paced.map((i) => VALUES[i]);
    const m = y.reduce((a, b) => a + b, 0) / y.length;
    const post = gpPosterior(paced.map((i) => GRID[i]), y, GRID, Number(ell.value), SF, SN, m);
    const best = Math.max(...y);
    const ei = post.mu.map((mu, i) => expectedImprovement(mu, Math.sqrt(post.variance[i]), best));
    const eiMax = Math.max(...ei, 1e-12);
    const next = seq[k];
    const bestSite = paced[y.indexOf(best)];
    const dist = Math.hypot(GRID[bestSite][0] - ORIGIN[0], GRID[bestSite][1] - ORIGIN[1]);
    const markers = [
      ...paced.map((i) => ({ x: GRID[i][0], y: GRID[i][1], color: "#ffffff", radius: 3.2 })),
      { x: ORIGIN[0], y: ORIGIN[1], color: COLORS.orange, radius: 4.5 },
      { x: GRID[next][0], y: GRID[next][1], color: COLORS.blue, radius: 4 },
    ];
    const { ctx, width, height } = maps;
    ctx.clearRect(0, 0, width, height);
    const panels = narrow
      ? [{ x: 0, y: 0, w: width, h: height / 2 }, { x: 0, y: height / 2, w: width, h: height / 2 }]
      : [{ x: 0, y: 0, w: width / 2, h: height }, { x: width / 2, y: 0, w: width / 2, h: height }];
    const common = { nx: NX, ny: NX, extent: [-H / 2, (NX - 1) * H + H / 2, -H / 2, (NX - 1) * H + H / 2] };
    drawField(maps, { ...common, field: post.mu, range: [-0.4, 1.0], panel: panels[0], title: "Estimated similarity", unit: "score", markers });
    drawField(maps, { ...common, field: ei.map((v) => v / eiMax), range: [0, 1], panel: panels[1], title: "Expected improvement (scaled)", unit: "", markers });
    readout.textContent =
      `After ${k} pacing sites, the best one is ${dist.toFixed(1)} mm from the origin ` +
      `(similarity ${best.toFixed(2)}). Next suggested site: (${GRID[next][0]}, ${GRID[next][1]}) mm.` +
      (Math.hypot(GRID[bestSite][0] - DECOY[0], GRID[bestSite][1] - DECOY[1]) < 10 ? " The search is near the weaker decoy peak." : "");
  }
  recompute();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m41-d1-root");
if (root) mount(root);
