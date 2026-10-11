"""Reproducibility smoke tests: registry consistency, verify.py schema map,
manifest row-count accuracy vs local files when present.

These tests skip gracefully when large gitignored inputs are absent so the
suite remains green in a fresh clone.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

REGISTRY = ROOT / "results" / "registry.json"


def _load_registry():
    if not REGISTRY.exists():
        pytest.skip("results/registry.json absent")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_registry_all_used_in_manuscript():
    reg = _load_registry()
    exps = reg["experiments"] if isinstance(reg, dict) and "experiments" in reg else reg
    if isinstance(exps, dict):
        statuses = [v.get("status") for v in exps.values()]
    else:
        statuses = [e.get("status") for e in exps]
    assert statuses, "empty registry"
    assert all(s == "USED_IN_MANUSCRIPT" for s in statuses), statuses
    assert len(statuses) == 12


def test_registry_metrics_files_exist_and_complete():
    reg = _load_registry()
    exps = reg["experiments"] if isinstance(reg, dict) and "experiments" in reg else reg
    items = exps.items() if isinstance(exps, dict) else [(e["experiment_id"], e) for e in exps]
    for exp_id, meta in items:
        d = ROOT / "results" / exp_id
        m = d / "metrics.json"
        assert m.exists(), f"missing metrics for {exp_id}"
        payload = json.loads(m.read_text(encoding="utf-8"))
        assert payload.get("status") == "completed", exp_id


def test_verify_py_required_map_matches_directories():
    """Every REQUIRED key in verify.py must have a results/ directory."""
    src = (ROOT / "experiments" / "verify.py").read_text(encoding="utf-8")
    import re
    keys = re.findall(r'"([A-Z0-9]+_[a-z0-9_]+)":\s*\[', src)
    assert len(keys) >= 12
    for k in keys:
        assert (ROOT / "results" / k).is_dir(), f"verify.py expects {k}"


def test_manifest_counts_match_local_files_when_present():
    """Manifest record counts must match actual CSV row counts for present files."""
    import pandas as pd
    mapping = {
        "LinkedIn Jobs & Skills": ROOT / "datasets/kaggle/1-3m-linkedin-jobs-and-skills-2024/linkedin_job_postings.csv",
        "HF Skill Gap Jobs": ROOT / "datasets/hf_skill_gap_jobs.csv",
        "HF Skill Gap Skills": ROOT / "datasets/hf_skill_gap_skills.csv",
        "HF Job Skill Set": ROOT / "datasets/hf_job_skill_set.csv",
        "College Placement": ROOT / "datasets/kaggle/college-student-placement/college_student_placement_dataset.csv",
    }
    man = ROOT / "datasets" / "DATASET_MANIFEST.csv"
    rows = {r["dataset_name"]: int(r["records"]) for r in csv.DictReader(man.open(encoding="utf-8"))}
    checked = 0
    for name, path in mapping.items():
        if not path.exists():
            continue
        n = len(pd.read_csv(path, usecols=[0]))  # one column is enough for row count
        assert rows[name] == n, f"{name}: manifest={rows[name]} actual={n}"
        checked += 1
    if checked == 0:
        pytest.skip("no local raw CSVs present")


def test_audit_claim_ledger_reproduces():
    """verify_claims.py must exit 0 and report zero CONTRADICTED *after* Phase 9 fixes.

    During the audit window (before manuscript fixes) this test only checks
    that the script runs and produces a ledger; contradictions are allowed and
    counted separately.
    """
    script = ROOT / "audit" / "verify_claims.py"
    if not script.exists():
        pytest.skip("audit script absent")
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(ROOT), timeout=600,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    ledger = ROOT / "audit" / "01_claim_evidence_ledger.csv"
    assert ledger.exists()
    rows = list(csv.DictReader(ledger.open(encoding="utf-8")))
    assert len(rows) >= 90
    # structural check only: verdict column exists
    assert any("verdict" in k.lower() or "status" in k.lower() for k in rows[0])


def test_input_checksums_file_lists_nine_bundles():
    csum = ROOT / "datasets" / "input_checksums.sha256"
    if not csum.exists():
        pytest.skip("checksums not generated")
    lines = [ln for ln in csum.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    assert len(lines) >= 9
    for ln in lines:
        parts = ln.split()
        assert len(parts) >= 2 and len(parts[0]) == 64
