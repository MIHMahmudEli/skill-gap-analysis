# CPU re-run plan for the registered analyses (PLAN ONLY — nothing executed)

Author instruction 2026-10-12 (batch 2, step 5): *propose, do not execute.* This document
is the proposal. No experiment was re-run for it, no environment was built, and no file
outside this report changed.

## 1. Objective

Re-run every analysis that feeds a number in either manuscript inside **one compliant
environment** — a local, CPU-only machine, no cloud notebooks, no third-party accounts —
and show that the published numbers come back. Scope is exactly the 12 experiments with
`status = USED_IN_MANUSCRIPT` / `VERIFIED` in `results/registry.json` (ALIGN01–04, CURR01,
GEO01, INTL01, PLAC01, SENS01, STAT01, STAT02, TRENDS01) plus the audit layer
(`audit/verify_claims.py`, `experiments/verify.py`, `datasets/synthetic_checks*.py`).
**CURR02, ALIGN05 and ALIGN06 are excluded**: they are author-gated (labelling files and
the licence checklist) and are not run by this plan.

## 2. The single compliant environment

| Item | Specification |
| --- | --- |
| Machine | one local CPU machine (the same class as the author's laptop); no GPU, no cloud notebook |
| OS / Python | Windows or Linux; Python 3.11, `venv` + `pip install -r requirements.txt` (pinned, already committed) |
| Network | off after staging. Stage inputs once, verify with `python datasets/compute_checksums.py` against `datasets/input_checksums.sha256` (Route A: the frozen Kaggle bundle; Route B: the 12 Kaggle + 3 HuggingFace sources in `datasets/DATASET_MANIFEST.csv`) |
| Determinism knobs | `seed = 42` in every experiment (already set); `TOKENIZERS_PARALLELISM=false`; `OMP_NUM_THREADS=1` `MKL_NUM_THREADS=1` `OPENBLAS_NUM_THREADS=1` for bit-stable reductions; `torch.use_deterministic_algorithms(True)` where available; model pinned to `all-MiniLM-L6-v2` with the revision hash resolved at stage time |
| Execution | `python reproduce_local.py` (env → checksums → experiments → verify → claims → citations), then `python -m pytest` |
| Comparison | `audit/verify_claims.py` re-derives all 103 checks with the tolerance `abs(ms-art) < 1e-6 + 1e-9*max(...)`; `experiments/verify.py` re-runs every registry sanity check |

## 3. Does anything need a GPU? No.

Every recorded run is reproducible on CPU. The five results artifacts that record
`device: cuda` (ALIGN02, ALIGN03, ALIGN04, CURR01, VALID01) used the GPU only to encode
text with Sentence-BERT; `sentence-transformers` falls back to CPU with no code change,
and every experiment already pins its seed. Recorded runtimes and CPU expectations:

| Experiment | Recorded runtime (GPU where noted) | Expected CPU wall-clock |
| --- | --- | --- |
| ALIGN01 lexical bootstrap | 16 s (CPU) | ~20 s |
| ALIGN02 semantic SBERT | 46 s (cuda) | 10–20 min |
| ALIGN03 domain gap | 225 s (cuda) | 30–60 min |
| ALIGN04 nested LinkedIn superset | 524 s (cuda) | 2–4 h (1.29M postings encoded) |
| CURR01 CS2023 anchor | 43 s (cuda) | 5–15 min |
| GEO01, INTL01, PLAC01, STAT02, TRENDS01 | 0.1–26 s (CPU) | < 1 min each |
| SENS01 sensitivity | 188 s (CPU) | ~4 min |
| STAT01 placement core | 156 s (CPU) | ~3 min |
| VALID01 ESCO gold | 216 s (cuda) | 20–45 min |
| **Total** | **~24 min recorded** | **~3–6 h**, dominated by the two embedding passes |

If wall-clock matters, ALIGN04 can be encoded once and cached; that changes nothing in the
artifacts, only the re-run time.

## 4. Procedure (order matters)

1. Fresh clone + fresh venv (steps L1/L2 of `reports/CLEAN_ROOM_REPRO.md`).
2. Stage inputs (Route A or B), verify checksums.
3. `python reproduce_local.py` — runs the experiment modules in registry order and writes
   `results/<EXPERIMENT>/metrics.json`.
4. `python experiments/verify.py` → must print `all_verified: true`.
5. `python audit/verify_claims.py` → must print `checks=103 matched=103`.
6. `python -m pytest` → must print all tests passed.
7. Diff the new `results/*/metrics.json` against the committed ones: every published
   number must match exactly or within the stated tolerance. Record any field that moves.

## 5. What would change in the paper and the README

Reproducibility text is reworded from "executed on NVIDIA GPU instances through Kaggle
Notebooks" to **deterministic and CPU re-runnable**, and the account-bearing kernel
references are replaced by experiment identifiers. Concretely:

- `paper/main.tex` §V (*Reproducibility and Data Availability*): drop the GPU/cloud
  sentence, add the CPU/determinism sentence and the clean-room pointer (draft below).
- `paper/tables/tab_experiments.tex` (+ the supplement table): the "Kernel" column becomes
  "Experiment ID" — the handles are already `anon/<slug>` after the anonymity sweep, and
  this removes the last reason to name a host.
- `paper_placement/main.tex` reproducibility paragraph: same substitution.
- `README.md`: the experiment table's namespace column and the phrase "Kaggle Notebooks"
  are replaced by experiment IDs and "CPU re-runnable"; the GPU mention is deleted.
- Nothing numerical changes: no metric, table value, CI or count is touched by rewording.

### Draft replacement data-availability paragraph (no account names)

> Every quantitative result in this article originates from a pre-specified experiment that
> is deterministic and CPU re-runnable from the released inputs: each stage fixes its random
> seed (42), pins its embedding model, and writes machine-readable metrics that an
> independent verification script re-derives and compares under a $10^{-6}$ tolerance.
> Table~\ref{tab:experiments} lists the experiment identifiers and their verification
> status. Inputs, their checksums, and a step-by-step clean-room procedure for reproducing
> every table and figure on a separate machine are documented in
> \texttt{reports/CLEAN\_ROOM\_REPRO.md}; no table or figure is hand-transcribed, and no
> result depends on cloud-hosted notebooks or on GPU hardware.

## 6. Known risks to record when the plan is executed

- **Cross-BLAS float drift.** Bit-identical JSON is not guaranteed across BLAS builds; the
  comparison must be tolerance-based (verify_claims already is). Anything outside
  `1e-6 + 1e-9*max(...)` is a real discrepancy, not noise, and must be reported.
- **SENS01 byte identity** (the item under a one-hour time-box in batch 2, step 8): its
  status is recorded in `reports/SENS01_DETERMINISM.md`; if unresolved, the plan compares
  SENS01 numerically, not byte-wise.
- **This machine cannot run `reproduce_stats.py`**: the WDAC/AppLocker policy blocks the
  `statsmodels` `_arma_innovations` DLL. That is an environment defect of the author's
  laptop, not a property of the pipeline; the clean-room machine is not expected to share
  it.
- **Not covered:** CURR02, ALIGN05, ALIGN06 (author-gated), and any result that depends on
  them.
