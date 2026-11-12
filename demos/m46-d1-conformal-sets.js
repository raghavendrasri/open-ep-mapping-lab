// m46-d1 · Conformal prediction sets for a three-class rhythm model. MIT License.
// Synthetic class probabilities from a fixed seed; the conformal code is tested against Python.
import { conformalSets } from "./m46-common.js";
import { normals } from "./m45-common.js";
import { COLORS, addReadout, addSelect, addSlider, el, setupCanvas } from "./plot.js";

const CLASSES = ["sinus rhythm", "AF", "early beats"];
const SEPARATION = [3.0, 2.0, 1.0]; // how far each class's own logit sits above the others (illustrative)

function makeData(n, seed) {
  const z = normals(4 * n, seed);
  const P = [];
  const y = [];
  for (let i = 0; i < n; i++) {
    const k = Math.floor(((z[4 * i + 3] + 4) * 1000) % 3);
    const logits = [0, 1, 2].map((j) => z[4 * i + j] + (j === k ? SEPARATION[k] : 0));
    const m = Math.max(...logits);
    const e = logits.map((v) => Math.exp(v - m));
    const s = e.reduce((a, b) => a + b, 0);
    P.push(e.map((v) => v / s));
    y.push(k);
  }
  return { P, y };
}

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A classifier gives each recording probabilities for three rhythm classes; the third class is the hardest to " +
        "tell apart. Conformal prediction turns them into a set of classes that should contain the true one with " +
        "probability at least 1 − α, using 600 calibration recordings. Left: coverage in each true class (target as a " +
        "dashed line). Right: how many classes the sets contain. Empty sets mean no class looked plausible.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 260, label: "Coverage by class and the distribution of prediction-set sizes" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const alpha = addSlider(controls, { id: "m46-d1-alpha", label: "Error rate α", min: 0.02, max: 0.3, step: 0.01, value: 0.1, digits: 2, onInput: draw });
  const mode = addSelect(controls, {
    id: "m46-d1-mode",
    label: "Thresholds",
    options: [{ value: "marginal", label: "one for all classes" }, { value: "class", label: "one per class" }],
    value: "marginal",
    onChange: draw,
  });
  const cal = makeData(600, 11);
  const test = makeData(3000, 12);

  function draw() {
    const a = Number(alpha.value);
    const sets = conformalSets(cal.P, cal.y, test.P, a, mode.value === "class");
    const cov = [0, 1, 2].map((k) => {
      const idx = test.y.map((v, i) => (v === k ? i : -1)).filter((i) => i >= 0);
      return idx.filter((i) => sets[i][k]).length / idx.length;
    });
    const sizes = [0, 0, 0, 0];
    sets.forEach((s) => sizes[s.filter(Boolean).length]++);
    const overall = test.y.filter((v, i) => sets[i][v]).length / test.y.length;
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    const panel = (x0, w, values, labels, colour, yMax, title, target) => {
      const top = 24;
      const bottom = height - 46;
      const Y = (v) => bottom - (v / yMax) * (bottom - top);
      ctx.strokeStyle = "#8c959f";
      ctx.strokeRect(x0, top, w, bottom - top);
      ctx.fillStyle = COLORS.ink;
      ctx.textAlign = "center";
      ctx.textBaseline = "bottom";
      ctx.fillText(title, x0 + w / 2, top - 6);
      ctx.textBaseline = "middle";
      ctx.textAlign = "right";
      for (const t of [0, yMax / 2, yMax]) ctx.fillText(t.toFixed(yMax === 1 ? 1 : 0), x0 - 4, Y(t));
      const bw = w / values.length;
      values.forEach((v, i) => {
        ctx.fillStyle = colour;
        ctx.fillRect(x0 + i * bw + bw * 0.2, Y(v), bw * 0.6, bottom - Y(v));
        ctx.fillStyle = COLORS.ink;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(labels[i], x0 + (i + 0.5) * bw, bottom + 4);
      });
      if (target !== undefined) {
        ctx.strokeStyle = COLORS.vermillion;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(x0, Y(target));
        ctx.lineTo(x0 + w, Y(target));
        ctx.stroke();
        ctx.setLineDash([]);
      }
    };
    panel(60, 250, cov, CLASSES, COLORS.blue, 1, "coverage by true class (share)", 1 - a);
    panel(380, 240, sizes.map((s) => s / sets.length), ["0", "1", "2", "3"], COLORS.green, 1, "set size (share of recordings)");
    ctx.fillStyle = COLORS.ink;
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText("classes in the set", 500, height - 4);
    readout.textContent =
      `α = ${a.toFixed(2)}: overall coverage ${(100 * overall).toFixed(1)}% (target at least ${(100 * (1 - a)).toFixed(0)}%). ` +
      `By class: ${CLASSES.map((c, k) => `${c} ${(100 * cov[k]).toFixed(1)}%`).join(", ")}. ` +
      `Mean set size ${(sizes.reduce((s, v, i) => s + v * i, 0) / sets.length).toFixed(2)}; empty sets ${(100 * sizes[0] / sets.length).toFixed(1)}%.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m46-d1-root");
if (root) mount(root);
