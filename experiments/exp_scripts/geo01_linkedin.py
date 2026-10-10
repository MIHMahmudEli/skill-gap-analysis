"""GEO01: Geographic distribution of LinkedIn job postings.

Inputs : linkedin_job_postings.csv (chunked read; ~1.35M rows).
Outputs: metrics.json, geo_country_shares.csv

Metric : share of postings per search_country (exact counts), plus
         top-10 job titles overall.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd

TOP_TITLES_N = 10


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
             "1-3m-linkedin-jobs-and-skills-2024" / name)
    candidates.append(local)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    path = resolve("linkedin_job_postings.csv")
    country_counts = Counter()
    title_counts = Counter()
    n_rows = 0
    for chunk in pd.read_csv(path, chunksize=100_000, low_memory=False):
        n_rows += len(chunk)
        if "search_country" in chunk.columns:
            country_counts.update(chunk["search_country"].dropna().astype(str))
        elif "job_location" in chunk.columns:
            country_counts.update(chunk["job_location"].dropna().astype(str))
        if "job_title" in chunk.columns:
            title_counts.update(chunk["job_title"].dropna().astype(str))
        elif "title" in chunk.columns:
            title_counts.update(chunk["title"].dropna().astype(str))

    total_loc = sum(country_counts.values())
    rows = []
    for country, count in country_counts.most_common():
        rows.append({
            "country": country,
            "postings": int(count),
            "share_pct": round(100.0 * count / total_loc, 2),
        })
    geo_df = pd.DataFrame(rows)

    top_titles = [{"title": t, "count": int(c)}
                  for t, c in title_counts.most_common(TOP_TITLES_N)]

    metrics = {
        "experiment_id": "GEO01_linkedin_shares",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "dataset": "linkedin_job_postings.csv",
        "n_rows": n_rows,
        "n_with_location": total_loc,
        "top_countries": rows[:10],
        "top_titles": top_titles,
    }
    geo_df.to_csv(out_dir / "geo_country_shares.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(geo_df.head(10).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
