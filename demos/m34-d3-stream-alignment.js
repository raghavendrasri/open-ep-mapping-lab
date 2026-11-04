// m34-d3 · Aligning an electrogram stream with a location stream. MIT License.
import { alignmentErrorBound } from "./m34-common.js";
import { COLORS, addReadout, addSlider, el, setupCanvas } from "./plot.js";

const R = 10; // mm, radius of the catheter's path (illustrative)

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A catheter tip moves around a circle. Gray dots: location samples. For each recorded point, blue is where the " +
        "signal was really acquired and red is where the point lands after interpolating the location stream at a time " +
        "that is off by the timing offset.",
    ),
  );
  const view = setupCanvas(root, { width: 640, height: 320, label: "Catheter path with true and misplaced points" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const v = addSlider(controls, { id: "m34-d3-v", label: "Catheter speed v", min: 0, max: 100, step: 5, value: 20, digits: 0, unit: "mm/s", onInput: draw });
  const dt = addSlider(controls, { id: "m34-d3-dt", label: "Timing offset Δt", min: -100, max: 100, step: 5, value: 30, digits: 0, unit: "ms", onInput: draw });
  const h = addSlider(controls, { id: "m34-d3-h", label: "Location sample interval h", min: 5, max: 400, step: 5, value: 100, digits: 0, unit: "ms", onInput: draw });

  function pos(t, w) {
    return [R * Math.cos(w * t), R * Math.sin(w * t)];
  }

  function draw() {
    const vv = Number(v.value);
    const off = Number(dt.value) / 1000;
    const hh = Number(h.value) / 1000;
    const w = vv / R; // rad/s
    const tEnd = vv > 0 ? (2 * Math.PI) / w : 1;
    const samples = [];
    for (let t = -1; t <= tEnd + 1; t += hh) samples.push([t, ...pos(t, w)]);
    const interp = (t) => {
      const i = Math.min(samples.length - 2, Math.max(0, Math.floor((t - samples[0][0]) / hh)));
      const [t0, x0, y0] = samples[i];
      const [, x1, y1] = samples[i + 1];
      const f = (t - t0) / hh;
      return [x0 + f * (x1 - x0), y0 + f * (y1 - y0)];
    };

    const { ctx, width, height } = view;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, width, height);
    const s = (height - 40) / (2 * R + 4);
    const X = (x) => width / 2 + x * s;
    const Y = (y) => height / 2 - y * s;
    ctx.strokeStyle = "#d0d7de";
    ctx.beginPath();
    ctx.arc(X(0), Y(0), R * s, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.fillStyle = COLORS.gray;
    for (const [, x, y] of samples) ctx.fillRect(X(x) - 1.5, Y(y) - 1.5, 3, 3);

    let maxErr = 0;
    for (let i = 0; i < 16; i++) {
      const t = (i / 16) * tEnd;
      const [xt, yt] = pos(t, w);
      const [xa, ya] = interp(t + off);
      maxErr = Math.max(maxErr, Math.hypot(xa - xt, ya - yt));
      ctx.strokeStyle = COLORS.gray;
      ctx.beginPath();
      ctx.moveTo(X(xt), Y(yt));
      ctx.lineTo(X(xa), Y(ya));
      ctx.stroke();
      ctx.fillStyle = COLORS.blue;
      ctx.beginPath();
      ctx.arc(X(xt), Y(yt), 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.fillStyle = COLORS.vermillion;
      ctx.beginPath();
      ctx.arc(X(xa), Y(ya), 3, 0, 2 * Math.PI);
      ctx.fill();
    }
    ctx.fillStyle = COLORS.ink;
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.fillText(`path radius ${R} mm`, 12, 20);

    const bound = alignmentErrorBound(vv, off, hh, R);
    readout.textContent =
      `Largest misplacement ${maxErr.toFixed(2)} mm; bound v|Δt| + h²v²/(8r) = ${bound.toFixed(2)} mm ` +
      `(timing part ${(vv * Math.abs(off)).toFixed(2)} mm).`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m34-d3-root");
if (root) mount(root);
