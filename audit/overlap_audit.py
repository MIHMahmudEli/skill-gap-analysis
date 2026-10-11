"""Q1 provenance audit (Step 1a): pairwise overlap across ALL posting-type datasets.

Keys
----
- job_link       : datasets that carry a LinkedIn job_link identifier.
- composite      : normalized title+company+date+location where no link exists.
- title          : normalized title only (aggregate tables without company/date).
- full-row       : exact duplicate rows within/between same-schema files.

Outputs datasets/OVERLAP_AUDIT.csv and prints a markdown-ready summary.
Re-run: python audit/overlap_audit.py
"""
from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "datasets" / "OVERLAP_AUDIT.csv"

LINK_FILES = {
    "linkedin_job_postings": ROOT / "datasets/kaggle/1-3m-linkedin-jobs-and-skills-2024/linkedin_job_postings.csv",
    "linkedin_job_skills": ROOT / "datasets/kaggle/1-3m-linkedin-jobs-and-skills-2024/job_skills.csv",
    "hf_jobs": ROOT / "datasets/hf_skill_gap_jobs.csv",
    "hf_skills": ROOT / "datasets/hf_skill_gap_skills.csv",
    "ds_job_postings": ROOT / "datasets/kaggle/data-science-job-postings-and-skills/job_postings.csv",
}

AI_FILES = {
    "ai_job_dataset": ROOT / "datasets/kaggle/global-ai-job-market-and-salary-trends-2025/ai_job_dataset.csv",
    "ai_job_dataset1": ROOT / "datasets/kaggle/global-ai-job-market-and-salary-trends-2025/ai_job_dataset1.csv",
    "ai_ds_2020_2026": ROOT / "datasets/kaggle/ai-and-data-science-job-market-dataset-20202026/AI Job Market Dataset.csv",
}

STUDENT_FILES = {
    "college_placement": ROOT / "datasets/kaggle/college-student-placement/college_student_placement_dataset.csv",
    "global_placement": ROOT / "datasets/kaggle/global-student-placement-2025-dataset/global_placement.csv",
    "intl_graduates": ROOT / "datasets/kaggle/international-graduates-employment-dataset/dataset.csv",
    "ngess": ROOT / "datasets/kaggle/ngess-graduate-employment-dataset/NGESS Graduate Employment Dataset.csv",
    "student_career_success": ROOT / "datasets/kaggle/student-career-success-prediction-dataset/student_career_success_dataset.csv",
    "career_change": ROOT / "datasets/kaggle/field-of-study-vs-occupation/career_change_prediction_dataset.csv",
    "fresher_india": ROOT / "datasets/kaggle/indian-fresher-job-market-who-gets-hired-and-why/fresher_hiring_india_dataset.csv",
    "india_skills_profiles": ROOT / "datasets/kaggle/india-professional-skills-intelligence-dataset/india_professional_skills_intelligence.csv",
}

USA_FILE = ROOT / "datasets/kaggle/usa-job-market-skills-and-title-analysis/usa_job_posting_dataset.csv"

rows: list[dict] = []


def add(**kw) -> None:
    rows.append(kw)


def norm(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)


# ---------------------------------------------------------------- job_link group
links: dict[str, set[str]] = {}
for name, path in LINK_FILES.items():
    s = pd.read_csv(path, usecols=["job_link"], dtype=str)["job_link"].dropna()
    uniq = set(s)
    links[name] = uniq
    add(
        dataset_a=name, dataset_b="", key_type="job_link", scope="within",
        n_a=len(s), n_b="", n_overlap=len(s) - len(uniq), pct_of_a=round(100 * (len(s) - len(uniq)) / len(s), 3),
        pct_of_b="", note="within-file duplicate job_link rows (n_overlap = dup rows)",
    )

for a, b in itertools.combinations(links, 2):
    sa, sb = links[a], links[b]
    inter = len(sa & sb)
    add(
        dataset_a=a, dataset_b=b, key_type="job_link", scope="pairwise",
        n_a=len(sa), n_b=len(sb), n_overlap=inter,
        pct_of_a=round(100 * inter / len(sa), 3) if sa else "",
        pct_of_b=round(100 * inter / len(sb), 3) if sb else "",
        note="A subset of B" if inter == len(sa) and len(sa) < len(sb)
        else ("B subset of A" if inter == len(sb) and len(sb) < len(sa)
        else ("identical" if inter == len(sa) == len(sb) else "partial")),
    )

# ------------------------------------------------------- AI job datasets (composite)
ai_frames = {n: pd.read_csv(p, dtype=str, low_memory=False) for n, p in AI_FILES.items()}


def ai_key(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in ["job_title", "company_name", "posting_date", "location"] if c in df.columns]
    return norm(df[cols].fillna("").agg("|".join, axis=1)) if cols else norm(df.iloc[:, 0])


ai_keys = {n: set(ai_key(df)) for n, df in ai_frames.items()}
for n, df in ai_frames.items():
    k = set(ai_key(df))
    add(dataset_a=n, dataset_b="", key_type="composite", scope="within",
        n_a=len(df), n_b="", n_overlap=len(df) - len(k), pct_of_a=round(100 * (len(df) - len(k)) / len(df), 3),
        pct_of_b="", note=f"within-file duplicate composite keys; cols={list(df.columns)}")

for a, b in itertools.combinations(ai_keys, 2):
    sa, sb = ai_keys[a], ai_keys[b]
    inter = len(sa & sb)
    add(dataset_a=a, dataset_b=b, key_type="composite", scope="pairwise",
        n_a=len(sa), n_b=len(sb), n_overlap=inter,
        pct_of_a=round(100 * inter / len(sa), 3), pct_of_b=round(100 * inter / len(sb), 3),
        note="identical" if inter == len(sa) == len(sb) else ("A subset of B" if inter == len(sa) else ("B subset of A" if inter == len(sb) else "partial")))

# full-row equality for the two ai_job_dataset* files (shared columns)
d1, d2 = ai_frames["ai_job_dataset"], ai_frames["ai_job_dataset1"]
shared = [c for c in d1.columns if c in d2.columns]
h1 = pd.util.hash_pandas_object(d1[shared].fillna(""), index=False)
h2 = pd.util.hash_pandas_object(d2[shared].fillna(""), index=False)
inter = len(set(h1) & set(h2))
add(dataset_a="ai_job_dataset", dataset_b="ai_job_dataset1", key_type="full-row(shared cols)", scope="pairwise",
    n_a=len(h1), n_b=len(h2), n_overlap=inter,
    pct_of_a=round(100 * inter / len(h1), 3), pct_of_b=round(100 * inter / len(h2), 3),
    note=f"shared cols={shared}; only-in-B cols={[c for c in d2.columns if c not in d1.columns]}")

# ------------------------------------------------------------------- USA aggregate
usa = pd.read_csv(USA_FILE, dtype=str)
usa_titles = set(norm(usa["Job Posting Title"]))
add(dataset_a="usa_job_market", dataset_b="", key_type="title", scope="within",
    n_a=len(usa), n_b="", n_overlap=len(usa) - len(usa_titles),
    pct_of_a=round(100 * (len(usa) - len(usa_titles)) / len(usa), 3), pct_of_b="",
    note=f"aggregate title x skill rows; unique titles={len(usa_titles)}")

# title-string overlap USA vs LinkedIn postings (string-level, NOT record identity)
li_titles = set()
for chunk in pd.read_csv(LINK_FILES["linkedin_job_postings"], usecols=["job_title"], dtype=str, chunksize=200_000):
    li_titles |= set(norm(chunk["job_title"].dropna()))
inter = len(usa_titles & li_titles)
add(dataset_a="usa_job_market", dataset_b="linkedin_job_postings", key_type="title", scope="pairwise",
    n_a=len(usa_titles), n_b=len(li_titles), n_overlap=inter,
    pct_of_a=round(100 * inter / len(usa_titles), 3), pct_of_b=round(100 * inter / len(li_titles), 3),
    note="generic title strings; NOT record identity (no company/date on USA side)")

# ------------------------------------------- student/placement datasets: within dup
for n, p in STUDENT_FILES.items():
    df = pd.read_csv(p, dtype=str, low_memory=False)
    h = set(pd.util.hash_pandas_object(df.fillna(""), index=False))
    add(dataset_a=n, dataset_b="", key_type="full-row", scope="within",
        n_a=len(df), n_b="", n_overlap=len(df) - len(h),
        pct_of_a=round(100 * (len(df) - len(h)) / len(df), 3), pct_of_b="",
        note=f"exact duplicate rows; cols={list(df.columns)}")

# pairwise full-row only where schemas align (requires shared identifying columns)
identifying = ["job_title", "company_name", "candidate_id", "student_id", "profile_id", "Respondent_ID", "job_id"]
for a, b in itertools.combinations(STUDENT_FILES, 2):
    da = pd.read_csv(STUDENT_FILES[a], dtype=str, low_memory=False)
    db = pd.read_csv(STUDENT_FILES[b], dtype=str, low_memory=False)
    shared_id = [c for c in identifying if c in da.columns and c in db.columns]
    if not shared_id:
        add(dataset_a=a, dataset_b=b, key_type="none", scope="pairwise",
            n_a=len(da), n_b=len(db), n_overlap="", pct_of_a="", pct_of_b="",
            note="disjoint schemas; no shared identifying column")
        continue
    ka = set(norm(da[shared_id].fillna("").agg("|".join, axis=1)))
    kb = set(norm(db[shared_id].fillna("").agg("|".join, axis=1)))
    inter = len(ka & kb)
    add(dataset_a=a, dataset_b=b, key_type="+".join(shared_id), scope="pairwise",
        n_a=len(ka), n_b=len(kb), n_overlap=inter,
        pct_of_a=round(100 * inter / len(ka), 3), pct_of_b=round(100 * inter / len(kb), 3),
        note="")

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False)
print(f"wrote {OUT} rows={len(out)}")
print(out.to_string(index=False))
