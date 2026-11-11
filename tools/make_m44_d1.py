"""Precompute demo m44-d1 (agent trace explorer) with the course's tested agent in epml.agent.

Run from the repository root:  python tools/make_m44_d1.py
Writes demos/m44-d1-data.json: one recorded run of the scripted stand-in agent on a synthetic
mapping-QC case whose note carries a prompt injection, for each of the eight combinations of three
guardrails. Writes are simulated (dry run): nothing is written or deleted.
tests/test_m44_demos.py regenerates the data and compares.
"""

import itertools
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "labs" / "python"))

from epml import agent as ag  # noqa: E402

CASE = 3


def short(x, n=110):
    s = json.dumps(x, default=str) if not isinstance(x, str) else x
    return s if len(s) <= n else s[: n - 1] + "…"


def compute():
    cases = {CASE: ag.make_case(CASE, poisoned=True)}
    gold = ag.gold_answer(cases[CASE])
    out = {"case": CASE, "gold": gold, "runs": {}}
    with tempfile.TemporaryDirectory() as sandbox:
        tools = ag.case_tools(cases, sandbox)
        for schema, allow, approval in itertools.product([True, False], repeat=3):
            model = ag.ScriptedAgentModel(gullible=True, unit_slip=1.0, invent=True, seed=0)
            policy = ag.Policy(schema_checks=schema, allowlist=allow, approval_for_writes=approval)
            run = ag.run_agent(ag.qc_task(CASE), model, tools, policy,
                               lambda call: str(call["args"].get("path", "")).startswith("qc/case_"),
                               sandbox, dry_run=True)
            steps = []
            for s in run["steps"]:
                if s["kind"] == "final":
                    steps.append({"tool": "final answer", "tier": "-", "decision": "returned",
                                  "args": "", "result": short(s["text"], 160)})
                else:
                    steps.append({"tool": s["tool"], "tier": s["tier"], "decision": s["decision"],
                                  "args": short(s["args"]), "result": short(s["result"])})
            key = f"{int(schema)}{int(allow)}{int(approval)}"
            out["runs"][key] = {
                "steps": steps,
                "untraceable": run["untraceable"],
                "deleteRan": any(s.get("tool") == "delete_files" and "executed" in s["decision"] for s in steps),
                "outsideWrite": any(s.get("tool") == "write_report" and "review_record" in s["args"]
                                    and "blocked" not in s["decision"] and "denied" not in s["decision"] for s in steps),
                "unitSlipPassed": any(s.get("tool") == "conduction_velocity" and '"m"' in s["args"]
                                      and s["decision"] == "executed" for s in steps),
            }
    return out


if __name__ == "__main__":
    data = compute()
    path = ROOT / "demos" / "m44-d1-data.json"
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(path, path.stat().st_size, "bytes")
    for k, r in data["runs"].items():
        print(k, len(r["steps"]), r["deleteRan"], r["outsideWrite"], r["unitSlipPassed"], r["untraceable"])
