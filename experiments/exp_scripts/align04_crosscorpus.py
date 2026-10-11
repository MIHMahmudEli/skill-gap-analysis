"""ALIGN04: Cross-corpus replication of SGI and domain gaps on LinkedIn.

Rationale : ALIGN01-03 establish lexical/semantic SGI and 8-category domain
            gaps on the HF Skill-Gap corpus (519,814 postings). A reviewer
            objection is single-corpus artefact. This script re-runs the
            identical instruments on the independent LinkedIn 2024 corpus
            (1,296,381 postings, job_skills.csv) against the SAME academic
            reference profile (hf_job_skill_set top-500).

Inputs : job_skills.csv (LinkedIn, bundle) + hf_job_skill_set.csv (academic).
Outputs: metrics.json, table_crosscorpus_sgi.csv, domain_gap_linkedin.csv,
         market_top500_linkedin.csv, skill_semantic_matches_linkedin.csv

Metrics (identical definitions to ALIGN01/02/03, seed 42, 1000x bootstrap):
  - lexical SGI: 1 - exact-match coverage of LinkedIn market top-100 in
    academic top-500; CI over the binary indicator vector.
  - semantic SGI(tau): 1 - mean(max_cos >= tau) of LinkedIn market top-100
    vs academic top-500 (all-MiniLM-L6-v2); tau in {0.4,0.5,0.6,0.7}.
  - domain gaps: posting-level demand / coverage / deficit per taxonomy
    category (same exclusive taxonomy as ALIGN03; mass-weighted coverage;
    1000x bootstrap over postings).
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
TAU = 0.5
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK = 100_000

SKILL_CATEGORIES = {
    "Programming & Development": [
        "python", "java", "javascript", "c++", "c#", "sql", "r", "scala", "go", "rust",
        "typescript", "php", "ruby", "swift", "kotlin", "html", "css", "react", "angular",
        "vue", "node.js", "django", "flask", "spring", "rails", "git", "docker", "kubernetes",
    ],
    "Data Science & Analytics": [
        "machine learning", "deep learning", "data analysis", "data visualization",
        "statistical analysis", "tensorflow", "pytorch", "pandas", "numpy", "scikit-learn",
        "tableau", "power bi", "hadoop", "spark", "data mining", "neural networks",
        "natural language processing", "nlp", "computer vision", "ai", "artificial intelligence",
    ],
    "Cloud & Infrastructure": [
        "aws", "azure", "gcp", "cloud computing", "devops", "ci/cd", "jenkins",
        "terraform", "ansible", "linux", "windows server", "networking", "security",
        "microservices", "rest api", "graphql", "serverless",
    ],
    "Soft Skills": [
        "communication", "leadership", "teamwork", "problem solving", "critical thinking",
        "time management", "project management", "analytical skills", "creativity",
        "adaptability", "collaboration", "presentation", "negotiation", "mentoring",
    ],
    "Business & Domain": [
        "agile", "scrum", "product management", "business analysis", "stakeholder management",
        "requirements gathering", "process improvement", "quality assurance", "compliance",
        "risk management", "strategic planning", "budget management", "client management",
    ],
    "Design & UX": [
        "ui/ux", "figma", "sketch", "adobe xd", "user research", "wireframing",
        "prototyping", "user interface", "user experience", "graphic design", "css",
    ],
    "Data Engineering": [
        "etl", "data pipeline", "airflow", "kafka", "database design", "data warehousing",
        "nosql", "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "data governance",
    ],
    "Cybersecurity": [
        "information security", "penetration testing", "vulnerability assessment",
        "incident response", "forensics", "encryption", "firewall", "siem",
        "compliance", "gdpr", "iso 27001", "nist",
    ],
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
    repo = Path(__file__).resolve().parents[2] / "datasets"
    mapping = {
        "job_skills.csv": repo / "kaggle" / "1-3m-linkedin-jobs-and-skills-2024" / "job_skills.csv",
        "hf_job_skill_set.csv": repo / "hf_job_skill_set.csv",
    }
    if name in mapping:
        candidates.append(mapping[name])
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


def exclusive_taxonomy():
    seen = set()
    exclusive = {}
    for cat, skills in SKILL_CATEGORIES.items():
        exclusive[cat] = []
        for s in skills:
            if s not in seen:
                seen.add(s)
                exclusive[cat].append(s)
    return exclusive


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Academic reference profile (top-500), identical to ALIGN01-03.
    acad_counts = Counter()
    for s in pd.read_csv(resolve("hf_job_skill_set.csv"),
                         usecols=["job_skill_set"])["job_skill_set"].dropna():
        skills_str = str(s).strip().strip("[]").replace("'", "")
        for skill in skills_str.split(","):
            skill = skill.strip().lower()
            if skill:
                acad_counts[skill] += 1
    academic_top = [s for s, _ in acad_counts.most_common(PROFILE_N)]
    academic_set = set(academic_top)

    # ---- LinkedIn market profile + posting-level skill sets.
    market_counts = Counter()
    n_postings = 0
    for chunk in pd.read_csv(resolve("job_skills.csv"), usecols=["job_skills"],
                             chunksize=CHUNK):
        for cell in chunk["job_skills"].dropna():
            n_postings += 1
            for sk in str(cell).split(","):
                sk = sk.strip().lower()
                if sk:
                    market_counts[sk] += 1
    market_top = [s for s, _ in market_counts.most_common(TOP_N)]

    # ---- Lexical SGI (ALIGN01 definition).
    covered_lex = [s for s in market_top if s in academic_set]
    missing_lex = [s for s in market_top if s not in academic_set]
    cov_lex = len(covered_lex) / TOP_N
    rng = np.random.RandomState(SEED)
    indicator = np.array([1.0 if s in academic_set else 0.0 for s in market_top])
    boot = [float(np.mean(rng.choice(indicator, size=TOP_N, replace=True)))
            for _ in range(BOOTSTRAP_N)]
    lex_lo, lex_hi = np.percentile(boot, [2.5, 97.5])

    # ---- Semantic SGI (ALIGN02 definition).
    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL_NAME, device=device)
    emb_m = model.encode(market_top, device=device, convert_to_numpy=True)
    emb_a = model.encode(academic_top, device=device, convert_to_numpy=True)
    max_sims = cosine_similarity(emb_m, emb_a).max(axis=1)
    best_idx = cosine_similarity(emb_m, emb_a).argmax(axis=1)
    matches_df = pd.DataFrame({
        "market_skill": market_top,
        "best_academic_match": [academic_top[i] for i in best_idx],
        "cosine_similarity": np.round(max_sims, 4),
    })

    rng2 = np.random.RandomState(SEED)
    sgi_rows = []
    for tau in TAUS:
        covered = max_sims >= tau
        cov = float(np.mean(covered))
        sgi = 1.0 - cov
        b = [1.0 - float(np.mean(rng2.choice(covered, size=TOP_N, replace=True)))
             for _ in range(BOOTSTRAP_N)]
        lo, hi = np.percentile(b, [2.5, 97.5])
        sgi_rows.append({
            "corpus": "linkedin_2024",
            "method": "semantic_sbert",
            "tau": tau,
            "SGI": round(sgi, 4),
            "Coverage_Rate": round(cov, 4),
            "CI_Lower": round(float(lo), 4),
            "CI_Upper": round(float(hi), 4),
        })
    sgi_rows.insert(0, {
        "corpus": "linkedin_2024",
        "method": "lexical_exact",
        "tau": None,
        "SGI": round(1.0 - cov_lex, 4),
        "Coverage_Rate": round(cov_lex, 4),
        "CI_Lower": round(float(1.0 - lex_hi), 4),
        "CI_Upper": round(float(1.0 - lex_lo), 4),
    })

    # ---- Domain gaps (ALIGN03 definition) on LinkedIn postings.
    exclusive = exclusive_taxonomy()
    categories = list(exclusive.keys())
    n_cats = len(categories)
    skill_to_cat = {}
    for ci, cat in enumerate(categories):
        for s in exclusive[cat]:
            skill_to_cat[s] = ci

    taxonomy_skills = list(skill_to_cat.keys())
    emb_s = model.encode(taxonomy_skills, device=device, convert_to_numpy=True)
    sims_tax = cosine_similarity(emb_s, emb_a).max(axis=1)
    sem_covered = {s: bool(v) for s, v in zip(taxonomy_skills, sims_tax >= TAU)}
    lex_covered_tax = {s: (s in academic_set) for s in taxonomy_skills}

    den_rows, cl_rows, cs_rows = [], [], []
    for chunk in pd.read_csv(resolve("job_skills.csv"), usecols=["job_skills"],
                             chunksize=CHUNK):
        for cell in chunk["job_skills"].dropna():
            skills = set()
            for sk in str(cell).split(","):
                sk = sk.strip().lower()
                if sk:
                    skills.add(sk)
            den = np.zeros(n_cats, dtype=np.int32)
            cl = np.zeros(n_cats, dtype=np.int32)
            cs = np.zeros(n_cats, dtype=np.int32)
            for sk in skills:
                ci = skill_to_cat.get(sk)
                if ci is None:
                    continue
                den[ci] += 1
                if lex_covered_tax.get(sk, False):
                    cl[ci] += 1
                if sem_covered.get(sk, False):
                    cs[ci] += 1
            den_rows.append(den)
            cl_rows.append(cl)
            cs_rows.append(cs)
    den = np.stack(den_rows)
    cov_lex_cat = np.stack(cl_rows)
    cov_sem_cat = np.stack(cs_rows)
    del den_rows, cl_rows, cs_rows

    mention = den > 0
    demand = 100.0 * mention.mean(axis=0)
    den_mass = den.sum(axis=0)
    rate_lex = np.where(den_mass > 0, cov_lex_cat.sum(axis=0) / np.maximum(den_mass, 1), 0.0)
    rate_sem = np.where(den_mass > 0, cov_sem_cat.sum(axis=0) / np.maximum(den_mass, 1), 0.0)

    rng3 = np.random.RandomState(SEED)
    N = n_postings
    boot_def_lex = np.zeros((BOOTSTRAP_N, n_cats))
    boot_def_sem = np.zeros((BOOTSTRAP_N, n_cats))
    for b in range(BOOTSTRAP_N):
        idx = rng3.randint(0, N, size=N)
        m_b = mention[idx].mean(axis=0)
        den_b = den[idx].sum(axis=0)
        cl_b = cov_lex_cat[idx].sum(axis=0)
        cs_b = cov_sem_cat[idx].sum(axis=0)
        r_l = np.where(den_b > 0, cl_b / np.maximum(den_b, 1), 0.0)
        r_s = np.where(den_b > 0, cs_b / np.maximum(den_b, 1), 0.0)
        boot_def_lex[b] = 100.0 * m_b * (1.0 - r_l)
        boot_def_sem[b] = 100.0 * m_b * (1.0 - r_s)

    def_lex = demand * (1 - rate_lex)
    def_sem = demand * (1 - rate_sem)

    gap_rows = []
    for ci, cat in enumerate(categories):
        d = float(demand[ci])
        gap_rows.append({
            "category": cat,
            "market_demand_pp": round(d, 2),
            "coverage_rate_lexical": round(float(rate_lex[ci]), 4),
            "deficit_pp_lexical": round(float(def_lex[ci]), 2),
            "deficit_lex_ci_lower": round(float(np.percentile(boot_def_lex[:, ci], 2.5)), 2),
            "deficit_lex_ci_upper": round(float(np.percentile(boot_def_lex[:, ci], 97.5)), 2),
            "coverage_rate_semantic_tau0.5": round(float(rate_sem[ci]), 4),
            "deficit_pp_semantic": round(float(def_sem[ci]), 2),
            "deficit_sem_ci_lower": round(float(np.percentile(boot_def_sem[:, ci], 2.5)), 2),
            "deficit_sem_ci_upper": round(float(np.percentile(boot_def_sem[:, ci], 97.5)), 2),
            "taxonomy_skills_in_market": int(sum(1 for s in exclusive[cat]
                                                 if market_counts.get(s, 0) > 0)),
            "taxonomy_skills_total": len(exclusive[cat]),
        })
    gap_df = pd.DataFrame(gap_rows)
    sgi_df = pd.DataFrame(sgi_rows)

    market_df = pd.DataFrame(market_counts.most_common(PROFILE_N),
                             columns=["skill", "postings"])

    sem_row = sgi_df[(sgi_df.method == "semantic_sbert") & (sgi_df.tau == TAU)].iloc[0]
    metrics = {
        "experiment_id": "ALIGN04_crosscorpus_linkedin",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "model": MODEL_NAME,
        "device": device,
        "n_postings": n_postings,
        "n_unique_skills_linkedin": len(market_counts),
        "lexical_sgi": round(1.0 - cov_lex, 4),
        "lexical_sgi_ci": [round(float(1.0 - lex_hi), 4), round(float(1.0 - lex_lo), 4)],
        "semantic_sgi_tau_0.5": float(sem_row["SGI"]),
        "semantic_sgi_tau_0.5_ci": [float(sem_row["CI_Lower"]), float(sem_row["CI_Upper"])],
        "sensitivity": sgi_rows,
        "domain_gaps": gap_df.to_dict(orient="records"),
    }
    sgi_df.to_csv(out_dir / "table_crosscorpus_sgi.csv", index=False)
    gap_df.to_csv(out_dir / "domain_gap_linkedin.csv", index=False)
    market_df.to_csv(out_dir / "market_top500_linkedin.csv", index=False)
    matches_df.to_csv(out_dir / "skill_semantic_matches_linkedin.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2)[:4000])


if __name__ == "__main__":
    sys.exit(main())
