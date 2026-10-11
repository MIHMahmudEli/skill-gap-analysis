# Changelog — Q1-Readiness Audit Branch

Base: `abbff83` (`main`, Tier A/B complete) → branch `q1-readiness-audit`.

| Commit | Phase | Summary |
|---|---|---|
| `b942782` | 0–1 | Repository inventory; claim ledger (103 claims; 96 reproduced; H6/corpus defects flagged) |
| `d181139` | 2 | Data provenance: linked-pair double-count; academic ref 1,167; usage map; 22-file quality CSV |
| `146a33e` | 3 | SGI exact local reproduction; **profile-size confound** (P=100 vs 500); matched-profile 2×2 |
| `838669a` | 4–7 | CURR01 validation doc; STAT01/INTL01 exact reproduction (H6 RD −0.44 pp); STAT02 clean; Crossref citation check + 5 bib DOI/year fixes |
| `5ecfd48` | 8 | tests/ (13), CI workflow, input checksums, `reproduce_local.py`, manifest count corrections |
| `ac43045` | 9–10 | Manuscript fixes (D-1…D-4, confound rewrite, revision log); tab_crosscorpus 2×2; ledger 0 contradicted |
| (this) | 11–12 | Journal-format verification (ToE/BJET/IJETHE); final readiness report; README update |

**Invariants held:** no raw data edits; no experiment metric edits; no silent
estimand changes; no fabricated references; double-blind anonymization kept.
