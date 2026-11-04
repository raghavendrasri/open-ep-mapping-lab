"""m34 equation checks: data rate, buffering, queues, latency, filter delay and timing error.

Each test checks an equation in modules/m34-software-architecture.qmd by a route that does not use
the closed form it is checking (counting, simulation, SymPy or brute force).
"""

import numpy as np
import pytest
import sympy as sp
from scipy import signal

from epml import systems as sy


def test_data_rate_by_counting_bytes():
    """eq-m34-data-rate: R = N f_s b. Pack one second of a simulated stream and count the bits."""
    n_ch, fs, bits = 8, 500, 16
    stream = np.zeros((fs, n_ch), dtype=np.int16)  # one second of samples
    assert stream.nbytes * 8 == sy.data_rate_bps(n_ch, fs, bits)
    assert sy.data_rate_bps(n_ch, fs, bits, overhead=0.25) == pytest.approx(1.25 * n_ch * fs * bits)


@pytest.mark.parametrize("fs,t_stall", [(1000, 0.05), (2000, 0.2)])
def test_buffer_bound(fs, t_stall):
    """eq-m34-buffer: a buffer of R T samples rides out a stall of T seconds; one sample less drops one."""
    needed = int(round(sy.buffer_bits(fs, t_stall)))  # rate in samples/s gives a size in samples
    assert sy.stall_drops(fs, t_stall, needed) == 0
    assert sy.stall_drops(fs, t_stall, needed - 1) == 1


def test_littles_law_on_a_sample_path():
    """eq-m34-littles-law: for a system empty at the start and end of [0, T], L = lambda W exactly,
    with L the time average in system, lambda = arrivals / T and W the mean time in system."""
    rng = np.random.default_rng(3)
    arrivals = np.sort(rng.uniform(0, 50, 400))
    services = rng.gamma(2.0, 0.04, 400)  # not exponential: the law does not depend on it
    _, depart = sy.simulate_queue(arrivals, services)
    t1 = depart.max() + 1.0
    L = sy.time_average_in_system(arrivals, depart, 0.0, t1)
    lam = len(arrivals) / t1
    W = np.mean(depart - arrivals)
    assert L == pytest.approx(lam * W, rel=1e-9)


def test_mm1_mean_number_symbolic():
    """eq-m34-mm1-number: with p_n = (1 - rho) rho^n, the probabilities sum to 1 and the mean number in
    the system is rho / (1 - rho), for 0 < rho < 1."""
    rho = sp.symbols("rho", positive=True)
    n = sp.symbols("n", integer=True, nonnegative=True)

    def converged(expr):  # SymPy returns Piecewise((value, |rho| < 1), (Sum, True))
        value = sp.Sum(expr, (n, 0, sp.oo)).doit()
        return value.args[0][0] if isinstance(value, sp.Piecewise) else value

    total = (1 - rho) * converged(rho**n)  # keep the constant factor outside the sum
    mean = (1 - rho) * converged(n * rho**n)
    assert sp.simplify(total - 1) == 0
    assert sp.simplify(mean - rho / (1 - rho)) == 0


@pytest.mark.parametrize("rho", [0.3, 0.6, 0.85])
def test_mm1_mean_time_by_simulation(rho):
    """eq-m34-mm1: W = 1 / (mu - lambda). A long M/M/1 simulation agrees within a few percent."""
    rng = np.random.default_rng(int(rho * 100))
    mu = 100.0  # items per second
    lam = rho * mu
    arrivals, services = sy.poisson_queue(lam, mu, 400_000, rng)
    _, depart = sy.simulate_queue(arrivals, services)
    W = np.mean((depart - arrivals)[20_000:])  # drop the start-up transient
    assert W == pytest.approx(sy.mm1_mean_time(lam, mu), rel=0.06)
    assert sy.mm1_mean_number(lam, mu) == pytest.approx(lam * sy.mm1_mean_time(lam, mu))


def test_latency_grows_without_bound_near_full_load():
    """eq-m34-mm1: W(rho) / W(0) = 1 / (1 - rho), so doubling the load from 0.45 to 0.9 multiplies W by 5.5."""
    mu = 1.0
    assert sy.mm1_mean_time(0.9, mu) / sy.mm1_mean_time(0.45, mu) == pytest.approx(5.5)
    assert sy.mm1_mean_time(1.0, mu) == np.inf


def test_latency_budget_by_simulation():
    """eq-m34-latency-budget: a result ready at a random time waits for the next display refresh,
    on average half a frame and at most one frame, after the stage delays add up."""
    rng = np.random.default_rng(7)
    proc, queue, frame = [0.004, 0.010, 0.002], [0.001, 0.003, 0.0], 1 / 60
    mean, worst = sy.latency_budget(proc, queue, frame)
    ready = rng.uniform(0, 100, 200_000) + sum(proc) + sum(queue)  # ready time after the stages
    shown = np.ceil(ready / frame) * frame  # next refresh
    latency = shown - (ready - sum(proc) - sum(queue))
    assert latency.mean() == pytest.approx(mean, rel=2e-3)
    assert latency.max() <= worst + 1e-12


@pytest.mark.parametrize("n_taps,fs", [(31, 1000.0), (101, 2000.0)])
def test_fir_group_delay(n_taps, fs):
    """eq-m34-fir-delay: a symmetric FIR filter delays a pulse by (M - 1) / (2 f_s)."""
    taps = signal.firwin(n_taps, 0.2)  # linear-phase low-pass
    t = np.arange(4000) / fs
    t0 = 1.0
    pulse = np.exp(-0.5 * ((t - t0) / 0.01) ** 2)
    out = np.convolve(pulse, taps)[: len(t)]
    delay = t[np.argmax(out)] - t0
    assert delay == pytest.approx(sy.fir_group_delay(n_taps, fs), abs=1 / fs)


def test_misregistration_from_timing_offset():
    """eq-m34-misregistration: reading the position dt late, for a catheter at speed v, puts the point
    v dt away along its path."""
    v, dt = 20.0, 0.015  # test inputs: mm/s and s
    t = np.linspace(0, 1, 1001)
    x = v * t
    shifted = np.interp(t - dt, t, x)
    assert np.max(np.abs((x - shifted)[t > dt])) == pytest.approx(sy.misregistration(v, dt))


@pytest.mark.parametrize("h", [0.01, 0.02, 0.05])
def test_interpolation_error_bound(h):
    """eq-m34-interp-error: linear interpolation of x(t) = A sin(w t) sampled every h stays within
    h^2/8 max|x''| = h^2 A w^2 / 8, and approaches it."""
    A, w = 5.0, 2 * np.pi * 1.5  # test inputs
    ts = np.arange(0, 2, h)
    fine = np.linspace(0, ts[-1], 200_001)
    err = np.max(np.abs(np.interp(fine, ts, A * np.sin(w * ts)) - A * np.sin(w * fine)))
    bound = sy.linear_interp_error_bound(h, A * w**2)
    assert err <= bound * (1 + 1e-9)
    assert err > 0.8 * bound


def test_steep_rise_with_other_service_times():
    """Text claim under eq-m34-mm1: with non-exponential service times (gamma, shape 4) delay still
    rises steeply near full load: mean time in system at 90% load is several times that at 45%."""
    rng = np.random.default_rng(11)
    mu = 100.0
    W = {}
    for rho in (0.45, 0.9):
        arrivals = np.cumsum(rng.exponential(1 / (rho * mu), 300_000))
        services = rng.gamma(4.0, 1 / (4.0 * mu), 300_000)  # mean 1/mu, less variable than exponential
        _, depart = sy.simulate_queue(arrivals, services)
        W[rho] = np.mean((depart - arrivals)[20_000:])
    assert W[0.9] / W[0.45] > 3
