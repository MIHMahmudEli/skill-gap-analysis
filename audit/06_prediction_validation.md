# Phase 6 — Predictive Model & External Validation Audit

*Date: 2026-10-11 · Local rerun: `experiments/exp_scripts/stat02_external_valid.py`
on local CSVs → exact match with `results/STAT02_external_validation/metrics.json`
(0.7680 / 0.2986 / 0.7808; 0.5757; refs 0.7816 / 0.7142).*

## 6.1 Protocol Audit (leakage, tuning, splits)

| Check | Finding |
|---|---|
| Scaler fitted on train only | ✓ (`train_lr` fits StandardScaler on train; `evaluate` only transforms) |
| Target labels used for tuning | ✗ none — pure zero-shot transfer ✓ |
| Feature sets pre-specified | ✓ subsets A/B documented in metrics + manuscript |
| Hyperparameter tuning | none (defaults) — no nested-CV leakage risk |
| Train/test overlap across cohorts | distinct datasets; no shared IDs observed |
| Threshold | default 0.5 — not recalibrated for target prevalence (disclosed implicitly by reporting base rates) |
| Group/time splits | not applicable (cross-sectional benchmarks) |

**Verdict:** protocol is clean. The weak external numbers are honest transport
failures, not pipeline bugs.

## 6.2 The 29.9% Accuracy @ 78.08% Base Rate

Confirmed same cohort (Student Career Success, N=50,000) and target
(Placement_Status) in train-ref and transfer rows. Mechanism: model trained
at 16.6% prevalence outputs low P(placed) scores; at threshold 0.5 almost all
target rows predict "not placed" while 78% are "placed" → accuracy ≈ 22–30%.
Discrimination (AUC 0.768) survives. The manuscript states this correctly
(§IV-D5). **No defect.**

## 6.3 Label Quality of the Training Benchmark

STAT01 tree audit (99.92% k-of-n agreement; depth-4 CART train acc 1.0)
shows the College Placement labels are a deterministic threshold function of
the features — the benchmark is semi-synthetic. Already disclosed
(Limitation 1). Consequence: internal AUC 0.94 is **not** a claim about real
hiring; external AUC 0.768/0.576 is the more realistic anchor. Framing in
manuscript is appropriately cautious.

## 6.4 Metric Completeness Gaps (recommendations, not defects)

- No **calibration curve / Brier score** for the transfer model (ranking vs
  probability quality differ under prevalence shift). One figure or sentence
  would strengthen the transportability story.
- No **PR-AUC** (more informative than ROC-AUC at 78% base rate).
- No majority-baseline column in the external table (trivial baseline
  accuracy on SCS = 78.1%; stating it makes the 29.9% interpretable at a
  glance).
- Feature-distribution shift (e.g., CGPA scale 0–10 vs 0–4?) not
  quantified; "domain-standardized" wording is slightly loose since the
  *source* scaler is applied.

## 6.5 Baselines

- Internal: majority 83.4% acc / AUC 0.5 ✓ reported.
- External: in-dataset LR references (0.782 / 0.714) ✓ reported — good
  context showing ceiling.

## 6.6 Actions

| # | Action | Phase |
|---|---|---|
| 6.6.1 | Optional: add PR-AUC + majority-baseline line to external table | 9/10 |
| 6.6.2 | Optional: one calibration sentence | 9 |
| 6.6.3 | Keep 29.9%/78.08% explanation (already correct) | — |
