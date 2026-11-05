// Small canvas plotting and control helpers for the course demos. MIT License.
// No dependencies, so demos run offline.

// Okabe-Ito palette: distinguishable with common color-vision deficiencies.
export const COLORS = {
  blue: "#0072B2",
  vermillion: "#D55E00",
  green: "#009E73",
  purple: "#CC79A7",
  orange: "#E69F00",
  sky: "#56B4E9",
  gray: "#6e7781",
  ink: "#1f2328",
};

export function setupCanvas(parent, { width = 640, height = 240, label }) {
  const canvas = document.createElement("canvas");
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", label);
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  canvas.style.width = "100%";
  canvas.style.maxWidth = `${width}px`;
  canvas.style.height = "auto";
  canvas.style.display = "block";
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  parent.appendChild(canvas);
  return { canvas, ctx, width, height };
}

export function niceTicks(min, max, count = 5) {
  const span = max - min;
  if (!(span > 0)) return [min];
  const raw = span / count;
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 2.5, 5, 10].map((f) => f * mag).find((s) => span / s <= count + 0.5) || 10 * mag;
  const ticks = [];
  for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-9; v += step) {
    ticks.push(Math.abs(v) < step * 1e-9 ? 0 : v);
  }
  return ticks;
}

function fmt(v) {
  const a = Math.abs(v);
  if (a === 0) return "0";
  if (a >= 100 || Number.isInteger(v)) return String(Math.round(v * 100) / 100);
  return v.toPrecision(2).replace(/\.?0+$/, "");
}

// Line plot. series: [{x, y, color, width, dash, label}]; markers: [{x, y, color, label}];
// vlines: [{x, color, dash, label}].
export function drawPlot(p, opts) {
  const { ctx, width, height } = p;
  const m = { l: 58, r: 14, t: 14, b: 42, ...(opts.margin || {}) };
  const [x0, x1] = opts.xRange;
  const [y0, y1] = opts.yRange;
  const X = (v) => m.l + ((v - x0) / (x1 - x0)) * (width - m.l - m.r);
  const Y = (v) => height - m.b - ((v - y0) / (y1 - y0)) * (height - m.t - m.b);

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
  ctx.lineWidth = 1;

  // grid and ticks
  ctx.strokeStyle = "#e6e8eb";
  ctx.fillStyle = COLORS.gray;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  for (const v of niceTicks(x0, x1, opts.xTicks || 6)) {
    ctx.beginPath();
    ctx.moveTo(X(v), m.t);
    ctx.lineTo(X(v), height - m.b);
    ctx.stroke();
    ctx.fillText(fmt(v), X(v), height - m.b + 4);
  }
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (const v of niceTicks(y0, y1, opts.yTicks || 4)) {
    ctx.beginPath();
    ctx.moveTo(m.l, Y(v));
    ctx.lineTo(width - m.r, Y(v));
    ctx.stroke();
    ctx.fillText(fmt(v), m.l - 6, Y(v));
  }

  // axes
  ctx.strokeStyle = "#8c959f";
  ctx.strokeRect(m.l, m.t, width - m.l - m.r, height - m.t - m.b);
  if (y0 < 0 && y1 > 0) {
    ctx.beginPath();
    ctx.moveTo(m.l, Y(0));
    ctx.lineTo(width - m.r, Y(0));
    ctx.stroke();
  }

  // axis labels
  ctx.fillStyle = COLORS.ink;
  ctx.textAlign = "center";
  ctx.textBaseline = "bottom";
  ctx.fillText(opts.xLabel, m.l + (width - m.l - m.r) / 2, height - 4);
  ctx.save();
  ctx.translate(14, m.t + (height - m.t - m.b) / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.textBaseline = "middle";
  ctx.fillText(opts.yLabel, 0, 0);
  ctx.restore();

  // clip to plot area
  ctx.save();
  ctx.beginPath();
  ctx.rect(m.l, m.t, width - m.l - m.r, height - m.t - m.b);
  ctx.clip();

  for (const vl of opts.vlines || []) {
    ctx.strokeStyle = vl.color || COLORS.gray;
    ctx.setLineDash(vl.dash || [4, 4]);
    ctx.beginPath();
    ctx.moveTo(X(vl.x), m.t);
    ctx.lineTo(X(vl.x), height - m.b);
    ctx.stroke();
    ctx.setLineDash([]);
  }

  for (const s of opts.series) {
    ctx.strokeStyle = s.color || COLORS.blue;
    ctx.lineWidth = s.width || 2;
    ctx.setLineDash(s.dash || []);
    ctx.beginPath();
    for (let i = 0; i < s.x.length; i++) {
      const px = X(s.x[i]);
      const py = Y(s.y[i]);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.setLineDash([]);
  }

  for (const mk of opts.markers || []) {
    ctx.fillStyle = mk.color || COLORS.ink;
    ctx.beginPath();
    ctx.arc(X(mk.x), Y(mk.y), mk.radius || 4.5, 0, 2 * Math.PI);
    ctx.fill();
  }
  ctx.restore();

  // legend
  const items = [
    ...opts.series.filter((s) => s.label),
    ...(opts.vlines || []).filter((v) => v.label).map((v) => ({ ...v, dash: v.dash || [4, 4], width: 1.5 })),
    ...(opts.markers || []).filter((v) => v.label),
  ];
  if (items.length) {
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    let y = m.t + 10;
    const xText = opts.legendLeft ? m.l + 34 : width - m.r - 8 - Math.max(...items.map((it) => ctx.measureText(it.label).width));
    for (const it of items) {
      ctx.strokeStyle = it.color || COLORS.blue;
      ctx.fillStyle = it.color || COLORS.ink;
      ctx.lineWidth = it.width || 2;
      ctx.setLineDash(it.dash || []);
      ctx.beginPath();
      if ("y" in it && !("series" in it) && typeof it.y === "number") {
        ctx.arc(xText - 16, y, 4, 0, 2 * Math.PI);
        ctx.fill();
      } else {
        ctx.moveTo(xText - 28, y);
        ctx.lineTo(xText - 6, y);
        ctx.stroke();
      }
      ctx.setLineDash([]);
      ctx.fillStyle = COLORS.ink;
      ctx.fillText(it.label, xText, y);
      y += 17;
    }
  }
  return { X, Y };
}

// Polar plot of r(theta) on a square canvas. curves: [{theta, r, color, dash, label}].
export function drawPolar(p, { curves, rMax = 1, marker, title }) {
  const { ctx, width, height } = p;
  const cx = width / 2;
  const cy = height / 2 + 14;
  const R = Math.min(width, height) / 2 - 34;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#e6e8eb";
  ctx.fillStyle = COLORS.gray;
  ctx.font = '11px "IBM Plex Sans", system-ui, sans-serif';
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  for (const f of [0.25, 0.5, 0.75, 1]) {
    ctx.beginPath();
    ctx.arc(cx, cy, R * f, 0, 2 * Math.PI);
    ctx.stroke();
  }
  for (let deg = 0; deg < 360; deg += 45) {
    const t = (deg * Math.PI) / 180;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + R * Math.cos(t), cy - R * Math.sin(t));
    ctx.stroke();
    ctx.fillText(`${deg}°`, cx + (R + 14) * Math.cos(t), cy - (R + 14) * Math.sin(t));
  }
  for (const c of curves) {
    ctx.strokeStyle = c.color || COLORS.blue;
    ctx.lineWidth = c.width || 2;
    ctx.setLineDash(c.dash || []);
    ctx.beginPath();
    c.theta.forEach((t, i) => {
      const r = (Math.min(c.r[i], rMax) / rMax) * R;
      const px = cx + r * Math.cos(t);
      const py = cy - r * Math.sin(t);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    });
    ctx.stroke();
    ctx.setLineDash([]);
  }
  if (marker) {
    const r = (Math.min(marker.r, rMax) / rMax) * R;
    ctx.fillStyle = marker.color || COLORS.ink;
    ctx.beginPath();
    ctx.arc(cx + r * Math.cos(marker.theta), cy - r * Math.sin(marker.theta), 5, 0, 2 * Math.PI);
    ctx.fill();
  }
  if (title) {
    ctx.fillStyle = COLORS.ink;
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    ctx.fillText(title, 6, 4);
  }
}

// A labeled range slider. Arrow keys work natively. Returns the input element.
export function addSlider(parent, { id, label, min, max, step, value, unit = "", digits = 2, onInput }) {
  const row = document.createElement("div");
  row.className = "demo-control";
  const lab = document.createElement("label");
  lab.htmlFor = id;
  lab.textContent = label;
  const input = document.createElement("input");
  Object.assign(input, { type: "range", id, min, max, step, value });
  const out = document.createElement("output");
  out.htmlFor = id;
  const show = () => {
    const text = `${Number(input.value).toFixed(digits)}${unit ? " " + unit : ""}`;
    out.textContent = text;
    input.setAttribute("aria-valuetext", text);
  };
  input.addEventListener("input", () => {
    show();
    onInput();
  });
  show();
  row.append(lab, input, out);
  parent.appendChild(row);
  return input;
}

// A polite live region that screen readers announce when its text changes.
export function addReadout(parent) {
  const div = document.createElement("div");
  div.className = "demo-readout";
  div.setAttribute("aria-live", "polite");
  parent.appendChild(div);
  return div;
}

export function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

// A labeled drop-down. options: [{value, label}]. Keyboard works natively. Returns the select.
export function addSelect(parent, { id, label, options, value, onChange }) {
  const row = document.createElement("div");
  row.className = "demo-control";
  const lab = document.createElement("label");
  lab.htmlFor = id;
  lab.textContent = label;
  const select = document.createElement("select");
  select.id = id;
  for (const o of options) {
    const opt = document.createElement("option");
    opt.value = String(o.value);
    opt.textContent = o.label;
    select.appendChild(opt);
  }
  select.value = String(value);
  select.addEventListener("change", onChange);
  row.append(lab, select);
  parent.appendChild(row);
  return select;
}

// A button inside the controls row.
export function addButton(parent, { label, onClick }) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "demo-button";
  button.textContent = label;
  button.addEventListener("click", onClick);
  parent.appendChild(button);
  return button;
}

// Viridis (perceptually uniform, readable with common color-vision deficiencies), sampled from
// matplotlib's map at ten points and interpolated linearly.
const VIRIDIS = ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58",
  "#b5de2b", "#fde725"].map((h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)));

export function viridis(t) {
  const u = Math.min(1, Math.max(0, t)) * (VIRIDIS.length - 1);
  const i = Math.min(VIRIDIS.length - 2, Math.floor(u));
  const f = u - i;
  return VIRIDIS[i].map((c, k) => Math.round(c + f * (VIRIDIS[i + 1][k] - c)));
}

// Diverging map for signed differences: Okabe-Ito blue (negative), white (0), vermillion (positive).
export function diverging(t) {
  const neg = [0, 114, 178];
  const pos = [213, 94, 0];
  const s = Math.min(1, Math.max(-1, t));
  const end = s < 0 ? neg : pos;
  return [255, 255, 255].map((w, k) => Math.round(w + Math.abs(s) * (end[k] - w)));
}

// A 2D scalar field on a regular grid, drawn in the panel {x, y, w, h} of a canvas from setupCanvas.
// field: row-major values (row 0 at the bottom), null for no data; extent [x0, x1, y0, y1];
// range [lo, hi]; colormap(t) with t in [0, 1] (or [-1, 1] when signed); band: draw isochrone-like
// bands of this width; mask: optional booleans drawn in gray (for example scar); markers [{x, y}].
export function drawField(p, opts) {
  const { ctx } = p;
  const { nx, ny, field, extent, range, panel, title } = opts;
  const cmap = opts.colormap || viridis;
  const signed = opts.signed || false;
  const m = { l: 44, r: 10, t: 20, b: 36 };
  const W = panel.w - m.l - m.r - 46;
  const H = panel.h - m.t - m.b;
  const side = Math.min(W, H);
  const x0p = panel.x + m.l;
  const y0p = panel.y + m.t;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(panel.x, panel.y, panel.w, panel.h);
  const cw = side / nx;
  const ch = side / ny;
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const k = j * nx + i;
      let color;
      if (opts.mask && opts.mask[k]) color = [140, 149, 159];
      else if (field[k] === null || !Number.isFinite(field[k])) color = [235, 237, 240];
      else {
        let v = field[k];
        if (opts.band) v = Math.floor(v / opts.band) * opts.band + opts.band / 2;
        const t = signed ? v / Math.max(Math.abs(range[0]), Math.abs(range[1])) : (v - range[0]) / (range[1] - range[0]);
        color = cmap(t);
      }
      ctx.fillStyle = `rgb(${color[0]},${color[1]},${color[2]})`;
      ctx.fillRect(x0p + i * cw, y0p + side - (j + 1) * ch, cw + 0.6, ch + 0.6);
    }
  }
  ctx.strokeStyle = "#8c959f";
  ctx.lineWidth = 1;
  ctx.strokeRect(x0p, y0p, side, side);
  const [ex0, ex1, ey0, ey1] = extent;
  const X = (v) => x0p + ((v - ex0) / (ex1 - ex0)) * side;
  const Y = (v) => y0p + side - ((v - ey0) / (ey1 - ey0)) * side;
  for (const mk of opts.markers || []) {
    ctx.fillStyle = mk.color || COLORS.ink;
    ctx.strokeStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(X(mk.x), Y(mk.y), mk.radius || 2.5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
  }
  ctx.font = '11px "IBM Plex Sans", system-ui, sans-serif';
  ctx.fillStyle = COLORS.gray;
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  for (const v of niceTicks(ex0, ex1, 4)) ctx.fillText(fmt(v), X(v), y0p + side + 3);
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  for (const v of niceTicks(ey0, ey1, 4)) ctx.fillText(fmt(v), x0p - 4, Y(v));
  ctx.fillStyle = COLORS.ink;
  ctx.textAlign = "center";
  ctx.textBaseline = "bottom";
  ctx.fillText(opts.xLabel || "x (mm)", x0p + side / 2, y0p + side + 30);
  ctx.save();
  ctx.translate(panel.x + 10, y0p + side / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.textBaseline = "middle";
  ctx.fillText(opts.yLabel || "y (mm)", 0, 0);
  ctx.restore();
  ctx.textAlign = "left";
  ctx.textBaseline = "top";
  if (title) ctx.fillText(title, x0p, panel.y + 3);
  // color bar
  const bx = x0p + side + 10;
  const bw = 10;
  for (let s = 0; s < side; s++) {
    const t = 1 - s / side;
    const c = signed ? cmap(2 * t - 1) : cmap(t);
    ctx.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`;
    ctx.fillRect(bx, y0p + s, bw, 1.5);
  }
  ctx.strokeRect(bx, y0p, bw, side);
  ctx.fillStyle = COLORS.gray;
  ctx.textAlign = "left";
  ctx.textBaseline = "middle";
  const lim = signed ? Math.max(Math.abs(range[0]), Math.abs(range[1])) : null;
  const lo = signed ? -lim : range[0];
  const hi = signed ? lim : range[1];
  for (const v of niceTicks(lo, hi, 4)) ctx.fillText(fmt(v), bx + bw + 3, y0p + side - ((v - lo) / (hi - lo)) * side);
  if (opts.unit) {
    ctx.textBaseline = "bottom";
    ctx.fillText(opts.unit, bx - 2, y0p - 2);
  }
  return { X, Y };
}
