// m43-d2 · Retrieval over the course glossary and formula sheet with TF-IDF and cosine similarity.
// MIT License. Corpus written by tools/make_m43_d2.py; the ranking is checked against Python.
import { buildIndex, search } from "./m43-common.js";
import { COLORS, addReadout, addSelect, addSlider, el, setupCanvas } from "./plot.js";

// Glossary entries are shown by their term; formula-sheet items by their title.
function labeller(corpus) {
  const titles = new Map(corpus.docs.map((d) => [d.id, d.text.split(". ")[0]]));
  return (id) => (id.startsWith("glossary:") ? id.slice(9) : `Formula: ${titles.get(id)}`);
}

async function mount(root) {
  const corpus = await (await fetch(new URL("./m43-d2-corpus.json", import.meta.url))).json();
  const index = buildIndex(corpus.docs, corpus.stop);
  const label = labeller(corpus);
  root.appendChild(
    el(
      "p",
      "demo-description",
      `A search over ${corpus.docs.length} pieces of course text: every glossary entry and every formula-sheet item. ` +
        "Choose one of the lab's test questions or type your own. Bars show the cosine similarity of each of the top " +
        "results to the question; the gold answer of a test question is drawn in green.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Cosine similarity of the top retrieved course entries" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const k = addSlider(controls, { id: "m43-d2-k", label: "Results shown (k)", min: 1, max: 10, step: 1, value: 5, digits: 0, onInput: draw });
  const pick = addSelect(controls, {
    id: "m43-d2-question",
    label: "Test question",
    options: corpus.questions.map((q, i) => ({ value: i, label: q.q })),
    value: 0,
    onChange: () => {
      box.value = corpus.questions[Number(pick.value)].q;
      draw();
    },
  });
  const row = el("div", "demo-control");
  const lab = el("label", null, "Your question");
  lab.htmlFor = "m43-d2-text";
  const box = document.createElement("input");
  Object.assign(box, { type: "text", id: "m43-d2-text", value: corpus.questions[0].q, size: 48 });
  box.addEventListener("input", draw);
  row.append(lab, box);
  controls.appendChild(row);

  function draw() {
    const query = box.value;
    const hits = search(index, query, Number(k.value));
    const qi = corpus.questions.findIndex((q) => q.q === query);
    const gold = qi >= 0 ? new Set(corpus.questions[qi].gold.map((g) => `glossary:${g}`)) : new Set();
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    const left = 250;
    const right = width - 60;
    const top = 16;
    const rowH = Math.min(44, (height - top - 44) / Math.max(hits.length, 1));
    const maxScore = 1;
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.strokeStyle = "#e6e8eb";
    ctx.fillStyle = COLORS.gray;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (let t = 0; t <= 1.0001; t += 0.25) {
      const x = left + (t / maxScore) * (right - left);
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, top + rowH * hits.length);
      ctx.stroke();
      ctx.fillText(t.toFixed(2), x, top + rowH * hits.length + 4);
    }
    ctx.fillStyle = COLORS.ink;
    ctx.fillText("cosine similarity to the question (unitless)", (left + right) / 2, top + rowH * hits.length + 22);
    hits.forEach((h, i) => {
      const y = top + i * rowH;
      ctx.fillStyle = gold.has(h.id) ? COLORS.green : COLORS.blue;
      ctx.fillRect(left, y + 0.2 * rowH, (h.score / maxScore) * (right - left), 0.6 * rowH);
      ctx.fillStyle = COLORS.ink;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      let name = `${i + 1}. ${label(h.id)}`;
      while (ctx.measureText(name).width > left - 12 && name.length > 4) name = name.slice(0, -2) + "…";
      ctx.fillText(name, left - 8, y + rowH / 2);
      ctx.textAlign = "left";
      ctx.fillText(h.score.toFixed(2), left + (h.score / maxScore) * (right - left) + 6, y + rowH / 2);
    });
    const top1 = hits[0];
    let text = top1 && top1.score > 0
      ? `Top ${hits.length}: ${hits.map((h) => `${label(h.id)} (${h.score.toFixed(2)})`).join("; ")}. ` +
        `Words shared with the first result: ${top1.words.join(", ") || "none"}.`
      : "No course entry shares a word with this question: lexical retrieval needs shared words.";
    if (gold.size) {
      const all = search(index, query, index.ids.length);
      const rank = all.findIndex((h) => gold.has(h.id)) + 1;
      text += ` Gold answer rank: ${rank}${rank > Number(k.value) ? ", outside the results shown" : ""}.`;
    }
    readout.textContent = text;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m43-d2-root");
if (root) mount(root);
