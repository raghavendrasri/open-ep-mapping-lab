// m55-d1 · Fiducial error is not target error: predicted target registration error over a plane for a landmark
// layout (eq-m55-tre, first-order). MIT License. Tested in tests/test_m55_demos.py.
import { fiducialLayout, predictedFre, predictedTre } from "./m55-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawField, el, setupCanvas, viridis } from "./plot.js";

const HALF = 60;
const N = 61;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Landmarks (white dots) are located with some error and used to register an image to the map. The color is " +
        "the predicted root-mean-square error at each point of the plane through them, the target registration " +
        "error. The error the system reports at the landmarks themselves (fiducial registration error) does not " +
        "change with their layout; the error at a target (black dot) does, and grows away from the landmarks.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Predicted target registration error over a plane, with landmark positions" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const tx = addSlider(controls, { id: "m55-d1-target", label: "Target position (x)", min: -50, max: 50, step: 1, value: -30, digits: 0, unit: "mm", onInput: draw });
  const n = addSlider(controls, { id: "m55-d1-n", label: "Number of landmarks", min: 3, max: 12, step: 1, value: 6, digits: 0, onInput: draw });
  const fle = addSlider(controls, { id: "m55-d1-fle", label: "Landmark localization error (RMS)", min: 0.5, max: 6, step: 0.5, value: 2, digits: 1, unit: "mm", onInput: draw });
  const layout = addSelect(controls, {
    id: "m55-d1-layout",
    label: "Layout",
    options: ["spread", "clustered", "nearly collinear"].map((v) => ({ value: v, label: v })),
    value: "clustered",
    onChange: draw,
  });
  const axis = Array.from({ length: N }, (_, i) => -HALF + (2 * HALF * i) / (N - 1));

  function draw() {
    const F = fiducialLayout(layout.value, Number(n.value));
    const e = Number(fle.value);
    const pts = [];
    for (const y of axis) for (const x of axis) pts.push([x, y, 0]);
    const field = predictedTre(F, pts, e);
    const target = [Number(tx.value), 0, 0];
    const tre = predictedTre(F, [target], e)[0];
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    drawField(cv, {
      nx: N, ny: N, field, extent: [-HALF, HALF, -HALF, HALF], range: [0, 15], colormap: viridis,
      panel: { x: 120, y: 0, w: 400, h: height }, title: "Predicted target registration error (mm)", unit: "mm",
      markers: [
        ...F.map((p) => ({ x: p[0], y: p[1], color: "#ffffff", radius: 4 })),
        { x: target[0], y: target[1], color: COLORS.ink, radius: 5 },
      ],
    });
    const fre = predictedFre(Number(n.value), e);
    readout.textContent =
      `${n.value} landmarks, ${layout.value}, localization error ${e.toFixed(1)} mm. Expected fiducial registration ` +
      `error ${fre.toFixed(1)} mm for any layout; predicted error at the target ${tre.toFixed(1)} mm ` +
      `(${(tre / fre).toFixed(1)} times the reported value).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m55-d1-root");
if (root) mount(root);
