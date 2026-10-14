# SENS02 pre-registration — occupational reference-profile covering-set sweep at fixed market profile size *K* = 100

**Status:** PRE-REGISTERED, NOT RUN. Registry entry `results/registry.json →
SENS02_covering_set_sweep` is created by this commit with status `REGISTERED`
and **no** `metrics.json` exists (test_reproducibility `NOT_YET_RUN`). No
number below has been computed; every value in §6 that is not explicitly
labelled *expected* was written before the run. Written 2026-10-14 per the
author's definition-fix batch (step 4). Amendments after this commit must be
appended as dated, reasoned amendment blocks — never by silent edit.

## 1. Question

Is the headline level change **lexical/semantic SGI 0.52/0.32 → 0.37/0.14**
between ALIGN01/02 (HF, reference-profile covering set *P* = 100) and
ALIGN03/04 (LinkedIn, *P* = 500) caused by the **market corpus** or by the
**covering-set size**?

SENS01's `matched_profile_replication` block already shows both corpora give
0.52/0.32 at *P* = 100 and 0.37/0.14 at *P* = 500, i.e. two points of the
curve. That block is a *post-hoc* reproduction embedded inside another
experiment: it sweeps only two sizes, carries no bootstrap of its own, and is
not separately registered. SENS02 turns it into a registered experiment with
the full size grid, both bootstraps, and both corpora.

**Primary quantity:** SGI as a function of covering-set size *P*_acad at fixed
*K* = 100, per corpus.

> **Notation.** *P*_acad is the size of the occupational reference-profile
> covering set (the manuscript's *P*; "academic" in this symbol is the source
> label of `datasets/hf_job_skill_set.csv`). It is **not** SENS01's grid
> dimension — that is the market posting sample size, written
> *n*_post (renamed 2026-10-14, manuscript §III-C). SENS02 does not touch
> *n*_post at all.

## 2. Fixed design (nothing varies but *P*_acad)

| Component | Value | Source |
|---|---|---|
| Market profile size *K* | **100**, from the **full** corpus (no sub-sampling) | ALIGN01/02 headline |
| Covering-set size *P*_acad | **{100, 250, 500, 1000, all}** | swept — the only axis |
| Corpora | `hf_2024` (518,953 postings), `linkedin_2024` (1,294,296) | `datasets/` |
| Reference profile | all 1,167 rows of `hf_job_skill_set.csv`, 5,047 distinct skills | ALIGN01/02 |
| Matcher | lexical = exact skill-string intersection; semantic = `all-MiniLM-L6-v2`, cosine ≥ τ | imported, unmodified |
| Thresholds τ | {0.4, 0.5, 0.6, 0.7}, baseline 0.5 | ALIGN02 |
| SGI | `SGI = 1 − coverage` | SENS01 |
| Seed | **42** | all experiments |
| Profile tie-break | (count desc, first-seen idx asc) = `Counter.most_common` | `sens01.top_profile` |

Grid size: 2 corpora × 5 *P*_acad × (1 lexical + 4 semantic) = **50 cells**.

*"all"* = every skill present in the reference profile (all non-zero entries of
the academic count vector, 5,047 skills), i.e. the covering set is no longer
truncated.

## 3. Non-circularity firewall (binding)

1. **No posting sub-sampling.** The market side of every *point estimate* uses
   the full corpus, exactly as the headline does. The *n*_post axis of SENS01
   is neither read nor written.
2. **The instrument is imported, not rewritten.** Corpus loaders, `TokenIndex`,
   `full_counts`, `top_profile`, `skill_ci` and the embedding path come from
   `experiments/exp_scripts/sens01_sgi_sensitivity.py` loaded by path. SENS02
   adds exactly one new function — an *asymmetric* coverage indicator taking
   separate *K* and *P*_acad — plus the driver.
3. **No registered number may change.** SENS02 writes only into
   `results/SENS02_covering_set_sweep/`. `table_sensitivity_grid.csv`,
   `metrics.json` of every other experiment, and every manuscript figure are
   untouched.

## 4. Bootstrap (two intervals per cell, same definitions as SENS01)

**CI_skill — skill-list uncertainty, B = 1000.**
Resample the *K* = 100 binary coverage indicators with replacement; percentile
[2.5, 97.5] over replicates of SGI. Identical construction to the headline
interval: "how far would this move if a different top-*K* list had topped the
frequency ranking?". One `RandomState(42)` per cell, so index draws are paired
across cells.

**CI_post — posting-level uncertainty, B = 500.**
Resample postings **with replacement at the full corpus size** (518,953 /
1,294,296) *and* all 1,167 reference-profile rows, then rebuild **both**
profiles inside every replicate: market top-100 from the resampled postings,
occupational top-*P*_acad from the resampled reference rows. Percentile
[2.5, 97.5] over replicate SGIs.

*Implementation note (deviation from SENS01's code path, fixed before the
run).* SENS01's `sample_counts` materialises an `(n, maxlen)` gather; with
`maxlen = 463` a full-corpus draw is a ~2 GB allocation, which is why SENS01
marks its own `n_post = all` rows `NaN`. SENS02 needs that draw at every
replicate, so it uses the algebraically identical sparse form
`counts = w @ T` with `w = bincount(rng.randint(0, n, n))` and
`T = coo_matrix` of the row×skill counts. Probed 2026-10-14: bit-identical to
`sample_counts` on the same RNG draw (`array_equal == True`), 0.03 s (hf) and
0.13 s (linkedin) per replicate. The interval definition in this section is
therefore unchanged; only the arithmetic that evaluates it is cheaper.

Stream scheme: market replicate *i* of corpus *c* → `RandomState(42 + 1000·c + i)`;
reference-row replicate *i* → `RandomState(42 + 5000 + i)`, **shared across
corpora** so the two corpora are compared under an identical reference-row draw.

## 5. Outputs

```
results/SENS02_covering_set_sweep/
  table_covering_set_sweep.csv   # 50 rows, one per cell
  metrics.json                   # status, grid, registered contrasts
```

CSV columns: `corpus, match, tau, K, P_acad, SGI, coverage, CI_skill_lo,
CI_skill_hi, CI_post_lo, CI_post_hi`.
`P_acad` is written as the integer size or the literal `all`.
Column names here are new; **no existing registered column is renamed.**

## 6. Registered contrasts (evaluated and recorded by the run)

| ID | Contrast | Expected |
|---|---|---|
| R1 | *P*_acad = 100, *K* = 100, lexical, both corpora | **0.52** exactly (reproduces ALIGN01 headline *and* SENS01 `matched_profile`) |
| R2 | *P*_acad = 100, semantic τ = 0.5, both corpora | **0.32** ± 0.02 |
| R3 | *P*_acad = 500, lexical, both corpora | **0.37** exactly (reproduces ALIGN04) |
| R4 | *P*_acad = 500, semantic τ = 0.5, both corpora | **0.14** ± 0.02 |
| R5 | **Level change:** SGI(100) − SGI(500), lexical, per corpus | **0.15** on both corpora → the 0.52→0.37 change is a covering-set effect |
| R6 | Cross-corpus gap at each *P*_acad | ≤ 0.01 lexical, ≤ 0.02 semantic @ τ = 0.5 |
| R7 | Monotonicity | coverage non-decreasing in *P*_acad (SGI non-increasing) at every corpus × match × τ |

**Decision rule for the manuscript's profile-size paragraph (§5 of the batch).**
If R5 holds on *both* corpora **and** R6 holds, the level difference is
*fully* explained by covering-set size and corpus contributes nothing at
matched *P*_acad — the paragraph may cite SENS02 instead of
SENS01/ALIGN04 alone. If either fails, the paragraph keeps its current
wording and SENS02 is reported as a null/qualifying result.

## 7. Reporting rules and non-goals (binding)

1. **No headline number changes.** 52.0 %, 32.0 %, [23.0 %, 41.0 %], 0.37,
   0.14, 30.4 % stand as published; SENS02 neither replaces nor re-estimates them.
2. **R7 is descriptive.** A monotone curve is a mechanical consequence of a
   growing covering set; it is not evidence about labour markets.
3. **The absolute level at large *P*_acad is a parameter choice, not a
   discovery.** Report the curve; do not re-centre any claim on it.
4. **Sensitivity, not inference.** No p-values, no hypothesis verdicts H1–H3
   are re-opened by SENS02.
5. The abstract mentions SENS02 **only** if the result changes the
   interpretation of an existing abstract sentence (author instruction, batch
   step 5).

## 8. Registration, seed, artifacts

* Experiment ID: `SENS02_covering_set_sweep`
* Registry: `results/registry.json`, entry created **by this commit**, status
  `REGISTERED`, `run_mode: local`, `seed: 42`, deps
  `["SENS01_sgi_sensitivity", "ALIGN01_lexical_bootstrap", "ALIGN02_semantic_sbert", "ALIGN04_crosscorpus_linkedin"]`
* Test hook: `tests/test_reproducibility.py → NOT_YET_RUN =
  {"SENS02_covering_set_sweep"}` until the run finishes; the ID is removed in
  the same commit that lands `metrics.json`.
* Script: `experiments/exp_scripts/sens02_covering_set_sweep.py`
* Verification: `experiments/verify.py → REQUIRED["SENS02_covering_set_sweep"]
  = ["metrics.json", "table_covering_set_sweep.csv"]` added **with the run**,
  then `audit/verify_claims.py` checks R1–R7 and the ledger gains the rows.

## 9. Amendments

*(none yet — append dated blocks here; never edit §1–§8 silently)*
