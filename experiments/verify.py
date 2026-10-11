"""Post-hoc verification of downloaded experiment outputs.

Checks schema/presence of required artifacts and cross-experiment
consistency. Writes results/verification_report.json and flips registry
statuses COMPLETED -> VERIFIED on success.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REGISTRY_PATH, RESULTS_DIR, read_json, utc_now, write_json

REQUIRED = {
    "ALIGN01_lexical_bootstrap": ["metrics.json", "market_top500.csv",
                                  "academic_top500.csv", "lexical_alignment.json"],
    "ALIGN02_semantic_sbert": ["metrics.json", "table_sensitivity_tau.csv",
                               "skill_semantic_matches.csv"],
    "ALIGN03_domain_gap": ["metrics.json", "domain_gap_table.csv",
                           "taxonomy_skill_counts.csv"],
    "STAT01_placement_core": ["metrics.json", "table1_descriptive.csv",
                              "table2_chi_square.csv", "table3_correlation.csv",
                              "table_vif.csv", "table4_logistic.csv",
                              "table5_rf_importance.csv", "table6_cv_seed42.csv",
                              "table6b_cv_multiseed.csv", "tree_audit.json"],
    "STAT02_external_validation": ["metrics.json", "external_validation.csv"],
    "GEO01_linkedin_shares": ["metrics.json", "geo_country_shares.csv"],
    "TRENDS01_ai_longitudinal": ["metrics.json", "trends_yearly.csv"],
    "INTL01_internship_effect": ["metrics.json", "internship_effect.csv"],
    "PLAC01_global_by_country": ["metrics.json", "placement_by_country.csv"],
    "VALID01_esco_gold": ["metrics.json", "table_valid_pairs.csv",
                          "table_valid_coverage.csv", "pair_results.csv"],
    "ALIGN04_crosscorpus_linkedin": ["metrics.json", "table_crosscorpus_sgi.csv",
                                     "domain_gap_linkedin.csv",
                                     "market_top500_linkedin.csv",
                                     "skill_semantic_matches_linkedin.csv"],
    "CURR01_cs2023_anchor": ["metrics.json", "table_cs2023_per_ka.csv",
                             "table_cs2023_sensitivity.csv",
                             "cs2023_topic_matches.csv"],
}


def check_numeric_sanity(exp_id: str, dir_path: Path) -> list[str]:
    issues = []
    m = json.loads((dir_path / "metrics.json").read_text(encoding="utf-8"))
    if m.get("status") != "completed":
        issues.append("metrics.status != completed")
    if m.get("runtime_sec", 1) <= 0:
        issues.append("non-positive runtime")

    if exp_id == "ALIGN01_lexical_bootstrap":
        if not (0 <= m["sgi"] <= 1):
            issues.append("SGI out of range")
        if not (m["sgi_ci_lower"] <= m["sgi"] <= m["sgi_ci_upper"]):
            issues.append("SGI outside its own CI")
    elif exp_id == "ALIGN02_semantic_sbert":
        sens = pd.read_csv(dir_path / "table_sensitivity_tau.csv")
        if list(sens.tau) != [0.4, 0.5, 0.6, 0.7]:
            issues.append("tau grid mismatch")
        if not ((sens.CI_Lower <= sens.SGI) & (sens.SGI <= sens.CI_Upper)).all():
            issues.append("some SGI outside CI")
        if not sens.SGI.is_monotonic_increasing:
            issues.append("SGI not monotone in tau")
    elif exp_id == "ALIGN03_domain_gap":
        dg = pd.read_csv(dir_path / "domain_gap_table.csv")
        if len(dg) != 8:
            issues.append(f"expected 8 categories, got {len(dg)}")
        if (dg.deficit_pp_lexical < -1e-6).any():
            issues.append("negative lexical deficit")
        if (dg.deficit_pp_semantic < -1e-6).any():
            issues.append("negative semantic deficit")
        # semantic coverage should never be worse than lexical on average
        if (dg["coverage_rate_semantic_tau0.5"].mean()
                < dg["coverage_rate_lexical"].mean()):
            issues.append("mean semantic coverage below lexical coverage")
    elif exp_id == "STAT01_placement_core":
        t4 = pd.read_csv(dir_path / "table4_logistic.csv")
        for f in ["Communication_Skills", "CGPA"]:
            row = t4[t4.Feature == f]
            if row.empty or row.Significance.iloc[0] not in ("*", "**", "***"):
                issues.append(f"expected significant coefficient for {f}")
        t6 = pd.read_csv(dir_path / "table6_cv_seed42.csv")
        lr = t6[t6.model == "Logistic Regression"].iloc[0]
        if not (0.8 < lr.accuracy < 0.95):
            issues.append(f"LR CV accuracy unexpected: {lr.accuracy}")
    elif exp_id == "STAT02_external_validation":
        ev = pd.read_csv(dir_path / "external_validation.csv")
        transfer = ev[ev.train.str.startswith("College")]
        if len(transfer) != 2:
            issues.append("expected 2 transfer rows")
        for _, r in transfer.iterrows():
            if not (0.5 < r.auc < 1.0):
                issues.append(f"transfer AUC out of range: {r.auc}")
    elif exp_id == "GEO01_linkedin_shares":
        geo = pd.read_csv(dir_path / "geo_country_shares.csv")
        if abs(geo.share_pct.head(10).sum() - 100) > 15:
            issues.append("top-10 country shares far from 100%")
        us = geo[geo.country.str.upper().isin(["UNITED STATES", "US", "USA"])]
        if us.empty or not (80 <= us.share_pct.iloc[0] <= 92):
            issues.append("US share outside plausible 80-92% band")
    elif exp_id == "INTL01_internship_effect":
        m2 = json.loads((dir_path / "metrics.json").read_text(encoding="utf-8"))
        lo, hi = m2["risk_difference_ci_pp"]
        if not (lo <= m2["risk_difference_pp"] <= hi):
            issues.append("risk difference outside CI")
        if m2["risk_difference_pp"] <= 0:
            issues.append("internship effect not positive")
    elif exp_id == "PLAC01_global_by_country":
        m3 = json.loads((dir_path / "metrics.json").read_text(encoding="utf-8"))
        if not (0 < m3["overall_placement_rate_pct"] < 100):
            issues.append("overall rate out of range")
    elif exp_id == "VALID01_esco_gold":
        m4 = json.loads((dir_path / "metrics.json").read_text(encoding="utf-8"))
        if not (m4["n_positive"] > 500 and m4["n_negative"] > 500):
            issues.append("unexpected pair counts")
        if not (0.2 < m4["kappa_at_tau_0.5"] <= 1.0):
            issues.append(f"kappa out of plausible range: "
                          f"{m4['kappa_at_tau_0.5']}")
        if not (0.6 < m4["auc_cosine"] <= 1.0):
            issues.append(f"cosine AUC out of plausible range: {m4['auc_cosine']}")
        for cov in m4["esco_coverage"]:
            if not (0.05 <= cov["lexical_coverage"] <= 0.98) or \
               not (0.05 <= cov["semantic_coverage_tau0.5"] <= 0.99):
                issues.append(f"ESCO coverage out of range: {cov}")
        t = pd.read_csv(dir_path / "table_valid_pairs.csv")
        taus = sorted(t.dropna(subset=["tau"]).tau.round(1).tolist())
        if taus != [0.4, 0.5, 0.6, 0.7]:
            issues.append(f"tau grid mismatch in valid pairs table: {taus}")
    elif exp_id == "ALIGN04_crosscorpus_linkedin":
        if not (1_000_000 <= m["n_postings"] <= 1_400_000):
            issues.append(f"unexpected posting count: {m['n_postings']}")
        if not (0 <= m["lexical_sgi"] <= 1):
            issues.append("lexical SGI out of range")
        if not (0 <= m["semantic_sgi_tau_0.5"] <= 1):
            issues.append("semantic SGI out of range")
        dg = pd.read_csv(dir_path / "domain_gap_linkedin.csv")
        if len(dg) != 8:
            issues.append(f"expected 8 categories, got {len(dg)}")
        if (dg.deficit_pp_lexical < -1e-6).any() or (dg.deficit_pp_semantic < -1e-6).any():
            issues.append("negative deficit")
        sgi = pd.read_csv(dir_path / "table_crosscorpus_sgi.csv")
        sem = sgi[sgi.method == "semantic_sbert"]
        if not sem.SGI.is_monotonic_increasing:
            issues.append("semantic SGI not monotone in tau")
    elif exp_id == "CURR01_cs2023_anchor":
        if m["n_kas"] != 17:
            issues.append(f"expected 17 KAs, got {m['n_kas']}")
        if m["n_topics"] < 2000:
            issues.append(f"too few CS2023 topics: {m['n_topics']}")
        if not (0 <= m["overall_coverage_sem_tau_0.5"] <= 1):
            issues.append("overall coverage out of range")
        if not (0 <= m["reverse_coverage_academic_tau_0.5"] <= 1):
            issues.append("reverse coverage out of range")
        per_ka = pd.read_csv(dir_path / "table_cs2023_per_ka.csv")
        if len(per_ka) != 17:
            issues.append(f"per-KA table has {len(per_ka)} rows")
        if not ((per_ka["coverage_sem_tau_0.4"] >= per_ka["coverage_sem_tau_0.5"]).all()
                and (per_ka["coverage_sem_tau_0.5"] >= per_ka["coverage_sem_tau_0.6"]).all()):
            issues.append("per-KA coverage not monotone in tau")
    return issues


def main() -> None:
    reg = read_json(REGISTRY_PATH)
    report = {"verified_utc": utc_now(), "experiments": {}}
    all_ok = True
    for exp_id, required in REQUIRED.items():
        d = RESULTS_DIR / exp_id
        entry = reg["experiments"].get(exp_id, {})
        status = entry.get("status", "MISSING")
        missing = [f for f in required if not (d / f).exists()]
        issues = []
        if not missing:
            try:
                issues = check_numeric_sanity(exp_id, d)
            except Exception as e:
                issues = [f"sanity check crashed: {e}"]
        ok = status in ("COMPLETED", "VERIFIED", "USED_IN_MANUSCRIPT") \
            and not missing and not issues
        report["experiments"][exp_id] = {
            "registry_status": status,
            "missing_files": missing,
            "issues": issues,
            "verified": ok,
        }
        if ok:
            if status == "COMPLETED":
                reg["experiments"][exp_id]["status"] = "VERIFIED"
                reg["experiments"][exp_id]["verified_utc"] = utc_now()
        else:
            all_ok = False
    report["all_verified"] = all_ok
    write_json(REGISTRY_PATH, reg)
    write_json(RESULTS_DIR / "verification_report.json", report)
    print(json.dumps(report, indent=2))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
