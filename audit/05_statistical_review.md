# Phase 5 — Statistical Audit

*Date: 2026-10-11 · Tool: `audit/reproduce_stats.py` →
`audit/05_stat_reproduction.json` (independent local re-fit from raw CSVs,
statsmodels 0.15.0 / scikit-learn 1.9.0, seed 42).*

## 5.1 Independent Reproduction Table (STAT01 / INTL01)

| Quantity | Published | Reproduced | Δ | Verdict |
|---|---|---|---|---|
| N / placed / base rate | 10,000 / 1,659 / 16.59% | same | 0 | ✓ |
| Welch CGPA t / d | 39.37 / 0.913 | 39.37 / 0.913 | 0 | ✓ |
| Welch Comm t / d | 35.79 / 0.918 | 35.79 / 0.918 | 0 | ✓ |
| Welch Projects t / d | 27.21 / 0.599 | 27.21 / 0.599 | 0 | ✓ |
| AcadPerf p / d | 0.1386 / −0.040 | 0.1386 / −0.040 | 0 | ✓ |
| ExtraCurr p / d | 0.6383 / −0.013 | 0.6383 / −0.013 | 0 | ✓ |
| χ² internship (V) | 0.31 (0.006), p=0.578 | 0.31 (0.006), p=0.5778 | ~0 | ✓ |
| χ² projects (V) | 719.82 (0.268) | 721.47 (0.269)* | +1.65 | ✓ (binning) |
| Logistic OR Comm / CGPA / IQ / Projects | 6.547 / 6.277 / 5.157 / 3.204 | identical to 4 d.p. | 0 | ✓ |
| Logistic OR Internship (p) | 1.019 (0.620 ns) | 1.019 (0.620 ns) | 0 | ✓ |
| Logit in-sample acc | 0.9013 | 0.9013 | 0 | ✓ |
| VIF (all features) | 1.000–1.001 | 1.000–1.001 | 0 | ✓ |
| CV 5-fold LR acc / AUC | 0.9011 / 0.9406 | 0.9011 / **0.9407** | +0.0001 | ✓ (fold RNG tie) |
| CV RF / DT acc | 0.9999 / 0.9997 | 1.0000 / 0.9997 | ≤0.0001 | ✓ |
| Majority baseline | 0.8341 | 0.8341 | 0 | ✓ |
| **Internship RD (college, univariate)** | *"+0.08 pp"* (manuscript) | **−0.4442 pp** | — | ✗ **contradicts manuscript** |
| INTL01: emp w/ w/o internship, RD | 57.60 / 42.26 / +15.34 | 57.60 / 42.26 / +15.34 | 0 | ✓ |

\* χ²-projects: audit used raw `Projects_Completed` categories (df>2);
STAT01 grouped into 3 bins (df=2). Both p ≈ 1e−150; V differs by 0.001.
Not a defect; grouping should stay documented (it is, in the script).

**Conclusion:** every inferential statistic in RQ4/RQ5 reproduces from raw
data except the manuscript's "+0.08 pp" internship sentence (Phase 1 D-1).

## 5.2 Uncertainty and Sampling Units

| Analysis | Resampling unit in code | Appropriateness |
|---|---|---|
| SGI CIs (ALIGN01/02/04) | top-100 **skill indicators** | List-composition uncertainty; not market sampling error. Acceptable if worded precisely (Phase 3.6). |
| Domain-deficit CIs (ALIGN03/04) | **postings** (1,000×) | Appropriate for posting-level estimands; ignores employer clustering (postings from same employer not resampled as clusters — moderate concern; employer IDs exist in LinkedIn jobs table). |
| CURR01 | CS2023 **topics** | Appropriate. |
| VALID01 κ/acc | **pairs** (1,000×) | Pairs from same mention are dependent; mention-level cluster bootstrap would be stricter. CIs may be slightly narrow. |
| INTL01 RD | normal/binomial approx on 300K rows | Fine at this N. |
| Logistic Wald CIs | MLE asymptotics | Fine at N=10K, no separation. |

## 5.3 Hypothesis Testing / Multiplicity

- Six hypotheses (H1–H6) are now explicitly stated (§II-E) with named
  experiments — good practice; verdicts in Table XIII.
- No family-wise correction across the many Welch tests / 8 domain gaps /
  5 classifiers. The manuscript does not claim FWER control; primary claims
  ride on effect sizes with CIs rather than on thresholded p-values —
  acceptable, but one sentence ("exploratory tests are not multiplicity-
  corrected; primary inferences are interval-based") would preempt a
  reviewer objection.
- "Supported" for H5 via INTL01 (+15.3 pp) is an **observational contrast**,
  not a causal test; §III/§V-A call the design associative (Limitation 10)
  — consistent, keep.

## 5.4 Regression and Causal Interpretation

- Model spec reproduced exactly (standardized predictors, intercept,
  statsmodels Logit). Odds ratios per 1 SD — correctly labeled.
- Internship null in multivariate model (OR≈1.02, p=0.62) **plus**
  univariate RD≈−0.44 pp jointly refute H6 on this cohort; INTL01's +15.3 pp
  is a different dataset/population (international graduates) and supports
  a descriptive association only. The manuscript must not present INTL01 as
  causal (it currently does not — Limitation 10 covers this).
- No propensity scores / IV / DiD — appropriate not to imply causality.

## 5.5 Robustness Already Present

- Multi-seed CV (seeds 0–9) — in STAT01 artifacts ✓.
- τ-sweep for SGI ✓; profile-size sweep added by this audit (Phase 3).
- External cohorts STAT02 ✓ (Phase 6).

## 5.6 Actions

| # | Action | Phase |
|---|---|---|
| 5.6.1 | Replace "+0.08 pp" with −0.44 pp (univariate) and/or OR-only phrasing; fix Table XIII attribution | 9 |
| 5.6.2 | Optional: one sentence on multiplicity posture | 9 |
| 5.6.3 | Optional: mention-level cluster bootstrap for VALID01 CIs (would need re-run; not blocking) | later |
