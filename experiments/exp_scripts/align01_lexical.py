"""ALIGN01: Lexical (exact string-match) curriculum-market alignment.

Inputs : market skill corpus (hf_skill_gap_skills) + academic reference
         corpus (hf_job_skill_set).
Outputs: metrics.json, market_top500.csv, academic_top500.csv,
         lexical_alignment.json

Metric : top-100 exact-match coverage; SGI = 1 - coverage; 1000x
         non-parametric bootstrap CI on the coverage indicator vector.
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
BOOTSTRAP_N = 1000
TOP_N = 100
PROFILE_N = 500


def resolve(name: str) -> Path:
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    repo = Path(__file__).resolve().parents[2] / "datasets"
    mapping = {
        "hf_skill_gap_skills.csv": repo / "hf_skill_gap_skills.csv",
        "hf_job_skill_set.csv": repo / "hf_job_skill_set.csv",
    }
    if name in mapping:
        candidates.append(mapping[name])
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    market_rows = []
    for s in pd.read_csv(resolve("hf_skill_gap_skills.csv"),
                         usecols=["job_skills"])["job_skills"].dropna():
        for skill in str(s).split(","):
            skill = skill.strip().lower()
            if skill:
                market_rows.append(skill)
    market_counts = Counter(market_rows).most_common(PROFILE_N)
    market_df = pd.DataFrame(market_counts, columns=["skill", "job_postings"])

    acad_rows = []
    for s in pd.read_csv(resolve("hf_job_skill_set.csv"),
                         usecols=["job_skill_set"])["job_skill_set"].dropna():
        skills_str = str(s).strip().strip("[]").replace("'", "")
        for skill in skills_str.split(","):
            skill = skill.strip().lower()
            if skill:
                acad_rows.append(skill)
    acad_counts = Counter(acad_rows).most_common(PROFILE_N)
    acad_df = pd.DataFrame(acad_counts, columns=["skill", "frequency"])

    market_top = market_df["skill"].head(TOP_N).tolist()
    acad_top = acad_df["skill"].head(TOP_N).tolist()
    market_set, acad_set = set(market_top), set(acad_top)
    covered = market_set & acad_set
    missing = market_set - acad_set
    coverage = len(covered) / len(market_set)

    # Bootstrap CI over the binary coverage indicator of market top-N skills.
    rng = np.random.RandomState(SEED)
    indicator = np.array([1.0 if s in acad_set else 0.0 for s in market_top])
    boot_cov = [float(np.mean(rng.choice(indicator, size=len(indicator), replace=True)))
                for _ in range(BOOTSTRAP_N)]
    ci_lo, ci_hi = np.percentile(boot_cov, [2.5, 97.5])

    metrics = {
        "experiment_id": "ALIGN01_lexical_bootstrap",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "top_n": TOP_N,
        "market_corpus_token_count": len(market_rows),
        "academic_corpus_token_count": len(acad_rows),
        "coverage_rate": round(coverage, 4),
        "sgi": round(1.0 - coverage, 4),
        "sgi_ci_lower": round(1.0 - ci_hi, 4),
        "sgi_ci_upper": round(1.0 - ci_lo, 4),
        "coverage_ci_lower": round(ci_lo, 4),
        "coverage_ci_upper": round(ci_hi, 4),
        "n_covered": len(covered),
        "n_missing": len(missing),
        "missing_skills": sorted(missing),
        "covered_skills": sorted(covered),
    }
    market_df.to_csv(out_dir / "market_top500.csv", index=False)
    acad_df.to_csv(out_dir / "academic_top500.csv", index=False)
    with open(out_dir / "lexical_alignment.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    sys.exit(main())
