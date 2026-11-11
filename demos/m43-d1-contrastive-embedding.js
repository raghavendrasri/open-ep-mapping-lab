// m43-d1 · Contrastive embedding: recordings of the same patient pull together during pretraining.
// MIT License. Data precomputed by tools/make_m43_d1.py from labs/python/epml/foundation.py.
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const PALETTE = [COLORS.blue, COLORS.vermillion, COLORS.green, COLORS.purple, COLORS.orange, COLORS.sky, COLORS.gray, COLORS.ink];

async function mount(root) {
  const data = await (await fetch(new URL("./m43-d1-data.json", import.meta.url))).json();
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Six synthetic recordings from each of eight patients (one color per patient) are passed through an encoder " +
        "while it is pretrained with the contrastive loss on 2,000 other unlabeled patients. Top: the 16-dimensional " +
        "embeddings projected onto their first two principal components. Bottom: the training loss, with the chance " +
        "level of a batch of 128. Move the slider to step through training; choose what counts as a positive pair.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Embeddings of 48 recordings from 8 patients, projected to two dimensions" });
  const lossCv = setupCanvas(root, { width: 640, height: 170, label: "Contrastive training loss against training step" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const n = data.snaps.length;
  const step = addSlider(controls, { id: "m43-d1-step", label: "Training step", min: 0, max: n - 1, step: 1, value: n - 1, digits: 0, onInput: draw });
  const mode = addSelect(controls, {
    id: "m43-d1-mode",
    label: "Positive pairs",
    options: [
      { value: "patient", label: "two recordings of one patient" },
      { value: "recording", label: "two augmentations of one recording" },
    ],
    value: "patient",
    onChange: draw,
  });

  function draw() {
    const i = Number(step.value);
    const s = data.snaps[i];
    step.nextSibling.textContent = String(s);
    step.setAttribute("aria-valuetext", `step ${s}`);
    const d = data.modes[mode.value];
    const f = d.frames[i];
    const limX = 1.15 * Math.max(0.2, ...f.xy.map((p) => Math.abs(p[0])));
    const limY = 1.2 * Math.max(0.2, ...f.xy.map((p) => Math.abs(p[1])));
    drawPlot(cv, {
      xRange: [-limX, limX],
      yRange: [-limY, limY],
      xLabel: "principal component 1 (unitless)",
      yLabel: "component 2",
      series: [],
      markers: f.xy.map((p, k) => ({ x: p[0], y: p[1], color: PALETTE[data.groups[k]], radius: 5 })),
    });
    const steps = d.loss.map((_, k) => k);
    drawPlot(lossCv, {
      xRange: [0, data.snaps[n - 1]],
      yRange: [0, 8],
      xLabel: "training step",
      yLabel: "loss (nats)",
      series: [
        { x: steps, y: d.loss, color: COLORS.blue, width: 1.5, label: "contrastive loss" },
        { x: [0, data.snaps[n - 1]], y: [data.chance, data.chance], color: COLORS.gray, width: 1.5, dash: [4, 3], label: "chance, ln 128" },
      ],
      vlines: [{ x: s, color: COLORS.vermillion }],
    });
    readout.textContent =
      `Step ${s}: same-patient recordings have mean cosine ${f.sameCos.toFixed(2)} (other patients ${f.otherCos.toFixed(2)}). ` +
      `For ${(100 * f.nnAcc).toFixed(0)}% of 400 test recordings the nearest neighbour is the other recording of the same patient ` +
      `(chance 0.25%). A linear probe on these features, trained on 10 labelled patients, detects a wide QRS with AUC ` +
      `${f.probeAuc.toFixed(2)}; the same model on the raw samples reaches ${data.rawProbeAuc.toFixed(2)}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m43-d1-root");
if (root) mount(root);
