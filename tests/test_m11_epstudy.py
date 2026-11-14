"""m11 · The EP study: equation tests."""

import numpy as np
import pytest

from epml import epstudy as E
from epml.arrhythmia import traveling_pulse


def test_intervals():
    """eq-m11-intervals: AH and HV from the steepest downslopes of the atrial, His and ventricular deflections, within
    0.2 ms on a synthetic recording with noise."""
    t, x = E.his_recording(50.0, 120.0, 165.0, noise=0.02, seed=3)
    ta = E.local_time(t, x, (30, 80))
    th = E.local_time(t, x, (100, 140))
    tv = E.local_time(t, x, (145, 200))
    ah, hv = E.intervals(ta, th, tv)
    assert ah == pytest.approx(70.0, abs=0.2) and hv == pytest.approx(45.0, abs=0.2)


def test_avnode():
    """eq-m11-avnode: nodal conduction time is NCT_max at the nodal refractory period, falls toward NCT_min with
    recovery time, and the node blocks below ERP_N."""
    p = E.AVN
    assert float(E.nodal_time(p["erp"])) == pytest.approx(p["nct_max"])
    assert float(E.nodal_time(1e6)) == pytest.approx(p["nct_min"])
    assert np.isnan(E.nodal_time(p["erp"] - 1))
    rts = np.linspace(p["erp"], 600, 50)
    assert np.all(np.diff(E.nodal_time(rts)) < 0)


def test_wenckebach():
    """eq-m11-wenckebach: with a stable fixed point ((NCT_max - NCT_min) / tau < 1) conduction is 1:1 down to
    ERP_N + NCT_max = 241 ms; below it nodal times lengthen beat by beat until a beat blocks (Wenckebach), with
    ratios that fall as the rate rises, down to 2:1."""
    cl_w, slope = E.wenckebach_cl()
    assert cl_w == pytest.approx(241.0) and slope < 1
    assert E.conduction_ratio(E.av_sequence(cl_w + 1, 60)) == (1, 1)
    assert E.conduction_ratio(E.av_sequence(220.0, 60)) == (4, 3)
    assert E.conduction_ratio(E.av_sequence(150.0, 60)) == (2, 1)
    seq = E.av_sequence(220.0, 60)
    cycle = seq[-4:]
    k = int(np.where(np.isnan(cycle))[0][0])
    conducted = np.roll(cycle, -k - 1)[:3]
    assert np.all(np.diff(conducted) > 0)                  # progressive prolongation before the block


def test_ppi():
    """eq-m11-ppi: entraining reentry on a Mitchell-Schaeffer ring, the post-pacing interval exceeds the tachycardia
    cycle length by about 2 d / CV when pacing a branch d mm from the circuit, and only slightly (rate-related
    slowing) when pacing on the circuit; faster pacing lengthens the PPI inside the circuit."""
    pulse = traveling_pulse()
    tcl0, ppi0, _ = E.entrainment(ring=100.0, d=0.0, offset=20.0, pulse=pulse)
    tcl2, ppi2, cv2 = E.entrainment(ring=100.0, d=20.0, offset=20.0, pulse=pulse)
    assert 0 <= ppi0 - tcl0 < 20
    assert abs((ppi2 - tcl2) - 2 * 20.0 / cv2) < 15
    assert E.ppi_outside(tcl2, 20.0, cv2) - tcl2 == pytest.approx(40.0 / cv2)
    _, ppi_fast, _ = E.entrainment(ring=100.0, d=0.0, offset=60.0, pulse=pulse)
    assert ppi_fast - tcl0 > ppi0 - tcl0 + 15
