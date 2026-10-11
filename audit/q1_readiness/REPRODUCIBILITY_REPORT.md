# REPRODUCIBILITY REPORT

*Date: 2026-10-11 · Environment: Windows · Python 3.14 · pytest 9.1 · MiKTeX
(pdflatex+bibtex documented) · Branch: `main` (clean before final reconciliation
edits); deliverables under `audit/q1_readiness/`.*

---

## 1. Environment

| Item | Value |
|---|---|
| Python | 3.14.6 |
| pytest | 9.1.1 |
| Raw data | Local under `datasets/` (gitignored; ~6.6 GB); SHA-256 in `datasets/input_checksums.sha256` |
| GPU experiments | Historical source of truth: Kaggle `Moshinali/skill-gap-experiments`; results mirrored under `results/<EXP_ID>/` |
| Credentials | `.env` (Kaggle/HF) — never logged or printed |

## 2. Commands executed (audit + package + final reconciliation)

| Command | Result |
|---|---|
| `python audit/verify_claims.py` | **checks=103; matched=103; mismatched=0** (post F-1/F-2; C158–C161 added) |
| `python audit/build_ledger.py` | Counter(reproduced=107, partially_reproduced=1) total 108 |
| `python audit/validate_data.py` | 22-file quality CSV (prior session) |
| `python audit/verify_citations.py` | 52 entries; 35 DOI verified; 0 unresolved; 17 no-DOI justified |
| `python reproduce_local.py --skip stats` | stages: env, checksums (9/9), verify (12/12), claims, citations — **all ok** |
| `python -m pytest tests/ -q` | **13 passed** |
| `python experiments/verify.py` | **all_verified: true** |
| pdflatex + bibtex + pdflatex ×2 (`paper/`) | **16 pp; 0 errors / 0 undefined / 0 overfull** (clean rebuild after F-1 edits) |
| Independent H6 recompute (raw CSV) | RD −0.4442 pp; rates 16.32%/16.77% — matches STAT01 |
| Pandas reparse of local raw CSVs | hf jobs/skills = 519,814 each (identical `job_link` sets); LinkedIn = 1,348,454; academic ref = 1,167 — naive line counts inflated by embedded newlines |
| Manifest sum recompute | 3,163,517 raw; unique = 3,163,517 − 519,814 = 2,643,703 |

## 3. Tests

- `tests/test_common.py` — taxonomy/seeds/helpers
- `tests/test_reproducibility.py` — hard-gates **zero contradicted** claims;
  registry/artifact presence; key metric invariants

## 4. Known reproduction caveats

- Full Kaggle GPU re-execution not re-run in this audit window; GPU
  metrics.json + verification_report are the retained source of truth.
- SGI/STAT/CURR01/STAT02 **local CPU re-runs** matched published values
  bit-for-bit where executed.
- Display-rounding epsilon for C120/C143 (1-dp vs 2-dp) is intentional and
  documented; not a ledger contradiction.
- Crossref citation stage requires network; offline runs should skip
  citations stage (`reproduce_local.py` supports stage control).
- Stats stage skipped in the final reconciliation pass (`--skip stats`);
  H6/PLAC01/INTL01 values independently re-verified from raw CSVs and
  artifacts in prior passes.
- Naive `wc`/line counts of multi-line CSVs are **wrong**; use a CSV parser
  (documented F-4).

## 5. Missing dependencies / data for third parties

| Need | Impact if missing |
|---|---|
| Raw CSVs (Kaggle/HF download) | Cannot recompute SGI/token counts from scratch |
| `results/*/metrics.json` | Cannot re-verify registered claims |
| Network (Crossref) | Citation stage fails open; other stages unaffected |
| LaTeX distribution | PDF rebuild blocked; `.tex`/`.bib` still valid |

## 6. Integrity statements

- No raw data file was modified by the audit.
- No experiment `metrics.json` was altered to change conclusions.
- Manuscript changes are limited to evidence-backed corrections and
  documented in the issue register + changelog.
- `make_latex.py` regenerates auto tables/figures but **overwrites** the
  hand-audited `tab_crosscorpus.tex` and legacy figure PDFs — restore with
  `git checkout --` after regeneration (documented F-5/R-11).
