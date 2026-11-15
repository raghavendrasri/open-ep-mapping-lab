// m13-d2 · Contact-force estimation from three sensors (eq-m13-force, eq-m13-force-noise). MIT License.
// Tested in tests/test_m13_demos.py.
import { ellipse, forceCovariance, forceMatrix } from "./m13-common.js";
import { COLORS, addReadout, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "Three strain sensors around the tip's spring element, at 0° and ±γ (gray spokes). Each reads the axial force " +
        "plus the lateral force projected on its direction, with independent noise of one unit. The blue ellipse is " +
        "the one-standard-deviation error of the estimated lateral force, from least squares. Symmetric spacing " +
        "(γ = 120°) gives a round, small ellipse.",
    ),
  );
  const cv = setupCanvas(root, { width: 420, height: 380, label: "Sensor layout and lateral-force error ellipse" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const bS = addSlider(controls, { id: "m13-d2-beta", label: "Angle γ of sensors 2 and 3", min: 30, max: 170, step: 5, value: 120, digits: 0, unit: "°", onInput: draw });
  const rS = addSlider(controls, { id: "m13-d2-ratio", label: "Axial ÷ lateral sensitivity", min: 0.25, max: 4, step: 0.05, value: 1, digits: 2, onInput: draw });

  function draw() {
    const beta = Number(bS.value), ratio = Number(rS.value);
    const C = forceMatrix([0, beta, -beta], ratio, 1);
    const S = forceCovariance(C, 1);
    const e = ellipse(S[0][0], S[0][1], S[1][1]);
    const series = [0, beta, -beta].map((d) => {
      const p = (d * Math.PI) / 180;
      return { x: [0, 1.6 * Math.cos(p)], y: [0, 1.6 * Math.sin(p)], color: COLORS.gray, width: 2 };
    });
    series.push({ x: e.x, y: e.y, color: COLORS.blue, width: 2.5, label: "1-SD error, lateral force" });
    drawPlot(cv, { xRange: [-2.6, 2.6], yRange: [-2.4, 2.4], xLabel: "lateral force error, x (noise units)", yLabel: "lateral force error, y (noise units)", series });
    const sd = [0, 1, 2].map((i) => Math.sqrt(S[i][i]).toFixed(2));
    readout.textContent = `SD of the estimate (noise units): Fx ${sd[0]}, Fy ${sd[1]}, axial ${sd[2]}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m13-d2-root");
if (root) mount(root);
