#!/usr/bin/env python3
"""Compute SGI + CI for HF market top-100 vs academic top-500 (audit Phase 10 table).

Same definitions as ALIGN01 (lexical) / ALIGN02 (semantic): seed 42, 1000x
bootstrap over the length-100 coverage indicator vector; SGI = 1 - coverage.
"""
import json, sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
from common import resolve_input, SEED, BOOTSTRAP_N, SBERT_MODEL

skills = pd.read_csv(resolve_input("market_skills"))
acad = pd.read_csv(resolve_input("academic_skills"))

mkt = Counter()
for v in skills["job_skills"].dropna():
    mkt.update(t.strip().lower() for t in str(v).split(",") if t.strip())
aca = Counter()
for s in acad["job_skill_set"].dropna():
    s = str(s).strip().strip("[]").replace("'", "")
    aca.update(t.strip().lower() for t in s.split(",") if t.strip())

market_top = [t for t, _ in mkt.most_common(100)]
acad_top = [t for t, _ in aca.most_common(500)]
academic_set = set(acad_top)
print("acad sample:", acad_top[:5], "| n_acad_unique:", len(aca))

# Lexical (ALIGN01 definition)
indicator = np.array([1.0 if s in academic_set else 0.0 for s in market_top])
rng = np.random.RandomState(SEED)
boot_cov = [float(np.mean(rng.choice(indicator, size=100, replace=True)))
            for _ in range(BOOTSTRAP_N)]
lex_lo, lex_hi = np.percentile(boot_cov, [2.5, 97.5])
lex_sgi = 1.0 - indicator.mean()
lex_ci = [round(1.0 - lex_hi, 4), round(1.0 - lex_lo, 4)]
print("HF acad500 lexical SGI", round(lex_sgi, 4), lex_ci)

# Semantic (ALIGN02 definition)
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer(SBERT_MODEL)
emb_m = model.encode(market_top, convert_to_numpy=True)
emb_a = model.encode(acad_top, convert_to_numpy=True)
max_sims = cosine_similarity(emb_m, emb_a).max(axis=1)

sem = {}
for tau in [0.4, 0.5, 0.6, 0.7]:
    covered = (max_sims >= tau).astype(float)
    rng = np.random.RandomState(SEED)
    boot = [1.0 - float(np.mean(rng.choice(covered, size=len(covered), replace=True)))
            for _ in range(BOOTSTRAP_N)]
    lo, hi = np.percentile(boot, [2.5, 97.5])
    sgi = 1.0 - covered.mean()
    print(f"HF acad500 sem tau={tau}: SGI={sgi:.4f} CI=[{lo:.4f}, {hi:.4f}]")
    sem[str(tau)] = {"sgi": round(float(sgi), 4), "ci": [round(float(lo), 4), round(float(hi), 4)]}

out = {
    "market_K": 100, "academic_P": 500, "seed": SEED, "bootstrap_n": BOOTSTRAP_N,
    "model": SBERT_MODEL,
    "lexical_sgi": round(float(lex_sgi), 4),
    "lexical_ci": lex_ci,
    "semantic": sem,
}
Path("audit/_sgi_sensitivity/hf_acad500.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print("wrote audit/_sgi_sensitivity/hf_acad500.json")
