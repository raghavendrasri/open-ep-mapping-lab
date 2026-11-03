// m03-d4 · Far-field rejection. MIT License.
import { DEFAULTS, linspace, ptp, unipolar } from "./m03-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";


// Illustrative far-field source: a current dipole on the bipole axis at distance R, moment along
// the axis, with a biphasic time course centered at T_FAR. Strength is set so that, at R = R_REF,
// its unipolar peak-to-peak equals the local unipolar peak-to-peak. These are not physiological values.
const T_FAR = 25; // ms
const SIG_FAR = 5; // ms
const R_REF = 20; // mm

function farTime(t) {
  const z = (t - T_FAR) / SIG_FAR;
  return -z * Math.exp(-0.5 * z * z);
}

function dipolePotential(x, R) {
  // dipole at (R, 0, h) pointing along x; electrode at (x, 0, h): potential ∝ (x - R) / |x - R|^3
  const r = x - R;
  return r / Math.abs(r) ** 3;
}

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A local wavefront passes the catheter at time 0, and a distant source fires later. " +
        "Each panel is scaled so the local signal has the same size, so you can compare how much of the distant source each recording picks up.",
    ),
  );
  const top = setupCanvas(root, { width: 640, height: 190, label: "Unipolar electrogram with a distant source" });
  const bottom = setupCanvas(root, { width: 640, height: 190, label: "Bipolar electrogram with a distant source" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const rIn = addSlider(controls, { id: "m03-d4-r", label: "Distance to far source R", min: 10, max: 100, step: 5, value: 30, unit: "mm", digits: 0, onInput: draw });

  const a = DEFAULTS.w + DEFAULTS.h;
  const c = DEFAULTS.c;
  const d = DEFAULTS.d;
  const t = linspace(-15, 50, 651);
  const localU = Array.from(t, (tt) => unipolar(-c * tt, a));
  const localB = Array.from(t, (tt) => unipolar(-c * tt + d / 2, a) - unipolar(-c * tt - d / 2, a));
  const localUPtp = ptp(localU);
  const localBPtp = ptp(localB);
  const farShape = Array.from(t, farTime);
  const farShapePtp = ptp(farShape);
  // strength so the unipolar far-field equals the local unipolar peak-to-peak at R = R_REF
  const p0 = localUPtp / (farShapePtp * Math.abs(dipolePotential(0, R_REF)));

  function draw() {
    const R = Number(rIn.value);
    const fu = p0 * dipolePotential(0, R);
    const fb = p0 * (dipolePotential(d / 2, R) - dipolePotential(-d / 2, R));
    const uni = Array.from(t, (_, i) => (localU[i] + fu * farShape[i]) / localUPtp);
    const bip = Array.from(t, (_, i) => (localB[i] + fb * farShape[i]) / localBPtp);
    const lim = (arr) => Math.max(0.8, ...arr.map(Math.abs)) * 1.1;

    drawPlot(top, {
      xRange: [-15, 50],
      yRange: [-lim(uni), lim(uni)],
      xLabel: "time (ms)",
      yLabel: "unipolar / local p-p",
      series: [{ x: t, y: uni, color: COLORS.blue, label: "unipolar" }],
      vlines: [{ x: 0, color: COLORS.gray, label: "local activation" }, { x: T_FAR, color: COLORS.vermillion, label: "far source" }],
    });
    drawPlot(bottom, {
      xRange: [-15, 50],
      yRange: [-lim(bip), lim(bip)],
      xLabel: "time (ms)",
      yLabel: "bipolar / local p-p",
      series: [{ x: t, y: bip, color: COLORS.ink, label: "bipolar" }],
      vlines: [{ x: 0, color: COLORS.gray }, { x: T_FAR, color: COLORS.vermillion }],
    });

    const shareU = (Math.abs(fu) * farShapePtp) / localUPtp;
    const shareB = (Math.abs(fb) * farShapePtp) / localBPtp;
    readout.textContent =
      `At R = ${R} mm, the far source is ${shareU.toFixed(2)} × the local signal on the unipole ` +
      `and ${shareB.toFixed(3)} × on the bipole (spacing ${d} mm).`;
  }
  draw();
  // Redraw once the page fonts have loaded, so canvas labels use them too.
  if (document.fonts) document.fonts.ready.then(draw);
}

// Start after every constant above is defined.
const root = document.getElementById("m03-d4-root");
if (root) mount(root);
