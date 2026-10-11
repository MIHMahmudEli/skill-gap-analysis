# REPRODUCIBILITY REPORT

*Date: 2026-10-11 · Environment: Windows · Python 3.14 · pytest 9.1 · MiKTeX
(partial — pdflatex+bibtex documented) · Branch package from `main` `41223eb`.*

---

## 1. Environment

| Item | Value |
|---|---|
| Python | 3.14.6 |
| pytest | 9.1.1 |
| Raw data | Local under `datasets/` (gitignored; ~6.6 GB); SHA-256 in `datasets/input_checksums.sha256` |
| GPU experiments | Historical source of truth: Kaggle `Moshinali/skill-gap-experiments`; results mirrored under `results/<EXP_ID>/` |
| Credentials | `.env` (Kaggle/HF) — never logged or printed |

## 2. Commands executed (audit + package)

| Command | Result |
|---|---|
| `python audit/verify_claims.py` | checks=99; mismatched=2 rounding-only (C120, C143); ledger 107 reproduced / 1 partial |
| `python audit/build_ledger.py` | Counter(reproduced=107, partially_reproduced=1) total 108 |
| `python audit/validate_data.py` | 22-file quality CSV (prior session) |
| `python audit/verify_citations.py` | 52 entries; 35 DOI verified; 0 unresolved; 17 no-DOI justified |
| `python reproduce_local.py` | stages: env, checksums (9/9), verify (12/12), claims, stats, citations — **all ok** |
| `python -m pytest tests/ -q` | **13 passed** |
| pdflatex + bibtex + pdflatex ×2 (`paper/`) | **16 pp; 0 errors / 0 undefined / 0 overfull** (prior session; PDF tracked) |
| `python audit/q1_readiness/build_package.py` | wrote reference (52), experiment (12), claim (108), dataset (18) CSVs |

## 3. Tests

- `tests/test_common.py` — taxonomy/seeds/helpers
- `tests/test_reproducibility.py` — hard-gates **zero contradicted** claims;
  registry/artifact presence; key metric invariants

## 4. Known reproduction caveats

- Full Kaggle GPU re-execution not re-run in this audit window; GPU
  metrics.json + verification_report are the retained source of truth.
- SGI/STAT/CURR01/STAT02 **local CPU re-runs** matched published values
  bit-for-bit where executed.
- `audit/verify_claims.py` may print 1–2 “MISMATCH” lines for display
  rounding (manuscript 1-decimal vs artifact 2-decimal); these are **not**
  ledger contradictions.
- Crossref citation stage requires network; offline runs should skip
  citations stage (`reproduce_local.py` supports stage control).

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
  documented in Revision Log + issue register.
