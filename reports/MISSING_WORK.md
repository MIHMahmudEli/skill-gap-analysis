# Missing Work / Outstanding Gaps

*Snapshot: 2026-10-10, after all 9 experiments reached `USED_IN_MANUSCRIPT`
and `paper/main.pdf` compiled cleanly (12 pp, 0 errors).*

## Blocking for submission (small)

1. **Git commit of the current state** — 22 files changed and uncommitted
   (experiment suite fixes, registry, `make_latex.py`, generated tables/
   figures, manuscript, README, requirements, reports). Awaiting explicit user
   approval to commit; no secrets staged (`.env` is git-ignored).
2. **`LICENSE` file** — README references `LICENSE` (MIT) but the file does
   not exist. Needs owner decision on license text before publication of the
   repository URL in the manuscript.
3. **Author/title metadata** — manuscript is double-blind redacted by design;
   target journal must be chosen and the template/conversion applied at
   submission time (currently IEEEtran journal format).

## Methodological gaps (documented in Limitations, not blocking)

4. **No human gold-standard validation** — skill extraction, taxonomy
   mapping, and SBERT matching have no inter-annotator agreement (Cohen's κ).
   Recommended before a second submission round: annotate a stratified sample
   (≈300 market–academic skill pairs) with two raters.
5. **RQ3 corpus composition** — the 519K skills corpus is dominated by
   generic/healthcare/retail competencies, so taxonomy demand shares are
   modest (Programming 3.97% of postings). An optional robustness experiment
   (`ALIGN04`) would re-run the domain-gap metric on a CS-heavy corpus
   (LinkedIn 1.35M or USA Job Market 316K) as an appendix sensitivity check.
6. **Geographic scope** — LinkedIn corpus is US/UK/CA/AU only (85.2% US);
   no EU/Asia posting data. Recorded as limitation; a follow-up could ingest
   the India/APAC corpora already in the manifest for Tier-1 balance.

## Cleanup / hygiene (non-blocking)

7. **Legacy Kaggle kernels** — 9 private `-a1` ERROR kernels remain on
   non-`nihanshadman` accounts (e.g., `rssiam/sg-stat01-placement-a1`).
   `kaggle kernels delete` is broken in CLI 2.2.4; delete manually via the
   Kaggle web UI. They do not affect results.
8. **Stale derived CSVs in `datasets/`** — `table1_…csv` … `table6_…csv`,
   `table_sensitivity_tau.csv`, `skill_semantic_matches.csv` (Oct 8) are
   pre-experiment copies superseded by `results/<EXP_ID>/`. Either delete or
   move to `datasets/_legacy/`.
9. **Legacy visualization script** — `datasets/analysis.py` still generates
   the old fig1–fig12 set with hardcoded values; authoritative figures now
   come from `experiments/make_latex.py`. Consider archiving the legacy
   script to avoid accidental reuse.
10. **Unused verified artifacts** — available but not yet placed in the
    manuscript (candidate appendix/rebuttal material): correlation matrix
    (`table3_correlation.csv`), RF importances (`table5_rf_importance.csv`),
    internship-by-field rates (`internship_effect_by_field.csv`), top job
    titles (GEO01), salary-by-experience (TRENDS01), ALIGN03 semantic
    deficit CIs.

## Verified-and-fixed (no longer missing)

- STAT01 intercept bug (ORs biased 3×) → fixed, re-run on GPU, re-verified.
- External AUC 0.6764 → **0.576** corrected in manuscript.
- Fabricated TikZ constants (trend frequencies, domain-gap table, geo
  shares) → replaced by generated artifacts from verified CSVs.
- `references.bib` parse error (commented retracted entry) → removed;
  bibtex 0 errors.
- README stale function names/metrics → rewritten.
- `requirements.txt` pinned to a different environment → updated to the
  verified stack (pandas 3.0.5, sklearn 1.9.0, statsmodels 0.15.0, …).
