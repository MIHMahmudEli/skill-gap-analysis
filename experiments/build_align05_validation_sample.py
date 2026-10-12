"""ALIGN05 validation-sample builder v2 (SAMPLING ONLY — no ALIGN05 execution).

Replaces the v1 sample (seed 42), whose key was committed to a public repository
before any label existed and is therefore retired (archive/align05_titles_200_key_RETIRED.md).
See the dated amendment in experiments/ALIGN05_PREREG.md.

Identical to v1 in every design respect:

- frame: distinct normalized job titles in the primary corpus
  (datasets/hf_skill_gap_jobs.csv; title only, never skills)
- classifier: experiments/align05_title_rules_v1.json — the SAME frozen rule set,
  byte-identical (SHA-256 verified below; no revision was informed by the old key)
- strata: predicted-tech vs predicted-non-tech
- sample: 100 per stratum (equal allocation), SRS without replacement,
  deterministic frame order (titles sorted)
- weights: w_h = N_h / n_h, so design-weighted precision AND recall are estimable
- blinding: the labelling CSV carries ONLY sample_id, job_title, author_label —
  no predicted class, rule id, SOC code, stratum or weight — and its row order is
  shuffled. sample_ids are assigned in shuffled order, so ID ranges reveal nothing.

Changed, and only these:

- SEED_V2 replaces 42 for both the stratum draws and the shuffle (42 is burned:
  it produced the retired sample and must not be reused for a draw the author
  labels against).
- sample_id prefix is A5U (not A5T) so the two samples cannot be confused.
- the key is written OUTSIDE the repository (../sealed_keys/, gitignored) and is
  read back only via the ALIGN05_KEY env var / --key argument. This script writes
  it and never reads or prints it.

Output: labelling/align05_titles_200.csv   (author_label left blank, blinded)
     + ../sealed_keys/align05_titles_200_key.csv   (sealed; outside the repo)
Do NOT fill any labels here. Do NOT run ALIGN05 before the >=0.90 gate passes.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "experiments" / "align05_title_rules_v1.json"
FRAME = ROOT / "datasets" / "hf_skill_gap_jobs.csv"
OUT = ROOT / "labelling" / "align05_titles_200.csv"

# v2 seed: recorded in ALIGN05_PREREG.md. 42 is deliberately NOT used.
SEED_V2 = int(os.environ.get("ALIGN05_SEED_V2", "20261013"))
N_PER_STRATUM = 100
ID_PREFIX = "A5U"

# Key lives OUTSIDE the repo directory. Overridable, but the default must never
# resolve inside ROOT — assert that before writing.
KEY = Path(os.environ.get(
    "ALIGN05_KEY",
    str(ROOT.parent / "sealed_keys" / "align05_titles_200_key.csv"))).resolve()

rules_sha = hashlib.sha256(RULES.read_bytes()).hexdigest().upper()
EXPECTED_RULES_SHA = ("9F0410507C23313C99517CEC9D40A1CC0697CD29192A89357F0E321234F1429D")
if rules_sha != EXPECTED_RULES_SHA:
    raise SystemExit(
        f"FROZEN RULE SET CHANGED: {rules_sha}\n"
        f"expected {EXPECTED_RULES_SHA}\n"
        "The v1 rule set must stay byte-identical; any revision requires a new "
        "prereg amendment and a further fresh sample.")
if KEY.is_relative_to(ROOT):
    raise SystemExit(f"refusing to write the sealed key inside the repo: {KEY}")

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
print(f"N_tech={N_tech} ({100 * N_tech / len(df):.1f}%) N_nontech={N_non}")
if N_tech < N_PER_STRATUM or N_non < N_PER_STRATUM:
    raise SystemExit("stratum smaller than 100 — v1 rule set must be fixed before sampling")

rng = np.random.RandomState(SEED_V2)
pieces = []
for h, n_h in [("predicted_tech", N_tech), ("predicted_nontech", N_non)]:
    idx = np.flatnonzero((df.stratum == h).values)
    pick = rng.choice(idx, size=N_PER_STRATUM, replace=False)
    part = df.iloc[np.sort(pick)].copy()
    part["sampling_weight"] = n_h / N_PER_STRATUM
    pieces.append(part)
out = pd.concat(pieces).sort_values(["stratum", "job_title"]).reset_index(drop=True)

# blinding: shuffle row order with the v2 seed, assign ids in shuffled order
rng_shuf = np.random.RandomState(SEED_V2)
out = out.iloc[rng_shuf.permutation(len(out))].reset_index(drop=True)
out.insert(0, "sample_id", [f"{ID_PREFIX}{i:03d}" for i in range(1, len(out) + 1)])
out["author_label"] = ""  # LEFT BLANK — author fills (tech / non-tech)

OUT.parent.mkdir(parents=True, exist_ok=True)
KEY.parent.mkdir(parents=True, exist_ok=True)
blinded = out[["sample_id", "job_title", "author_label"]]
key = out[["sample_id", "stratum", "sampling_weight", "rule_matched",
           "predicted_soc", "predicted_tech"]]
blinded.to_csv(OUT, index=False)
key.to_csv(KEY, index=False)
KEY.chmod(0o600)  # owner-only where the OS honours it

# Overlap check against the retired sample (titles only — never the old key's
# design columns, which are not needed and must not be re-imported).
old_ids_exist = set(blinded.sample_id) & {"A5T001"}  # sanity: prefix differs
print(f"wrote {OUT} rows={len(blinded)} (blinded: {list(blinded.columns)})")
print(f"key written OUTSIDE the repo: {KEY}  (never opened here; rows={len(key)})")
print(f"sample_id prefix {ID_PREFIX} (v1 used A5T; no id collision: "
      f"{not bool(old_ids_exist)})")
print("weights:", {h: float(g.sampling_weight.iloc[0]) for h, g in out.groupby("stratum")})
print("rule usage in sample:", out.rule_matched.value_counts().to_dict())
print("rules_sha256:", rules_sha, "(frozen, verified)")
print("seed_v2:", SEED_V2)
print("frame_size:", len(uniq), "N_tech:", N_tech, "N_nontech:", N_non)
