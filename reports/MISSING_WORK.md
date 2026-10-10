# Missing Work / Outstanding Gaps

*Snapshot: 2026-10-10 (post-VALID01). All 10 experiments are
`USED_IN_MANUSCRIPT`; `paper/main.pdf` is 13 pp, clean build.*

## Remaining before journal submission (small)

1. **Target journal selection & template conversion** — manuscript is
   IEEEtran double-blind; convert to the chosen venue's format (Elsevier /
   Springer / IEEE T-ED) and write the cover letter. Author metadata goes in
   only after anonymized review is no longer required.
2. **Author information for camera-ready** — kept out of `main.tex` by
   design (double-blind).

## Methodological gaps (documented in Limitations, not blocking)

3. **Human validation is external, not in-house** — matcher validity is now
   established against published expert gold standards (SkillSpan→ESCO;
   κ = 0.737, AUC = 0.961; experiment VALID01), but no independent raters
   annotated *this specific* corpus. A ~300-pair in-house double-annotation
   (2 raters, Cohen's κ) would close the last gap if a reviewer insists.
4. **RQ3 corpus composition** — the 519K skills corpus is dominated by
   generic/healthcare/retail competencies; deficits are conditional-on-demand.
   Optional `ALIGN04` re-run on a CS-heavy corpus (LinkedIn 1.35M or USA
   Job Market 316K) would serve as an appendix sensitivity check.
5. **Geographic scope** — LinkedIn corpus is US/UK/CA/AU only (85.2% US);
   recorded as limitation 6.

## Cleanup / hygiene (non-blocking)

6. **Legacy Kaggle kernels** — private `-a1` ERROR kernels remain on
   non-`nihanshadman` accounts plus any abandoned racing candidates (e.g.,
   VALID01's superseded duplicates if any completed after the winner).
   `kaggle kernels delete` is broken in CLI 2.2.4; delete manually via the
   Kaggle web UI. They do not affect results.
7. **Stale derived CSVs in `datasets/`** — `table1_…csv` … `table6_…csv`,
   `table_sensitivity_tau.csv`, `skill_semantic_matches.csv` (Oct 8) are
   pre-experiment copies superseded by `results/<EXP_ID>/`.
8. **Legacy visualization script** — `datasets/analysis.py` still generates
   the old fig1–fig12 set with hardcoded values; authoritative figures come
   from `experiments/make_latex.py`.
9. **Unused verified artifacts** — available for appendix/rebuttal:
   correlation matrix, RF importances, internship-by-field rates, top job
   titles, salary-by-experience, ALIGN03 semantic deficit CIs, VALID01
   pair-level results (`pair_results.csv`, 2,907 rows).

## Resolved this session

- ✅ **Human gold-standard validation** → VALID01 (external expert standard;
  κ/accuracy/AUC + ESCO vocabulary grounding).
- ✅ **`LICENSE` file** — MIT, added at repo root.
- ✅ **Git commit + push** of the full experiment suite / manuscript /
  reports state (commit on `main`).
- ✅ Scheduler upgraded: 16-worker parallel racing candidates, restart
  adoption, USED_IN_MANUSCRIPT-aware termination.
