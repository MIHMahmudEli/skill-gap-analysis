"""Shared utilities for the skill-gap experiment package.

Used both locally (scheduler/verification) and inside Kaggle kernels
(each experiment script is self-contained and inlines the few helpers it
needs; this module is the local-side source of truth).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = REPO_ROOT / "results"
REGISTRY_PATH = RESULTS_DIR / "registry.json"
ENV_PATH = REPO_ROOT / ".env"
DATASETS_DIR = REPO_ROOT / "datasets"

SEED = 42
BOOTSTRAP_N = 1000
TAU_THRESHOLDS = [0.4, 0.5, 0.6, 0.7]
SBERT_MODEL = "all-MiniLM-L6-v2"
KAGGLE_INPUT_DATASET = "studyhub991/skill-gap-inputs-v1"

# Canonical file names inside the Kaggle input bundle (and local fallbacks).
BUNDLE_FILES = {
    "market_skills": "hf_skill_gap_skills.csv",
    "academic_skills": "hf_job_skill_set.csv",
    "linkedin_postings": "linkedin_job_postings.csv",
    "college_placement": "college_student_placement_dataset.csv",
    "student_career": "student_career_success_dataset.csv",
    "global_placement": "global_placement.csv",
    "ai_trends": "ai_job_market_2020_2026.csv",
    "international_grads": "international_graduates_dataset.csv",
}

LOCAL_FALLBACKS = {
    "market_skills": DATASETS_DIR / "hf_skill_gap_skills.csv",
    "academic_skills": DATASETS_DIR / "hf_job_skill_set.csv",
    "linkedin_postings": DATASETS_DIR / "kaggle" / "1-3m-linkedin-jobs-and-skills-2024" / "linkedin_job_postings.csv",
    "college_placement": DATASETS_DIR / "kaggle" / "college-student-placement" / "college_student_placement_dataset.csv",
    "student_career": DATASETS_DIR / "kaggle" / "student-career-success-prediction-dataset" / "student_career_success_dataset.csv",
    "global_placement": DATASETS_DIR / "kaggle" / "global-student-placement-2025-dataset" / "global_placement.csv",
    "ai_trends": DATASETS_DIR / "kaggle" / "ai-and-data-science-job-market-dataset-20202026" / "AI Job Market Dataset.csv",
    "international_grads": DATASETS_DIR / "kaggle" / "international-graduates-employment-dataset" / "dataset.csv",
}

KAGGLE_INPUT_ROOTS = [
    Path("/kaggle/input") / KAGGLE_INPUT_DATASET.replace("/", "-"),
    Path("/kaggle/input") / KAGGLE_INPUT_DATASET.split("/")[1],
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_input(key: str) -> Path:
    """Resolve an input file for local or Kaggle execution."""
    name = BUNDLE_FILES[key]
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in KAGGLE_INPUT_ROOTS:
        candidates.append(root / "bundle" / name)
        candidates.append(root / name)
    if key in LOCAL_FALLBACKS:
        candidates.append(LOCAL_FALLBACKS[key])
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"Input '{key}' ({name}) not found. Tried: {[str(c) for c in candidates]}"
    )


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, default=str)


def read_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_env_workers(env_path: Path = ENV_PATH):
    """Parse .env tolerating duplicate Username/Kaggel_Token keys (16 workers)."""
    workers = []
    cur_user = None
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            name, value = s.split("=", 1)
            name, value = name.strip(), value.strip()
            if not value:
                continue
            if name == "Username":
                cur_user = value
            elif name in ("Kaggel_Token", "Kaggel_Tokhon") and cur_user:
                workers.append({"username": cur_user, "token": value})
    return workers


def git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        return out
    except Exception:
        return "unknown"


def experiment_metadata(exp_id: str, dataset_keys, model, hyperparameters,
                        protocol, seed=SEED, gpu=True) -> dict:
    return {
        "experiment_id": exp_id,
        "timestamp_utc": utc_now(),
        "seed": seed,
        "datasets": {k: BUNDLE_FILES[k] for k in dataset_keys},
        "model": model,
        "hyperparameters": hyperparameters,
        "protocol": protocol,
        "code_commit": git_commit(),
        "python_version": sys.version.split()[0],
        "gpu": gpu,
        "bootstrap_n": BOOTSTRAP_N,
        "tau_thresholds": TAU_THRESHOLDS,
        "sbert_model": SBERT_MODEL if "sbert" in model.lower() or "semantic" in model.lower() else None,
    }
