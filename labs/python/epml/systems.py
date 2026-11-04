"""Pipeline models for module m34 (mapping-system software architecture).

Units: time in seconds, rates in items per second or bits per second, distance in mm unless stated.
Every function here is checked by tests/test_m34_*.py against an independent route (SymPy,
simulation or brute force). See modules/m34-software-architecture.qmd, Derivations.
"""

import math
from collections import deque

import numpy as np

# ---------------------------------------------------------------- data rate and buffering


def data_rate_bps(n_channels, fs, bits, overhead=0.0):
    """Raw data rate R = N f_s b, times (1 + overhead) for framing. Bits per second."""
    return n_channels * fs * bits * (1.0 + overhead)


def buffer_bits(rate_bps, t_stall):
    """Smallest buffer that rides out a consumer stall of t_stall seconds: B = R T."""
    return rate_bps * t_stall


class RingBuffer:
    """Fixed-capacity FIFO. When full, a push is dropped and counted (no overwrite)."""

    def __init__(self, capacity):
        self.capacity = int(capacity)
        self.items = deque()
        self.dropped = 0

    def push(self, item):
        if len(self.items) >= self.capacity:
            self.dropped += 1
            return False
        self.items.append(item)
        return True

    def pop(self):
        return self.items.popleft() if self.items else None

    def __len__(self):
        return len(self.items)


def stall_drops(fs, t_stall, capacity):
    """Samples lost when a producer at fs samples/s keeps writing into a RingBuffer of
    `capacity` samples while the consumer is stalled for t_stall seconds (buffer empty at start)."""
    buf = RingBuffer(capacity)
    for k in range(int(round(fs * t_stall))):
        buf.push(k)
    return buf.dropped


# ---------------------------------------------------------------- queues


def simulate_queue(arrivals, services):
    """Single server, first in first out. arrivals: sorted arrival times; services: service times.

    Returns (start, depart) arrays. Each item waits for the server to be free.
    """
    arrivals = np.asarray(arrivals, dtype=float)
    services = np.asarray(services, dtype=float)
    start = np.empty_like(arrivals)
    depart = np.empty_like(arrivals)
    free_at = -np.inf
    for i, (a, s) in enumerate(zip(arrivals, services)):
        start[i] = max(a, free_at)
        depart[i] = start[i] + s
        free_at = depart[i]
    return start, depart


def time_average_in_system(arrivals, depart, t0, t1):
    """Time-average number of items in the system over [t0, t1], from the step function N(t)."""
    events = np.concatenate([np.c_[arrivals, np.ones_like(arrivals)], np.c_[depart, -np.ones_like(depart)]])
    events = events[np.argsort(events[:, 0], kind="stable")]
    area, n, t_prev = 0.0, 0, t0
    for t, step in events:
        t_clip = min(max(t, t0), t1)
        area += n * (t_clip - t_prev)
        t_prev = t_clip
        n += int(step)
    area += n * (t1 - t_prev)
    return area / (t1 - t0)


def mm1_mean_number(lam, mu):
    """Mean number in an M/M/1 system: L = rho / (1 - rho), rho = lam / mu < 1."""
    rho = lam / mu
    if rho >= 1:
        return math.inf
    return rho / (1.0 - rho)


def mm1_mean_time(lam, mu):
    """Mean time in an M/M/1 system: W = 1 / (mu - lam) for lam < mu."""
    return math.inf if lam >= mu else 1.0 / (mu - lam)


def poisson_queue(lam, mu, n_items, rng):
    """Arrival and service times for an M/M/1 queue: exponential gaps (rate lam) and services (rate mu)."""
    arrivals = np.cumsum(rng.exponential(1.0 / lam, n_items))
    services = rng.exponential(1.0 / mu, n_items)
    return arrivals, services


# ---------------------------------------------------------------- latency budget


def latency_budget(processing, queueing, frame_period):
    """End-to-end latency of a chain of stages shown on a display refreshed every frame_period.

    Returns (mean, worst): the stage delays add; a result then waits for the next refresh,
    on average half a frame (uniform phase) and at most a full frame.
    """
    base = float(np.sum(processing) + np.sum(queueing))
    return base + 0.5 * frame_period, base + frame_period


# ---------------------------------------------------------------- filters and timing


def fir_group_delay(n_taps, fs):
    """Group delay of a linear-phase (symmetric) FIR filter with n_taps taps: (M - 1) / (2 f_s)."""
    return (n_taps - 1) / (2.0 * fs)


def misregistration(speed, dt):
    """Distance a catheter moving at `speed` covers during a timing error dt: |dx| = v |dt|."""
    return abs(speed) * abs(dt)


def linear_interp_error_bound(h, max_second_derivative):
    """Bound on linear-interpolation error between samples h apart: h^2/8 * max|x''|."""
    return h**2 / 8.0 * max_second_derivative
