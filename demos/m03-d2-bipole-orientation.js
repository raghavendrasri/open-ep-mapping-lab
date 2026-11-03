// m03-d2 · Bipole orientation and spacing. MIT License.
import { DEFAULTS, bipolarPlanar, linspace, ptp, unipolar } from "./m03-common.js";
import { COLORS, addReadout, addSlider, drawPlot, drawPolar, el, setupCanvas } from "./plot.js";


function drawSchematic(p, theta, d) {
  const { ctx, width, height } = p;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  const cx = width / 2;
  const cy = height / 2 + 8;
  // wavefront: a vertical line moving to the right
  ctx.strokeStyle = COLORS.vermillion;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(cx - 70, cy - 70);
  ctx.lineTo(cx - 70, cy + 70);
  ctx.stroke();
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(cx - 64, cy - 78);
  ctx.lineTo(cx - 20, cy - 78);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(cx - 20, cy - 78);
  ctx.lineTo(cx - 28, cy - 83);
  ctx.lineTo(cx - 28, cy - 73);
  ctx.closePath();
  ctx.fillStyle = COLORS.vermillion;
  ctx.fill();
  // bipole: two electrodes at +/- d/2 along angle theta (scaled for display)
  const L = 12 + 6 * d;
  const ux = Math.cos(theta);
  const uy = Math.sin(theta);
  ctx.strokeStyle = COLORS.ink;
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(cx - L * ux, cy + L * uy);
  ctx.lineTo(cx + L * ux, cy - L * uy);
  ctx.stroke();
  for (const [sx, col] of [[1, COLORS.blue], [-1, COLORS.green]]) {
    ctx.fillStyle = col;
    ctx.beginPath();
    ctx.arc(cx + sx * L * ux, cy - sx * L * uy, 7, 0, 2 * Math.PI);
    ctx.fill();
  }
  ctx.fillStyle = COLORS.ink;
  ctx.font = "12px system-ui, sans-serif";
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  ctx.fillText("wave direction →", 6, 4);
  ctx.fillText("schematic, not to scale", 6, height - 18);
}

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A planar wave travels left to right past a bipole. Top: the two unipolar signals (distal, proximal) and their difference, the bipolar electrogram. " +
        "Bottom left: the bipole and the wave. Bottom right: bipolar peak-to-peak versus bipole angle, relative to a bipole aligned with the wave; " +
        "the dashed curve is the close-bipole prediction, |cos θ|.",
    ),
  );
  const traces = setupCanvas(root, { width: 640, height: 240, label: "Unipolar and bipolar electrograms versus time" });
  const row = el("div", "demo-row");
  root.appendChild(row);
  const schematic = setupCanvas(row, { width: 260, height: 240, label: "Schematic of the wavefront and the bipole" });
  const polar = setupCanvas(row, { width: 260, height: 260, label: "Bipolar peak-to-peak versus bipole angle, polar plot" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const thetaIn = addSlider(controls, { id: "m03-d2-theta", label: "Bipole angle θ", min: 0, max: 180, step: 5, value: 30, unit: "°", digits: 0, onInput: draw });
  const dIn = addSlider(controls, { id: "m03-d2-d", label: "Spacing d", min: 0.5, max: 10, step: 0.5, value: DEFAULTS.d, unit: "mm", digits: 1, onInput: draw });

  const a = DEFAULTS.w + DEFAULTS.h;
  const c = DEFAULTS.c;
  const t = linspace(-15, 15, 601);
  const thetas = linspace(0, 2 * Math.PI, 181);

  function draw() {
    const theta = (Number(thetaIn.value) * Math.PI) / 180;
    const d = Number(dIn.value);
    const delta = 0.5 * d * Math.cos(theta);
    const u1 = Array.from(t, (tt) => unipolar(-c * tt + delta, a));
    const u2 = Array.from(t, (tt) => unipolar(-c * tt - delta, a));
    const vb = Array.from(t, (tt) => bipolarPlanar(-c * tt, d, theta, a));

    drawPlot(traces, {
      xRange: [-15, 15],
      yRange: [-1, 1],
      xLabel: "time (ms)",
      yLabel: "potential (relative units)",
      series: [
        { x: t, y: u1, color: COLORS.blue, width: 1.2, label: "distal unipole" },
        { x: t, y: u2, color: COLORS.green, width: 1.2, dash: [5, 3], label: "proximal unipole" },
        { x: t, y: vb, color: COLORS.ink, width: 2.5, label: "bipolar" },
      ],
    });

    const s = linspace(-60, 60, 1201);
    const ref = ptp(Array.from(s, (v) => bipolarPlanar(v, d, 0, a)));
    const r = Array.from(thetas, (th) => ptp(Array.from(s, (v) => bipolarPlanar(v, d, th, a))) / ref);
    const rNow = ptp(vb) / ref;
    drawPolar(polar, {
      curves: [
        { theta: thetas, r: Array.from(thetas, (th) => Math.abs(Math.cos(th))), color: COLORS.gray, dash: [4, 4], width: 1.2 },
        { theta: thetas, r, color: COLORS.ink },
      ],
      marker: { theta, r: rNow, color: COLORS.vermillion },
      title: "peak-to-peak / aligned",
    });
    drawSchematic(schematic, theta, d);

    readout.textContent =
      `At θ = ${thetaIn.value}°, bipolar peak-to-peak is ${(100 * rNow).toFixed(0)}% of an aligned bipole; ` +
      `the close-bipole formula predicts ${(100 * Math.abs(Math.cos(theta))).toFixed(0)}%. ` +
      `Spacing ${d.toFixed(1)} mm is ${(d / a).toFixed(1)} × a = w + h; the formula holds when spacing is much smaller than a.`;
  }
  draw();
}

// Start after every constant above is defined.
const root = document.getElementById("m03-d2-root");
if (root) mount(root);
