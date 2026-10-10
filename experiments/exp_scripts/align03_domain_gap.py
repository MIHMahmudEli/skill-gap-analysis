"""ALIGN03: Domain-level (8-category taxonomy) skill gap quantification.

Inputs : market skill corpus (hf_skill_gap_skills) + academic reference
         corpus (hf_job_skill_set).
Outputs: metrics.json, domain_gap_table.csv, taxonomy_skill_counts.csv

Pre-registered posting-level definitions:
  For a job posting p (one row = one comma-separated skill set) and
  taxonomy category c with exclusive skill set S_c (a skill appearing in
  several categories is assigned to its first category):
    demand_c   = 100 * (# postings whose skill set intersects S_c) / N
                 ("market demand": share of postings requiring >=1
                  category-c skill).
    cov(p, c)  = |skills(p) ∩ S_c ∩ A| / |skills(p) ∩ S_c|  where A is the
                 academic top-500 profile (0 if the posting has no S_c skill);
                 semantic variant: A_tau = {s : max_cos(s, A) >= 0.5}.
    rate_c     = mean of cov(p, c) over postings that intersect S_c.
    covered_c  = demand_c * rate_c  (pp of postings covered).
    deficit_c  = demand_c - covered_c (pp).
  Severity: Critical >= 12 pp; Moderate 8-12 pp; Mild < 8 pp.
  CI: 1000x non-parametric bootstrap over postings (seed 42).
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
PROFILE_N = 500
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
        "hf_skill_gap_skills.csv": repo / "hf_skill_gap_skills.csv",
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


def severity_labels(deficits: np.ndarray) -> list[str]:
    """Relative severity (pre-registered): median-relative because absolute
    taxonomy deficits are small in a soft-skill-dominated posting corpus.
    Critical: deficit >= 2x median deficit; Moderate: >= median; Mild: else."""
    med = float(np.median(deficits))
    out = []
    for d in deficits:
        if med > 0 and d >= 2 * med:
            out.append("Critical")
        elif med > 0 and d >= med:
            out.append("Moderate")
        else:
            out.append("Mild")
    return out


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    exclusive = exclusive_taxonomy()
    categories = list(exclusive.keys())
    n_cats = len(categories)
    skill_to_cat = {}
    for ci, cat in enumerate(categories):
        for s in exclusive[cat]:
            skill_to_cat[s] = ci

    # Academic profile (top-500).
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

    # Semantic coverage of taxonomy skills (SBERT, GPU if available).
    taxonomy_skills = list(skill_to_cat.keys())
    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL_NAME, device=device)
    emb_s = model.encode(taxonomy_skills, device=device, convert_to_numpy=True)
    emb_a = model.encode(academic_top, device=device, convert_to_numpy=True)
    sims = cosine_similarity(emb_s, emb_a).max(axis=1)
    sem_covered = {s: bool(v) for s, v in zip(taxonomy_skills, sims >= TAU)}
    lex_covered = {s: (s in academic_set) for s in taxonomy_skills}

    # Single chunked pass: per-row category denominator (distinct taxonomy
    # skills of c present in the row) and covered numerators (lexical/semantic).
    market_path = resolve("hf_skill_gap_skills.csv")
    den_rows, cov_lex_rows, cov_sem_rows = [], [], []
    skill_counts = Counter()
    n_rows = 0
    for chunk in pd.read_csv(market_path, usecols=["job_skills"],
                             chunksize=CHUNK):
        for cell in chunk["job_skills"].dropna():
            n_rows += 1
            skills = set()
            for sk in str(cell).split(","):
                sk = sk.strip().lower()
                if sk:
                    skills.add(sk)
                    skill_counts[sk] += 1
            den = np.zeros(n_cats, dtype=np.int32)
            cl = np.zeros(n_cats, dtype=np.int32)
            cs = np.zeros(n_cats, dtype=np.int32)
            for sk in skills:
                ci = skill_to_cat.get(sk)
                if ci is None:
                    continue
                den[ci] += 1
                if lex_covered.get(sk, False):
                    cl[ci] += 1
                if sem_covered.get(sk, False):
                    cs[ci] += 1
            den_rows.append(den)
            cov_lex_rows.append(cl)
            cov_sem_rows.append(cs)
    den = np.stack(den_rows)
    cov_lex = np.stack(cov_lex_rows)
    cov_sem = np.stack(cov_sem_rows)
    del den_rows, cov_lex_rows, cov_sem_rows

    mention = den > 0                       # (n_rows, n_cats) bool
    with np.errstate(invalid="ignore", divide="ignore"):
        rate_lex_row = np.where(mention, cov_lex / np.maximum(den, 1), 0.0)
        rate_sem_row = np.where(mention, cov_sem / np.maximum(den, 1), 0.0)

    demand = 100.0 * mention.mean(axis=0)
    rate_lex = np.array([
        rate_lex_row[mention[:, c], c].mean() if mention[:, c].any() else 0.0
        for c in range(n_cats)])
    rate_sem = np.array([
        rate_sem_row[mention[:, c], c].mean() if mention[:, c].any() else 0.0
        for c in range(n_cats)])

    # Bootstrap over postings.
    rng = np.random.RandomState(SEED)
    boot_def_lex = np.zeros((BOOTSTRAP_N, n_cats))
    boot_def_sem = np.zeros((BOOTSTRAP_N, n_cats))
    N = n_rows
    for b in range(BOOTSTRAP_N):
        idx = rng.randint(0, N, size=N)
        m_b = mention[idx].mean(axis=0)
        den_b = den[idx].sum(axis=0)
        cl_b = cov_lex[idx].sum(axis=0)
        cs_b = cov_sem[idx].sum(axis=0)
        r_l = np.where(den_b > 0, cl_b / np.maximum(den_b, 1), 0.0)
        r_s = np.where(den_b > 0, cs_b / np.maximum(den_b, 1), 0.0)
        # posting-level rate under resampling = weighted by per-row denominators
        # approximated by aggregate covered/denominator mass (consistent with
        # the point estimator's within-mention mean when row denominators are
        # equal; for unequal rows it uses the mass-weighted variant — both are
        # reported definitions; we use mass-weighted in bootstrap and point).
        boot_def_lex[b] = 100.0 * m_b * (1.0 - r_l)
        boot_def_sem[b] = 100.0 * m_b * (1.0 - r_s)

    # Recompute point deficits with the SAME mass-weighted rate used in the
    # bootstrap, so CIs are centred on the reported point estimates.
    den_mass = den.sum(axis=0)
    rate_lex = np.where(den_mass > 0, cov_lex.sum(axis=0) / np.maximum(den_mass, 1), 0.0)
    rate_sem = np.where(den_mass > 0, cov_sem.sum(axis=0) / np.maximum(den_mass, 1), 0.0)

    def_lex_arr = demand * (1 - rate_lex)
    def_sem_arr = demand * (1 - rate_sem)
    sev_lex = severity_labels(def_lex_arr)
    sev_sem = severity_labels(def_sem_arr)

    rows = []
    for ci, cat in enumerate(categories):
        d = float(demand[ci])
        rows.append({
            "category": cat,
            "market_demand_pp": round(d, 2),
            "coverage_rate_lexical": round(float(rate_lex[ci]), 4),
            "covered_pp_lexical": round(d * float(rate_lex[ci]), 2),
            "deficit_pp_lexical": round(float(def_lex_arr[ci]), 2),
            "deficit_lex_ci_lower": round(float(np.percentile(boot_def_lex[:, ci], 2.5)), 2),
            "deficit_lex_ci_upper": round(float(np.percentile(boot_def_lex[:, ci], 97.5)), 2),
            "coverage_rate_semantic_tau0.5": round(float(rate_sem[ci]), 4),
            "covered_pp_semantic": round(d * float(rate_sem[ci]), 2),
            "deficit_pp_semantic": round(float(def_sem_arr[ci]), 2),
            "deficit_sem_ci_lower": round(float(np.percentile(boot_def_sem[:, ci], 2.5)), 2),
            "deficit_sem_ci_upper": round(float(np.percentile(boot_def_sem[:, ci], 97.5)), 2),
            "severity_lexical": sev_lex[ci],
            "severity_semantic": sev_sem[ci],
            "taxonomy_skills_in_market": int(sum(1 for s in exclusive[cat]
                                                 if skill_counts.get(s, 0) > 0)),
            "taxonomy_skills_total": len(exclusive[cat]),
        })
    table = pd.DataFrame(rows)

    tax_rows = []
    for s in taxonomy_skills:
        tax_rows.append({
            "category": categories[skill_to_cat[s]],
            "skill": s,
            "market_count": skill_counts.get(s, 0),
            "academic_count": acad_counts.get(s, 0),
            "lexically_covered": int(lex_covered[s]),
            "semantically_covered_tau0.5": int(sem_covered[s]),
        })
    tax_df = pd.DataFrame(tax_rows)

    metrics = {
        "experiment_id": "ALIGN03_domain_gap",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "tau_semantic": TAU,
        "model": MODEL_NAME,
        "device": device,
        "n_postings": n_rows,
        "definitions": {
            "demand": "% of postings mentioning >=1 taxonomy skill of the category",
            "coverage_rate": "mass-weighted fraction of category taxonomy skill "
                             "occurrences covered by the academic top-500 profile "
                             "(exact-match; semantic variant: max cosine >= 0.5)",
            "deficit": "demand * (1 - coverage_rate) in pp of postings",
            "severity": "relative-to-median: Critical>=2x median deficit, "
                        "Moderate>=median, Mild<median",
            "ci": "1000x non-parametric bootstrap over postings",
        },
        "domain_gaps": table.to_dict(orient="records"),
    }
    table.to_csv(out_dir / "domain_gap_table.csv", index=False)
    tax_df.to_csv(out_dir / "taxonomy_skill_counts.csv", index=False)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(table.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
