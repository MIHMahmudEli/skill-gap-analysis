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

# Experiments that are registered and VERIFIED but not yet cited in the
# manuscript (their manuscript integration task is still pending), plus
# experiments deliberately excluded from the manuscript.
#
# The end-state invariant the test below enforces is "every registered
# experiment is either USED_IN_MANUSCRIPT, staged for integration, or
# explicitly marked not-used with a recorded reason"; while a revision adds
# new experiments, staged ones are allowed *only* in COMPLETED/VERIFIED
# state, and not-used ones *only* in VERIFIED state with a
# `manuscript_use_reason`, must exist in the registry, and are counted
# explicitly. Remove an ID from this list in the same commit that (a) cites
# the experiment in paper/main.tex and (b) flips its registry status to
# USED_IN_MANUSCRIPT.
#
# SENS01: staged for the Phase-2 revision (P2-3 abstract/sensitivity
# rewrite, `reports/Q1_REVISION_PLAN.md`); verified 2026-10-11.
PENDING_MANUSCRIPT_INTEGRATION = {"SENS01_sgi_sensitivity"}
# TRENDS01: excluded from the manuscript 2026-10-12 (author instruction):
# RQ1-trend claims, Fig. 6b and the "spanning 2020 through 2026" phrasing
# were removed because the corpus carries STRONG generator signatures (top
# evidence tier for an unverified-provenance file; datasets/REAL_VS_SYNTHETIC.csv).
# Registry entry and artifacts retained; reason
# recorded in results/registry.json under `manuscript_use_reason`.
NOT_USED_IN_MANUSCRIPT = {"TRENDS01_ai_longitudinal"}
# Experiments registered in advance of their first execution, per the
# "registered before execution" rule in their preregistration
# (ALIGN06_PREREG.md section 8). While an ID is listed here its registry
# status is REGISTERED (or RUNNING / COMPLETED once a run is under way) and
# its metrics.json may not exist yet. Remove an ID from this list in the same
# commit that finishes its run.
NOT_YET_RUN = {"ALIGN06_onet_demand_profile"}


def _load_registry():
    if not REGISTRY.exists():
        pytest.skip("results/registry.json absent")
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_registry_all_used_in_manuscript():
    reg = _load_registry()
    exps = reg["experiments"] if isinstance(reg, dict) and "experiments" in reg else reg
    if isinstance(exps, dict):
        ids = list(exps.keys())
        statuses = [v.get("status") for v in exps.values()]
    else:
        ids = [e["experiment_id"] for e in exps]
        statuses = [e.get("status") for e in exps]
    assert statuses, "empty registry"
    staged = PENDING_MANUSCRIPT_INTEGRATION
    not_used = NOT_USED_IN_MANUSCRIPT
    not_yet_run = NOT_YET_RUN
    unknown = (staged | not_used | not_yet_run) - set(ids)
    assert not unknown, f"staging list references missing experiments: {unknown}"
    for exp_id, status in zip(ids, statuses):
        if exp_id in staged:
            assert status in ("COMPLETED", "VERIFIED"), (
                f"{exp_id} is staged for integration but not verified: {status}")
        elif exp_id in not_used:
            assert status == "VERIFIED", (
                f"{exp_id} is marked not-used-in-manuscript but status is {status}")
            entry = (exps[exp_id] if isinstance(exps, dict)
                     else next(e for e in exps if e["experiment_id"] == exp_id))
            assert entry.get("manuscript_use") == "not_used_in_manuscript", exp_id
            assert entry.get("manuscript_use_reason"), (
                f"{exp_id} is marked not-used but carries no manuscript_use_reason")
        elif exp_id in not_yet_run:
            assert status in ("REGISTERED", "RUNNING", "COMPLETED", "VERIFIED"), (
                f"{exp_id} is registered but has an unexpected status: {status}")
        else:
            assert status == "USED_IN_MANUSCRIPT", (exp_id, status)
    assert len(statuses) == 12 + len(staged) + len(not_yet_run), statuses


def test_registry_metrics_files_exist_and_complete():
    reg = _load_registry()
    exps = reg["experiments"] if isinstance(reg, dict) and "experiments" in reg else reg
    items = exps.items() if isinstance(exps, dict) else [(e["experiment_id"], e) for e in exps]
    for exp_id, meta in items:
        d = ROOT / "results" / exp_id
        m = d / "metrics.json"
        if exp_id in NOT_YET_RUN and not m.exists():
            continue  # registered before execution (ALIGN06_PREREG.md §8)
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
    """verify_claims.py must exit 0; ledger must have ZERO contradicted claims
    (Phase 9 manuscript fixes are on this branch)."""
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
    vc = next(k for k in rows[0] if "verdict" in k.lower() or "status" in k.lower())
    from collections import Counter
    counts = Counter(r[vc] for r in rows)
    assert counts.get("contradicted", 0) == 0, f"contradicted claims remain: {counts}"
    assert counts.get("reproduced", 0) >= 90, counts


def test_input_checksums_file_lists_nine_bundles():
    csum = ROOT / "datasets" / "input_checksums.sha256"
    if not csum.exists():
        pytest.skip("checksums not generated")
    lines = [ln for ln in csum.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    assert len(lines) >= 9
    for ln in lines:
        parts = ln.split()
        assert len(parts) >= 2 and len(parts[0]) == 64
