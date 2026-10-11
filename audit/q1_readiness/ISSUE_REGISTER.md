# ISSUE REGISTER — Q1 Readiness Audit

Severity: CRITICAL > HIGH > MEDIUM > LOW. Resolution requires **evidence**,
not wording alone (wording-only resolutions marked as such).

| ID | Severity | Evidence | Affected | Required action | Resolution |
|---|---|---|---|---|---|
| D-1a | CRITICAL | `audit/05_stat_reproduction.json` intern_RD_pp=−0.4442; ledger H6 | Abstract, Intro, §IV, Conclusion, H6 | State RD −0.44 pp (16.32% vs 16.77%); do not claim positive internship effect | **RESOLVED** — manuscript updated; ledger 0 contradictions |
| D-1b | HIGH | STAT01 vs INTL01 artifact paths | H6 test attribution | Attribute primary test to STAT01; reserve INTL01 for H5 | **RESOLVED** |
| D-2 | HIGH | `audit/02_data_provenance.md` unique ≈2,643,703 | Abstract, §I, §III-A | Distinguish raw inventory vs unique vs experiment inputs | **RESOLVED** |
| D-3 | HIGH | Manifest local row counts | Table I, Dataset section | LinkedIn 1,348,454; HF jobs/skills 519,814; academic ref 1,167 | **RESOLVED** |
| D-4 | CRITICAL (construct) | `audit/03_sgi_validation.md` 2×2; `align0{1,2,3,4}` P=100 vs 500 | §IV-B2, H3, Table crosscorpus | Rewrite around matched-profile sensitivity; drop unsupported corpus-composition story | **RESOLVED** — `tab_crosscorpus.tex` + text |
| D-5 | HIGH | Same as D-4 | “Identical procedures” claim | Narrow or remove | **RESOLVED** |
| C-1 | CRITICAL (construct) | `hf_job_skill_set.csv` n=1,167; 5 job categories | Academic profile construct | Never call observed university curriculum; keep CURR01 anchor + Limitation | **MITIGATED** — wording + Table I; residual proxy limitation remains (inherent) |
| L-1 | MEDIUM | Crossref/claim spot-check | §related work daberao citation | Reword support claim | **RESOLVED** |
| B-1 | MEDIUM | Crossref | `korrapati2025aligning` | Full DOI + title | **RESOLVED** |
| B-2 | MEDIUM | Crossref | `zhang2022skillspan` | Add DOI | **RESOLVED** |
| B-3 | MEDIUM | Crossref | `green2022development` | Add DOI | **RESOLVED** |
| B-4 | MEDIUM | Crossref | `senger2024deep` | Add DOI | **RESOLVED** |
| B-5 | MEDIUM | Crossref | `kruger2025improving` | Add DOI | **RESOLVED** |
| B-6 | MEDIUM | Crossref | `alhazmi2025aligning` | Year 2025 + pages | **RESOLVED** |
| B-7 | LOW | HTTP 200 | `decorte2022negative` | CEUR URL | **RESOLVED** |
| B-8 | LOW | Crossref truncation | `schlippe2023skill` | Document weak title match | **ACCEPTED** (PARTIALLY_VERIFIED) |
| B-9 | LOW | Sparse ASEE metadata | `cuckov2022quantifying` | Document year gap | **ACCEPTED** (PARTIALLY_VERIFIED) |
| B-10 | LOW | online-first vs issue | `scandurra2024employability` | Keep issue year | **ACCEPTED** (PARTIALLY_VERIFIED) |
| M-1 | MEDIUM | Phase 8 | Reproducibility | Add tests, CI, checksums, entry point | **RESOLVED** |
| M-2 | MEDIUM | Phase 8 | Manifest | Correct 3 counts | **RESOLVED** |
| M-3 | MEDIUM | Phase 10 | Figures/tables | All 7 figs + 12 tables present & referenced; crosscorpus table rewritten | **RESOLVED** |
| R-1 | MEDIUM | Phase 3.6 | SGI bootstrap unit | Disclose skill-list vs posting bootstrap | **RESOLVED** (methods/discussion) |
| R-2 | MEDIUM | Phase 5 | χ²-projects 721.47 vs published 719.82 | Binning difference documented; not silent | **RESOLVED** (documented) |
| R-3 | MEDIUM | Phase 5.6.2 | Multiplicity | Interval posture; optional note | **OPEN (non-blocking)** |
| R-4 | MEDIUM | Phase 6.4 | Transfer calibration | Report calibration / PR-AUC | **OPEN (non-blocking)** |
| R-5 | HIGH | Phase 2 | Academic profile construct language | Keep proxy language permanently | **OPEN residual** — design limitation, not fixable without new data |
| R-6 | MEDIUM | Phase 0 R5 | CS2023 line-by-line audit | Hand-check 2,197 topics | **OPEN** |
| R-7 | MEDIUM | Phase 5 | Employer-clustered bootstrap for domain CIs | Implement if time | **OPEN (recommended)** |
| R-8 | LOW | Phase 8 | VALID01 `n_positive_by_type` metadata zeros | Fix metadata emitter | **OPEN (non-blocking)** |
| R-9 | MEDIUM | Phase 11–12 | Venue format (page/word/class) | Convert after venue choice | **OPEN (author)** |
| R-10 | MEDIUM | Phase 8 | Full human proofread | Manual | **OPEN (author)** |
| R-11 | LOW | Phase 11 | `make_latex.py` can clobber crosscorpus table | Prefer hand table or update generator | **OPEN** |
| G-1 | MEDIUM | Phase 1 inventory | Orphan datasets in repo | Document unused; no claim of use | **RESOLVED** (documented) |
| G-2 | LOW | Phase 2 | ai_job_dataset vs ai_job_dataset1 duplicate copies | Inventory flag | **OPEN (inventory)** |
