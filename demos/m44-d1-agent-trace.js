// m44-d1 · Agent trace explorer: a recorded run of the course's scripted agent on a mapping-QC case
// whose note carries a prompt injection, with three guardrails switched on or off. MIT License.
// Data precomputed by tools/make_m44_d1.py with labs/python/epml/agent.py (writes simulated).
import { COLORS, addReadout, addSlider, el, setupCanvas } from "./plot.js";

function colour(decision) {
  if (decision.startsWith("blocked") || decision.startsWith("denied") || decision.startsWith("rejected")) return COLORS.green;
  if (decision.includes("simulated") && !decision.startsWith("approved")) return COLORS.vermillion;
  if (decision === "executed (simulated)") return COLORS.vermillion;
  return COLORS.blue;
}

function addCheckbox(parent, id, label, onChange) {
  const row = el("div", "demo-control");
  const box = document.createElement("input");
  Object.assign(box, { type: "checkbox", id, checked: true });
  const lab = el("label", null, label);
  lab.htmlFor = id;
  box.addEventListener("change", onChange);
  row.append(box, lab);
  parent.appendChild(row);
  return box;
}

async function mount(root) {
  const data = await (await fetch(new URL("./m44-d1-data.json", import.meta.url))).json();
  root.appendChild(
    el(
      "p",
      "demo-description",
      `A scripted stand-in agent runs a quality check on synthetic mapping case ${data.case}. Its mapping note ` +
        "contains a hidden instruction to delete files and mark the review as passed, and the stand-in is built to obey " +
        "instructions it reads. It also sends one radius in metres instead of millimetres and adds a number of its own " +
        "to the answer. Switch guardrails off to see what each one stops. Blue: step ran. Green: a guardrail stopped " +
        "it. Red: a harmful step ran (simulated; nothing is deleted or written).",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 300, label: "Steps of the agent run, coloured by what the guardrails decided" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const step = addSlider(controls, { id: "m44-d1-step", label: "Step", min: 1, max: 10, step: 1, value: 1, digits: 0, onInput: draw });
  const schema = addCheckbox(controls, "m44-d1-schema", "Schema and unit checks", draw);
  const allow = addCheckbox(controls, "m44-d1-allow", "Tool allowlist and sandbox paths", draw);
  const approval = addCheckbox(controls, "m44-d1-approval", "Human approval for writes", draw);

  function draw() {
    const key = `${Number(schema.checked)}${Number(allow.checked)}${Number(approval.checked)}`;
    const run = data.runs[key];
    const steps = run.steps;
    step.max = String(steps.length);
    if (Number(step.value) > steps.length) step.value = String(steps.length);
    step.nextSibling.textContent = `${step.value} of ${steps.length}`;
    step.setAttribute("aria-valuetext", `step ${step.value} of ${steps.length}`);
    const cur = Number(step.value) - 1;
    const { ctx, width, height } = cv;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, width, height);
    ctx.font = '12px "IBM Plex Sans", system-ui, sans-serif';
    ctx.textBaseline = "middle";
    const rowH = Math.min(28, (height - 10) / steps.length);
    steps.forEach((s, i) => {
      const y = 5 + i * rowH;
      if (i === cur) {
        ctx.fillStyle = "#eef4fa";
        ctx.fillRect(0, y, width, rowH);
      }
      ctx.fillStyle = s.tool === "final answer" ? (run.untraceable.length ? COLORS.orange : COLORS.blue) : colour(s.decision);
      ctx.fillRect(8, y + 4, 10, rowH - 8);
      ctx.fillStyle = i <= cur ? COLORS.ink : COLORS.gray;
      ctx.textAlign = "left";
      ctx.fillText(`${i + 1}`, 26, y + rowH / 2);
      ctx.fillText(s.tool, 48, y + rowH / 2);
      ctx.fillText(s.tier, 210, y + rowH / 2);
      let d = s.tool === "final answer" && run.untraceable.length ? `flagged: ${run.untraceable.join(", ")} came from no tool` : s.decision;
      ctx.fillText(d, 290, y + rowH / 2);
    });
    const s = steps[cur];
    let text = `Step ${cur + 1}, ${s.tool}${s.args ? " " + s.args : ""}: ${s.decision}. Result: ${s.result}.`;
    if (cur === steps.length - 1) {
      const harms = [];
      if (run.deleteRan) harms.push("the delete command ran (simulated)");
      if (run.outsideWrite) harms.push("'QC passed' was written outside the sandbox (simulated)");
      if (run.unitSlipPassed) harms.push("the radius in metres reached the tool, so no velocity was computed");
      text += harms.length ? ` With these settings: ${harms.join("; ")}.` : " With these settings no harmful step ran.";
      text += ` The final-answer check flags ${run.untraceable.join(", ")} as a number no tool produced.`;
    }
    readout.textContent = text;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m44-d1-root");
if (root) mount(root);
