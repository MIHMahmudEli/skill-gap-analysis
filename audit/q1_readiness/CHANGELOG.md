# CHANGELOG — Q1 Readiness Package

Base for this package: `main` @ `41223eb` (includes full Phases 0–12 audit).
Package branch: `q1-readiness-package`.

| When | Change | Evidence / rationale |
|---|---|---|
| 2026-10-10–11 | Claim ledger created and expanded to 108 claims | `audit/01_claim_evidence_ledger.csv`; `verify_claims.py` |
| 2026-10-10–11 | Data provenance recomputed; manifest counts fixed | `audit/02_data_provenance.md`; local CSV row counts |
| 2026-10-10–11 | SGI exact reproduction; profile-size confound verified | `audit/_sgi_sensitivity/`; 2×2 reanalysis |
| 2026-10-10–11 | STAT01/INTL01/STAT02/CURR01 local reproductions | `audit/05_stat_reproduction.json`; `_stat02_out`; `_curr01_out` |
| 2026-10-10–11 | Bibliography Crossref audit + DOI/year fixes | `audit/07_citation_check.csv`; `paper/references.bib` |
| 2026-10-10–11 | Manuscript numerical/construct fixes (D-1…D-5) | `paper/main.tex`; Revision Log; ledger → 0 contradicted |
| 2026-10-10–11 | Reproducibility: tests, CI, checksums, entry point | `tests/`; `.github/workflows/ci.yml`; `reproduce_local.py` |
| 2026-10-10–11 | Journal format constraints (ToE/BJET/IJETHE) | `audit/11_journal_format.md`; live author pages |
| 2026-10-11 | **This package:** `audit/q1_readiness/*` deliverables generated from verified artifacts | `build_package.py`; SCImago snapshot for quartiles |
| 2026-10-11 | `reference_audit.csv` (52), `dataset_audit.csv` (18), `experiment_audit.csv` (12), `claim_evidence_matrix.csv` (108) | Built from prior-audit CSVs/JSON; no new fabricated rows |
| 2026-10-11 | **Adversarial re-verification:** branch/commit/tests/12 artifacts/H6 raw recompute/PDF rebuild | `FINAL_ADVERSARIAL_REVIEW.md` |
| 2026-10-11 | **Manuscript hygiene:** removed internal Revision Log from `main.tex` (PDF 16→15 pp) | Phase 7 submission rule |
| 2026-10-11 | **Construct wording:** Algorithm/embedding/RQ2/Discussion “syllabus” → reference-profile; contribution corpus bullet fixed; curriculum-adaptation claim narrowed | Adversarial V-2…V-4 |
| 2026-10-11 | Independent re-run of H6 from raw CSV: RD −0.4442 pp matches STAT01 | `college_student_placement_dataset.csv` |
| 2026-10-11 | **TikZ figures:** replaced all 7 matplotlib PDF figures with print-safe TikZ/pgfplots macros (`paper/figures/tikz_figs.tex`); data re-read from ALIGN01/03, GEO01, TRENDS01, STAT01, INTL01 artifacts only | Clean pdflatex: 0 errors/0 overfull/0 undefined refs; 13/13 tests pass |
| 2026-10-11 | **Fig 2a/2b/4b grouped bars:** explicit `ybar`+`bar shift` (auto-shift broken by `forget plot`) | Matches matplotlib `x-w,x,x+w` layout |
| 2026-10-11 | **Reconciliation pass:** corrected stale pre-audit raw sum 3,176,266 → **3,163,517** in `paper/main.tex` (§III-A + Tab. I caption) to match corrected `datasets/DATASET_MANIFEST.csv`; README updated to exact raw/unique split | Manifest sum recomputed = 3,163,517; unique = 3,163,517 − 519,814 = 2,643,703 |
| 2026-10-11 | **Reconciliation:** curriculum-overclaim sweep — abstract “curriculum deficits” → “reference-profile deficits”; RQ2 “curriculum descriptors” → “reference-profile descriptors”; Discussion “curriculum coverage” → “reference-profile coverage”; VALID01 “true curriculum–market alignment” → “true skill alignment” (gold standard is ESCO, not syllabi) | Evidence-supported wording only |
| 2026-10-11 | **verify_claims.py:** C120/C143 1-dp display-rounding epsilon; C150 updated to require 3,163,517 and absence of 3,176,266 | 99/99 matched, 0 mismatched |
| 2026-10-11 | **Restored** hand-audited Phase 9/10 `tab_crosscorpus.tex` (matched-profile 2×2) that `make_latex.py` had overwritten with the pre-audit auto-generated table; restored legacy figure PDFs (TikZ is authoritative) | `git checkout` of authoritative artifacts |

**Invariants:** no raw data edits; no experiment metric edits; no silent
estimand changes; no fabricated citations; audit notes kept out of
`paper/main.tex` body.
