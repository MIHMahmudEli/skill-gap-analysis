# CPU re-run vs. committed artifacts

Author instruction 2026-10-12 (batch 3, step 3). Implements `reports/CPU_RERUN_PLAN.md`:
every registered experiment that reads raw inputs was re-executed on **CPU only**
(`OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1`, seed 42 pinned in each script, offline after
staging) into `results_cpu/`, isolated from `results/` via `SKILLGAP_OUTPUT_DIR`.
Nothing under `results/` was written; the manuscript and registry are untouched.
Runner: `scripts/run_cpu_rerun.py`.

Comparison rule: every numeric leaf of `metrics.json` is compared recursively.
Environment-dependent fields are excluded by construction (`runtime_sec`, `device`,
`seed`, `bootstrap_n`, `status`, timestamps, kernel slug). Tolerance is
`max(1e-9, 1e-6 × |value|)` — the author's 1e-6 relative rule.

## Result

**288 numeric fields compared across 8 experiments; 0 beyond tolerance;
every difference is exactly 0.** The agreement is bit-exact, not merely within
tolerance — the seven CPU-native experiments use no floating-point reductions that
depend on the BLAS threading level, and their outputs are integer counts, rounded
proportions and seeded-bootstrap percentiles that reproduce identically.

**Scope of the word "bit-exact" here.** It means the 288 numeric leaves of
`metrics.json` under the comparison rule above, and it is claimed **only** for
these 8 locally re-run experiments. The 5 embedding experiments listed in the next
section were verified later on a CPU-only Kaggle kernel and carry a narrower claim
in `reports/CPU_VS_COMMITTED_KAGGLE.md`: headline metrics agree at reported
precision; per-pair cosine similarities differ by at most 1e-4 (CPU vs GPU float
differences).

| | |
|---|---|
| Experiments re-run on CPU | 8 of 13 |
| Numeric fields compared | 288 |
| Beyond 1e-6 relative | **0** |
| Largest observed |diff| | 0 |

## Blocked: 5 embedding experiments could not re-run on this machine

> **Superseded 2026-10-13.** This section records the state at the time of this
> report. The block below is machine-level and still real, but the gap it
> describes is now closed: all 5 were re-executed on a CPU-only Kaggle kernel and
> verified against the committed artifacts — `reports/CPU_VS_COMMITTED_KAGGLE.md`,
> where the claim is headline metrics agree at reported precision; per-pair cosine
> similarities differ by at most 1e-4 (CPU vs GPU float differences). The text
> below is retained unchanged as the record of why they could not run here.

no CPU run — `import torch` blocked on this machine by an Application Control (WDAC/AppLocker) policy: `torch._C` fails to load with *"DLL load failed while importing _C:
An Application Control policy has blocked this file."* This affects
`ALIGN02_semantic_sbert, ALIGN03_domain_gap, ALIGN04_crosscorpus_linkedin, CURR01_cs2023_anchor, VALID01_esco_gold`. SENS01 is the sixth embedding experiment: it did re-run, in
batch-2 step 8, before the block appeared, and its outputs are byte-identical.

- The block is **machine-level, not a repository defect**: it is the same policy that
  already prevents `reproduce_stats.py` from importing `statsmodels` on this laptop
  (documented in `reports/CLEAN_ROOM_REPRO.md` §11).
- It is **new since batch-2 step 8**: SENS01 imported torch and completed a full
  byte-identical CPU run at commit `6a7fab4`; the same import now fails. The policy
  appears to have been refreshed or tightened between those runs.
- Python 3.12 is also installed but has no `torch`, so there is no alternative
  interpreter on this machine.
- The only experiment metric these five contribute to a manuscript headline is the
  embedding-based SGI; their committed values are **unchanged and unverified on CPU**,
  and are reported here as such rather than as agreeing. On a clean machine with the
  pinned `torch` and `sentence-transformers` versions the five are expected to re-run
  (their seeds and model revision are pinned), but that claim is **not evidenced by
  this report**.

No stop-point was triggered: no headline metric differs (the eight that ran agree
exactly), no registered number changed, and nothing here needs labels, downloads, or
CURR02/ALIGN05/ALIGN06. The five blocked experiments are an environment limitation, recorded above
and in the status board.

## Per-metric comparison

### ALIGN01_lexical_bootstrap

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `academic_corpus_token_count` | 20970 | 20970 | 0.000e+00 | 2.1e-02 | yes |
| `coverage_ci_lower` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `coverage_ci_upper` | 0.58 | 0.58 | 0.000e+00 | 5.8e-07 | yes |
| `coverage_rate` | 0.48 | 0.48 | 0.000e+00 | 4.8e-07 | yes |
| `market_corpus_token_count` | 1.07934e+07 | 1.07934e+07 | 0.000e+00 | 1.1e+01 | yes |
| `n_covered` | 48 | 48 | 0.000e+00 | 4.8e-05 | yes |
| `n_missing` | 52 | 52 | 0.000e+00 | 5.2e-05 | yes |
| `sgi` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `sgi_ci_lower` | 0.42 | 0.42 | 0.000e+00 | 4.2e-07 | yes |
| `sgi_ci_upper` | 0.63 | 0.63 | 0.000e+00 | 6.3e-07 | yes |
| `top_n` | 100 | 100 | 0.000e+00 | 1.0e-04 | yes |

### GEO01_linkedin_shares

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `n_rows` | 1.34845e+06 | 1.34845e+06 | 0.000e+00 | 1.3e+00 | yes |
| `n_with_location` | 1.34845e+06 | 1.34845e+06 | 0.000e+00 | 1.3e+00 | yes |
| `top_countries[0].postings` | 1.14934e+06 | 1.14934e+06 | 0.000e+00 | 1.1e+00 | yes |
| `top_countries[0].share_pct` | 85.23 | 85.23 | 0.000e+00 | 8.5e-05 | yes |
| `top_countries[1].postings` | 113421 | 113421 | 0.000e+00 | 1.1e-01 | yes |
| `top_countries[1].share_pct` | 8.41 | 8.41 | 0.000e+00 | 8.4e-06 | yes |
| `top_countries[2].postings` | 55972 | 55972 | 0.000e+00 | 5.6e-02 | yes |
| `top_countries[2].share_pct` | 4.15 | 4.15 | 0.000e+00 | 4.2e-06 | yes |
| `top_countries[3].postings` | 29719 | 29719 | 0.000e+00 | 3.0e-02 | yes |
| `top_countries[3].share_pct` | 2.2 | 2.2 | 0.000e+00 | 2.2e-06 | yes |
| `top_titles[0].count` | 7325 | 7325 | 0.000e+00 | 7.3e-03 | yes |
| `top_titles[1].count` | 5818 | 5818 | 0.000e+00 | 5.8e-03 | yes |
| `top_titles[2].count` | 5356 | 5356 | 0.000e+00 | 5.4e-03 | yes |
| `top_titles[3].count` | 5346 | 5346 | 0.000e+00 | 5.3e-03 | yes |
| `top_titles[4].count` | 5203 | 5203 | 0.000e+00 | 5.2e-03 | yes |
| `top_titles[5].count` | 4924 | 4924 | 0.000e+00 | 4.9e-03 | yes |
| `top_titles[6].count` | 4791 | 4791 | 0.000e+00 | 4.8e-03 | yes |
| `top_titles[7].count` | 4218 | 4218 | 0.000e+00 | 4.2e-03 | yes |
| `top_titles[8].count` | 4190 | 4190 | 0.000e+00 | 4.2e-03 | yes |
| `top_titles[9].count` | 2955 | 2955 | 0.000e+00 | 3.0e-03 | yes |

### INTL01_internship_effect

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `by_field[0].difference_pp` | 15.39 | 15.39 | 0.000e+00 | 1.5e-05 | yes |
| `by_field[0].n` | 50144 | 50144 | 0.000e+00 | 5.0e-02 | yes |
| `by_field[0].rate_with_internship_pct` | 57.82 | 57.82 | 0.000e+00 | 5.8e-05 | yes |
| `by_field[0].rate_without_internship_pct` | 42.43 | 42.43 | 0.000e+00 | 4.2e-05 | yes |
| `by_field[1].difference_pp` | 15.22 | 15.22 | 0.000e+00 | 1.5e-05 | yes |
| `by_field[1].n` | 49819 | 49819 | 0.000e+00 | 5.0e-02 | yes |
| `by_field[1].rate_with_internship_pct` | 57.42 | 57.42 | 0.000e+00 | 5.7e-05 | yes |
| `by_field[1].rate_without_internship_pct` | 42.2 | 42.2 | 0.000e+00 | 4.2e-05 | yes |
| `by_field[2].difference_pp` | 14.93 | 14.93 | 0.000e+00 | 1.5e-05 | yes |
| `by_field[2].n` | 50098 | 50098 | 0.000e+00 | 5.0e-02 | yes |
| `by_field[2].rate_with_internship_pct` | 57.72 | 57.72 | 0.000e+00 | 5.8e-05 | yes |
| `by_field[2].rate_without_internship_pct` | 42.79 | 42.79 | 0.000e+00 | 4.3e-05 | yes |
| `by_field[3].difference_pp` | 15.26 | 15.26 | 0.000e+00 | 1.5e-05 | yes |
| `by_field[3].n` | 49932 | 49932 | 0.000e+00 | 5.0e-02 | yes |
| `by_field[3].rate_with_internship_pct` | 57.55 | 57.55 | 0.000e+00 | 5.8e-05 | yes |
| `by_field[3].rate_without_internship_pct` | 42.3 | 42.3 | 0.000e+00 | 4.2e-05 | yes |
| `by_field[4].difference_pp` | 15.37 | 15.37 | 0.000e+00 | 1.5e-05 | yes |
| `by_field[4].n` | 50091 | 50091 | 0.000e+00 | 5.0e-02 | yes |
| `by_field[4].rate_with_internship_pct` | 57.59 | 57.59 | 0.000e+00 | 5.8e-05 | yes |
| `by_field[4].rate_without_internship_pct` | 42.23 | 42.23 | 0.000e+00 | 4.2e-05 | yes |
| `by_field[5].difference_pp` | 15.88 | 15.88 | 0.000e+00 | 1.6e-05 | yes |
| `by_field[5].n` | 49916 | 49916 | 0.000e+00 | 5.0e-02 | yes |
| `by_field[5].rate_with_internship_pct` | 57.48 | 57.48 | 0.000e+00 | 5.7e-05 | yes |
| `by_field[5].rate_without_internship_pct` | 41.6 | 41.6 | 0.000e+00 | 4.2e-05 | yes |
| `chi2` | 6813.13 | 6813.13 | 0.000e+00 | 6.8e-03 | yes |
| `chi2_p` | 0 | 0 | 0.000e+00 | 1.0e-09 | yes |
| `cohens_h` | 0.308 | 0.308 | 0.000e+00 | 3.1e-07 | yes |
| `cramers_v` | 0.1507 | 0.1507 | 0.000e+00 | 1.5e-07 | yes |
| `employment_rate_with_internship_pct` | 57.6 | 57.6 | 0.000e+00 | 5.8e-05 | yes |
| `employment_rate_without_internship_pct` | 42.26 | 42.26 | 0.000e+00 | 4.2e-05 | yes |
| `n_total` | 300000 | 300000 | 0.000e+00 | 3.0e-01 | yes |
| `risk_difference_ci_pp[0]` | 14.99 | 14.99 | 0.000e+00 | 1.5e-05 | yes |
| `risk_difference_ci_pp[1]` | 15.73 | 15.73 | 0.000e+00 | 1.6e-05 | yes |
| `risk_difference_pp` | 15.34 | 15.34 | 0.000e+00 | 1.5e-05 | yes |

### PLAC01_global_by_country

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `by_country[0].ci_lower_pct` | 61.03 | 61.03 | 0.000e+00 | 6.1e-05 | yes |
| `by_country[0].ci_upper_pct` | 65.27 | 65.27 | 0.000e+00 | 6.5e-05 | yes |
| `by_country[0].n` | 1985 | 1985 | 0.000e+00 | 2.0e-03 | yes |
| `by_country[0].placed` | 1254 | 1254 | 0.000e+00 | 1.3e-03 | yes |
| `by_country[0].placement_rate_pct` | 63.17 | 63.17 | 0.000e+00 | 6.3e-05 | yes |
| `by_country[1].ci_lower_pct` | 60.08 | 60.08 | 0.000e+00 | 6.0e-05 | yes |
| `by_country[1].ci_upper_pct` | 64.29 | 64.29 | 0.000e+00 | 6.4e-05 | yes |
| `by_country[1].n` | 2040 | 2040 | 0.000e+00 | 2.0e-03 | yes |
| `by_country[1].placed` | 1269 | 1269 | 0.000e+00 | 1.3e-03 | yes |
| `by_country[1].placement_rate_pct` | 62.21 | 62.21 | 0.000e+00 | 6.2e-05 | yes |
| `by_country[2].ci_lower_pct` | 59.37 | 59.37 | 0.000e+00 | 5.9e-05 | yes |
| `by_country[2].ci_upper_pct` | 63.66 | 63.66 | 0.000e+00 | 6.4e-05 | yes |
| `by_country[2].n` | 1976 | 1976 | 0.000e+00 | 2.0e-03 | yes |
| `by_country[2].placed` | 1216 | 1216 | 0.000e+00 | 1.2e-03 | yes |
| `by_country[2].placement_rate_pct` | 61.54 | 61.54 | 0.000e+00 | 6.2e-05 | yes |
| `by_country[3].ci_lower_pct` | 58.57 | 58.57 | 0.000e+00 | 5.9e-05 | yes |
| `by_country[3].ci_upper_pct` | 62.91 | 62.91 | 0.000e+00 | 6.3e-05 | yes |
| `by_country[3].n` | 1942 | 1942 | 0.000e+00 | 1.9e-03 | yes |
| `by_country[3].placed` | 1180 | 1180 | 0.000e+00 | 1.2e-03 | yes |
| `by_country[3].placement_rate_pct` | 60.76 | 60.76 | 0.000e+00 | 6.1e-05 | yes |
| `by_country[4].ci_lower_pct` | 57.86 | 57.86 | 0.000e+00 | 5.8e-05 | yes |
| `by_country[4].ci_upper_pct` | 62.09 | 62.09 | 0.000e+00 | 6.2e-05 | yes |
| `by_country[4].n` | 2057 | 2057 | 0.000e+00 | 2.1e-03 | yes |
| `by_country[4].placed` | 1234 | 1234 | 0.000e+00 | 1.2e-03 | yes |
| `by_country[4].placement_rate_pct` | 59.99 | 59.99 | 0.000e+00 | 6.0e-05 | yes |
| `n_total` | 10000 | 10000 | 0.000e+00 | 1.0e-02 | yes |
| `overall_ci_pct[0]` | 60.57 | 60.57 | 0.000e+00 | 6.1e-05 | yes |
| `overall_ci_pct[1]` | 62.48 | 62.48 | 0.000e+00 | 6.2e-05 | yes |
| `overall_placement_rate_pct` | 61.53 | 61.53 | 0.000e+00 | 6.2e-05 | yes |
| `salary_mean_placed` | 90105.9 | 90105.9 | 0.000e+00 | 9.0e-02 | yes |

### SENS01_sgi_sensitivity

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `academic_rows` | 1167 | 1167 | 0.000e+00 | 1.2e-03 | yes |
| `align04_asymmetric_replication.linkedin_2024_lexical_K100.expected_published` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `align04_asymmetric_replication.linkedin_2024_lexical_K100.got` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `align04_asymmetric_replication.linkedin_2024_semantic_K100_tau0.5.expected_published` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `align04_asymmetric_replication.linkedin_2024_semantic_K100_tau0.5.got` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `anchor_reproduction.hf_2024_lexical_K100.expected_published` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `anchor_reproduction.hf_2024_lexical_K100.got` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `anchor_reproduction.hf_2024_semantic_K100_tau0.5.expected_published` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `anchor_reproduction.hf_2024_semantic_K100_tau0.5.got` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `distinct_profile_skills_embedded` | 23456 | 23456 | 0.000e+00 | 2.3e-02 | yes |
| `grid.K[0]` | 50 | 50 | 0.000e+00 | 5.0e-05 | yes |
| `grid.K[1]` | 100 | 100 | 0.000e+00 | 1.0e-04 | yes |
| `grid.K[2]` | 200 | 200 | 0.000e+00 | 2.0e-04 | yes |
| `grid.K[3]` | 500 | 500 | 0.000e+00 | 5.0e-04 | yes |
| `grid.P[0]` | 100 | 100 | 0.000e+00 | 1.0e-04 | yes |
| `grid.P[1]` | 250 | 250 | 0.000e+00 | 2.5e-04 | yes |
| `grid.P[2]` | 500 | 500 | 0.000e+00 | 5.0e-04 | yes |
| `grid.P[3]` | 1000 | 1000 | 0.000e+00 | 1.0e-03 | yes |
| `grid.tau[0]` | 0.4 | 0.4 | 0.000e+00 | 4.0e-07 | yes |
| `grid.tau[1]` | 0.5 | 0.5 | 0.000e+00 | 5.0e-07 | yes |
| `grid.tau[2]` | 0.6 | 0.6 | 0.000e+00 | 6.0e-07 | yes |
| `grid.tau[3]` | 0.7 | 0.7 | 0.000e+00 | 7.0e-07 | yes |
| `manuscript_claim_checks.hf_2024_P100_symmetric_lexical.expected_manuscript` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `manuscript_claim_checks.hf_2024_P100_symmetric_lexical.got` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `manuscript_claim_checks.hf_2024_P100_symmetric_semantic_tau0.5.expected_manuscript` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `manuscript_claim_checks.hf_2024_P100_symmetric_semantic_tau0.5.got` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `manuscript_claim_checks.hf_2024_P500_asymmetric_lexical.expected_manuscript` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `manuscript_claim_checks.hf_2024_P500_asymmetric_lexical.got` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `manuscript_claim_checks.hf_2024_P500_asymmetric_semantic_tau0.5.expected_manuscript` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `manuscript_claim_checks.hf_2024_P500_asymmetric_semantic_tau0.5.got` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P100_symmetric_lexical.expected_manuscript` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P100_symmetric_lexical.got` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P100_symmetric_semantic_tau0.5.expected_manuscript` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P100_symmetric_semantic_tau0.5.got` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P500_asymmetric_lexical.expected_manuscript` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P500_asymmetric_lexical.got` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P500_asymmetric_semantic_tau0.5.expected_manuscript` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `manuscript_claim_checks.linkedin_2024_P500_asymmetric_semantic_tau0.5.got` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `matched_profile_replication.hf_2024.P100_symmetric_lexical` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `matched_profile_replication.hf_2024.P100_symmetric_semantic_tau0.5` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `matched_profile_replication.hf_2024.P500_asymmetric_lexical` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `matched_profile_replication.hf_2024.P500_asymmetric_semantic_tau0.5` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `matched_profile_replication.linkedin_2024.P100_symmetric_lexical` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `matched_profile_replication.linkedin_2024.P100_symmetric_semantic_tau0.5` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `matched_profile_replication.linkedin_2024.P500_asymmetric_lexical` | 0.37 | 0.37 | 0.000e+00 | 3.7e-07 | yes |
| `matched_profile_replication.linkedin_2024.P500_asymmetric_semantic_tau0.5` | 0.14 | 0.14 | 0.000e+00 | 1.4e-07 | yes |
| `n_postings.hf_2024` | 518953 | 518953 | 0.000e+00 | 5.2e-01 | yes |
| `n_postings.linkedin_2024` | 1.2943e+06 | 1.2943e+06 | 0.000e+00 | 1.3e+00 | yes |
| `n_table_rows` | 200 | 200 | 0.000e+00 | 2.0e-04 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.lexical.max` | 0.728 | 0.728 | 0.000e+00 | 7.3e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.lexical.min` | 0.52 | 0.52 | 0.000e+00 | 5.2e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.4.max` | 0.24 | 0.24 | 0.000e+00 | 2.4e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.4.min` | 0.094 | 0.094 | 0.000e+00 | 9.4e-08 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.5.max` | 0.42 | 0.42 | 0.000e+00 | 4.2e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.5.min` | 0.26 | 0.26 | 0.000e+00 | 2.6e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.6.max` | 0.53 | 0.53 | 0.000e+00 | 5.3e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.6.min` | 0.32 | 0.32 | 0.000e+00 | 3.2e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.7.max` | 0.605 | 0.605 | 0.000e+00 | 6.0e-07 | yes |
| `sgi_ranges_over_KP_grid.hf_2024.semantic_tau_0.7.min` | 0.44 | 0.44 | 0.000e+00 | 4.4e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.lexical.max` | 0.736 | 0.736 | 0.000e+00 | 7.4e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.lexical.min` | 0.53 | 0.53 | 0.000e+00 | 5.3e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.4.max` | 0.25 | 0.25 | 0.000e+00 | 2.5e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.4.min` | 0.094 | 0.094 | 0.000e+00 | 9.4e-08 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.5.max` | 0.38 | 0.38 | 0.000e+00 | 3.8e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.5.min` | 0.258 | 0.258 | 0.000e+00 | 2.6e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.6.max` | 0.48 | 0.48 | 0.000e+00 | 4.8e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.6.min` | 0.34 | 0.34 | 0.000e+00 | 3.4e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.7.max` | 0.58 | 0.58 | 0.000e+00 | 5.8e-07 | yes |
| `sgi_ranges_over_KP_grid.linkedin_2024.semantic_tau_0.7.min` | 0.45 | 0.45 | 0.000e+00 | 4.5e-07 | yes |

### STAT01_placement_core

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `base_rate_placed` | 0.1659 | 0.1659 | 0.000e+00 | 1.7e-07 | yes |
| `chi_square[0].Cramers_V` | 0.006 | 0.006 | 0.000e+00 | 6.0e-09 | yes |
| `chi_square[0].chi2` | 0.31 | 0.31 | 0.000e+00 | 3.1e-07 | yes |
| `chi_square[0].df` | 1 | 1 | 0.000e+00 | 1.0e-06 | yes |
| `chi_square[0].p_value` | 0.5778 | 0.5778 | 0.000e+00 | 5.8e-07 | yes |
| `chi_square[1].Cramers_V` | 0.268 | 0.268 | 0.000e+00 | 2.7e-07 | yes |
| `chi_square[1].chi2` | 719.821 | 719.821 | 0.000e+00 | 7.2e-04 | yes |
| `chi_square[1].df` | 2 | 2 | 0.000e+00 | 2.0e-06 | yes |
| `chi_square[1].p_value` | 4.931e-157 | 4.931e-157 | 0.000e+00 | 1.0e-09 | yes |
| `logistic_insample_accuracy` | 0.9013 | 0.9013 | 0.000e+00 | 9.0e-07 | yes |
| `logistic_pseudo_r2_mcfadden` | 0.513 | 0.513 | 0.000e+00 | 5.1e-07 | yes |
| `n_not_placed` | 8341 | 8341 | 0.000e+00 | 8.3e-03 | yes |
| `n_placed` | 1659 | 1659 | 0.000e+00 | 1.7e-03 | yes |
| `n_total` | 10000 | 10000 | 0.000e+00 | 1.0e-02 | yes |
| `table4_logistic[0].Coefficient` | 1.8368 | 1.8368 | 0.000e+00 | 1.8e-06 | yes |
| `table4_logistic[0].OR_CI_Lower` | 5.6214 | 5.6214 | 0.000e+00 | 5.6e-06 | yes |
| `table4_logistic[0].OR_CI_Upper` | 7.0081 | 7.0081 | 0.000e+00 | 7.0e-06 | yes |
| `table4_logistic[0].Odds_Ratio` | 6.2765 | 6.2765 | 0.000e+00 | 6.3e-06 | yes |
| `table4_logistic[0].Std_Error` | 0.0562 | 0.0562 | 0.000e+00 | 5.6e-08 | yes |
| `table4_logistic[0].p_value` | 6.754e-234 | 6.754e-234 | 0.000e+00 | 1.0e-09 | yes |
| `table4_logistic[0].z` | 32.655 | 32.655 | 0.000e+00 | 3.3e-05 | yes |
| `table4_logistic[1].Coefficient` | 1.879 | 1.879 | 0.000e+00 | 1.9e-06 | yes |
| `table4_logistic[1].OR_CI_Lower` | 5.8615 | 5.8615 | 0.000e+00 | 5.9e-06 | yes |
| `table4_logistic[1].OR_CI_Upper` | 7.313 | 7.313 | 0.000e+00 | 7.3e-06 | yes |
| `table4_logistic[1].Odds_Ratio` | 6.5471 | 6.5471 | 0.000e+00 | 6.5e-06 | yes |
| `table4_logistic[1].Std_Error` | 0.0564 | 0.0564 | 0.000e+00 | 5.6e-08 | yes |
| `table4_logistic[1].p_value` | 5.286e-243 | 5.286e-243 | 0.000e+00 | 1.0e-09 | yes |
| `table4_logistic[1].z` | 33.291 | 33.291 | 0.000e+00 | 3.3e-05 | yes |
| `table4_logistic[2].Coefficient` | 1.1644 | 1.1644 | 0.000e+00 | 1.2e-06 | yes |
| `table4_logistic[2].OR_CI_Lower` | 2.9249 | 2.9249 | 0.000e+00 | 2.9e-06 | yes |
| `table4_logistic[2].OR_CI_Upper` | 3.5099 | 3.5099 | 0.000e+00 | 3.5e-06 | yes |
| `table4_logistic[2].Odds_Ratio` | 3.2041 | 3.2041 | 0.000e+00 | 3.2e-06 | yes |
| `table4_logistic[2].Std_Error` | 0.0465 | 0.0465 | 0.000e+00 | 4.6e-08 | yes |
| `table4_logistic[2].p_value` | 2.444e-138 | 2.444e-138 | 0.000e+00 | 1.0e-09 | yes |
| `table4_logistic[2].z` | 25.037 | 25.037 | 0.000e+00 | 2.5e-05 | yes |
| `table4_logistic[3].Coefficient` | 0.0192 | 0.0192 | 0.000e+00 | 1.9e-08 | yes |
| `table4_logistic[3].OR_CI_Lower` | 0.9449 | 0.9449 | 0.000e+00 | 9.4e-07 | yes |
| `table4_logistic[3].OR_CI_Upper` | 1.0997 | 1.0997 | 0.000e+00 | 1.1e-06 | yes |
| `table4_logistic[3].Odds_Ratio` | 1.0194 | 1.0194 | 0.000e+00 | 1.0e-06 | yes |
| `table4_logistic[3].Std_Error` | 0.0387 | 0.0387 | 0.000e+00 | 3.9e-08 | yes |
| `table4_logistic[3].p_value` | 0.6197 | 0.6197 | 0.000e+00 | 6.2e-07 | yes |
| `table4_logistic[3].z` | 0.496 | 0.496 | 0.000e+00 | 5.0e-07 | yes |
| `table4_logistic[4].Coefficient` | 1.6404 | 1.6404 | 0.000e+00 | 1.6e-06 | yes |
| `table4_logistic[4].OR_CI_Lower` | 4.6494 | 4.6494 | 0.000e+00 | 4.6e-06 | yes |
| `table4_logistic[4].OR_CI_Upper` | 5.72 | 5.72 | 0.000e+00 | 5.7e-06 | yes |
| `table4_logistic[4].Odds_Ratio` | 5.157 | 5.157 | 0.000e+00 | 5.2e-06 | yes |
| `table4_logistic[4].Std_Error` | 0.0529 | 0.0529 | 0.000e+00 | 5.3e-08 | yes |
| `table4_logistic[4].p_value` | 2.135e-211 | 2.135e-211 | 0.000e+00 | 1.0e-09 | yes |
| `table4_logistic[4].z` | 31.03 | 31.03 | 0.000e+00 | 3.1e-05 | yes |
| `table4_logistic[5].Coefficient` | -0.0207 | -0.0207 | 0.000e+00 | 2.1e-08 | yes |
| `table4_logistic[5].OR_CI_Lower` | 0.9086 | 0.9086 | 0.000e+00 | 9.1e-07 | yes |
| `table4_logistic[5].OR_CI_Upper` | 1.0559 | 1.0559 | 0.000e+00 | 1.1e-06 | yes |
| `table4_logistic[5].Odds_Ratio` | 0.9795 | 0.9795 | 0.000e+00 | 9.8e-07 | yes |
| `table4_logistic[5].Std_Error` | 0.0383 | 0.0383 | 0.000e+00 | 3.8e-08 | yes |
| `table4_logistic[5].p_value` | 0.5884 | 0.5884 | 0.000e+00 | 5.9e-07 | yes |
| `table4_logistic[5].z` | -0.541 | -0.541 | 0.000e+00 | 5.4e-07 | yes |
| `tree_audit.cart_vs_kofn_agreement` | 0.9992 | 0.9992 | 0.000e+00 | 1.0e-06 | yes |
| `tree_audit.depth4_cart_train_accuracy` | 1 | 1 | 0.000e+00 | 1.0e-06 | yes |
| `tree_audit.kofn_agreement_with_labels` | 0.9992 | 0.9992 | 0.000e+00 | 1.0e-06 | yes |

### STAT02_external_validation

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `results[0].accuracy` | 0.2986 | 0.2986 | 0.000e+00 | 3.0e-07 | yes |
| `results[0].auc` | 0.768 | 0.768 | 0.000e+00 | 7.7e-07 | yes |
| `results[0].base_rate` | 0.7808 | 0.7808 | 0.000e+00 | 7.8e-07 | yes |
| `results[0].f1_weighted` | 0.2346 | 0.2346 | 0.000e+00 | 2.3e-07 | yes |
| `results[0].n` | 50000 | 50000 | 0.000e+00 | 5.0e-02 | yes |
| `results[1].accuracy` | 0.8073 | 0.8073 | 0.000e+00 | 8.1e-07 | yes |
| `results[1].auc` | 0.7816 | 0.7816 | 0.000e+00 | 7.8e-07 | yes |
| `results[1].base_rate` | 0.7808 | 0.7808 | 0.000e+00 | 7.8e-07 | yes |
| `results[1].f1_weighted` | 0.7763 | 0.7763 | 0.000e+00 | 7.8e-07 | yes |
| `results[1].n` | 50000 | 50000 | 0.000e+00 | 5.0e-02 | yes |
| `results[2].accuracy` | 0.6153 | 0.6153 | 0.000e+00 | 6.2e-07 | yes |
| `results[2].auc` | 0.5757 | 0.5757 | 0.000e+00 | 5.8e-07 | yes |
| `results[2].base_rate` | 0.6153 | 0.6153 | 0.000e+00 | 6.2e-07 | yes |
| `results[2].f1_weighted` | 0.4688 | 0.4688 | 0.000e+00 | 4.7e-07 | yes |
| `results[2].n` | 10000 | 10000 | 0.000e+00 | 1.0e-02 | yes |
| `results[3].accuracy` | 0.6846 | 0.6846 | 0.000e+00 | 6.8e-07 | yes |
| `results[3].auc` | 0.7142 | 0.7142 | 0.000e+00 | 7.1e-07 | yes |
| `results[3].base_rate` | 0.6153 | 0.6153 | 0.000e+00 | 6.2e-07 | yes |
| `results[3].f1_weighted` | 0.6694 | 0.6694 | 0.000e+00 | 6.7e-07 | yes |
| `results[3].n` | 10000 | 10000 | 0.000e+00 | 1.0e-02 | yes |

### TRENDS01_ai_longitudinal

| Metric | Committed | CPU | abs diff | tol | ok |
|---|---|---|---|---|---|
| `n_postings` | 10345 | 10345 | 0.000e+00 | 1.0e-02 | yes |
| `salary_anova.anova_f` | 3615.56 | 3615.56 | 0.000e+00 | 3.6e-03 | yes |
| `salary_anova.p_value` | 0 | 0 | 0.000e+00 | 1.0e-09 | yes |
| `yearly_shares[0].cloud_share_pct` | 52.04 | 52.04 | 0.000e+00 | 5.2e-05 | yes |
| `yearly_shares[0].deep_learning_share_pct` | 50.89 | 50.89 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[0].ml_share_pct` | 48.84 | 48.84 | 0.000e+00 | 4.9e-05 | yes |
| `yearly_shares[0].python_share_pct` | 47.48 | 47.48 | 0.000e+00 | 4.7e-05 | yes |
| `yearly_shares[0].sql_share_pct` | 51.91 | 51.91 | 0.000e+00 | 5.2e-05 | yes |
| `yearly_shares[0].year` | 2020 | 2020 | 0.000e+00 | 2.0e-03 | yes |
| `yearly_shares[1].cloud_share_pct` | 53.85 | 53.85 | 0.000e+00 | 5.4e-05 | yes |
| `yearly_shares[1].deep_learning_share_pct` | 50.61 | 50.61 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[1].ml_share_pct` | 51.01 | 51.01 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[1].python_share_pct` | 49.66 | 49.66 | 0.000e+00 | 5.0e-05 | yes |
| `yearly_shares[1].sql_share_pct` | 50.47 | 50.47 | 0.000e+00 | 5.0e-05 | yes |
| `yearly_shares[1].year` | 2021 | 2021 | 0.000e+00 | 2.0e-03 | yes |
| `yearly_shares[2].cloud_share_pct` | 47.05 | 47.05 | 0.000e+00 | 4.7e-05 | yes |
| `yearly_shares[2].deep_learning_share_pct` | 48.73 | 48.73 | 0.000e+00 | 4.9e-05 | yes |
| `yearly_shares[2].ml_share_pct` | 49.73 | 49.73 | 0.000e+00 | 5.0e-05 | yes |
| `yearly_shares[2].python_share_pct` | 47.59 | 47.59 | 0.000e+00 | 4.8e-05 | yes |
| `yearly_shares[2].sql_share_pct` | 51.41 | 51.41 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[2].year` | 2022 | 2022 | 0.000e+00 | 2.0e-03 | yes |
| `yearly_shares[3].cloud_share_pct` | 51.38 | 51.38 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[3].deep_learning_share_pct` | 51.1 | 51.1 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[3].ml_share_pct` | 53.51 | 53.51 | 0.000e+00 | 5.4e-05 | yes |
| `yearly_shares[3].python_share_pct` | 52.2 | 52.2 | 0.000e+00 | 5.2e-05 | yes |
| `yearly_shares[3].sql_share_pct` | 49.79 | 49.79 | 0.000e+00 | 5.0e-05 | yes |
| `yearly_shares[3].year` | 2023 | 2023 | 0.000e+00 | 2.0e-03 | yes |
| `yearly_shares[4].cloud_share_pct` | 50.73 | 50.73 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[4].deep_learning_share_pct` | 49.07 | 49.07 | 0.000e+00 | 4.9e-05 | yes |
| `yearly_shares[4].ml_share_pct` | 51 | 51 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[4].python_share_pct` | 48.8 | 48.8 | 0.000e+00 | 4.9e-05 | yes |
| `yearly_shares[4].sql_share_pct` | 50.4 | 50.4 | 0.000e+00 | 5.0e-05 | yes |
| `yearly_shares[4].year` | 2024 | 2024 | 0.000e+00 | 2.0e-03 | yes |
| `yearly_shares[5].cloud_share_pct` | 51.11 | 51.11 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[5].deep_learning_share_pct` | 48.41 | 48.41 | 0.000e+00 | 4.8e-05 | yes |
| `yearly_shares[5].ml_share_pct` | 52.26 | 52.26 | 0.000e+00 | 5.2e-05 | yes |
| `yearly_shares[5].python_share_pct` | 51.11 | 51.11 | 0.000e+00 | 5.1e-05 | yes |
| `yearly_shares[5].sql_share_pct` | 49.9 | 49.9 | 0.000e+00 | 5.0e-05 | yes |
| `yearly_shares[5].year` | 2025 | 2025 | 0.000e+00 | 2.0e-03 | yes |
| `yearly_shares[6].cloud_share_pct` | 51.91 | 51.91 | 0.000e+00 | 5.2e-05 | yes |
| `yearly_shares[6].deep_learning_share_pct` | 49.86 | 49.86 | 0.000e+00 | 5.0e-05 | yes |
| `yearly_shares[6].ml_share_pct` | 49.18 | 49.18 | 0.000e+00 | 4.9e-05 | yes |
| `yearly_shares[6].python_share_pct` | 48.36 | 48.36 | 0.000e+00 | 4.8e-05 | yes |
| `yearly_shares[6].sql_share_pct` | 48.23 | 48.23 | 0.000e+00 | 4.8e-05 | yes |
| `yearly_shares[6].year` | 2026 | 2026 | 0.000e+00 | 2.0e-03 | yes |
