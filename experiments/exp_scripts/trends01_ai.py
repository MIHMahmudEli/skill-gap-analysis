"""TRENDS01: Longitudinal AI/data skill demand 2020-2026.

Inputs : ai_job_market_2020_2026.csv
Outputs: metrics.json, trends_yearly.csv, trends_salary_by_experience.csv

Metric : per-year share of postings requiring python/sql/ml/cloud/deep
         learning (binary indicator columns); salary stats by experience.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from scipy import stats

SKILL_COLS = {
    "python": "skills_python",
    "sql": "skills_sql",
    "ml": "skills_ml",
    "deep_learning": "skills_deep_learning",
    "cloud": "skills_cloud",
}


def resolve(name: str) -> Path:
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    local = (Path(__file__).resolve().parents[2] / "datasets" / "kaggle" /
             "ai-and-data-science-job-market-dataset-20202026" / "AI Job Market Dataset.csv")
    candidates.append(local)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(resolve("ai_job_market_2020_2026.csv"))
    n = len(df)

    yearly = df.groupby("job_posting_year")[list(SKILL_COLS.values())].mean().round(4)
    yearly_pct = (yearly * 100).round(2).reset_index()
    yearly_pct.columns = ["year"] + [f"{k}_share_pct" for k in SKILL_COLS]

    sal = []
    if "salary" in df.columns and "experience_level" in df.columns:
        groups = [g["salary"].dropna() for _, g in df.groupby("experience_level")
                  if len(g["salary"].dropna()) > 1]
        f_stat, p_val = stats.f_oneway(*groups)
        for level, g in df.groupby("experience_level"):
            sal.append({
                "experience_level": level,
                "n": int(len(g)),
                "salary_mean": round(float(g["salary"].mean()), 2),
                "salary_sd": round(float(g["salary"].std()), 2),
            })
        sal_meta = {"anova_f": round(float(f_stat), 3), "p_value": float(f"{p_val:.4g}")}
    else:
        sal_meta = {}

    metrics = {
        "experiment_id": "TRENDS01_ai_longitudinal",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "dataset": "ai_job_market_2020_2026.csv",
        "n_postings": n,
        "yearly_shares": yearly_pct.to_dict(orient="records"),
        "salary_anova": sal_meta,
    }
    yearly_pct.to_csv(out_dir / "trends_yearly.csv", index=False)
    pd.DataFrame(sal).to_csv(out_dir / "trends_salary_by_experience.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(yearly_pct.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
