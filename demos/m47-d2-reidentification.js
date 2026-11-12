// m47-d2 · Re-identification risk in a synthetic registry as quasi-identifiers are released or coarsened.
// MIT License. classSizes and reidRisk are tested against Python (tests/test_m47_demos.py).
import { normals } from "./m45-common.js";
import { classSizes, reidRisk, uniforms } from "./m47-common.js";
import { COLORS, addReadout, addSelect, addSlider, el, setupCanvas } from "./plot.js";

const N = 2000;
const BUCKETS = [[1, 1, "1"], [2, 4, "2–4"], [5, 9, "5–9"], [10, 19, "10–19"], [20, Infinity, "20+"]];

// Synthetic registry from a fixed seed: age, sex code, region (30 codes, unevenly used), day of year,
// device model. All distributions are illustrative; no real people.
function registry() {
  const z = normals(N, 21);
  const u = uniforms(4 * N, 22);
  const w = Array.from({ length: 30 }, (_, i) => 1 / (i + 1));
  const cum = [];
  w.reduce((s, v, i) => (cum[i] = s + v), 0);
  const total = cum[29];
  const pick = (p) => cum.findIndex((c) => p * total <= c);
  const age = [];
  const sex = [];
  const region = [];
  const day = [];
  const device = [];
  for (let i = 0; i < N; i++) {
    age.push(Math.min(95, Math.max(18, Math.round(65 + 12 * z[i]))));
    sex.push(u[4 * i] < 0.5 ? 0 : 1);
    region.push(pick(u[4 * i + 1]));
    day.push(Math.floor(365 * u[4 * i + 2]));
    device.push(u[4 * i + 3] < 0.6 ? 0 : u[4 * i + 3] < 0.9 ? 1 : 2);
  }
  return { age, sex, region, day, device };
}

const RELEASES = [
  { value: "as", label: "age, sex", cols: ["age", "sex"] },
  { value: "asd", label: "age, sex, device", cols: ["age", "sex", "device"] },
  { value: "asdr", label: "age, sex, device, region", cols: ["age", "sex", "device", "region"] },
  { value: "asdrm", label: "… and procedure month", cols: ["age", "sex", "device", "region", "month"] },
  { value: "asdrd", label: "… and procedure day", cols: ["age", "sex", "device", "region", "day"] },
];

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A synthetic registry of 2,000 procedures. Choose which fields are released and how coarsely age is " +
        "grouped. Records that share all released values form a class; someone who knows a person's values " +
        "and that they are in the registry picks the right record with probability one over the class size. " +
        "The bars show the share of records in classes of each size; size 1 means unique.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 240, label: "Share of records by equivalence-class size" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const width = addSlider(controls, { id: "m47-d2-age", label: "Age group width (years)", min: 1, max: 20, step: 1, value: 1, digits: 0, onInput: draw });
  const release = addSelect(controls, { id: "m47-d2-release", label: "Released fields", options: RELEASES, value: "asdr", onChange: draw });
  const reg = registry();

  function draw() {
    const wy = Number(width.value);
    const cols = RELEASES.find((r) => r.value === release.value).cols;
    const table = {
      age: reg.age.map((a) => Math.floor(a / wy) * wy),
      sex: reg.sex,
      device: reg.device,
      region: reg.region,
      month: reg.day.map((d) => Math.floor(d / 30)),
      day: reg.day,
    };
    const sizes = classSizes(cols.map((c) => table[c]));
    const risk = reidRisk(sizes);
    const shares = BUCKETS.map(([lo, hi]) => sizes.filter((f) => f >= lo && f <= hi).length / N);
    const { ctx, width: W, height: H } = cv;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    const x0 = 70;
    const w = W - x0 - 20;
    const top = 16;
    const bottom = H - 44;
    const Y = (v) => bottom - v * (bottom - top);
    ctx.strokeStyle = "#e6e8eb";
    ctx.fillStyle = COLORS.gray;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (const t of [0, 0.25, 0.5, 0.75, 1]) {
      ctx.beginPath();
      ctx.moveTo(x0, Y(t));
      ctx.lineTo(x0 + w, Y(t));
      ctx.stroke();
      ctx.fillText(t.toFixed(2), x0 - 6, Y(t));
    }
    ctx.strokeStyle = "#8c959f";
    ctx.strokeRect(x0, top, w, bottom - top);
    const bw = w / BUCKETS.length;
    shares.forEach((s, i) => {
      ctx.fillStyle = i === 0 ? COLORS.vermillion : COLORS.blue;
      ctx.fillRect(x0 + i * bw + bw * 0.2, Y(s), bw * 0.6, bottom - Y(s));
      ctx.fillStyle = COLORS.ink;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(BUCKETS[i][2], x0 + (i + 0.5) * bw, bottom + 4);
    });
    ctx.textBaseline = "bottom";
    ctx.fillText("class size (records sharing all released values)", x0 + w / 2, H - 4);
    ctx.save();
    ctx.translate(16, (top + bottom) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = "middle";
    ctx.fillText("share of records", 0, 0);
    ctx.restore();
    readout.textContent =
      `Released: ${cols.join(", ")}; age in ${wy}-year groups. ${(100 * risk.unique).toFixed(1)}% of records are unique. ` +
      `Smallest class k = ${risk.k} (largest risk ${risk.max.toFixed(2)}); average risk ${risk.average.toFixed(3)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m47-d2-root");
if (root) mount(root);
