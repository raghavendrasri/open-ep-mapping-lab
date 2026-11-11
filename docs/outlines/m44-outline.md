# m44 outline · Agentic AI in EP

Stage 1 (outline) for module m44, written together with stages 2–6 (author decision, 2026-11-11).
Plan source: `docs/outlines/part7-overview.md` (section "Agentic AI in EP").

## Scope

What an agent is (model, tools, memory, loop, policy), levels of autonomy, EP use cases with their
human checkpoints, how reliability compounds over a chain of steps and what checks and reviewers buy,
correlated errors, guardrails that run outside the model (schemas with units, allowlist and sandbox,
approval for writes, audit log, number tracing), prompt injection, and evaluating an agent on a task
suite. Out of scope: agents acting on clinical systems or devices, vendor products, level-4 autonomy.

## Learning goals

1. Name the parts of an agent and build a minimal one.
2. Place a use case on the autonomy scale and name its human checkpoint.
3. Derive how per-step reliability compounds over a chain, and what a check and a reviewer buy.
4. Explain why independence can fail and what that does to task success.
5. Defend an agent against prompt injection with a policy outside the model.
6. Evaluate an agent on a task suite and audit its traces.

## Equations (tests in `tests/test_m44_agent.py`)

| Label | Content | Check |
| --- | --- | --- |
| eq-m44-chain | P = ∏ p_i = p^n | Products; Monte Carlo; 20-task suite of the scripted agent |
| eq-m44-check | [p + (1−p) c p_r]^n | SymPy for p_r = 1; limits c = 0 and c = 1; Monte Carlo |
| eq-m44-escape | E = N(1 − P)(1 − r) | Numbers; r = 1 gives 0 |
| eq-m44-mixture | (1−h) p_e^n + h p_h^n ≥ p̄^n | Jensen inequality; Monte Carlo; no spread gives equality |

## Demos

| ID | Badge | Content |
| --- | --- | --- |
| m44-d1 | simulation | Trace of the scripted agent on a poisoned mapping case under all eight guardrail combinations (precomputed by `tools/make_m44_d1.py`, writes simulated) |
| m44-d2 | exact | Task success against steps with and without a check, and errors past a reviewer |

## Code lab (`labs/python/m44_lab.ipynb`)

A tool schemas; B one task end to end with approval and audit log; C prompt injection under eight
guardrail settings; D 20-task suite at p = 1.0, 0.9, 0.8 with and without a check, escaped errors,
correlated errors; E number tracing and a trace audit; F AFDB record 04015 (download): heart rate by
rhythm through a tool; G optional real model, skipped in CI.

## Sources

PubMed: jiang2025medagentbench and chen2026medagentbench (Stanford), zhao2026 (PMC full text for the
architecture, physician comparison and reference audit), feli2025, jamthikar2026 (preprint),
patel2025, khosravi2026, iwai2025, neiman2024, covino2024, antoun2025, meisenzahl2024, svennberg2025.
arXiv (alphaXiv): yao2023react, park2023generative and khattab2023dspy (Stanford),
schmidgall2024agentclinic (Stanford and Johns Hopkins), rebedea2023guardrails (NVIDIA). zakka2024 from
m43.

## Open points for the author

- Part F (AFDB) has not run locally (no PhysioNet access here); it was exercised with stand-in
  annotations.
- The scripted agent's faults (gullibility, unit slip, invented number, per-step error rate) are ours;
  the lab says so wherever their numbers appear.
- AgentClinic findings are described qualitatively from its paper; no figures quoted.
