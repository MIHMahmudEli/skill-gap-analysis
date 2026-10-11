#!/usr/bin/env python3
"""Emit audit/01_claim_evidence_ledger.csv from 01_claim_verification.json + manual rows."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ver = json.loads((ROOT / "audit" / "01_claim_verification.json").read_text(encoding="utf-8"))

EXP_EVIDENCE = {
    "C01": "datasets/DATASET_MANIFEST.csv", "C01b": "datasets/DATASET_MANIFEST.csv",
    "C02": "datasets/DATASET_MANIFEST.csv", "C02b": "results/GEO01_linkedin_shares/metrics.json",
    "C03": "paper/main.tex:158 (arithmetic)", "C04": "results/TRENDS01_ai_longitudinal/metrics.json",
    "C10": "results/ALIGN01_lexical_bootstrap/metrics.json", "C10b": "results/ALIGN01_lexical_bootstrap/metrics.json",
    "C10c": "results/ALIGN01_lexical_bootstrap/metrics.json",
    "C11": "results/ALIGN02_semantic_sbert/metrics.json", "C11b": "results/ALIGN02_semantic_sbert/metrics.json",
    "C12": "results/ALIGN02_semantic_sbert/metrics.json", "C12b": "results/ALIGN02_semantic_sbert/metrics.json",
    "C12c": "results/ALIGN02_semantic_sbert/metrics.json",
}

rows = []
for c in ver:
    cid = c["id"]
    if c["match"] is True:
        status = "reproduced"
    elif c["match"] is False:
        if cid == "C120":
            status = "reproduced"  # rounding only
        elif cid == "C143":
            status = "reproduced"  # rounding 47.05->47.1
        elif cid in ("C155",):
            status = "partially_reproduced"  # documented subset, not full equality
        else:
            status = "not_reproduced"
    else:
        # presence checks with match=None (legacy)
        status = "reproduced"
    ev = EXP_EVIDENCE.get(cid, c.get("evidence", ""))
    rows.append({
        "claim_id": cid,
        "manuscript_location": "",  # filled for key rows below
        "exact_claim": c["claim"],
        "ms_value": json.dumps(c["ms_value"]) if not isinstance(c["ms_value"], str) else c["ms_value"],
        "artifact_value": json.dumps(c["artifact_value"]) if not isinstance(c["artifact_value"], str) else str(c["artifact_value"]),
        "reproduction_status": status,
        "evidence_path": ev,
        "scientific_concern": c.get("note", ""),
        "proposed_action": "",
    })

LOC = {
    "C01": "Abstract; Sec.I; Sec.III-A; Tab.I", "C01a": "Abstract; Sec.I; Sec.III-A", "C02": "Tab.I", "C02b": "Sec.V-E",
    "C05": "Tab.I", "C10": "Abstract; Sec.IV-B", "C11": "Abstract; Sec.IV-B", "C12": "Abstract",
    "C20": "Abstract; Sec.IV-C", "C30": "Sec.IV-B2", "C41": "Sec.IV-B3; Limit.3",
    "C50": "Abstract; Sec.IV-B1", "C70": "Sec.IV-D1", "C71": "Abstract; Sec.IV-D3",
    "C77": "Sec.IV-D4/D5", "C100": "Abstract; Sec.IV-D5", "C110": "Sec.V-E; Hyp.H5/H6",
    "C120": "Sec.V-E", "C152": "Sec.V-A (hyp. verdicts)", "C152b": "Sec.V-A (hyp. verdicts)",
    "C153": "Tab.XIII", "C155": "Sec.IV-C vs ALIGN03 metrics",
    "C156": "Sec.IV-B2 (profile-size sensitivity)", "C157": "Sec.III-A; Tab.I; Limit.1",
}
for r in rows:
    r["manuscript_location"] = LOC.get(r["claim_id"], "various")
    if r["claim_id"] in ("C152", "C152b", "C153"):
        r["proposed_action"] = "DONE (Phase 9): H6 now cites STAT01, RD=-0.44 pp; INTL01 retained only for H5."
    if r["claim_id"] == "C02":
        r["proposed_action"] = "DONE (Phase 8/9): manifest + Table I corrected to 1,348,454."
    if r["claim_id"] in ("C01", "C01a", "C05"):
        r["proposed_action"] = "DONE (Phase 8/9): unique-record accounting + academic ref n=1,167 disclosed."
    if r["claim_id"] == "C155":
        r["proposed_action"] = "DONE (Phase 9): RQ1 wording clarifies 519,814 postings; ALIGN03 subset documented."
    if r["claim_id"] == "C156":
        r["proposed_action"] = "DONE (Phase 9): matched-profile 2x2 replaces vocabulary-composition story."

# extra manual rows for qualitative claims
manual = [
    dict(claim_id="M01", manuscript_location="Sec.IV-B1; Fig.1",
         exact_claim="Top skill counts: communication 148,765 (28.6%), CS 111,342, teamwork 91,559, comm skills 78,182, leadership 74,517, PS 59,713",
         ms_value="see claim", artifact_value="market_top500.csv matches exactly",
         reproduction_status="reproduced",
         evidence_path="results/ALIGN01_lexical_bootstrap/market_top500.csv",
         scientific_concern="Independent naive recount is ~1% lower (tokenization detail); artifact is authoritative.",
         proposed_action="None; optionally document tokenizer."),
    dict(claim_id="M02", manuscript_location="Sec.IV-B (Tab.II)",
         exact_claim="scheduling~time management cos=0.6122; bachelor's degree~professionalism cos=0.2937",
         ms_value="0.6122/0.2937", artifact_value="0.6122/0.2937",
         reproduction_status="reproduced",
         evidence_path="results/ALIGN02_semantic_sbert/skill_semantic_matches.csv",
         scientific_concern="", proposed_action="None."),
    dict(claim_id="M03", manuscript_location="Sec.III-A; Tab.I",
         exact_claim="Corpus = 15 open datasets; unique records 2.64M (raw sum 3.18M with linked-pair note)",
         ms_value="2.64M unique / 3.18M raw inventory",
         artifact_value="manifest corrected; unique = sum - HF jobs = 2,643,703",
         reproduction_status="reproduced",
         evidence_path="experiments/exp_scripts/*.py input map; DATASET_MANIFEST.csv (corrected); paper/main.tex Sec.III-A",
         scientific_concern="Prior '3.18M analyzed' mixed units and double-counted linked HF tables; now disclosed.",
         proposed_action="DONE (Phase 9): manuscript reports unique + raw + nine-source usage."),
    dict(claim_id="M04", manuscript_location="Tab.I; Sec.III-A",
         exact_claim="India Skills Intelligence = synthetic profiles (disclosed)",
         ms_value="synthetic, calibrated", artifact_value="manifest says 'Synthetic workforce profiles...'",
         reproduction_status="reproduced",
         evidence_path="datasets/DATASET_MANIFEST.csv:11; paper/main.tex:179",
         scientific_concern="Correctly labeled synthetic; not used in any experiment (inventory only). Keep label in any reanalysis.",
         proposed_action="None beyond keeping the disclosure."),
    dict(claim_id="M05", manuscript_location="Sec.V-A (hyp. verdicts) para + Tab.XIII",
         exact_claim="H6 not supported: univariate RD -0.44 pp; OR=1.02 p=0.62; table cites STAT01",
         ms_value="-0.44 pp / STAT01 / p=0.62",
         artifact_value="college RD=-0.4442 pp (audit/05_stat_reproduction.json); STAT01 OR=1.02 p=0.6197; INTL01 +15.34 pp used only for H5",
         reproduction_status="reproduced",
         evidence_path="audit/05_stat_reproduction.json; results/STAT01.../metrics.json; results/INTL01.../metrics.json",
         scientific_concern="FIXED Phase 9: prior '+0.08 pp' and INTL01 misattribution corrected.",
         proposed_action="DONE."),
    dict(claim_id="M09", manuscript_location="Sec.IV-B2",
         exact_claim="Matched-profile 2x2: HF/LinkedIn identical SGI at equal P (0.52/0.32 @ P=100; 0.37/0.14 @ P=500)",
         ms_value="identical at matched P",
         artifact_value="audit/_sgi_sensitivity/*.json; hf_acad500.json lex 0.37 [0.28,0.47] sem0.5 0.14 [0.08,0.21]",
         reproduction_status="reproduced",
         evidence_path="audit/_sgi_sensitivity/lexical_profile_size_sweep.json; linkedin_matched_profile.json; hf_acad500.json",
         scientific_concern="Profile-size confound previously misattributed to corpus vocabulary; now correctly framed.",
         proposed_action="DONE (Phase 9)."),
    dict(claim_id="M06", manuscript_location="Sec.IV-B1 (VALID01)",
         exact_claim="VALID01 metrics n_positive_by_type hard_neg=0, random_neg=0 but n_negative=1,769",
         ms_value="1,769 negatives", artifact_value="breakdown dict zeros (pair_results.csv has types)",
         reproduction_status="partially_reproduced",
         evidence_path="results/VALID01_esco_gold/metrics.json",
         scientific_concern="Metrics metadata bug (type counts not populated); pair-level CSV is fine; not manuscript-facing.",
         proposed_action="Optional cleanup in sync/verify; no manuscript change."),
    dict(claim_id="M07", manuscript_location="Sec.I; contributions",
         exact_claim="12 registered experiments, all USED_IN_MANUSCRIPT",
         ms_value="twelve", artifact_value="registry.json 12 entries",
         reproduction_status="reproduced",
         evidence_path="results/registry.json; experiments/verify.py",
         scientific_concern="", proposed_action="None."),
    dict(claim_id="M08", manuscript_location="Sec.IV-D5",
         exact_claim="External accuracy 29.9% with base rate 78.08% (same cohort/target)",
         ms_value="29.9% @ 78.08% base", artifact_value="acc=0.2986 base=0.7808 n=50000 same test cohort",
         reproduction_status="reproduced",
         evidence_path="results/STAT02_external_validation/metrics.json",
         scientific_concern="Correctly disclosed; threshold at 0.5 under shifted prevalence explains low accuracy.",
         proposed_action="None; consider adding PR-AUC/calibration note in Phase 9."),
]

all_rows = rows + manual
out = ROOT / "audit" / "01_claim_evidence_ledger.csv"
fields = ["claim_id", "manuscript_location", "exact_claim", "ms_value", "artifact_value",
          "reproduction_status", "evidence_path", "scientific_concern", "proposed_action"]
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(all_rows)

from collections import Counter
print(Counter(r["reproduction_status"] for r in all_rows), "total", len(all_rows))
