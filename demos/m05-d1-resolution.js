// m05-d1 · Spectral resolution and leakage (eq-m05-resolution, eq-m05-leakage). MIT License.
// Tested in tests/test_m05_demos.py.
import { periodogramAt, twoTone } from "./m05-common.js";
import { COLORS, addReadout, addSelect, addSlider, drawPlot, el, setupCanvas } from "./plot.js";

const FS = 200;

function mount(root) {
  root.appendChild(
    el(
      "p",
      "demo-description",
      "The power spectrum of two equal tones, one fixed at 6 Hz and one you move, from a record of the length you " +
        "choose. Peaks closer than about one over the record length merge; the window trades a wider peak for lower " +
        "leakage into other frequencies.",
    ),
  );
  const cv = setupCanvas(root, { width: 640, height: 250, label: "Power spectrum of two tones" });
  const controls = el("div", "demo-controls");
  root.appendChild(controls);
  const readout = addReadout(root);
  const len = addSlider(controls, { id: "m05-d1-length", label: "Record length", min: 0.25, max: 4, step: 0.05, value: 1, digits: 2, unit: "s", onInput: draw });
  const f2 = addSlider(controls, { id: "m05-d1-f2", label: "Second tone", min: 6.2, max: 9, step: 0.05, value: 7, digits: 2, unit: "Hz", onInput: draw });
  const win = addSelect(controls, { id: "m05-d1-window", label: "Window", options: [{ value: "boxcar", label: "rectangular" }, { value: "hann", label: "Hann" }], value: "boxcar", onChange: draw });
  const freqs = Array.from({ length: 601 }, (_, i) => (15 * i) / 600);

  function draw() {
    const T = Number(len.value);
    const fb = Number(f2.value);
    const x = twoTone(FS, T, 6, fb);
    const P = periodogramAt(x, FS, freqs, win.value);
    const top = Math.max(...P);
    const db = P.map((v) => 10 * Math.log10(Math.max(v / top, 1e-6)));
    const band = freqs.map((f, i) => [f, db[i]]).filter(([f]) => f >= 6 && f <= fb);
    const dip = Math.min(...band.map(([, v]) => v));
    const ends = Math.min(db[Math.round(6 / (15 / 600))], db[Math.round(fb / (15 / 600))]);
    const resolved = band.length > 2 && dip < ends - 3;
    drawPlot(cv, {
      xRange: [0, 15],
      yRange: [-60, 8],
      xLabel: "frequency (Hz)",
      yLabel: "power (dB, relative to peak)",
      series: [{ x: freqs, y: db, color: COLORS.blue, width: 2, label: `${win.value === "hann" ? "Hann" : "rectangular"} window, ${T.toFixed(2)} s` }],
      vlines: [
        { x: 6, color: COLORS.gray, dash: [3, 3] },
        { x: fb, color: COLORS.gray, dash: [3, 3] },
      ],
    });
    readout.textContent =
      `Record ${T.toFixed(2)} s, so frequency resolution about ${(1 / T).toFixed(2)} Hz; tones ${(fb - 6).toFixed(2)} Hz apart: ` +
      `${resolved ? "two peaks." : "one merged peak."} Highest sidelobe of this window: ${win.value === "hann" ? "about -31 dB" : "about -13 dB"}.`;
  }
  draw();
  document.fonts?.ready.then(draw);
}

const root = document.getElementById("m05-d1-root");
if (root) mount(root);
