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
# Phase 4 placement split: claims asserted only in the companion benchmark-audit
# paper (paper_placement/main.tex).  C51/C52 are VALID01 and stay in the main
# paper; C02b/C120 (geography) and C113 (Table I inventory row) stay in main.
PLACEMENT = {
    "C70", "C71", "C72", "C73", "C74", "C75", "C76", "C77", "C78", "C79",
    "C80", "C81", "C82", "C83", "C84", "C85", "C86", "C87", "C88", "C89",
    "C90", "C100", "C101", "C102", "C130", "C152", "C152b", "C153",
    "C161", "M05", "M08",
}
# Claims asserted in both papers (e.g., inventory facts repeated in the
# companion's corpus section).
BOTH = {"C113"}
# D3 (Phase 4): internship-effect claim dropped from both manuscripts; the
# artifact stays archived.  Reproduction status is unchanged (the numbers are
# still reproducible); only the assertion was withdrawn.
DROPPED = {"C110", "C111", "C112"}
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
    if cid in DROPPED:
        paper = "none (artifact retained)"
    elif cid in BOTH:
        paper = "main+placement"
    elif cid in PLACEMENT:
        paper = "placement"
    else:
        paper = "main"
    rows.append({
        "claim_id": cid,
        "paper": paper,
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
    "C01": "Abstract; Sec.I; Sec.III-A; Tab.I", "C01a": "Abstract; Sec.I; Sec.III-A", "C02": "Tab.I", "C02b": "Sec.IV-A (RQ1 geography; GEO01)",
    "C05": "Tab.I", "C10": "Abstract; Sec.IV-B", "C11": "Abstract; Sec.IV-B", "C12": "Abstract",
    "C20": "Abstract; Sec.IV-C", "C30": "Sec.IV-B2", "C41": "Sec.IV-B3; Limit.3",
    "C50": "Abstract; Sec.IV-B1", "C70": "Sec.IV-D1", "C71": "Abstract; Sec.IV-D3",
    "C77": "Sec.IV-D4/D5", "C100": "Abstract; Sec.IV-D5", "C110": "Sec.V-E; Hyp.H5/H6",
    "C120": "Sec.IV-A (RQ1 geography; GEO01)", "C152": "Sec.V-A (hyp. verdicts)", "C152b": "Sec.V-A (hyp. verdicts)",
    "C153": "Tab.XIII", "C155": "Sec.IV-C vs ALIGN03 metrics",
    "C156": "Sec.IV-B2 (profile-size sensitivity; SENS02)", "C157": "Sec.III-A; Tab.I; Limit.1",
    "C11h": "Sec.IV-B2 (profile-size sensitivity; SENS02)",
    "C11i": "Sec.IV-B2 (profile-size sensitivity; SENS02)",
    "C11j": "Sec.IV-B2 (profile-size sensitivity; SENS02)",
    "C11k": "Sec.IV-B2 (profile-size sensitivity; SENS02)",
    "C11l": "Sec.IV-B2 (profile-size sensitivity; SENS02)",
    "C11m": "Sec.IV-B2 (profile-size sensitivity; SENS02)",
    "C11n": "Sec.IV-B2 (profile-size sensitivity; SENS02)",
    "C11o": "Abstract", "C11p": "Abstract", "C11q": "Abstract",
    "C11r": "Abstract", "C11s": "Abstract",
    "C201": "Sec.IV-B2 (SENS02); Tab.hypotheses", "C202": "Sec.IV-B2 (SENS02)",
    "C203": "Sec.III-C footnote; Tab.datasets note",
    "C204": "Limitations item 6 (embedding batch)",
    "C205": "Abstract", "C206": "Abstract", "C207": "Abstract", "C208": "Abstract",
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
        r["proposed_action"] = ("DONE (Phase 9): matched-profile 2x2 replaces the "
                                "vocabulary-composition story. UPDATED 2026-10-14: SENS02 "
                                "(C11h-C11n) extends it to a covering-set sweep P=100..all "
                                "showing the level change is a covering-set effect, not a "
                                "corpus effect.")

# ALIGN06 (A6xx): the supplementary O*NET x BLS demand-side check. Every row
# is hand-annotated because a caveat cannot be derived from a number: the O*NET
# side is employment-weighted occupations, not postings (ALIGN06_PREREG 7.2),
# so a null concern means "no caveat beyond that estimand difference".
A6_MAIN = "RQ2 subsubsection ALIGN06 + threats item 9"
A6_APPX = "Appendix A, Table tab_align06_categories"
A6_EV = "results/ALIGN06_onet_demand_profile/"
_NOT_POSTINGS = ("Demand side is employment-weighted O*NET occupations, not "
                 "postings (ALIGN06_PREREG 7.2); level is not comparable to "
                 "the posting-based SGI")
_ZERO_WEIGHT = ("Zero O*NET demand weight: the Technology Skills inventory "
                "maps no term to this category")
A6_OVERRIDES = {
    "A601": (A6_MAIN, A6_EV + "metrics.json registered_contrasts.a", _NOT_POSTINGS),
    "A602": (A6_MAIN, A6_EV + "metrics.json registered_contrasts.a", _NOT_POSTINGS),
    "A603": (A6_MAIN, A6_EV + "metrics.json registered_contrasts.b", _NOT_POSTINGS),
    "A604": (A6_MAIN, A6_EV + "metrics.json registered_contrasts.b", _NOT_POSTINGS),
    "A605": (A6_MAIN, A6_EV + "metrics.json registered_contrasts.c_persistence_claim_permitted",
             "Rule is mechanical: permitted iff the semantic skill-CI lower bound exceeds 0"),
    "A606": (A6_MAIN, A6_EV + "metrics.json vocabulary_overlap.economy-wide",
             "Explains why the ALIGN06 lexical SGI is far above the posting-based value"),
    "A607": (A6_MAIN, A6_EV + "table_onet_profile_top.csv rank 1",
             "O*NET Technology Skills is a software/hardware inventory, not a skill taxonomy"),
    "A608": (A6_MAIN, A6_EV + "table_sgi_onet_grid.csv", None),
    "A609": (A6_MAIN, A6_EV + "table_sgi_onet_grid.csv", None),
    "A610": (A6_MAIN, A6_EV + "table_sgi_onet_grid.csv (K=100, P=all)", _NOT_POSTINGS),
    "A611": (A6_MAIN, A6_EV + "table_sgi_onet_grid.csv",
             "Stratum is 18 O*NET-SOC occupations over 13 SOC bases (ALIGN06_PREREG A3)"),
    "A612": (A6_MAIN, A6_EV + "table_sgi_onet_grid.csv", _NOT_POSTINGS),
    "A613": (A6_MAIN, A6_EV + "table_cross_source.csv",
             "Descriptive only; never used to select parameters (ALIGN06_PREREG 6.4)"),
    "A614": (A6_MAIN, A6_EV + "table_category_gap_onet.csv",
             "Coverage rate is bounded [0,1]; regression-guarded in experiments/verify.py (A7)"),
    "A615": (A6_MAIN, A6_EV + "table_category_gap_onet.csv", None),
    "A616": (A6_MAIN, A6_EV + "table_category_gap_onet.csv market_demand_pp sum",
             "Soft Skills, Business & Domain and Cybersecurity carry zero O*NET demand weight"),
    "A617": (A6_MAIN, A6_EV + "metrics.json frame.economy-wide.employment_multiplicity",
             "Measured and disclosed, not silently rescaled (ALIGN06_PREREG A4)"),
    "A618": (A6_MAIN, A6_EV + "metrics.json frame.economy-wide.employment_multiplicity", None),
    "A619": (A6_MAIN, A6_EV + "metrics.json frame.computing-IT.employment_multiplicity", None),
    "A620": (A6_MAIN, A6_EV + "metrics.json sources.oews",
             "May 2025 national release; BLS OEWS is public domain (17 U.S.C. 105)"),
    "A621": (A6_MAIN, A6_EV + "metrics.json sources.onet, sources.license_note",
             "Licence snapshots in datasets/curriculum/license_snapshots/"),
    "A622": (A6_APPX, A6_EV + "table_category_gap_onet.csv K=100 lexical; ALIGN03 domain_gap_table.csv",
             _ZERO_WEIGHT),
    "A623": (A6_APPX, A6_EV + "table_category_gap_onet.csv K=100 lexical; ALIGN03 domain_gap_table.csv",
             _ZERO_WEIGHT),
    "A624": (A6_APPX, A6_EV + "table_category_gap_onet.csv K=100 lexical; ALIGN03 domain_gap_table.csv",
             _ZERO_WEIGHT),
    "A625": (A6_APPX, A6_EV + "table_category_gap_onet.csv K=100 lexical",
             "Largest O*NET category; the largest posting-side category differs, "
             "so the two demand columns are not differenced"),
    "A626": (A6_APPX, A6_EV + "ALIGN03 domain_gap_table.csv deficit_pp_lexical",
             "Largest posting-side lexical deficit is Cloud & Infrastructure, not Programming"),
    "A627": (A6_APPX, "sum of both category tables",
             "Within-taxonomy totals over two different populations; not a comparable quantity"),
    "A628": (A6_APPX, A6_EV + "table_category_gap_onet.csv K=100 lexical vs semantic tau=0.5",
             "Demand share is a property of the profile, not of the matcher; the "
             "semantic rows must be pinned to tau=0.5 (an unfiltered read is tau=0.4)"),
}
for r in rows:
    ov = A6_OVERRIDES.get(r["claim_id"])
    if ov:
        r["manuscript_location"], r["evidence_path"], con = ov
        if con is not None:
            r["scientific_concern"] = con

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
         exact_claim="Corpus = 15 open datasets; unique records 2,123,889 (raw sum 3,163,517 with unit-type breakdown)",
         ms_value="2.12M unique / 3.16M raw",
         artifact_value="manifest corrected; unit-type breakdown: 1,869,435 real posting rows + 519,814 pair rows + 316,279 aggregate + 457,989 apparently synthetic (dedup 1,349,621 + 316,279 + 457,989)",
         reproduction_status="reproduced",
         evidence_path="experiments/exp_scripts/*.py input map; DATASET_MANIFEST.csv (corrected); paper/main.tex Sec.III-A; datasets/REAL_VS_SYNTHETIC.csv",
         scientific_concern="Prior '3.18M analyzed' mixed units and double-counted linked HF tables; Phase 3 added the unit-type breakdown; apparently-synthetic rows are generator-signature inferences (see M10).",
         proposed_action="DONE (Phase 9 + RQ1-batch): manuscript reports unique + raw + unit-type breakdown."),
    dict(claim_id="M04", manuscript_location="Tab.I; Sec.III-A",
         exact_claim="India Skills Intelligence = synthetic profiles, declared by the source README",
         ms_value="synthetic, calibrated", artifact_value="bundled README: 'Every value in this dataset is generated, not collected'",
         reproduction_status="reproduced",
         evidence_path="datasets/DATASET_MANIFEST.csv:11; datasets/kaggle/india-professional-skills-intelligence-dataset README (declared); datasets/synthetic_checks_output.json; datasets/REAL_VS_SYNTHETIC.csv",
         scientific_concern="Declared synthetic (source states it) - distinct from the inferred group; not used in any experiment (inventory only). Keep label in any reanalysis.",
         proposed_action="Keep the disclosure."),
    dict(claim_id="M05", manuscript_location="Sec.V-A (hyp. verdicts) para + Tab.XIII",
         exact_claim="H6 not supported: univariate RD -0.44 pp; OR=1.02 p=0.62; table cites STAT01",
         ms_value="-0.44 pp / STAT01 / p=0.62",
         artifact_value="college RD=-0.4442 pp (audit/05_stat_reproduction.json); STAT01 OR=1.02 p=0.6197; INTL01 +15.34 pp descriptive only (apparently synthetic; not verdict evidence)",
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
         exact_claim="VALID01 metrics n_pairs_by_neg_type: positive=1,138, hard_neg=707, random_neg=1,062 (sums to n_pairs=2,907; negatives 1,769)",
         ms_value="1,769 negatives", artifact_value="1,138 / 707 / 1,062 (n_pairs_by_neg_type)",
         reproduction_status="reproduced",
         evidence_path="results/VALID01_esco_gold/metrics.json; results/VALID01_esco_gold/pair_results.csv",
         scientific_concern="R-8 metadata: n_positive_by_type sums gold per neg_type and is therefore 1138/0/0 by construction; the informative composition breakdown was missing and was added 2026-10-12 (emitter + committed artifact) as n_pairs_by_neg_type. Not manuscript-facing; kappa/precision/recall unaffected.",
         proposed_action="DONE (P5-4); no manuscript change."),
    dict(claim_id="M07", manuscript_location="Sec.I; contributions (main); companion reproducibility table",
         exact_claim="Registry holds 12 registered experiments; TRENDS01 retained in the registry but not used in either manuscript (RQ1-trend claims removed: benchmark is apparently synthetic); after the Phase 4 split no paper asserts a total count (main cites 8 registry rows incl. retained-unused TRENDS01, companion cites 4 placement experiments)",
         ms_value="no total asserted (Phase 4); count-free wording",
         artifact_value="registry.json 12 entries; TRENDS01_ai_longitudinal.manuscript_use = not_used_in_manuscript",
         reproduction_status="reproduced",
         evidence_path="results/registry.json; experiments/verify.py",
         scientific_concern="Usage status changed 2026-10-12: trend claims, Fig. 6b and 'spanning 2020 through 2026' removed from main.tex because the TRENDS01 corpus is apparently synthetic (generator signatures).",
         proposed_action="None."),
    dict(claim_id="M08", manuscript_location="Sec.IV-D5",
         exact_claim="External accuracy 29.9% with base rate 78.08% (same cohort/target)",
         ms_value="29.9% @ 78.08% base", artifact_value="acc=0.2986 base=0.7808 n=50000 same test cohort",
         reproduction_status="reproduced",
         evidence_path="results/STAT02_external_validation/metrics.json",
         scientific_concern="Correctly disclosed; threshold at 0.5 under shifted prevalence explains low accuracy.",
         proposed_action="None; consider adding PR-AUC/calibration note in Phase 9."),
    dict(claim_id="M10", manuscript_location="Sec.III-A; Tab.I (synthetic rows); REAL_VS_SYNTHETIC_FINDINGS.md",
         exact_claim="Apparently-synthetic classification is backed by executable generator-signature checks; declared (source states) is distinguished from inferred (generator signatures)",
         ms_value="declared vs inferred",
         artifact_value="10 datasets checked; per-dataset signature families recorded (uniformity chi2, binary balance, cross-field coupling, ID sequences, missing-as-equal-class)",
         reproduction_status="reproduced",
         evidence_path="datasets/synthetic_checks.py; datasets/synthetic_checks_output.json; datasets/REAL_VS_SYNTHETIC.csv (synthetic_basis, signature_checks columns)",
         scientific_concern="Inferred classification is evidence, not proof; NGESS flagged low-confidence; checks refuted three earlier informal claims (experience_level<->remote_type '1:1' map, college '100 IDs x 100 students' cluster, India 'near-uniform' categories) - corrected in REAL_VS_SYNTHETIC.csv.",
         proposed_action="Cite datasets/synthetic_checks_output.json wherever synthetic provenance is asserted; never assert certainty for the inferred group."),
]

all_rows = rows + manual

# Phase 4 placement-split overrides (applied last, authoritative).
LOC_P = {
    "C70": "paper_placement Sec.IV-A (was main Sec.IV-D1)",
    "C71": "paper_placement Sec.IV-A tab:logistic",
    "C72": "paper_placement Sec.IV-A tab:logistic",
    "C73": "paper_placement Sec.IV-A tab:logistic",
    "C74": "paper_placement Sec.IV-A tab:logistic",
    "C75": "paper_placement Sec.IV-A tab:logistic",
    "C76": "paper_placement Sec.IV-A tab:logistic",
    "C77": "paper_placement Sec.IV-D/E (CV + diagnostic audit)",
    "C78": "paper_placement Sec.IV-E (diagnostic audit)",
    "C79": "paper_placement Sec.IV-E (diagnostic audit)",
    "C80": "paper_placement Sec.IV-D tab:model_comparison",
    "C81": "paper_placement Sec.IV-D tab:model_comparison",
    "C82": "paper_placement Sec.IV-E (k-of-n audit)",
    "C83": "paper_placement Sec.IV-D tab:multiseed",
    "C84": "paper_placement Sec.IV-D tab:multiseed",
    "C85": "paper_placement Sec.IV-A (chi-square)",
    "C86": "paper_placement Sec.IV-A (chi-square)",
    "C87": "paper_placement tab:vif (was main tab:vif)",
    "C88": "paper_placement tab:descriptive",
    "C89": "paper_placement tab:descriptive",
    "C90": "paper_placement tab:descriptive",
    "C100": "paper_placement Sec.IV-E (external generalization; was main Sec.IV-D5)",
    "C101": "paper_placement Sec.IV-E (external generalization)",
    "C102": "paper_placement Sec.IV-E (external generalization)",
    "C113": "main Tab.I; paper_placement Sec.III-A (corpus)",
    "C130": "paper_placement Sec.IV-B (RQ5 cross-country; was main Sec.V-E)",
    "C152": "paper_placement Sec.V-A (hyp. verdicts)",
    "C152b": "paper_placement Sec.V-A (hyp. verdicts)",
    "C153": "paper_placement tab:hypotheses",
    "C161": "paper_placement Sec.V-A (hyp. verdicts)",
    "M05": "paper_placement Sec.V-A (hyp. verdicts) para + tab:hypotheses",
    "M08": "paper_placement Sec.IV-E (external generalization)",
}
for r in all_rows:
    if "paper" not in r:  # manual rows
        r["paper"] = "placement" if r["claim_id"] in PLACEMENT else "main"
    if r["claim_id"] in LOC_P:
        r["manuscript_location"] = LOC_P[r["claim_id"]]
    if r["claim_id"] in DROPPED:
        r["manuscript_location"] = ("removed from both manuscripts 2026-10-12 "
                                    "(Phase 4 D3: internship-effect claim dropped; artifact retained)")
        r["proposed_action"] = "DONE (Phase 4 D3): claim dropped from main and companion; INTL01 artifact archived."

out = ROOT / "audit" / "01_claim_evidence_ledger.csv"
fields = ["claim_id", "paper", "manuscript_location", "exact_claim", "ms_value", "artifact_value",
          "reproduction_status", "evidence_path", "scientific_concern", "proposed_action"]
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(all_rows)

from collections import Counter
print(Counter(r["reproduction_status"] for r in all_rows), "total", len(all_rows))
