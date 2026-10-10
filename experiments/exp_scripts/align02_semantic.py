"""ALIGN02: Sentence-BERT semantic curriculum-market alignment.

Inputs : market + academic skill corpora (same as ALIGN01).
Outputs: metrics.json, table_sensitivity_tau.csv, skill_semantic_matches.csv

Method : all-MiniLM-L6-v2 (384-d) embeddings of the top-100 market and
         academic skills; per-market-skill max cosine similarity to any
         academic skill; coverage at tau in {0.4,0.5,0.6,0.7};
         SGI(tau) = 1 - coverage; 1000x bootstrap percentile CI;
         Delta_SGI relative to tau=0.5.
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
from sklearn.metrics.pairwise import cosine_similarity

SEED = 42
BOOTSTRAP_N = 1000
TOP_N = 100
PROFILE_N = 500
TAUS = [0.4, 0.5, 0.6, 0.7]
MODEL_NAME = "all-MiniLM-L6-v2"


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
    market_df = pd.DataFrame(Counter(market_rows).most_common(PROFILE_N),
                             columns=["skill", "job_postings"])
    acad_rows = []
    for s in pd.read_csv(resolve("hf_job_skill_set.csv"),
                         usecols=["job_skill_set"])["job_skill_set"].dropna():
        skills_str = str(s).strip().strip("[]").replace("'", "")
        for skill in skills_str.split(","):
            skill = skill.strip().lower()
            if skill:
                acad_rows.append(skill)
    acad_df = pd.DataFrame(Counter(acad_rows).most_common(PROFILE_N),
                           columns=["skill", "frequency"])

    market_skills = market_df["skill"].head(TOP_N).tolist()
    academic_skills = acad_df["skill"].head(TOP_N).tolist()

    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL_NAME, device=device)
    market_emb = model.encode(market_skills, show_progress_bar=False,
                              convert_to_numpy=True)
    academic_emb = model.encode(academic_skills, show_progress_bar=False,
                                convert_to_numpy=True)

    sim = cosine_similarity(market_emb, academic_emb)
    max_sims = np.max(sim, axis=1)
    best_idx = np.argmax(sim, axis=1)

    matches_df = pd.DataFrame({
        "market_skill": market_skills,
        "best_academic_match": [academic_skills[i] for i in best_idx],
        "cosine_similarity": np.round(max_sims, 4),
    })

    rng = np.random.RandomState(SEED)
    rows = []
    default_covered = max_sims >= 0.5
    default_sgi = 1.0 - float(np.mean(default_covered))
    for tau in TAUS:
        covered = max_sims >= tau
        cov = float(np.mean(covered))
        sgi = 1.0 - cov
        boot = [1.0 - float(np.mean(rng.choice(covered, size=len(covered), replace=True)))
                for _ in range(BOOTSTRAP_N)]
        lo, hi = np.percentile(boot, [2.5, 97.5])
        rows.append({
            "tau": tau,
            "SGI": round(sgi, 4),
            "Coverage_Rate": round(cov, 4),
            "CI_Lower": round(float(lo), 4),
            "CI_Upper": round(float(hi), 4),
            "Delta_SGI": round(sgi - default_sgi, 4),
        })
    sens_df = pd.DataFrame(rows)

    metrics = {
        "experiment_id": "ALIGN02_semantic_sbert",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "model": MODEL_NAME,
        "device": device,
        "top_n": TOP_N,
        "sensitivity": rows,
        "sgi_at_tau_0.5": rows[1]["SGI"],
        "sgi_ci_at_tau_0.5": [rows[1]["CI_Lower"], rows[1]["CI_Upper"]],
    }
    sens_df.to_csv(out_dir / "table_sensitivity_tau.csv", index=False)
    matches_df.to_csv(out_dir / "skill_semantic_matches.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    sys.exit(main())
