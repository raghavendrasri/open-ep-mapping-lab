// m03-d5 · Omnipole from a square clique. MIT License.
import { DEFAULTS, bipolarPlanar, cliqueField, linspace, loopDirection, omnipolar, planeWaveSignals, ptp, squareClique } from "./m03-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";


function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "A plane wave crosses a square clique of four electrodes. Left: the estimated electric field over time (the field loop), " +
        "with the true wave direction (arrow) and the loop's principal axis (dashed). Right: peak-to-peak amplitude versus wave direction " +
        "for a horizontal bipole, a vertical bipole and the omnipole, each relative to a bipole aligned with the wave.",
    ),
  );
  const row = el("div", "demo-row");
  root.appendChild(row);
  const loop = setupCanvas(row, { width: 260, height: 260, label: "Electric field loop, E_y versus E_x" });
  const curves = setupCanvas(row, { width: 420, height: 260, label: "Peak-to-peak versus wave direction for two bipoles and the omnipole" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);

  const thIn = addSlider(controls, { id: "m03-d5-theta", label: "Wave direction", min: 0, max: 355, step: 5, value: 30, unit: "°", digits: 0, onInput: draw });
  const dIn = addSlider(controls, { id: "m03-d5-d", label: "Electrode spacing d", min: 0.5, max: 5, step: 0.25, value: DEFAULTS.d, unit: "mm", onInput: draw });

  const a = DEFAULTS.w + DEFAULTS.h;
  const c = DEFAULTS.c;
  const t = linspace(-20, 20, 401);
  const dirs = Array.from(linspace(0, 355, 72));

  function analyse(deg, d) {
    const th = (deg * Math.PI) / 180;
    const n = [Math.cos(th), Math.sin(th)];
    const { positions, pairs } = squareClique(d);
    const sig = planeWaveSignals(positions, n, t, c, a);
    const E = cliqueField(positions, sig, pairs);
    const omega = loopDirection(E.ex, E.ey);
    const horiz = ptp(sig[1].map((v, i) => v - sig[0][i]));
    const vert = ptp(sig[2].map((v, i) => v - sig[0][i]));
    const omni = ptp(omnipolar(E.ex, E.ey, d, omega));
    return { n, E, omega, horiz, vert, omni };
  }

  function draw() {
    const d = Number(dIn.value);
    const deg = Number(thIn.value);
    // reference: a bipole of spacing d aligned with the wave
    const sRef = linspace(-80, 80, 3201);
    const ref = ptp(Array.from(sRef, (s) => bipolarPlanar(s, d, 0, a)));
    const all = dirs.map((dg) => analyse(dg, d));
    const now = analyse(deg, d);

    let m = 0;
    for (let i = 0; i < t.length; i++) m = Math.max(m, Math.abs(now.E.ex[i]), Math.abs(now.E.ey[i]));
    m *= 1.15;
    drawPlot(loop, {
      xRange: [-m, m],
      yRange: [-m, m],
      xLabel: "E_x (relative units)",
      yLabel: "E_y (relative units)",
      xTicks: 3,
      yTicks: 3,
      margin: { l: 46, b: 40 },
      series: [
        { x: now.E.ex, y: now.E.ey, color: COLORS.blue, width: 2 },
        { x: [-m * now.omega[0], m * now.omega[0]], y: [-m * now.omega[1], m * now.omega[1]], color: COLORS.gray, width: 1.2, dash: [5, 4] },
        { x: [0, 0.8 * m * now.n[0]], y: [0, 0.8 * m * now.n[1]], color: COLORS.vermillion, width: 2.5 },
      ],
      markers: [{ x: 0.8 * m * now.n[0], y: 0.8 * m * now.n[1], color: COLORS.vermillion, radius: 4 }],
    });

    const omniRel = all.map((r) => r.omni / ref);
    drawPlot(curves, {
      xRange: [0, 360],
      yRange: [0, 1.4],
      xLabel: "wave direction (°)",
      yLabel: "peak-to-peak / aligned bipole",
      xTicks: 8,
      series: [
        { x: dirs, y: all.map((r) => r.horiz / ref), color: COLORS.blue, width: 1.5, label: "horizontal bipole" },
        { x: dirs, y: all.map((r) => r.vert / ref), color: COLORS.green, width: 1.5, dash: [5, 3], label: "vertical bipole" },
        { x: dirs, y: omniRel, color: COLORS.ink, width: 3, label: "omnipole" },
      ],
      vlines: [{ x: deg, color: COLORS.vermillion }],
    });

    const spread = (Math.max(...omniRel) / Math.min(...omniRel) - 1) * 100;
    const angleErr = (Math.acos(Math.min(1, Math.abs(now.omega[0] * now.n[0] + now.omega[1] * now.n[1]))) * 180) / Math.PI;
    readout.textContent =
      `Spacing ${d.toFixed(2)} mm (d/a = ${(d / a).toFixed(2)}): across all directions the omnipole varies by ${spread.toFixed(1)}%, ` +
      `while each fixed bipole goes from 0 to full amplitude. At ${deg}°, the loop axis is off the true direction by ${angleErr.toFixed(1)}°.`;
  }
  draw();
}

// Start after every constant above is defined.
const root = document.getElementById("m03-d5-root");
if (root) mount(root);
