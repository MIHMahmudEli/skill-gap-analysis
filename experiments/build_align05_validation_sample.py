"""ALIGN05 validation-sample builder (SAMPLING ONLY — no ALIGN05 execution).

Builds the stratified ~200-title hand-labelling CSV required by the ALIGN05
pre-registration (amendment 2026-10-12):

- frame: distinct normalized job titles in the primary corpus
  (datasets/hf_skill_gap_jobs.csv; title only, never skills)
- classifier: experiments/align05_title_rules_v1.json (v1, hashed in prereg)
- strata: predicted-tech vs predicted-non-tech
- sample: 100 per stratum, SRS without replacement, seed 42, deterministic
  frame order (titles sorted)
- weights: w_h = N_h / n_h (stratum population / stratum sample) so that
  design-weighted precision AND recall are estimable from the labelled CSV
- blinding (author instruction 2026-10-12): the labelling CSV carries ONLY
  sample_id, job_title, author_label — no predicted class, rule id, SOC code,
  stratum, or weight — and its row order is shuffled (fresh seed-42 draw).
  sample_ids are assigned in the shuffled order, so ID ranges carry no
  stratum information either. The design columns live in a separate key file
  that the author must not open until labelling is finished.

Output: labelling/align05_titles_200.csv (author_label left blank, blinded)
     + experiments/align05_titles_200_key.csv (DO NOT OPEN until finished).
Do NOT fill any labels here. Do NOT run ALIGN05 before the >=0.90 gate passes.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "experiments" / "align05_title_rules_v1.json"
FRAME = ROOT / "datasets" / "hf_skill_gap_jobs.csv"
OUT = ROOT / "labelling" / "align05_titles_200.csv"
SEED, N_PER_STRATUM = 42, 100

spec = json.loads(RULES.read_text(encoding="utf-8"))
negs = [re.compile(p, re.I) for p in spec["negations"]]
rules = [(r["id"], r["soc"], re.compile(r["pattern"], re.I)) for r in spec["rules"]]


def classify(title: str) -> tuple[str, str]:
    """-> (rule_id, soc). soc '' means predicted non-tech."""
    if any(p.search(title) for p in negs):
        return "NEG", ""
    for rid, soc, pat in rules:
        if pat.search(title):
            return rid, soc
    return "DEFAULT", ""


# frame: distinct normalized titles
titles = pd.read_csv(FRAME, usecols=["job_title"], dtype=str)["job_title"].dropna()
norm = titles.str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
uniq = sorted(set(norm))
print(f"postings={len(titles)} distinct normalized titles={len(uniq)}")

preds = [classify(t) for t in uniq]
df = pd.DataFrame({
    "job_title": uniq,
    "rule_matched": [p[0] for p in preds],
    "predicted_soc": [p[1] for p in preds],
})
df["predicted_tech"] = (df["predicted_soc"] != "").astype(int)
df["stratum"] = np.where(df.predicted_tech == 1, "predicted_tech", "predicted_nontech")

N_tech = int(df.predicted_tech.sum())
N_non = len(df) - N_tech
print(f"N_tech={N_tech} ({100*N_tech/len(df):.1f}%) N_nontech={N_non}")
if N_tech < N_PER_STRATUM or N_non < N_PER_STRATUM:
    raise SystemExit("stratum smaller than 100 — v1 rule set must be fixed before sampling")

rng = np.random.RandomState(SEED)
pieces = []
for h, n_h in [("predicted_tech", N_tech), ("predicted_nontech", N_non)]:
    idx = np.flatnonzero((df.stratum == h).values)
    pick = rng.choice(idx, size=N_PER_STRATUM, replace=False)
    part = df.iloc[np.sort(pick)].copy()
    part["sampling_weight"] = n_h / N_PER_STRATUM
    pieces.append(part)
out = pd.concat(pieces).sort_values(["stratum", "job_title"]).reset_index(drop=True)

# --- blinding step: shuffle row order (fresh seed-42 draw), assign sample_ids
# in the shuffled order so the ID ranges reveal nothing about strata.
rng_shuf = np.random.RandomState(SEED)
out = out.iloc[rng_shuf.permutation(len(out))].reset_index(drop=True)
out.insert(0, "sample_id", [f"A5T{i:03d}" for i in range(1, len(out) + 1)])
out["author_label"] = ""  # LEFT BLANK — author fills (tech / non-tech)

KEY = ROOT / "experiments" / "align05_titles_200_key.csv"  # DO NOT OPEN until labelling is finished

OUT.parent.mkdir(parents=True, exist_ok=True)
blinded = out[["sample_id", "job_title", "author_label"]]
key = out[["sample_id", "stratum", "sampling_weight", "rule_matched",
           "predicted_soc", "predicted_tech"]]
blinded.to_csv(OUT, index=False)
key.to_csv(KEY, index=False)

print(f"wrote {OUT} rows={len(blinded)} (blinded: {list(blinded.columns)})")
print(f"wrote {KEY} rows={len(key)} (sealed key; do not open before labelling is finished)")
print("weights:", {h: float(g.sampling_weight.iloc[0]) for h, g in out.groupby('stratum')})
print("rule usage in sample:", out.rule_matched.value_counts().to_dict())
print("rules_sha256:", hashlib.sha256(RULES.read_bytes()).hexdigest())
print("frame_size:", len(uniq), "N_tech:", N_tech, "N_nontech:", N_non)
