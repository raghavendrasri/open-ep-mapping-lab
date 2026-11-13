// m06-d1 · Edge paths against straight lines on a triangular lattice (eq-m06-geodesic). MIT License.
// Tested in tests/test_m06_demos.py.
import { latticePath, latticePathRatio } from "./m06-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "On a mesh of equilateral triangles, the shortest path that follows edges to a point 8 spacings away (orange) " +
        "against the straight line (black). Bottom: the ratio of the two for every direction. Refining the mesh " +
        "shrinks the steps but not the ratio, so distances measured along edges never converge to the true distance.",
    ),
  );
  const cvL = setupCanvas(root, { width: 640, height: 260, label: "Lattice, straight line and shortest edge path" });
  const cvR = setupCanvas(root, { width: 640, height: 200, label: "Path ratio against direction" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const angle = addSlider(controls, { id: "m06-d1-angle", label: "Direction", min: 0, max: 120, step: 1, value: 30, digits: 0, unit: "degrees", onInput: draw });
  const R = 8;
  const lattice = [];
  for (let j = -2; j <= 10; j++) {
    for (let i = -6; i <= 10; i++) {
      const x = i + 0.5 * j;
      const y = (j * Math.sqrt(3)) / 2;
      for (const [dx, dy] of [[1, 0], [0.5, Math.sqrt(3) / 2], [-0.5, Math.sqrt(3) / 2]]) {
        lattice.push({ x: [x, x + dx], y: [y, y + dy], color: "#d0d7de", width: 1 });
      }
    }
  }
  const thetas = Array.from({ length: 361 }, (_, i) => (120 * i) / 360);

  function draw() {
    const th = (Number(angle.value) * Math.PI) / 180;
    const { k, a, b } = latticePath(R, th);
    const e1 = [Math.cos(k * Math.PI / 3), Math.sin(k * Math.PI / 3)];
    const e2 = [Math.cos((k + 1) * Math.PI / 3), Math.sin((k + 1) * Math.PI / 3)];
    const mid = [a * e1[0], a * e1[1]];
    const end = [R * Math.cos(th), R * Math.sin(th)];
    drawPlot(cvL, {
      xRange: [-4, 10],
      yRange: [-1.5, 8.5],
      xLabel: "x (mesh spacings)",
      yLabel: "y (mesh spacings)",
      series: [
        ...lattice,
        { x: [0, end[0]], y: [0, end[1]], color: COLORS.ink, width: 2, label: "straight line" },
        { x: [0, mid[0], end[0]], y: [0, mid[1], end[1]], color: COLORS.vermillion, width: 2.5, label: "shortest edge path" },
      ],
      markers: [{ x: 0, y: 0, color: COLORS.ink }, { x: end[0], y: end[1], color: COLORS.ink }],
    });
    const r = latticePathRatio(th);
    drawPlot(cvR, {
      xRange: [0, 120],
      yRange: [0.95, 1.2],
      xLabel: "direction (degrees from a mesh edge)",
      yLabel: "edge path / straight line",
      series: [{ x: thetas, y: thetas.map((t) => latticePathRatio((t * Math.PI) / 180)), color: COLORS.blue, width: 2 }],
      markers: [{ x: Number(angle.value), y: r, color: COLORS.vermillion }],
    });
    readout.textContent =
      `Direction ${angle.value} degrees: the edge path is ${(100 * (r - 1)).toFixed(1)}% longer than the straight line ` +
      `(${a.toFixed(2)} + ${b.toFixed(2)} spacings against ${R}). The worst case, 15.5%, is halfway between edge directions.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m06-d1-root");
if (root) mount(root);
