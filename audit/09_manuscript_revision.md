# Phase 9 — Manuscript Revision (Verified Defect Fixes)

*Date: 2026-10-11 · Branch: `q1-readiness-audit` · Build: 16 pp, 0 errors,
0 undefined refs, 0 overfull boxes (pdflatex+bibtex, MiKTeX).*

All edits are evidence-backed from Phases 1–8; no estimands were silently
changed; raw data and experiment outputs untouched.

## 9.1 Defect Register → Applied Fixes

| ID | Defect | Manuscript fix | Evidence |
|---|---|---|---|
| **D-1** | H6 “+0.08 pp, p=0.62” unsupported; Table XIII cited INTL01 | Sec.V-A: univariate RD **−0.44 pp** (16.32% vs 16.77%); OR=1.02 p=0.62; Tab.XIII H6 → **STAT01**; INTL01 reserved for H5; hypothesis H6 test line updated | `audit/05_stat_reproduction.json` (`intern_RD_pp=-0.4442`) |
| **D-2** | “15 datasets / 3,176,266 records, we analyze” | Abstract/Intro/Sec.III-A/Conclusion: **2.64M unique** records; raw sum disclosed as inventory with linked-pair explanation; **nine** sources feed experiments | Phase 2 provenance; corrected manifest |
| **D-3** | LinkedIn 1,348,510 | Table I → **1,348,454**; manifest corrected | GEO01 `n_rows`; local CSV |
| **D-4** | “519,814 skill requirements” | RQ1 → “519,814 **skill-annotated postings**”; % = share of postings | HF skills CSV schema |
| Academic ref | “13,833 curriculum-domain skill taxonomy” | Table I → **1,167 job postings in 5 categories**; Limit.1 discloses proxy nature | local `hf_job_skill_set.csv` |
| **Profile confound** | “identical procedures”; vocabulary-composition explanation | Sec.III: K=100, P∈{100,500} disclosed; Algorithm 1 Top-K/Top-P; Sec.IV-B2 rewritten with matched-profile 2×2; vocabulary story **withdrawn** | `audit/_sgi_sensitivity/*.json`, `hf_acad500.json` |
| Weak cite | daberao for “curriculum reference profiles” | Reworded: profile-based matching precedent + CURR01 anchor | Phase 7 |
| Limit.5 | threshold sensitivity only | Added profile-size sensitivity (P) to Limit.5 | Phase 3 |

## 9.2 Revision Log (in manuscript)

End-of-paper `\section*{Revision Log}` lists (i)–(vii) corrections with
pointer to `audit/` ledger. Safe for double-blind (no author-identifying info).

## 9.3 Verification After Edit

| Gate | Result |
|---|---|
| `pdflatex` ×2 + `bibtex` | 16 pages, 0 errors, 0 undefined, 0 overfull |
| `audit/verify_claims.py` | 99 checks, 97 match; 2 mismatches = known rounding (C120/C143), ledger marks reproduced |
| Ledger statuses | **0 contradicted**, 107 reproduced, 1 partially (ALIGN03 subset, documented) |
| `pytest tests/` | 13 passed (now hard-gates zero contradictions) |

## 9.4 Deliberately Not Changed

- Experiment code / metrics (all reproductions already exact).
- SGI point estimates (still 0.52/0.32 headline at P=100; levels at P=500 reported as sensitivity, not substituted).
- H5 INTL01 +15.34 pp (correct for its cohort; different estimand from H6).
- Bootstrap unit (skill-level for SGI) — documented in Phase 3, not re-run.
- VALID01 `n_positive_by_type` metadata bug — non-manuscript-facing (M06).
