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
| 2026-10-11 | **Final repository reconciliation (Phases 1–9):** independently recomputed manifest sums (3,163,517 raw / 2,643,703 unique) via pandas; verified local file parses; re-verified H6 −0.44 pp and INTL01 +15.34 pp from raw CSV | Working tree vs `datasets/DATASET_MANIFEST.csv`; `college_student_placement_dataset.csv`; INTL01 artifacts |
| 2026-10-11 | **F-1 H5 construct fix (material):** prior H5 “Supported (INTL01)” used the international-graduate **internship** association (+15.34 pp) as if it were a domestic training premium; no registered experiment computed a domestic-vs-international training contrast. H5 retargeted to **PLAC01** cross-country placement rates (India 63.2% … Germany 60.0%, overlapping CIs) and reclassified **Not supported**; INTL01 retained only as observational descriptive context; abstract/intro/H5 paragraph/hypotheses table/conclusion/README updated | `results/PLAC01_global_by_country/metrics.json`; `audit/05_stat_reproduction.json`; `main.tex`; README |
| 2026-10-11 | **F-2 CS2023 characterization:** abstract “criterion validity” trio and contribution/conclusion wording now distinguish expert-validated ESCO agreement (κ=0.737) from computational-only CS2023 embedding anchor (no human line-by-line audit) | `experiments/exp_scripts/curr01_cs2023_anchor.py`; `results/CURR01_cs2023_anchor/metrics.json` |
| 2026-10-11 | **Abstract proxy disclosure:** SGI academic side labeled as employer-derived occupational reference profile (1,167 postings) proxy, not university syllabi | C-1/R-5 mitigation; `hf_job_skill_set.csv` |
| 2026-10-11 | **README sync:** proxy note, RQ2 label, ALIGN04/CURR01 → USED_IN_MANUSCRIPT, internship association wording + H6 null + H5 not supported, CS2023 computational label, 16-pp page count | Registry + manuscript |
| 2026-10-11 | **verify_claims.py:** C158–C161 added (H5 PLAC01, CS2023 computational label, abstract proxy, PLAC01 spread); claim matrix rows + F-1/F-2 notes; 103/103 matched, 0 mismatched | `audit/verify_claims.py`; `claim_evidence_matrix.csv` |
| 2026-10-11 | **Validation re-run after edits:** pytest 13/13; `experiments/verify.py` all_verified; `reproduce_local.py --skip stats` env/checksums/verify/claims/citations ok; clean pdflatex+bibtex compile **16 pp**, 0 errors / 0 undefined / 0 overfull | `paper/main.pdf`; logs |

**Invariants:** no raw data edits; no experiment metric edits; no silent
estimand changes; no fabricated citations; audit notes kept out of
`paper/main.tex` body.
