// m55-d2 · Overlay on a projection: an atrial model drawn on a C-arm view, with a registration error. Exact pinhole
// geometry (eq-m55-projection). MIT License. Tested in tests/test_m55_demos.py.
import { ellipsoidWireframe, project, visibleError } from "./m55-common.js";
import { COLORS, addReadout, addSelect, addSlider, el, setupCanvas } from "./plot.js";

const SEMI = [25, 20, 22];
const DIRS = {
  x: { label: "patient left-right", v: [1, 0, 0] },
  z: { label: "head-foot", v: [0, 0, 1] },
  y: { label: "front-back", v: [0, 1, 0] },
};

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A left atrial model (gray: where it truly is) and the same model after registration with an error (orange), " +
        "both projected onto the detector of a C-arm. Error across the beam shows as a shift; error along the beam " +
        "barely shows, only as a small change in magnification. Rotate the C-arm to see a hidden error appear.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Projected atrial model, true and with registration error" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const mag = addSlider(controls, { id: "m55-d2-error", label: "Registration error", min: 0, max: 10, step: 0.5, value: 5, digits: 1, unit: "mm", onInput: draw });
  const ang = addSlider(controls, { id: "m55-d2-angle", label: "C-arm angle", min: -60, max: 60, step: 5, value: 0, digits: 0, unit: "°", onInput: draw });
  const dir = addSelect(controls, {
    id: "m55-d2-direction",
    label: "Error direction",
    options: Object.entries(DIRS).map(([k, d]) => ({ value: k, label: d.label })),
    value: "y",
    onChange: draw,
  });
  const lines = ellipsoidWireframe(SEMI);

  function draw() {
    const e = DIRS[dir.value].v.map((c) => c * Number(mag.value));
    const a = Number(ang.value);
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#1f2328";
    ctx.fillRect(0, 0, width, height);
    const scale = 3.2;
    const cx = width / 2;
    const cy = height / 2;
    const drawLines = (offset, color, w) => {
      ctx.strokeStyle = color;
      ctx.lineWidth = w;
      for (const line of lines) {
        ctx.beginPath();
        line.forEach((p, i) => {
          const q = project([p[0] + offset[0], p[1] + offset[1], p[2] + offset[2]], 750, 1100, a);
          const X = cx + scale * q.u;
          const Y = cy - scale * q.v;
          if (i === 0) ctx.moveTo(X, Y);
          else ctx.lineTo(X, Y);
        });
        ctx.stroke();
      }
    };
    drawLines([0, 0, 0], "#8c959f", 1);
    drawLines(e, COLORS.orange, 1.2);
    ctx.fillStyle = "#ffffff";
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.textBaseline = "top";
    ctx.fillText(`C-arm ${a}°`, 10, 8);
    ctx.fillRect(width - 10 - 10 * scale * 1.4667, height - 16, 10 * scale * 1.4667, 2);
    ctx.fillText("10 mm at isocenter", width - 130, height - 34);
    const { seen, hidden } = visibleError(e, a);
    const c0 = project([0, 0, 0], 750, 1100, a);
    const c1 = project(e, 750, 1100, a);
    const shift = Math.hypot(c1.u - c0.u, c1.v - c0.v);
    readout.textContent =
      `${Number(mag.value).toFixed(1)} mm error ${DIRS[dir.value].label}, C-arm at ${a}°: ${seen.toFixed(1)} mm across ` +
      `the beam (visible), ${hidden.toFixed(1)} mm along it (hidden). The center moves ${shift.toFixed(1)} mm on the ` +
      `detector (magnification ${c0.m.toFixed(2)}).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m55-d2-root");
if (root) mount(root);
