"""STAT02: External validation / cross-dataset transfer of placement models.

Inputs : college_student_placement_dataset.csv (train),
         student_career_success_dataset.csv (target A),
         global_placement.csv (target B).
Outputs: metrics.json, external_validation.csv

Protocol:
  For each target, train a standardized logistic regression on the college
  dataset restricted to the feature subset observable in the target, then
  evaluate on the target without refitting (pure transfer). Feature maps:
    target A (student career): CGPA, Communication_Skills, Projects_Completed,
        Internships>0
    target B (global): cgpa, communication_score, internship_count>0
  Also report: target-specific in-dataset LR (reference upper bound),
  base rates, ROC-AUC, accuracy, F1.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, f1_score, roc_auc_score)
from sklearn.preprocessing import StandardScaler

SEED = 42


def resolve(name: str) -> Path:
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    repo = Path(__file__).resolve().parents[2] / "datasets" / "kaggle"
    mapping = {
        "college_student_placement_dataset.csv":
            repo / "college-student-placement" / "college_student_placement_dataset.csv",
        "student_career_success_dataset.csv":
            repo / "student-career-success-prediction-dataset" / "student_career_success_dataset.csv",
        "global_placement.csv":
            repo / "global-student-placement-2025-dataset" / "global_placement.csv",
    }
    if name in mapping:
        candidates.append(mapping[name])
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def evaluate(model, scaler, X, y):
    Xs = scaler.transform(X)
    pred = model.predict(Xs)
    proba = model.predict_proba(Xs)[:, 1]
    return {
        "n": int(len(y)),
        "base_rate": round(float(np.mean(y)), 4),
        "accuracy": round(float(accuracy_score(y, pred)), 4),
        "f1_weighted": round(float(f1_score(y, pred, average="weighted", zero_division=0)), 4),
        "auc": round(float(roc_auc_score(y, proba)), 4),
    }


def train_lr(X, y):
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model = LogisticRegression(max_iter=1000, random_state=SEED)
    model.fit(Xs, y)
    return model, scaler


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    college = pd.read_csv(resolve("college_student_placement_dataset.csv"))
    college["Placement_Binary"] = (college["Placement"] == "Yes").astype(int)
    college["Internship_Binary"] = (college["Internship_Experience"] == "Yes").astype(int)

    career = pd.read_csv(resolve("student_career_success_dataset.csv"))
    career["Placement_Binary"] = (career["Placement_Status"] == "Placed").astype(int)
    career["Internship_Binary"] = (career["Internships"] > 0).astype(int)

    glob = pd.read_csv(resolve("global_placement.csv"))
    glob["Placement_Binary"] = (glob["placement_status"] == "Placed").astype(int)
    glob["Internship_Binary"] = (glob["internship_count"] > 0).astype(int)

    rows = []

    # --- Target A: Student Career Success (N=50,000) ---
    # Academic_Performance is ordinal-categorical in the target (Poor..Excellent)
    # vs numeric 1-10 in college, so it is excluded from the transfer subset.
    feats_A_college = ["CGPA", "Communication_Skills", "Projects_Completed",
                       "Internship_Binary"]
    feats_A_target = ["CGPA", "Communication_Skills", "Projects_Completed",
                      "Internship_Binary"]
    tr = college[feats_A_college].dropna()
    y_tr = college.loc[tr.index, "Placement_Binary"]
    te = career[feats_A_target].dropna()
    y_te = career.loc[te.index, "Placement_Binary"]
    model, scaler = train_lr(tr.values, y_tr.values)
    res = evaluate(model, scaler, te.values, y_te.values)
    rows.append({"train": "College (features subset A)", "test": "Student Career Success",
                 **res})
    model_in, scaler_in = train_lr(te.values, y_te.values)
    res_in = evaluate(model_in, scaler_in, te.values, y_te.values)
    rows.append({"train": "Student Career Success (in-sample ref.)",
                 "test": "Student Career Success", **res_in})

    # --- Target B: Global Placement (N=10,000) ---
    feats_B_college = ["CGPA", "Communication_Skills", "Internship_Binary"]
    feats_B_target = ["cgpa", "communication_score", "Internship_Binary"]
    tr = college[feats_B_college].dropna()
    y_tr = college.loc[tr.index, "Placement_Binary"]
    te = glob[feats_B_target].dropna()
    y_te = glob.loc[te.index, "Placement_Binary"]
    model, scaler = train_lr(tr.values, y_tr.values)
    res = evaluate(model, scaler, te.values, y_te.values)
    rows.append({"train": "College (features subset B)", "test": "Global Placement", **res})
    model_in, scaler_in = train_lr(te.values, y_te.values)
    res_in = evaluate(model_in, scaler_in, te.values, y_te.values)
    rows.append({"train": "Global Placement (in-sample ref.)",
                 "test": "Global Placement", **res_in})

    out = pd.DataFrame(rows)
    metrics = {
        "experiment_id": "STAT02_external_validation",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "protocol": "train-on-college feature-subset, zero-shot transfer; in-dataset LR as reference",
        "feature_map_A": feats_A_college,
        "feature_map_B": feats_B_college,
        "results": rows,
    }
    out.to_csv(out_dir / "external_validation.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(out.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
