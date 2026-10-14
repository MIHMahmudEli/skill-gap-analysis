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
NOT_YET_RUN: set[str] = {"SENS02_covering_set_sweep"}


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
    # 13 base = 12 USED_IN_MANUSCRIPT + 1 not-used; any not-yet-run entry is
    # counted separately so the registry cannot grow silently.
    assert len(statuses) == 13 + len(staged) + len(not_yet_run), statuses


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


# ---------------------------------------------------------------------------
# ALIGN06 section 6.3 regression guard.
#
# The first ALIGN06 execution shipped a category table whose coverage_rate
# reached 1.204964 with CI_rate_upper 10.232392 -- impossible values for a
# share.  Cause: cov_matrix() built its flat scatter index as
# `cat_id * n + occ_id` and then reshaped to (n, n_cats); a row-major reshape
# requires `occ_id * n_cats + cat_id`.  With n=891 and n_cats=8 every covered
# (occupation, category) count landed in the wrong cell while `den`, written by
# direct indexing, stayed correct, so cov_b / den_b could exceed 1.  Recorded
# as ALIGN06_PREREG.md section 11 block A7.
#
# Two guards: the algebraic invariant on the committed artifact (this is what
# actually caught the defect), and a source check that the index convention at
# the single vulnerable site cannot be silently reverted.
# ---------------------------------------------------------------------------

ALIGN06_CAT_CSV = (ROOT / "results" / "ALIGN06_onet_demand_profile"
                   / "table_category_gap_onet.csv")
ALIGN06_RUNNER = ROOT / "experiments" / "align06_demand_profile.py"


def test_align06_category_coverage_rate_is_a_share():
    """coverage_rate is a weighted share and cannot leave [0, 1]; it must also
    satisfy the section 6.3 identity deficit = demand * (1 - coverage_rate)."""
    if not ALIGN06_CAT_CSV.exists():
        pytest.skip("ALIGN06 category table absent")
    import pandas as pd

    c = pd.read_csv(ALIGN06_CAT_CSV)
    assert len(c) == 160, f"expected 160 category rows, got {len(c)}"
    for col in ["market_demand_pp", "coverage_rate", "deficit_pp",
                "CI_rate_lower", "CI_rate_upper",
                "CI_deficit_lower", "CI_deficit_upper"]:
        c[col] = pd.to_numeric(c[col], errors="coerce")

    # the defect this test exists for
    assert ((c.coverage_rate >= -1e-12) & (c.coverage_rate <= 1 + 1e-12)).all(), (
        "coverage_rate outside [0,1] -- cov_matrix flat-index regression (A7): "
        f"{c.loc[(c.coverage_rate > 1 + 1e-12) | (c.coverage_rate < -1e-12),
                 ['category', 'match', 'K', 'tau', 'coverage_rate']]}")
    assert (c.CI_rate_lower >= -1e-12).all(), "CI_rate_lower negative"
    assert (c.CI_rate_upper <= 1 + 1e-12).all(), (
        "CI_rate_upper above 1 -- cov_matrix flat-index regression (A7)")
    assert (c.CI_rate_lower <= c.CI_rate_upper + 1e-12).all(), "inverted rate CI"

    # demand share is a percentage point quantity
    assert ((c.market_demand_pp >= -1e-9) & (c.market_demand_pp <= 100 + 1e-9)).all()

    # section 6.3 identity: deficit_pp = market_demand_pp * (1 - coverage_rate),
    # which only holds if cov and den are indexed on the same (occ, cat) grid
    err = (c.deficit_pp - c.market_demand_pp * (1.0 - c.coverage_rate)).abs()
    assert err.max() < 5e-3, f"section 6.3 identity broken, max abs err {err.max()}"

    # bootstrap intervals remain coherent with the point estimate
    assert (c.CI_deficit_lower <= c.CI_deficit_upper + 1e-9).all()
    inside = ((c.deficit_pp >= c.CI_deficit_lower - 1e-4)
              & (c.deficit_pp <= c.CI_deficit_upper + 1e-4))
    assert inside.all(), f"{int((~inside).sum())} deficits outside their own CI"


def test_align06_cov_matrix_flat_index_is_row_major():
    """The (n, n_cats) scatter at cov_matrix must stay row-major. Reverting to
    cat_id * n + occ_id silently redistributes every count (see A7)."""
    if not ALIGN06_RUNNER.exists():
        pytest.skip("ALIGN06 runner absent")
    src = ALIGN06_RUNNER.read_text(encoding="utf-8")
    assert "occ_arr_a[m] * n_cats + cat_id_a[m]" in src, (
        "row-major flat index missing from cov_matrix; the (n, n_cats) scatter "
        "must be occ_id * n_cats + cat_id_id")
    assert "cat_id_a[m] * n + occ_arr_a[m]" not in src, (
        "transposed flat index (cat_id * n + occ_id) reappeared in cov_matrix; "
        "this is the ALIGN06_PREREG.md A7 defect")


def test_align06_generated_category_table_pins_tau_0_5():
    """tab_align06_categories must read the semantic column at tau=0.5.

    table_category_gap_onet.csv holds four tau values (0.4/0.5/0.6/0.7) for
    every semantic row, so an unfiltered read silently returns tau=0.4. At
    tau=0.4 Cloud & Infrastructure reaches 100.0% semantic coverage; the
    manuscript and Appendix A quote 92.1% at tau=0.5.
    """
    tab = ROOT / "paper" / "tables" / "tab_align06_categories.tex"
    if not tab.exists():
        pytest.skip("generated category table absent")
    body = tab.read_text(encoding="utf-8")
    lines = [l for l in body.splitlines() if "&" in l and not l.startswith("%")]

    def cells(line: str) -> list:
        """Split a generated row on the cell separator. esc() turns '&' inside
        a category name into '\\&', which would otherwise shift the split, and
        every row ends with the LaTeX newline marker."""
        parts = [p.strip() for p in line.replace("\\&", "\x00").split("&")]
        parts[-1] = parts[-1].rstrip("\\").strip()
        return parts

    # '&' inside a category name is escaped by esc(), so rows read
    # "Cloud \& Infrastructure", not "Cloud & Infrastructure"
    cloud = [l for l in lines if l.startswith("Cloud \\& Infrastructure")]
    assert len(cloud) == 1, f"Cloud row missing or duplicated: {cloud}"
    c = cells(cloud[0])
    # cells: category, postings demand, postings cov lex, postings cov sem,
    #         ONET demand, ONET cov lex, ONET cov sem
    assert len(c) == 7, c
    assert c[6] == "92.1", (
        f"O*NET Cloud semantic coverage reads {c[6]}, expected 92.1 at "
        "tau=0.5 -- an unfiltered read of table_category_gap_onet.csv returns "
        "tau=0.4 (100.0); pin the semantic filter to tau == 0.5")

    # the three categories the manuscript names as carrying no O*NET demand
    # weight must read exactly 0.00 on the O*NET demand column
    for cat in ("Soft Skills", "Business \\& Domain", "Cybersecurity"):
        row = [l for l in lines if l.startswith(cat)]
        assert len(row) == 1, f"{cat} row missing or duplicated"
        assert cells(row[0])[4] == "0.00", row[0]

    # O*NET demand is matcher-independent, so only the semantic column may vary
    # with tau; the demand column must not
    prog = [l for l in lines if l.startswith("Programming \\& Development")]
    assert len(prog) == 1, "Programming row missing or duplicated"
    assert cells(prog[0])[4] == "21.67", prog[0]
