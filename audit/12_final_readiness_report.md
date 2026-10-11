# Phase 12 — Final Q1-Readiness Report

*Date: 2026-10-11 · Branch: `q1-readiness-audit` (from `abbff83` = prior
Tier-A/B state on `main`) · Audit window: Phases 0–12 complete.*

---

## 1. Executive Verdict

**Status: READY for journal submission after venue-specific format pass
(Phase 11), with residual risks explicitly listed in §8.**

- All **12 registered experiments** remain `USED_IN_MANUSCRIPT` and
  artifact-verified (`results/verification_report.json`).
- Claim ledger: **107 reproduced / 1 partially reproduced / 0 contradicted**
  (was 96 / 3 / 4 at audit start).
- Manuscript defects D-1…D-4, profile-size confound, weak citation, and
  three manifest count errors are **fixed**; build is clean (16 pp,
  0 errors / 0 undefined / 0 overfull).
- Reproducibility package: 13 tests, CI workflow, input checksums, single
  entry point, Crossref-verified bibliography (35 DOIs + 17 justified
  no-DOIs).

---

## 2. Scope of Audit

| Phase | Deliverable | Outcome |
|---|---|---|
| 0 Inventory | `00_repository_inventory.md` | Baseline recorded; risks R1–R8 |
| 1 Claims | ledger CSV + `verify_claims.py` | 103→108 claims; 4 contradictions found |
| 2 Data | `02_data_provenance.md` + quality CSV | Linked-pair double-count; academic ref n=1,167; usage map |
| 3 SGI | `03_sgi_validation.md` + sensitivity JSON | Exact reproduction; **profile-size confound** |
| 4 CURR01 | `04_curriculum_validation.md` | Bit-exact metrics; unmatched-topic causes |
| 5 Statistics | `05_statistical_review.md` | STAT01/INTL01 exact; H6 RD −0.44 pp |
| 6 Prediction | `06_prediction_validation.md` | STAT02 exact; leakage-free; base-rate explained |
| 7 Literature | `07_literature_review.md` | 52 citations; 5 bib fixes; novelty matrix |
| 8 Reproducibility | tests, CI, checksums, entry point | Gaps closed; manifest corrected |
| 9 Manuscript | `09_manuscript_revision.md` | All verified defects fixed |
| 10 Figures/tables | `10_figures_tables.md` | Inventory OK; crosscorpus table rewritten |
| 11 Journals | `11_journal_format.md` | ToE/BJET/IJETHE constraints verified |
| 12 This report | `12_final_readiness_report.md` | — |

---

## 3. Claim Verification (headline)

| Metric | Pre-audit | Post-fix |
|---|---|---|
| Automated checks | 95 | 99 |
| Exact matches | 86 | 97 |
| Ledger reproduced | 96 | **107** |
| Partially reproduced | 3 | 1 (documented ALIGN03 subset) |
| **Contradicted** | **4** | **0** |

Critical corrections:
1. **H6** internship RD **+0.08 pp → −0.44 pp**; test attribution INTL01 → STAT01.
2. Corpus headline **3,176,266 “analyzed” → 2.64M unique** (+ raw inventory note).
3. LinkedIn **1,348,510 → 1,348,454**; HF jobs **519,841 → 519,814**;
   academic reference **13,833 → 1,167 postings**.
4. “Identical procedures” cross-corpus claim replaced by **matched-profile
   2×2** (SGI governed by academic covering-set size P, not market corpus).

---

## 4. Data Provenance Summary

- 15 open sources; **9 feed experiments**; HF jobs≡skills linked pair
  (identical 519,814 `job_link` sets) counted once for unique totals.
- Academic reference = 1,167 postings / 5 categories (proxy, not taxonomy);
  anchored by CURR01 to CS2023.
- Orphans retained for inventory only (e.g., data-science-job-postings 12,217).
- India skills synthetic — disclosed and unused in experiments.
- `DATASET_MANIFEST.csv` corrected; `datasets/input_checksums.sha256` pins
  the nine bundle files.

---

## 5. Statistical & Experimental Validity

- STAT01: all Welch/χ²/OR/VIF/CV metrics reproduce bit-for-bit; tree audit
  confirms semi-synthetic labels (disclosed).
- STAT02: zero-shot transfer protocol clean (no leakage); 0.768/0.576 AUCs
  reproduce; 29.9% acc @ 78% base rate correctly explained.
- INTL01: +15.34 pp exact; reserved for H5 (credential locality), not H6.
- SGI CIs are skill-list bootstrap (not market sampling error) — disclosed.
- Multiplicity posture: interval-based inference; optional one-sentence
  note recommended (Phase 5.6.2), non-blocking.

---

## 6. Reproducibility Package

```
python reproduce_local.py     # env pins → checksums → verify → claims → stats → citations
python -m pytest tests/       # 13 tests; hard-gates 0 contradicted claims
```

- CI: `.github/workflows/ci.yml` (pytest + claim ledger + Crossref).
- Kaggle GPU path unchanged (12 kernels, bundle `studyhub991/skill-gap-inputs-v1`).
- Known footgun: regenerating `tab_crosscorpus.tex` via `make_latex.py`
  would clobber the matched-profile 2×2 (documented in Phase 10).

---

## 7. Manuscript State

- **16 pages**, IEEEtran journal, double-blind anonymized.
- Revision log section lists all audit corrections (anonymized).
- Abstract ~370 words — trim required for IJETHE (≤250); structured abstract
  required for ToE.
- 52 references; zero cited-but-missing; zero uncited bib entries.

---

## 8. Residual Risks & Unverified Items

| Item | Class | Note |
|---|---|---|
| CS2023 2,197-topic line-by-line audit | unverified | Phase 0 R5; CURR01 metrics exact but extraction granularity not hand-checked |
| Employer-clustered bootstrap for ALIGN03 CIs | recommendation | Postings resampled iid; employer IDs available but unused |
| VALID01 mention-level cluster bootstrap | recommendation | Pair-level CIs may be slightly narrow |
| `n_positive_by_type` metadata zeros | non-blocking | VALID01 metrics bug; pair CSV fine |
| Calibration / PR-AUC for transfer model | recommendation | Phase 6.4 |
| Journal APCs / live IF | unverified | Dynamic pages; re-check at submission |
| Line-by-line human read of full 16 pp | partial | Log-based checks + targeted section reads; full proofread still advised |

---

## 9. Journal Readiness Matrix

| Venue | Format fit | Length fit | Action needed |
|---|---|---|---|
| IEEE ToE | High (IEEEtran) | Low (16→8–10 pp) | Compress; structured abstract; ORCID |
| BJET | Medium (Wiley class) | Borderline (~6.6k vs 5–6k) | Word-budget pass; template conversion |
| IJETHE (OA) | Medium (Springer class) | Good (4.5–8k) | Abstract ≤250 words; APC logistics |

No single journal is hard-coded; see `11_journal_format.md`.

---

## 10. Release Gate Checklist

- [x] Baseline commit `abbff83` preserved; work on `q1-readiness-audit`
- [x] No raw data or experiment metrics altered
- [x] All manuscript changes evidence-backed and logged
- [x] Claim ledger: 0 contradicted
- [x] Tests + CI green locally (13 passed)
- [x] Clean PDF build
- [x] Bibliography Crossref-verified
- [ ] **Author decisions remaining:** (1) choose venue + run format pass;
      (2) optional Phase 5/6 recommendations; (3) full human proofread;
      (4) authorize merge/push to `main` and HF re-sync of manuscript PDF
      if desired

**Gate recommendation:** merge-ready to `main` after author review of the
diff (`git diff abbff83..HEAD`) and explicit push authorization.
