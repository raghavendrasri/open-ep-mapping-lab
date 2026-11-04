"""The m34-m36 browser demos must compute the same numbers as the tested Python models.

Runs demos/m34-common.js, m35-common.js and m36-common.js in Node and compares them with
labs/python/epml/systems.py, ml.py and product.py.
"""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from scipy import stats
from scipy.special import gammaln

from epml import ml
from epml import product as pr
from epml import systems as sy

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")

ARRIVALS = [0.0, 0.3, 0.35, 1.2, 1.25, 1.3, 4.0]
SERVICES = [0.5, 0.2, 0.9, 0.1, 0.4, 0.3, 0.2]

SCRIPT = """
import * as a from "%(m34)s";
import * as b from "%(m35)s";
import * as c from "%(m36)s";
const out = {};
out.depart = Array.from(a.queueDepartures(%(arr)s, %(srv)s));
out.dropDepart = Array.from(a.queueDepartures([0, 0, 0, 0, 0], [1, 1, 1, 1, 1], 2)).map(v => Number.isNaN(v) ? null : v);
out.rate = a.dataRateBps(8, 1000, 14, 0.1);
out.mm1 = [0.2, 0.5, 0.9].map(l => a.mm1MeanTime(l, 1));
out.align = a.alignmentErrorBound(20, -0.03, 0.1, 10);
out.cdf = [-3, -1.2, 0, 0.4, 2.5].map(z => b.normCdf(z));
out.pv = b.predictiveValues(0.85, 0.9, 0.07);
out.auc = [0, 0.8, 2.2].map(d => b.binormalAuc(d));
out.brier = b.brier([0.1, 0.8, 0.5, 0.95], [0, 1, 1, 0]);
const leak = b.clusteredRecords({ patients: 30, perPatient: 10, icc: 0.9, signal: 0 });
out.leak = [b.nearestNeighbourAccuracy(leak, false), b.nearestNeighbourAccuracy(leak, true)];
out.lgamma = [0.3, 1, 4.5, 30, 250].map(x => c.logGamma(x));
out.binom = [[0, 59, 0.05], [1, 93, 0.05], [3, 40, 0.12]].map(([k, n, p]) => c.binomCdf(k, n, p));
out.successRun = [[0.95, 0.95], [0.9, 0.9], [0.99, 0.95]].map(([R, C]) => c.successRunN(R, C));
out.acceptance = [0, 1, 2].map(k => c.acceptanceN(0.95, 0.95, k));
out.series = c.seriesRate([1e-4, 5e-5, 2e-4]);
out.rel = c.reliability(2000, 3.5e-4);
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def js():
    paths = {k: (ROOT / "demos" / f"{k}-common.js").as_uri() for k in ("m34", "m35", "m36")}
    script = SCRIPT % {**paths, "arr": json.dumps(ARRIVALS), "srv": json.dumps(SERVICES)}
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def test_m34_demo_math(js):
    _, depart = sy.simulate_queue(ARRIVALS, SERVICES)
    assert np.allclose(js["depart"], depart)
    assert js["dropDepart"] == [1, 2, None, None, None]  # capacity 2: the third arrival finds the stage full
    assert js["rate"] == pytest.approx(sy.data_rate_bps(8, 1000, 14, 0.1))
    assert js["mm1"] == pytest.approx([sy.mm1_mean_time(l, 1.0) for l in (0.2, 0.5, 0.9)])
    expected = sy.misregistration(20, -0.03) + sy.linear_interp_error_bound(0.1, 20**2 / 10)
    assert js["align"] == pytest.approx(expected)


def test_m35_demo_math(js):
    assert js["cdf"] == pytest.approx(stats.norm.cdf([-3, -1.2, 0, 0.4, 2.5]), abs=2e-7)
    ppv, npv = ml.predictive_values(0.85, 0.9, 0.07)
    assert (js["pv"]["ppv"], js["pv"]["npv"]) == pytest.approx((ppv, npv))
    assert js["auc"] == pytest.approx([ml.binormal_auc(d) for d in (0, 0.8, 2.2)], abs=2e-7)
    assert js["brier"] == pytest.approx(ml.brier_score([0.1, 0.8, 0.5, 0.95], [0, 1, 1, 0]))
    record_wise, patient_wise = js["leak"]
    assert record_wise > 0.9 and abs(patient_wise - 0.5) < 0.15  # no class signal: leakage only


def test_m36_demo_math(js):
    assert js["lgamma"] == pytest.approx(gammaln([0.3, 1, 4.5, 30, 250]), rel=1e-12, abs=1e-12)
    expected = [stats.binom.cdf(k, n, p) for k, n, p in [(0, 59, 0.05), (1, 93, 0.05), (3, 40, 0.12)]]
    assert js["binom"] == pytest.approx(expected, rel=1e-10)
    assert js["successRun"] == [pr.success_run_n(R, C) for R, C in [(0.95, 0.95), (0.9, 0.9), (0.99, 0.95)]]
    assert js["acceptance"] == [pr.acceptance_n(0.95, 0.95, k) for k in (0, 1, 2)]
    assert js["series"] == pytest.approx(pr.series_failure_rate([1e-4, 5e-5, 2e-4]))
    assert js["rel"] == pytest.approx(float(pr.reliability(2000, 3.5e-4)))
