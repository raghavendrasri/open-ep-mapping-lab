// m02-d2 · Solving Poisson's equation on a grid (eq-m02-poisson, eq-m02-fd), checked against the image solution.
// MIT License. Tested in tests/test_m02_demos.py.
import { twoMediaProblem } from "./m02-common.js";
import { addReadout, addSlider, diverging, drawField, el, setupCanvas } from "./plot.js";

const HALF = 10;
const DEPTH = 2;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A finite-difference solution of Poisson's equation in two dimensions: a small Gaussian source 2 mm below a flat " +
        "interface at y = 0, with conductivity 1 below and the value you choose above. Left: the computed " +
        "potential. Right: its difference from the exact image solution, which shrinks about fourfold each time the " +
        "grid spacing halves.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Finite-difference potential and its error" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const nodes = addSlider(controls, { id: "m02-d2-nodes", label: "Grid nodes per side", min: 20, max: 100, step: 4, value: 40, digits: 0, onInput: draw });
  const ratio = addSlider(controls, { id: "m02-d2-ratio", label: "Conductivity above (log10 of sigma2/sigma1)", min: -1, max: 1, step: 0.1, value: 0.5, digits: 1, onInput: draw });

  function draw() {
    const n = Number(nodes.value);
    const s2 = 10 ** Number(ratio.value);
    const sol = twoMediaProblem(n, HALF, 1, s2, DEPTH);
    let lo = Infinity;
    let hi = -Infinity;
    for (const v of sol.phi) {
      lo = Math.min(lo, v);
      hi = Math.max(hi, v);
    }
    const err = Array.from(sol.phi, (v, k) => (Math.hypot(sol.xs[k % n], sol.xs[Math.floor(k / n)] + DEPTH) > 2 ? v - sol.exact[k] : null));
    const emax = Math.max(1e-12, ...err.filter((v) => v !== null).map(Math.abs));
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    drawField(cv, {
      nx: n, ny: n, field: Array.from(sol.phi), extent: [-HALF, HALF, -HALF, HALF], range: [lo, hi],
      panel: { x: 0, y: 0, w: width / 2, h: height }, title: "potential (relative)",
      markers: [{ x: 0, y: -DEPTH, color: "#ffffff" }],
    });
    drawField(cv, {
      nx: n, ny: n, field: err, extent: [-HALF, HALF, -HALF, HALF], range: [-emax, emax], signed: true, colormap: diverging,
      panel: { x: width / 2, y: 0, w: width / 2, h: height }, title: "error against images (source disk blanked)",
    });
    readout.textContent =
      `${n} x ${n} nodes, spacing ${sol.h.toFixed(3)} mm, conductivity above ${s2.toFixed(2)}. SOR converged in ` +
      `${sol.iters} sweeps. Largest error more than 2 mm from the source: ${emax.toExponential(2)} ` +
      `(${(100 * emax / (hi - lo)).toFixed(3)}% of the potential range).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m02-d2-root");
if (root) mount(root);
