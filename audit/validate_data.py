#!/usr/bin/env python3
"""Phase 2: data provenance & quality validation (read-only).

Counts rows, checks schemas, duplicates, and cross-file linkage for every
locally available dataset. Writes audit/02_data_quality.csv and a JSON summary.
Does not modify raw data.
"""
from __future__ import annotations

import csv
import json
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KAG = ROOT / "datasets" / "kaggle"
OUT_JSON = ROOT / "audit" / "02_data_quality_summary.json"
OUT_CSV = ROOT / "audit" / "02_data_quality.csv"

manifest = list(csv.DictReader((ROOT / "datasets" / "DATASET_MANIFEST.csv").open(encoding="utf-8")))


def sha256_head(p: Path, n: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        h.update(f.read(n))
    return h.hexdigest()[:16]


def count_rows(p: Path) -> int:
    # cheap line count minus header (CSVs here have no embedded newlines in quotes for counts;
    # for huge files this is fast; verified against pandas for small files)
    with p.open("rb") as f:
        n = sum(1 for _ in f)
    return max(n - 1, 0)


rows_out = []
files = []

# local hf_* files
for p in sorted((ROOT / "datasets").glob("hf_*.csv")):
    files.append(p)
# kaggle tree
for p in sorted(KAG.rglob("*.csv")):
    files.append(p)

print(f"scanning {len(files)} csv files...")
for p in files:
    rel = str(p.relative_to(ROOT))
    mb = round(p.stat().st_size / 1e6, 2)
    try:
        if p.stat().st_size > 500_000_000:
            # huge: count lines + header only
            n = count_rows(p)
            cols = "SKIPPED_SCHEMA"
            dups = "NA"
            miss = "NA"
            note = "line-count only (>500MB)"
        else:
            df = pd.read_csv(p, low_memory=False)
            n = len(df)
            cols = ";".join(map(str, df.columns[:12])) + ("..." if df.shape[1] > 12 else "")
            # duplicate full rows (sample-safe: use hash of all cols)
            if n <= 2_000_000:
                dups = int(df.duplicated().sum())
            else:
                dups = "NA"
            miss = round(float(df.isna().mean().mean()) * 100, 2)
            note = ""
        rows_out.append({
            "path": rel, "size_mb": mb, "n_rows": n,
            "columns": cols, "dup_rows": dups, "mean_missing_pct": miss,
            "sha256_1mb_head": sha256_head(p), "note": note,
        })
        print(f"  {rel}: {n} rows")
    except Exception as e:  # noqa: BLE001
        rows_out.append({"path": rel, "size_mb": mb, "n_rows": "ERROR",
                         "columns": "", "dup_rows": "", "mean_missing_pct": "",
                         "sha256_1mb_head": "", "note": str(e)[:200]})
        print(f"  {rel}: ERROR {e}")

# --- targeted checks ---
summary = {"manifest_rows": len(manifest), "manifest_total": sum(int(r["records"]) for r in manifest)}

# 1. HF jobs vs skills linkage
jobs_p = ROOT / "datasets" / "hf_skill_gap_jobs.csv"
skills_p = ROOT / "datasets" / "hf_skill_gap_skills.csv"
if jobs_p.exists() and skills_p.exists():
    jcols = pd.read_csv(jobs_p, nrows=5).columns.tolist()
    scols = pd.read_csv(skills_p, nrows=5).columns.tolist()
    summary["hf_jobs_cols"] = jcols
    summary["hf_skills_cols"] = scols
    # overlap on job id if present
    idj = next((c for c in jcols if "job" in c.lower() and ("id" in c.lower() or c.lower().endswith("_id"))), None)
    ids = next((c for c in scols if "job" in c.lower() and ("id" in c.lower() or c.lower().endswith("_id"))), None)
    if idj and ids:
        jids = pd.read_csv(jobs_p, usecols=[idj])[idj].nunique()
        sids = pd.read_csv(skills_p, usecols=[ids])[ids].nunique()
        summary["hf_jobs_unique_ids"] = int(jids)
        summary["hf_skills_unique_ids"] = int(sids)
        print(f"HF linkage: jobs unique {idj}={jids}, skills unique {ids}={sids}")

# 2. LinkedIn postings vs job_skills
lp = KAG / "1-3m-linkedin-jobs-and-skills-2024" / "linkedin_job_postings.csv"
js = KAG / "1-3m-linkedin-jobs-and-skills-2024" / "job_skills.csv"
if lp.exists():
    # header + exact count via pandas only if feasible size; 396MB ok
    ldf = pd.read_csv(lp, usecols=lambda c: True, low_memory=False, nrows=None) if lp.stat().st_size < 800_000_000 else None
    if ldf is not None:
        summary["linkedin_postings_rows"] = int(len(ldf))
        summary["linkedin_postings_cols"] = ldf.columns.tolist()
        # link col
        lcol = "original_listed_time" if "original_listed_time" in ldf.columns else None
        print("linkedin rows", len(ldf))
        del ldf
if js.exists():
    # count only
    summary["linkedin_job_skills_rows"] = count_rows(js)
    print("job_skills rows", summary["linkedin_job_skills_rows"])

# 3. College placement schema sanity (used by STAT01)
cp = KAG / "college-student-placement" / "college_student_placement_dataset.csv"
if cp.exists():
    df = pd.read_csv(cp)
    summary["college_n"] = int(len(df))
    summary["college_placement_values"] = df["Placement"].value_counts(dropna=False).to_dict()
    summary["college_internship_values"] = df["Internship_Experience"].value_counts(dropna=False).to_dict()
    summary["college_dup_ids"] = int(df["College_ID"].duplicated().sum())

OUT_JSON.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["path", "size_mb", "n_rows", "columns",
                                      "dup_rows", "mean_missing_pct", "sha256_1mb_head", "note"])
    w.writeheader()
    w.writerows(rows_out)
print("wrote", OUT_CSV, "and", OUT_JSON)
print(json.dumps({k: v for k, v in summary.items() if k not in ("hf_jobs_cols", "hf_skills_cols",
                                                                 "linkedin_postings_cols")},
                 indent=2, default=str))
