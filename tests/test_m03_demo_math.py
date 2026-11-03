"""The browser demos (demos/m03-common.js) must compute the same numbers as the tested Python model.

Runs the JavaScript in Node and compares with labs/python/epml/electrograms.py.
"""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from scipy.special import j1

from epml import electrograms as py

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")

SCRIPT = """
import * as m from "%s";
const s = [-6, -2.5, -1, -0.2, 0, 0.3, 1.1, 4, 9];
const ks = [0, 0.1, 0.7, 1.5, 3.8317, 6, 12];
const out = {
  unipolar: s.map(v => m.unipolar(v, 1.3, 2)),
  unipolarDs: s.map(v => m.unipolarDs(v, 1.3, 2)),
  bipolar: s.map(v => m.bipolarPlanar(v, 2, 0.6, 1.3, 2)),
  bipolarMag: ks.map(k => m.bipolarTransferMag(k, 2, 0.4)),
  height: ks.map(k => m.heightTransfer(k, 1.2)),
  disk: ks.map(k => m.diskTransfer(k, 0.8)),
  j1: [0.5, 1, 2.4, 5, 10, 20, 29].map(x => m.besselJ1(x)),
};
const times = Array.from(m.linspace(-20, 20, 801));
const cl = m.squareClique(1.5);
const n = [Math.cos(0.7), Math.sin(0.7)];
const sig = m.planeWaveSignals(cl.positions, n, times, 1.0, 1.3);
const E = m.cliqueField(cl.positions, sig, cl.pairs);
const omega = m.loopDirection(E.ex, E.ey);
out.ex = Array.from(E.ex); out.ey = Array.from(E.ey);
out.omega = omega;
out.omniPtp = m.ptp(m.omnipolar(E.ex, E.ey, 1.5, omega));
out.times = times;
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def js():
    module_url = (ROOT / "demos" / "m03-common.js").as_uri()
    result = subprocess.run(
        ["node", "--input-type=module", "-e", SCRIPT % module_url],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


S = np.array([-6, -2.5, -1, -0.2, 0, 0.3, 1.1, 4, 9], dtype=float)
K = np.array([0, 0.1, 0.7, 1.5, 3.8317, 6, 12], dtype=float)


def test_unipolar_and_slope_match(js):
    np.testing.assert_allclose(js["unipolar"], py.unipolar(S, 1.3, 2), rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(js["unipolarDs"], py.unipolar_ds(S, 1.3, 2), rtol=1e-12, atol=1e-15)


def test_bipolar_matches(js):
    np.testing.assert_allclose(js["bipolar"], py.bipolar_planar(S, 2, 0.6, 1.3, 2), rtol=1e-12, atol=1e-15)


def test_transfer_functions_match(js):
    np.testing.assert_allclose(js["bipolarMag"], np.abs(py.bipolar_transfer(K, 2, 0.4)), rtol=1e-12, atol=1e-15)
    np.testing.assert_allclose(js["height"], py.height_transfer(K, 1.2), rtol=1e-12)
    np.testing.assert_allclose(js["disk"], py.disk_transfer(K, 0.8), atol=1e-9)


def test_bessel_j1_matches_scipy(js):
    x = np.array([0.5, 1, 2.4, 5, 10, 20, 29])
    np.testing.assert_allclose(js["j1"], j1(x), atol=1e-9)


def test_clique_and_omnipole_match(js):
    t = np.array(js["times"])
    positions = np.array([[-0.75, -0.75], [0.75, -0.75], [-0.75, 0.75], [0.75, 0.75]])
    pairs = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
    n = np.array([np.cos(0.7), np.sin(0.7)])
    u = py.unipolar(py.front_distance(positions, n, t, 1.0), 1.3)
    E = py.clique_field(positions, u, pairs)
    np.testing.assert_allclose(js["ex"], E[0], atol=1e-12)
    np.testing.assert_allclose(js["ey"], E[1], atol=1e-12)
    v, omega = py.omnipolar(E, 1.5)
    assert abs(abs(np.dot(js["omega"], omega)) - 1) < 1e-9
    assert js["omniPtp"] == pytest.approx(py.peak_to_peak(v), rel=1e-9)
