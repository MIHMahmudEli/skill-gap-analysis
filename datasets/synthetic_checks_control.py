#!/usr/bin/env python3
"""REAL-data control for the generator-signature checks.

Runs the *same* functions and the *same* analyst-chosen thresholds used by
datasets/synthetic_checks.py on a genuine corpus (the 1,348,454-row LinkedIn
2024 scrape), so that a reader can see what a real dataset looks like against
the screen.  Output sits next to the audited-dataset output:

    datasets/synthetic_checks_control_linkedin.json

What the control establishes (author ruling, 2026-10-12):

  * uniformity   -- fires on NOTHING real here: every low-cardinality column
                    rejects uniformity (p = 0, balance ratios 8 to 913).  A
                    non-rejection is therefore genuinely unusual, but it is
                    still compatible with quota/design-based sampling.
  * binary       -- the real flags are 96.3% / 96.1% / 0.1%, far from a coin
                    flip, so the family does not fire.  Note the schema gap:
                    the real columns are t/f strings, not 0/1 numerics, so the
                    check reports "not applicable" unless they are mapped.
  * coupling     -- FALSE POSITIVE on real data.  got_summary ~ got_ner gives
                    V = 0.985 because both are the scraper's own processing
                    flags, coupled by construction.  Only non-pipeline pairs
                    are interpretable.
  * id_sequence  -- does not discriminate.  The real corpus has opaque
                    trailing counters inside URLs, so the templated-counter
                    test does not fire, while real systems also use plain
                    sequential primary keys.  It is not counted towards any
                    evidence tier.
  * missingness  -- FALSE POSITIVE near zero.  job_location has 19 missing
                    values of 1,348,454 (1.4e-5); the share tolerance is an
                    absolute 0.01, so observed and expected both round to 0.0
                    and the independence term alone decides the flag.

Columns were chosen by schema before looking at outcomes: every low-cardinality
categorical (<= 20 levels), the three boolean pipeline flags, four column pairs,
the URL id column, and every column with any missingness.

Usage:  python datasets/synthetic_checks_control.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_checks import (  # noqa: E402
    ALPHA,
    BINARY_BALANCE_EPS,
    BALANCE_RATIO_MAX,
    COUPLING_V,
    binary_balance,
    cramers_v,
    id_sequence,
    missingness_pattern,
    uniformity_chi2,
)

ROOT = Path(__file__).resolve().parents[1]
LINKEDIN = (ROOT / "datasets" / "kaggle" / "1-3m-linkedin-jobs-and-skills-2024"
            / "linkedin_job_postings.csv")
OUT = ROOT / "datasets" / "synthetic_checks_control_linkedin.json"

CATEGORICAL = ["got_summary", "got_ner", "is_being_worked", "first_seen",
               "search_country", "job_level", "job_type"]
BINARY_FLAGS = ["got_summary", "got_ner", "is_being_worked"]
COUPLE = [("job_level", "job_type"), ("search_country", "job_type"),
          ("got_summary", "got_ner"), ("first_seen", "search_country")]
MISSINGNESS = [("company", "search_country"), ("job_location", "search_country")]


def run() -> dict:
    df = pd.read_csv(LINKEDIN, low_memory=False)
    out: dict = {
        "generated_by": "datasets/synthetic_checks_control.py",
        "corpus": str(LINKEDIN.relative_to(ROOT)),
        "rows": len(df),
        "role": ("REAL control: genuine web-scraped postings run through the "
                 "identical generator-signature checks and thresholds, so the "
                 "audited-file flags can be read against a known-real baseline"),
        "alpha": ALPHA,
        "coupling_v_threshold": COUPLING_V,
        "balance_ratio_max": BALANCE_RATIO_MAX,
        "binary_balance_eps": BINARY_BALANCE_EPS,
        "thresholds_status": ("analyst-chosen, not pre-registered; the checks are "
                              "descriptive screening, not a hypothesis test of "
                              "synthetic origin"),
        "checks": {},
        "false_positive_families": [
            {"family": "coupling",
             "example": "got_summary ~ got_ner",
             "why": ("both columns are the scraper's own processing flags, so they are "
                     "coupled by construction; Cramer's V >= 0.95 on real data. Only "
                     "non-pipeline column pairs are interpretable.")},
            {"family": "missingness",
             "example": "job_location",
             "why": ("19 missing values of 1,348,454 (share 1.4e-5); the share test uses "
                     "an absolute 0.01 tolerance, so observed and expected both round to "
                     "0.0 and only the independence term decides the flag.")},
        ],
        "non_discriminating_families": [
            {"family": "id_sequence",
             "why": ("fires on 9 of the 10 audited files and does not fire here, yet real "
                     "systems routinely use sequential primary keys and this corpus embeds "
                     "opaque trailing counters in its URLs. Recorded for completeness; not "
                     "counted towards any evidence tier.")},
        ],
    }

    for c in CATEGORICAL:
        if c in df.columns:
            out["checks"][f"uniformity::{c}"] = uniformity_chi2(df[c])
    for c in BINARY_FLAGS:
        if c in df.columns:
            out["checks"][f"binary::{c} (as-is; t/f schema)"] = binary_balance(df[c])
            out["checks"][f"binary::{c} (LABELLED t/f->1/0 mapping)"] = \
                binary_balance(df[c].map({"t": 1, "f": 0}))
    for a, b in COUPLE:
        if a in df.columns and b in df.columns:
            out["checks"][f"coupling::{a}~{b}"] = cramers_v(df[a], df[b])
    if "job_link" in df.columns:
        out["checks"]["ids::job_link"] = id_sequence(df["job_link"])
    for m, comp in MISSINGNESS:
        if m in df.columns and comp in df.columns:
            out["checks"][f"missingness::{m}|{comp}"] = missingness_pattern(df[m], df[comp])

    def _fired(r: dict) -> bool:
        return any(v is True for k, v in r.items()
                   if k.endswith("_consistent") or k == "near_deterministic_coupling")

    n_flags = sum(1 for r in out["checks"].values() if _fired(r))
    out["families_flagged"] = n_flags
    return out


def main() -> int:
    if not LINKEDIN.exists():
        print(f"MISSING control corpus: {LINKEDIN}")
        return 2
    out = run()
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False), encoding="utf-8")
    print(f"wrote {OUT} rows={out['rows']} checks={len(out['checks'])} "
          f"families_flagged={out['families_flagged']}")
    for name, r in out["checks"].items():
        hits = [k for k, v in r.items() if v is True
                and (k.endswith("_consistent") or k == "near_deterministic_coupling")]
        print(f"  {name:52s} -> {hits or ['no-flag']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
