// m06-d2 · Cotangent weights and Delaunay edges (eq-m06-cotan). MIT License. Tested in tests/test_m06_demos.py.
import { edgeCotanWeight } from "./m06-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Two triangles share the edge from (-1, 0) to (1, 0). The angles opposite that edge, alpha above and beta below, " +
        "set its weight in the cotangent Laplacian. Right: the weight against alpha for the beta you choose. When the " +
        "two angles add up to more than 180 degrees the edge is not locally Delaunay and its weight turns negative.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Two triangles and the weight of their shared edge" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const alpha = addSlider(controls, { id: "m06-d2-alpha", label: "Angle above (alpha)", min: 20, max: 160, step: 1, value: 60, digits: 0, unit: "degrees", onInput: draw });
  const beta = addSlider(controls, { id: "m06-d2-beta", label: "Angle below (beta)", min: 20, max: 160, step: 1, value: 60, digits: 0, unit: "degrees", onInput: draw });
  const as = Array.from({ length: 281 }, (_, i) => 20 + (140 * i) / 280);

  function draw() {
    const a = (Number(alpha.value) * Math.PI) / 180;
    const b = (Number(beta.value) * Math.PI) / 180;
    const top = 1 / Math.tan(a / 2);
    const bot = -1 / Math.tan(b / 2);
    const w = edgeCotanWeight(a, b);
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    const left = { ctx, width: width / 2, height, dpr: cv.dpr };
    drawPlot(left, {
      xRange: [-2.2, 2.2],
      yRange: [-3.2, 3.2],
      xLabel: "x",
      yLabel: "y",
      series: [
        { x: [-1, 0, 1, -1], y: [0, top, 0, 0], color: COLORS.blue, width: 2 },
        { x: [-1, 0, 1, -1], y: [0, bot, 0, 0], color: COLORS.green, width: 2 },
        { x: [-1, 1], y: [0, 0], color: w >= 0 ? COLORS.ink : COLORS.vermillion, width: 3 },
      ],
      markers: [{ x: 0, y: top, color: COLORS.blue }, { x: 0, y: bot, color: COLORS.green }],
    });
    ctx.save();
    ctx.translate(width / 2, 0);
    const right = { ctx, width: width / 2, height, dpr: cv.dpr };
    drawPlot(right, {
      xRange: [20, 160],
      yRange: [-2, 3],
      xLabel: "alpha (degrees)",
      yLabel: "edge weight",
      series: [
        { x: as, y: as.map((v) => edgeCotanWeight((v * Math.PI) / 180, b)), color: COLORS.blue, width: 2 },
        { x: [20, 160], y: [0, 0], color: COLORS.gray, dash: [3, 3] },
      ],
      vlines: [{ x: 180 - Number(beta.value), color: COLORS.vermillion, dash: [3, 3] }],
      markers: [{ x: Number(alpha.value), y: w, color: COLORS.vermillion }],
    });
    ctx.restore();
    const sum = Number(alpha.value) + Number(beta.value);
    readout.textContent =
      `alpha + beta = ${sum} degrees; edge weight (cot alpha + cot beta)/2 = ${w.toFixed(3)}. ` +
      (w >= -1e-12 ? "Non-negative: the edge is locally Delaunay." : "Negative: the edge is not locally Delaunay; flipping it would restore a non-negative weight.");
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m06-d2-root");
if (root) mount(root);
