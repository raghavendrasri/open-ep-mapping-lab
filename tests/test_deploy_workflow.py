"""Checks on the GitHub Pages deploy workflow."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "deploy-pages.yml"


def _deploy_job():
    data = yaml.safe_load(WORKFLOW.read_text())
    return data["jobs"]["deploy"]


def test_deploy_only_after_ci_passes():
    cond = " ".join(_deploy_job()["if"].split())
    assert "github.event.workflow_run.conclusion == 'success'" in cond


def test_deploy_skips_ci_runs_for_older_commits():
    # A late CI run for an older commit must not overwrite a newer deploy (2026-11-17 incident).
    cond = " ".join(_deploy_job()["if"].split())
    assert re.search(r"github\.event\.workflow_run\.head_sha\s*==\s*github\.sha", cond), cond


def test_deploy_checks_out_the_commit_ci_checked():
    checkout = next(s for s in _deploy_job()["steps"] if str(s.get("uses", "")).startswith("actions/checkout"))
    assert "github.event.workflow_run.head_sha" in checkout["with"]["ref"]
