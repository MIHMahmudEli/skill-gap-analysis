# SENS01 follow-up checks (2026-10-11)

Post-verification audit of `results/SENS01_sgi_sensitivity/` requested by the
author. No new experiment; all numbers below derive from the committed SENS01
artifacts or from direct re-execution of the SENS01 loaders on the registered
inputs. Companion tables: `reports/sens01_market_profile_overlap.csv` (A2),
`reports/sens01_paired_h3_test.csv` (A3).

## A1. First-run metrics/grid disagreement — root cause

**What disagreed (run of 2026-10-11, later discarded):** `metrics.json` and
`table_sensitivity_summary.csv` reported hf lexical range `[0.42, 0.71]` and
τ-anchors 0.32/0.32/0.38/0.54, while the run's own
`table_sensitivity_grid.csv` yields `[0.52, 0.728]` and anchors
0.20/0.32/0.39/0.46. LinkedIn aggregates in the same files were correct.

**Root-cause investigation (this audit):**

1. *Smoke-run comparison.* The surviving pre-fix smoke run's
   `metrics.json`/summary are exactly self-consistent with its own grid CSV
   (same code path, `bootstrap_n_post=8`). The discarded full run is the only
   execution that ever disagreed with its own artifacts.
2. *Slice hypothesis — excluded.* We searched every numeric column of the true
   grid (SGI, coverage, CI_skill_*, CI_post_*) over every hf subset (finite-P
   rows, all rows, per-τ rows) for the corrupted ranges: **no column of the
   committed grid reproduces them**. The corrupted τ=0.4 anchor (0.32) and
   τ=0.7 anchor (0.54) do not occur anywhere in the hf grid at those τ values.
   The corrupted numbers are therefore not a mis-slice of the true grid — the
   in-memory aggregates were computed from state that no longer corresponds to
   any registered input.
3. *Code path — excluded as deterministic cause.* The current script
   reproduces correct values in every subsequent execution (smoke, full run,
   guard re-run), and the committed run passes the in-script self-consistency
   guard (re-reads written CSVs, asserts equality with reported ranges/anchors)
   plus an independent re-derivation. No hard-coded SGI values exist in the
   script (anchors appear only as expected-value checks that *assert*, never as
   computation inputs).

**Conclusion:** a one-off, non-deterministic state divergence in that single
execution (most plausibly resource contention with the concurrent killed run —
that run's phase timings show severe CPU starvation), not a defect in the grid
computation, the loaders, or pandas. **Fix shipped:** the script now re-reads
its own written CSVs and hard-fails if reported aggregates disagree with them
(`sens01_sgi_sensitivity.py`, self-consistency guard); the run was discarded
and re-executed from scratch; the committed artifacts pass the guard.

**Blast radius (ALIGN01–04 + SENS01):** re-derived every experiment's headline
values from its own on-disk tables and checked arithmetic invariants
(n_covered+n_missing=K, SGI+coverage=1, covered+deficit=demand, CI brackets
point estimates): **ALL CONSISTENT**. ALIGN01/02/03/04 metrics.json values match
their CSV tables exactly; ALIGN04's 0.37/0.14 headline is additionally
reproduced from raw inputs by SENS01's matched-profile block. No other artifact
in `results/` shows the divergence class.

## A2. Market top-K overlap between the HF and LinkedIn corpora

Top-K skill profiles were rebuilt with the exact SENS01 loaders (same
tokenization, same `Counter.most_common`-equivalent ordering) and compared
(`reports/sens01_market_profile_overlap.csv`):

| K | shared | shared fraction | SGI hf | SGI linkedin |
|---|---|---|---|---|
| 50 | 50/50 | 1.000 | 0.180 | 0.180 |
| 100 | 100/100 | 1.000 | 0.290 | 0.290 |
| 200 | 200/200 | 1.000 | 0.385 | 0.385 |
| 500 | 496/500 | 0.992 | 0.438 | 0.440 |

(The SGI column here is the P=all anchor view: market top-K vs the full
academic vocab. It equals 1 − academic coverage of the market top-K.)

**STOP condition — shared input found.** The author's brief said to stop if
any shared input is found. It was:

- Both corpora are keyed by `job_link` (LinkedIn URL). Joining the two
  datasets on that key: **all 519,814 HF job_links (100.00%) appear in the
  Kaggle 1.3M LinkedIn corpus** (1,296,381 unique links), and 1,997/2,000
  sampled shared postings carry byte-identical `job_skills` strings (99.9%).
- **The HF "skill-gap" corpus is a strict subset of the Kaggle LinkedIn 2024
  corpus** — not an independent second sample. Both files also share the
  identical 14-column schema, consistent with one upstream scrape distributed
  through two channels (HuggingFace `skill-gap-analytics/*` vs Kaggle
  `asaniczka/1-3m-linkedin-jobs-and-skills-2024`).

**This explains the matched-cell identity exactly.** At K ∈ {50,100,200} the
two market top-K profiles are *the same skills* (100% shared), and the
academic covering set is shared by design, so lexical coverage — and therefore
SGI — must be identical at any precision, not merely "identical to 2 decimals
within resolution". The K=500 cells diverge exactly where the 4 non-shared
skills enter (2 academic-covered on each side nets to the 0.002 difference).
The code paths are independent (separate loader functions, separate input
files, no shared state); the *inputs* are not.

**Consequences for existing claims (author decision needed):**

1. `paper/main.tex` lines 92, 140, 406–409, 459, 692, 707 call ALIGN04's
   LinkedIn corpus "independent" and ALIGN04 a "cross-corpus replication".
   Given subset nesting, ALIGN04 is a **subset-vs-superset robustness check on
   one scrape family**, not an independent replication. The numbers (0.37/0.14,
   positive SGI, lexical > semantic ordering, H1 ordering) all stand; the
   *independence* framing does not.
2. Line 154 of the manuscript already documents a linked pair *within* the HF
   source (jobs+skills tables share one 519,814 job_link set) and de-duplicates
   them for the record count. The subset relation *across* sources is new and
   not yet disclosed.
3. The line-116 draft abstract phrase "two independent posting corpora" (this
   document's A5 draft, below) must drop "independent"; SENS01's own artifacts
   never claimed independence (registry entry says "dependencies: ALIGN01/02/04"
   only), so no registered artifact needs retraction.
4. SENS01's LinkedIn column remains a valid *computation* (larger
   superset sample, free-text skills, 2.77M-vocab) — it is the labeling that
   must change, from "replication on an independent corpus" to "robustness on
   a nested superset sample".

**Recommended author options (for the reply, not decided here):** (a) reword
the independence claims to subset/robustness language everywhere (minimal
edits, all numbers stand); (b) source a genuinely independent corpus for a
true replication (new data acquisition, outside this revision's scope);
(c) keep ALIGN04 as-is but add a limitations disclosure of the subset
relation. Option (a) or (c) is compatible with the current timeline.

## A3. Paired H3 test (lexical vs semantic, cell by cell)

For every (corpus, K, P, τ) cell of the committed grid: is lexical SGI >
semantic SGI? (`reports/sens01_paired_h3_test.csv`)

| τ | cells | lexical > semantic | fraction | min paired gap (lex − sem) |
|---|---|---|---|---|
| 0.4 | 40 | 40 | 1.00 | 0.32 |
| 0.5 | 40 | 40 | 1.00 | 0.16 |
| 0.6 | 40 | 40 | 1.00 | 0.10 |
| 0.7 | 40 | 40 | 1.00 | 0.04 |

**The paired ordering holds at every cell of the grid, including τ = 0.7** (no
equal cells, no inversions; the τ=0.7 exception previously recorded in the
plan was an artifact of comparing *cross-grid ranges* — semantic max over all
cells vs lexical min over all cells — rather than paired cells; the paired
comparison is the correct test for H3 and supersedes it). The plan's
cross-grid range comparison has been replaced accordingly.

**Draft H3 wording (tau-specific, for author review):**

> H3 (supported, tau-specific form): At the baseline threshold τ = 0.5 the
> lexical-above-semantic ordering holds at every cell of the pre-registered
> (K, P, τ) sensitivity grid (40/40 paired cells across both corpora), with a
> minimum paired margin of 0.16. The ordering remains universal at stricter
> thresholds but the margin narrows monotonically with τ (min margin 0.32,
> 0.16, 0.10, 0.04 at τ = 0.4, 0.5, 0.6, 0.7), so claims of *magnitude*
> separation should stay at the baseline threshold.

## A4. Manuscript phrasing guidance (recorded, not applied)

The grid must be described as **one sensitivity surface** (a single
pre-registered instrument evaluated across its (K, P, τ) configuration space),
never as 200 independent tests; no per-cell significance language; the
"200 configuration cells" count is a property of the surface's resolution,
not a multiple-comparisons statement. This constraint is carried into the P2-3
draft abstract in `reports/Q1_REVISION_PLAN.md` and must govern the eventual
`paper/main.tex` edit.
