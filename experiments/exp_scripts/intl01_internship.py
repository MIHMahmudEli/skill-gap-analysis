"""INTL01: Internship effect on employment (international graduates).

Inputs : international_graduates_dataset.csv (N=300,000)
Outputs: metrics.json, internship_effect.csv

Metric : employment rate with vs without internship; risk difference with
         1000x stratified bootstrap 95% CI; chi-square + Cramer's V;
         Cohen's h effect size; rates by field of study.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SEED = 42
BOOTSTRAP_N = 1000


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
             "international-graduates-employment-dataset" / "dataset.csv")
    candidates.append(local)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def cohen_h(p1: float, p2: float) -> float:
    return float(2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2)))


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(resolve("international_graduates_dataset.csv"))
    n = len(df)
    emp_col = "Employment_Status"
    int_col = "Internship_Experience"
    df["Employed"] = (df[emp_col] == "Employed").astype(int)

    ct = pd.crosstab(df[int_col], df[emp_col])
    chi2, p_chi, dof, _ = stats.chi2_contingency(ct)
    cramers_v = float(np.sqrt(chi2 / (n * (min(ct.shape) - 1))))

    with_int = df[df[int_col] == "Yes"]["Employed"]
    without = df[df[int_col] == "No"]["Employed"]
    p_with = float(with_int.mean())
    p_without = float(without.mean())
    rd = p_with - p_without
    h = cohen_h(p_with, p_without)

    rng = np.random.RandomState(SEED)
    a, b = with_int.values, without.values
    boot_rd = []
    for _ in range(BOOTSTRAP_N):
        s1 = rng.choice(a, size=len(a), replace=True)
        s2 = rng.choice(b, size=len(b), replace=True)
        boot_rd.append(float(s1.mean() - s2.mean()))
    ci_lo, ci_hi = np.percentile(boot_rd, [2.5, 97.5])

    rows = [
        {"internship": "Yes", "n": int(len(a)), "employed": int(a.sum()),
         "employment_rate_pct": round(100 * p_with, 2)},
        {"internship": "No", "n": int(len(b)), "employed": int(b.sum()),
         "employment_rate_pct": round(100 * p_without, 2)},
    ]

    by_field = []
    if "Field_of_Study" in df.columns:
        for field, g in df.groupby("Field_of_Study"):
            gw = g[g[int_col] == "Yes"]["Employed"]
            gn = g[g[int_col] == "No"]["Employed"]
            if len(gw) > 0 and len(gn) > 0:
                by_field.append({
                    "field": field,
                    "rate_with_internship_pct": round(100 * float(gw.mean()), 2),
                    "rate_without_internship_pct": round(100 * float(gn.mean()), 2),
                    "difference_pp": round(100 * float(gw.mean() - gn.mean()), 2),
                    "n": int(len(g)),
                })

    metrics = {
        "experiment_id": "INTL01_internship_effect",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "n_total": n,
        "employment_rate_with_internship_pct": round(100 * p_with, 2),
        "employment_rate_without_internship_pct": round(100 * p_without, 2),
        "risk_difference_pp": round(100 * rd, 2),
        "risk_difference_ci_pp": [round(100 * float(ci_lo), 2), round(100 * float(ci_hi), 2)],
        "cohens_h": round(h, 4),
        "chi2": round(float(chi2), 3),
        "chi2_p": float(f"{p_chi:.4g}"),
        "cramers_v": round(cramers_v, 4),
        "employment_status_distribution": df[emp_col].value_counts().to_dict(),
        "by_field": by_field,
    }
    pd.DataFrame(rows).to_csv(out_dir / "internship_effect.csv", index=False)
    pd.DataFrame(by_field).to_csv(out_dir / "internship_effect_by_field.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2, default=str)[:2500])


if __name__ == "__main__":
    sys.exit(main())
