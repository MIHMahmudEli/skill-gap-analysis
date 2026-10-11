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
        elif cid == "C152b":
            status = "contradicted"
        else:
            status = "not_reproduced"
    else:
        # presence checks
        if cid == "C152":
            status = "contradicted"  # number present but unsupported
        elif cid == "C153":
            status = "contradicted"  # misattribution
        elif cid == "C155":
            status = "partially_reproduced"
        else:
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
    "C01": "Abstract; Sec.I; Sec.III-A; Tab.I", "C02": "Tab.I", "C02b": "Sec.V-E",
    "C10": "Abstract; Sec.IV-B", "C11": "Abstract; Sec.IV-B", "C12": "Abstract",
    "C20": "Abstract; Sec.IV-C", "C30": "Sec.IV-B2", "C41": "Sec.IV-B3; Limit.3",
    "C50": "Abstract; Sec.IV-B1", "C70": "Sec.IV-D1", "C71": "Abstract; Sec.IV-D3",
    "C77": "Sec.IV-D4/D5", "C100": "Abstract; Sec.IV-D5", "C110": "Sec.V-E; Hyp.H5/H6",
    "C120": "Sec.V-E", "C152": "Sec.V-A (hyp. verdicts)", "C152b": "Sec.V-A (hyp. verdicts)",
    "C153": "Tab.XIII", "C155": "Sec.IV-C vs ALIGN03 metrics",
}
for r in rows:
    r["manuscript_location"] = LOC.get(r["claim_id"], "various")
    if r["claim_id"] in ("C152", "C152b"):
        r["proposed_action"] = ("Fix: replace '+0.08 pp' with computed college-cohort RD "
                                "(-0.44 pp; STAT01 multivariate OR=1.02, p=0.62 ns) or drop the number.")
    if r["claim_id"] == "C153":
        r["proposed_action"] = ("Fix: cite STAT01 (not INTL01) for H6; INTL01 internship contrast is "
                                "significant (+15.34 pp) and supports a different hypothesis.")
    if r["claim_id"] == "C02":
        r["proposed_action"] = "Investigate 56-row gap vs GEO01 (1,348,510 vs 1,348,454) in Phase 2."
    if r["claim_id"] == "C155":
        r["proposed_action"] = ("Document that ALIGN03 posting count (518,953) is the analyzed subset "
                                "of the 519,814-row skills table; align wording.")
    if r["claim_id"] == "C01":
        r["proposed_action"] = ("Phase 2: verify whether HF jobs+skills rows are linked views of the "
                                "same postings (double-count in 3,176,266 headline).")

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
         exact_claim="Corpus = 15 datasets, 3,176,266 records, analyzed",
         ms_value="3,176,266 across 15", artifact_value="manifest sum=3,176,266; ~9 datasets feed experiments",
         reproduction_status="partially_reproduced",
         evidence_path="experiments/exp_scripts/*.py input map; DATASET_MANIFEST.csv",
         scientific_concern=("Six datasets (HF jobs table, USA market, career-change, AI 15K, India skills, "
                              "NGESS, fresher) are inventory-only; HF jobs+skills are linked tables of the same "
                              "postings (~519,841 unique), so '3.18M records' mixes units and double-counts."),
         proposed_action="Phase 2/9: restate as '15 archived datasets; N_analyzed = X postings + Y student records'."),
    dict(claim_id="M04", manuscript_location="Tab.I; Sec.III-A",
         exact_claim="India Skills Intelligence = synthetic profiles (disclosed)",
         ms_value="synthetic, calibrated", artifact_value="manifest says 'Synthetic workforce profiles...'",
         reproduction_status="reproduced",
         evidence_path="datasets/DATASET_MANIFEST.csv:11; paper/main.tex:179",
         scientific_concern="Correctly labeled synthetic; not used in any experiment (inventory only). Keep label in any reanalysis.",
         proposed_action="None beyond keeping the disclosure."),
    dict(claim_id="M05", manuscript_location="Sec.V-A (hyp. verdicts) para + Tab.XIII",
         exact_claim="H6 not supported: risk difference +0.08 pp, p=0.62; table cites INTL01",
         ms_value="+0.08 pp / INTL01 / p=0.62",
         artifact_value="college RD=-0.44 pp (computed); STAT01 OR=1.02 p=0.6197; INTL01 RD=+15.34 pp p~0",
         reproduction_status="contradicted",
         evidence_path="datasets/kaggle/college-student-placement/college_student_placement_dataset.csv (computed 2026-10-11); results/STAT01.../metrics.json; results/INTL01.../metrics.json",
         scientific_concern="Two defects: (a) '+0.08 pp' matches no artifact (true univariate RD=-0.44 pp); (b) experiment misattribution INTL01 vs STAT01.",
         proposed_action="Fix in Phase 9: H6 verdict -> 'Not supported (STAT01: OR=1.02, p=0.62; univariate RD=-0.44 pp)'."),
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
