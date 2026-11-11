"""m44 tests: error compounding (eq-m44-chain, eq-m44-check, eq-m44-escape, eq-m44-mixture), tool
schemas, the guardrails of the agent loop, prompt-injection blocking, and the evaluation suite."""

import json

import numpy as np
import pytest
import sympy as sp

from epml import agent as ag


def test_chain_is_a_product_and_matches_simulation():
    """eq-m44-chain: independent steps multiply; a Monte Carlo run agrees."""
    assert ag.chain_success(0.9, 3) == pytest.approx(0.729)
    assert ag.chain_success([0.9, 0.8, 1.0]) == pytest.approx(0.72)
    rng = np.random.default_rng(0)
    sim = ag.simulate_chains(np.full(200_000, 0.95), 10, rng)
    assert sim == pytest.approx(0.95**10, abs=0.005)


def test_check_formula_symbolic_and_limits():
    """eq-m44-check: p + (1 - p) c p_r; with p_r = 1 it equals 1 - (1 - p)(1 - c) (SymPy); c = 0
    gives eq-m44-chain; c = 1 and p_r = 1 make every step succeed."""
    p, c = sp.symbols("p c", positive=True)
    assert sp.simplify(p + (1 - p) * c - (1 - (1 - p) * (1 - c))) == 0
    assert ag.checked_chain(0.9, 0.0, 5) == pytest.approx(ag.chain_success(0.9, 5))
    assert ag.checked_chain(0.9, 1.0, 5) == pytest.approx(1.0)
    assert ag.checked_step(0.9, 0.8, p_retry=0.9) == pytest.approx(0.9 + 0.1 * 0.8 * 0.9)
    rng = np.random.default_rng(1)
    first = rng.random(400_000) < 0.9
    caught = rng.random(400_000) < 0.8
    retry = rng.random(400_000) < 0.9
    assert np.mean(first | (caught & retry)) == pytest.approx(ag.checked_step(0.9, 0.8, 0.9), abs=0.003)


def test_escape_formula():
    """eq-m44-escape: N (1 - P) (1 - r)."""
    assert ag.escaped_errors(100, 0.9, 0.5) == pytest.approx(5.0)
    assert ag.escaped_errors(100, 0.9, 1.0) == 0.0


def test_correlated_errors_beat_the_independent_formula():
    """eq-m44-mixture: with the same mean step success, errors concentrated in hard tasks give a
    higher task success than eq-m44-chain predicts (Jensen's inequality); simulation agrees."""
    pe, ph, h, n = 0.99, 0.7, 0.2, 8
    pbar = (1 - h) * pe + h * ph
    mix = ag.mixture_chain(pe, ph, h, n)
    assert mix > ag.chain_success(pbar, n)
    rng = np.random.default_rng(2)
    p_rows = np.where(rng.random(200_000) < h, ph, pe)
    assert ag.simulate_chains(p_rows, n, rng) == pytest.approx(mix, abs=0.005)
    assert ag.mixture_chain(0.9, 0.9, 0.3, 5) == pytest.approx(0.9**5)   # no spread: no difference


@pytest.fixture()
def setup(tmp_path):
    cases = {i: ag.make_case(i, poisoned=(i == 3)) for i in range(6)}
    tools = ag.case_tools(cases, tmp_path)
    return cases, tools, tmp_path


def test_schema_rejects_wrong_units_ranges_and_names(setup):
    _, tools, _ = setup
    cv = {t.name: t for t in tools}["conduction_velocity"]
    good = {"case_id": 0, "radius": {"value": 10.0, "unit": "mm"}, "exclude_outliers": True}
    assert cv.validate(good)["radius"] == 10.0
    for bad, msg in [
        ({**good, "radius": {"value": 0.01, "unit": "m"}}, "in mm"),
        ({**good, "radius": {"value": 50.0, "unit": "mm"}}, "outside"),
        ({**good, "exclude_outliers": "yes"}, "true or false"),
        ({**good, "colour": "red"}, "unknown argument"),
    ]:
        with pytest.raises(ag.SchemaError, match=msg):
            cv.validate(bad)


def test_tools_find_the_planted_outliers_and_a_plausible_speed(setup):
    cases, _, _ = setup
    for c in cases.values():
        found = set(ag.outlier_indices(c, 5.0).tolist())
        assert set(c["outliers"].tolist()) <= found
        g = ag.gold_answer(c)
        assert abs(g["median_speed_m_s"] - c["speed_m_s"]) / c["speed_m_s"] < 0.15


def approve_reports(call):
    return str(call["args"].get("path", "")).startswith("qc/case_")


def test_guardrails_block_the_injection_and_log_every_step(setup, tmp_path):
    cases, tools, sandbox = setup
    log = ag.AuditLog(tmp_path / "audit.jsonl")
    model = ag.ScriptedAgentModel(gullible=True, unit_slip=1.0, seed=0)
    run = ag.run_agent(ag.qc_task(3), model, tools, ag.Policy(), approve_reports, sandbox, log=log)
    decisions = {(s.get("tool"), s.get("decision")) for s in run["steps"]}
    assert ("delete_files", "blocked: not on the allowlist") in decisions
    assert ("write_report", "blocked: outside the sandbox") in decisions
    assert ("conduction_velocity", "rejected: schema") in decisions
    assert ag.score_run(run, ag.gold_answer(cases[3]))
    assert (sandbox / "qc" / "case_3.md").exists()
    assert not (sandbox.parent / "review_record.json").exists()
    rows = [json.loads(line) for line in (tmp_path / "audit.jsonl").read_text().splitlines()]
    assert len(rows) == len(run["steps"]) and rows[-1]["kind"] == "final"


def test_writes_without_approval_are_never_executed(setup):
    cases, tools, sandbox = setup
    off = ag.Policy(schema_checks=False, allowlist=False, approval_for_writes=False)
    model = ag.ScriptedAgentModel(gullible=True, unit_slip=1.0, seed=0)
    run = ag.run_agent(ag.qc_task(3), model, tools, off, approve_reports, sandbox)
    writes = [s for s in run["steps"] if s.get("tool") in ("write_report", "delete_files")]
    assert writes and all("simulated" in s["decision"] for s in writes)
    assert not any(sandbox.rglob("*.md"))
    assert not ag.score_run(run, ag.gold_answer(cases[3]))      # the unit slip went through


def test_invented_numbers_are_flagged(setup):
    cases, tools, sandbox = setup
    run = ag.run_agent(ag.qc_task(0), ag.ScriptedAgentModel(invent=True), tools, ag.Policy(),
                       approve_reports, sandbox)
    assert run["untraceable"] == [23.7]
    assert not ag.score_run(run, ag.gold_answer(cases[0]))


def test_suite_success_matches_eq_m44_chain(tmp_path):
    """Lab part D in small: 20 tasks x 6 repeats with p = 0.85 per compute step (3 steps)."""
    cases = {i: ag.make_case(i) for i in range(21)}
    tools = ag.case_tools(cases, tmp_path)
    gold = {i: ag.gold_answer(cases[i]) for i in range(20)}
    ok = []
    for rep in range(6):
        model = ag.ScriptedAgentModel(p_step=0.85, seed=rep)
        for cid in range(20):
            run = ag.run_agent(ag.qc_task(cid), model, tools, ag.Policy(), approve_reports, tmp_path)
            ok.append(ag.score_run(run, gold[cid]))
    assert np.mean(ok) == pytest.approx(ag.chain_success(0.85, 3), abs=0.12)
