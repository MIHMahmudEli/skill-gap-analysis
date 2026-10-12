# Reproducibility paragraph — revised draft (print-only; NOT inserted)

Author instruction 2026-10-12 (batch 3, step 4): do not insert; rewrite so it says only
what is true.

## What the previous draft claimed vs. what is true

| Draft claim | Verdict |
|---|---|
| "executed on NVIDIA GPU instances through Kaggle Notebooks" | true of the original runs, but names a hosting account and implies cloud dependency — replaced |
| "an independent verification script **re-derives**" the results | **false.** `audit/verify_claims.py` is read-only: it extracts constants from `paper/main.tex` and compares them with `results/*/metrics.json` and key CSVs. It does not recompute anything from raw data. Reworded as a comparison against stored artifacts. |
| "no result depends on … GPU hardware" | **evidenced for 8 of 13 experiments only.** The five Sentence-BERT experiments could not be re-executed on this machine (torch blocked by an Application Control policy). Stated as such; not asserted for all. |
| "no table or figure is hand-transcribed" | **true**, and now strengthened: `tests/test_make_latex_regeneration.py` asserts all 14 tables regenerate byte-identically from the artifacts, and figures carry no metadata. |

## Revised draft

> Every quantitative result in this article comes from a registered experiment and is
> stored as a machine-readable artifact under `results/`, from which the tables and
> figures are generated rather than transcribed by hand (a test asserts that all 14
> tables regenerate byte-identically). An automated, read-only check
> (`audit/verify_claims.py`) extracts each quantitative constant from the manuscript and
> compares it against those stored artifacts — 103 checks, agreement required within
> 1e-6; this verifies that the paper reports what the artifacts contain, and is distinct
> from re-deriving the artifacts from the raw data. As a stronger and independent check,
> 8 of the 13 registered experiments were re-executed end-to-end on a single local CPU
> machine, offline, with pinned dependencies, fixed seeds (42) and single-threaded
> arithmetic; all 288 compared numeric fields reproduced exactly
> (`reports/CPU_VS_COMMITTED.md`). The remaining 5 experiments load Sentence-BERT and
> could not be re-executed on that machine because a local application-control policy
> blocks the runtime's shared library; their committed artifacts are unchanged, and
> reproducing them on any machine with the pinned `torch` and `sentence-transformers`
> versions is expected to succeed but is not claimed here as verified. Table X lists the
> experiment identifiers and their verification status; the placement-model experiments
> (STAT01, STAT02, PLAC01, INTL01) are reported in the companion benchmark audit.
> Inputs are listed with licence and SHA-256 checksum in `datasets/DATASET_MANIFEST.csv`
> and `datasets/input_checksums.sha256`, and the step-by-step clean-room procedure is in
> `reports/CLEAN_ROOM_REPRO.md`.

## Shorter alternative (same truth conditions, ~130 words)

> Every quantitative result comes from a registered experiment and is stored as a
> machine-readable artifact under `results/`, from which tables and figures are
> generated rather than transcribed. A read-only automated check compares each
> manuscript constant against those artifacts (103 checks, 1e-6 tolerance); it verifies
> that the paper reports what the artifacts contain, not that the artifacts can be
> re-derived from raw data. Separately, 8 of 13 experiments were re-executed end-to-end
> on a local CPU-only machine with pinned dependencies and fixed seeds, reproducing all
> 288 compared numeric fields exactly; the 5 Sentence-BERT experiments could not be
> re-run there because a local policy blocks the runtime library, and are not claimed as
> CPU-verified. Inputs, checksums and a clean-room procedure are in
> `datasets/DATASET_MANIFEST.csv` and `reports/CLEAN_ROOM_REPRO.md`.

Both drafts are apply-ready. Neither has been inserted into `paper/main.tex`, per
instruction. On insertion, `Table~\ref{tab:experiments}` replaces "Table X", and the
experiment-table "Kernel" column should be renamed "Experiment ID" at the same time
(the handles are already `anon/<slug>` after the anonymity sweep, and this removes the
last reason to name a host) — that column rename is a separate edit needing your go-ahead.
