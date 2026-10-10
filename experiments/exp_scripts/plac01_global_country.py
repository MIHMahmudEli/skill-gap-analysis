"""PLAC01: Global student placement rates by country.

Inputs : global_placement.csv (N=10,000)
Outputs: metrics.json, placement_by_country.csv

Metric : placement rate per country with Wilson 95% CI; overall rate;
         salary stats for placed students.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

import pandas as pd


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
             "global-student-placement-2025-dataset" / name)
    candidates.append(local)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(resolve("global_placement.csv"))
    df["Placed"] = (df["placement_status"] == "Placed").astype(int)
    n = len(df)
    overall = float(df["Placed"].mean())

    rows = []
    for country, g in df.groupby("country"):
        k, m = int(g["Placed"].sum()), int(len(g))
        lo, hi = wilson_ci(k, m)
        rows.append({
            "country": country,
            "n": m,
            "placed": k,
            "placement_rate_pct": round(100 * k / m, 2),
            "ci_lower_pct": round(100 * lo, 2),
            "ci_upper_pct": round(100 * hi, 2),
        })
    rows.sort(key=lambda r: -r["placement_rate_pct"])
    placed_df = df[df.Placed == 1]

    metrics = {
        "experiment_id": "PLAC01_global_by_country",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "n_total": n,
        "overall_placement_rate_pct": round(100 * overall, 2),
        "overall_ci_pct": [round(100 * wilson_ci(int(df.Placed.sum()), n)[0], 2),
                           round(100 * wilson_ci(int(df.Placed.sum()), n)[1], 2)],
        "by_country": rows,
        "salary_mean_placed": round(float(placed_df["salary"].mean()), 2) if "salary" in df else None,
    }
    pd.DataFrame(rows).to_csv(out_dir / "placement_by_country.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    sys.exit(main())
