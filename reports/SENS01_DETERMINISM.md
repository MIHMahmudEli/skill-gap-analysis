# SENS01 Determinism Check (Q1 Revision — Step 2)

Date: 2026-10-12 · Branch: `q1-revision` · Script: `experiments/exp_scripts/sens01_sgi_sensitivity.py` · Registered inputs: `datasets/hf_skill_gap_skills.csv`, `datasets/kaggle/1-3m-linkedin-jobs-and-skills-2024/job_skills.csv`, `datasets/hf_job_skill_set.csv`

Requested: run SENS01 three times under different CPU load (one with parallel jobs reduced), compare file hashes of all outputs; inspect for shared output paths, caches, parallel workers writing the same file, or reads during writes; label the first-run cause UNRESOLVED unless evidence is found.

## 1. Execution protocol

Every run wrote to a private temp directory via `SKILLGAP_OUTPUT_DIR`; the committed `results/SENS01_sgi_sensitivity/` was never a write target during these runs.

| Run | Condition | Wall time (from metrics.json) |
|---|---|---|
| det1 | idle CPU | 281.2 s |
| det2 | concurrent load (overlap-audit CSV reads + hash computations ran in parallel) | 285.9 s |
| det3 | parallelism reduced: `OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1` | 308.1 s |

Committed artifact baseline: 187.8 s (local re-execution of 2026-10-11 that produced the committed artifacts).

## 2. Hash comparison (SHA-256, vs. committed artifacts)

| Output | det1 | det2 | det3 |
|---|---|---|---|
| `table_sensitivity_grid.csv` (200 rows) | identical | identical | identical |
| `table_sensitivity_summary.csv` | identical | identical | identical |
| `figure_sensitivity_heatmap.png` | identical | identical | identical |
| `metrics.json` | differs in `runtime_sec` only | differs in `runtime_sec` only | differs in `runtime_sec` only |

Full key-by-key diff of `metrics.json` (all four files): the *only* differing key is `runtime_sec` (187.77 / 281.20 / 285.92 / 308.05). Every scientific field — all 200 grid rows, all summary aggregates, the matched-profile block, anchors, manuscript claim checks — is bit-identical across three executions and to the committed run. **SENS01 is deterministic under CPU-load variation and under single-threaded BLAS.**

## 3. Code inspection (requested hazard classes)

| Hazard class | Finding |
|---|---|
| Shared output paths | None. Script writes exactly four files, all under `out_dir` (env `SKILLGAP_OUTPUT_DIR`, default `/kaggle/working`). No other experiment script writes to `results/SENS01_sgi_sensitivity/`; each experiment has its own results directory. |
| Caches | None written or read. `SentenceTransformer(MODEL_NAME)` loads the local MiniLM snapshot (read-only); token index is built in-process per run; no on-disk feature/emb cache. |
| Parallel workers | None. Single Python process; no `multiprocessing`, `joblib`, `concurrent.futures`, or threading anywhere in the script (grep-verified). Only BLAS-level parallelism inside `emb @ emb.T`, which det3 shows does not affect results. |
| Concurrent writers to same file | Impossible in-process (sequential writes) and none cross-process (unique temp dirs per run). No append modes (`"a"`), no temp-file rename patterns, no deletes. |
| Reads during writes | One read-back exists — the self-consistency guard re-reads `table_sensitivity_grid.csv` *after* closing it and hard-fails if reported aggregates disagree. Sequential, same process, no concurrency. |

Randomness: every draw uses `np.random.RandomState(SEED + deterministic offset)` (`SEED=42`; per-cell seeds `SEED + 1000·ci + 10·pi`, bootstrap seeds offset per statistic). No unseeded RNG, no hash-seeding dependence (`PYTHONHASHSEED` not consulted).

## 4. Verdict on the 2026-10-11 first-run incident

- These runs demonstrate that the **current** pipeline is deterministic; they do not identify what corrupted the discarded first run.
- No evidence was found for any specific cause. Per author instruction, the incident cause remains **UNRESOLVED** (`reports/SENS01_FOLLOWUP.md` §A1, revised 2026-10-12); CPU contention is recorded as a hypothesis only.
- Mitigation unchanged: in-script self-consistency guard converts any future silent divergence into a hard failure; committed artifacts pass the guard.

## 5. Time-boxed addendum (batch 2, step 8, 2026-10-12)

One hour was spent on the only angle not already covered: whether the discarded
first run left any forensic trace that could identify its corruption mode.

1. **Git history — no trace exists.** `git log --all -- results/SENS01_sgi_sensitivity/`
   returns exactly one commit (`e946c8a`, the corrected run). The corrupt first run was
   never committed, so no earlier artifact version survives to diff against. The
   incident is *forensically unrecoverable by construction*, not merely unfound.
2. **Fourth execution, at the current commit** (`6a7fab4`), into a private output
   directory (`SKILLGAP_OUTPUT_DIR`), 184.7 s wall time, in-script guard `ok: true`:

   | Output | vs. committed |
   |---|---|
   | `table_sensitivity_grid.csv` | byte-identical (SHA-256 prefix `6eb372c860868c88`) |
   | `table_sensitivity_summary.csv` | byte-identical (`69fec7ac51b16f73`) |
   | `figure_sensitivity_heatmap.png` | byte-identical (`2453fa250d3ffce2`) |
   | `metrics.json` | differs in `runtime_sec` only (187.77 → 184.68) |

**Verdict.** *Resolved:* SENS01 is byte-identical across four independent executions
(idle CPU, loaded CPU, single-threaded BLAS, and at this commit), including the binary
PNG; the only non-reproducible field is the wall-clock measurement, which is not a
result. *Unresolved and closed:* the cause of the 2026-10-11 first-run divergence —
the corrupt run was never committed, so no evidence can survive, and per author
instruction no further work is done on it. The guard in
`experiments/exp_scripts/sens01_sgi_sensitivity.py` remains the mitigation: it makes a
recurrence a hard failure rather than a silent publication.
