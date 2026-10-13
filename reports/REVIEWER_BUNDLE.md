# Reviewer bundle — build record and verification result

Author instruction 2026-10-12 (batch 2, step 6): a history-free, identifier-free
export, built by script, verified by grep, with the result printed. Everything below
is the actual output of the run, not a description of one.

## How to build it

```bash
bash scripts/make_reviewer_bundle.sh <output-dir>   # refuses a dirty tree
bash scripts/verify_reviewer_bundle.sh <output-dir> # exit 1 on any leak
```

`make_reviewer_bundle.sh` exports the **clean tree at HEAD** with `git archive`
(so the bundle has no `.git`, no history, no branch or committer information), then
removes non-review material, replaces the README with the anonymized
`scripts/reviewer_README.md`, scrubs the two account slugs that live inside
executable code (bundle copy only — the repository keeps them so the pipeline still
runs on the original hosts), and finally runs the verifier.

## What is excluded, and why

| Excluded | Why |
| --- | --- |
| `.git/` (via `git archive`) | no history, no committer identity |
| `audit/`, `archive/`, `reports/`, `labelling/` | internal audit trail, archived run reports, revision reports and blinded labelling files — all carry handles or pre-publication material |
| `.github/` | CI config tied to a hosting account |
| `LICENSE`, root `README.md` | name the author; replaced by the anonymized reviewer README |
| `datasets/cs2023/CS2023_BoK.pdf` | third-party copyright (ACM/IEEE); the derived `cs2023_topics.csv` is included instead |
| `results/worker_map.json`, `results/registry.json` | the 16 host account names and their run namespaces |
| `results/*/metadata.json` | per-run kernel/user handles |
| `paper/**/*.{aux,log,bbl,blg,out}` | build artifacts |
| `scripts/verify_reviewer_bundle.sh` | holds the identifier list by design; shipping it would make the grep self-hit |

Kept and scrubbed (bundle copy only): the Kaggle input-bundle slug and the
output-archive slug inside `experiments/` become `<INPUT_BUNDLE>` / `<OUTPUT_ARCHIVE>` /
`<ACCOUNT>` — 17 files rewritten, 0 numerical values touched.

## Manifest diff: third run (159 files) → fourth run (199 files)

Batch 5, step 5. Fourth run at commit `6564c56`, tree clean, built by
`make_reviewer_bundle.sh` into `reviewer_bundle4`.

```
previous : reviewer_bundle3   159 files, 5.2 MB   (commit 0519f8f)
current  : reviewer_bundle4   199 files            (commit 6564c56)
delta    : +40
```

### Top level, old → new

| directory | old | new | delta |
|---|---:|---:|---:|
| `(root)` | 4 | 5 | +1 |
| `datasets/` | 41 | 41 | 0 |
| `experiments/` | 25 | 24 | **−1** |
| `paper/` | 19 | 19 | 0 |
| `paper_placement/` | 10 | 10 | 0 |
| `results/` | 55 | 55 | 0 |
| `results_cpu/` | 0 | 32 | **+32** |
| `scripts/` | 2 | 6 | +4 |
| `tests/` | 3 | 7 | +4 |
| **TOTAL** | **159** | **199** | **+40** |

### What the +40 is

- **`results_cpu/` (32 files, new directory)** — the CPU-rerun results tree that
  now backs the placement-model tables: `ALIGN01_lexical_bootstrap` (4),
  `GEO01_linkedin_shares` (2), `INTL01_internship_effect` (3),
  `PLAC01_global_by_country` (2), `SENS01_sgi_sensitivity` (5),
  `STAT01_placement_core` (11), `STAT02_external_validation` (2),
  `TRENDS01_ai_longitudinal` (3). **Contains no `worker_map.json`, no
  `registry.json` and no `metadata.json`** — checked explicitly, because
  `make_reviewer_bundle.sh` only sweeps `results/`, not `results_cpu/`.
- **`scripts/` +4** — `compare_cpu_results.py`, `pre-push`, `run_after_labels.sh`,
  `run_cpu_rerun.py`.
- **`tests/` +4** — `test_hash_eol_integrity.py`, `test_make_latex_regeneration.py`,
  `test_no_tracked_secrets.py`, `test_tex_render_integrity.py`.
- **`(root)` +1** — `.gitattributes`.

### The −1, and why it matters

The one file that disappeared is `experiments/align05_titles_200_key.csv`.
The third-run bundle **shipped it**. It has since been moved out of
`experiments/` to `archive/align05_titles_200_key_RETIRED.{csv,md}`, and
`archive/` is excluded from the export, so the key no longer reaches reviewers
by either route: it is neither at its old path nor in an excluded directory.

| forbidden path | old | new | verdict |
|---|---:|---:|---|
| `archive/` (whole tree) | 0 | 0 | **ABSENT** |
| `audit/` (whole tree) | 0 | 0 | **ABSENT** |
| `reports/` (whole tree) | 0 | 0 | **ABSENT** |
| `labelling/` (whole tree) | 0 | 0 | **ABSENT** |
| `.github/` | 0 | 0 | **ABSENT** |
| `.git/` (history) | 0 | 0 | **ABSENT** |
| **every `*_key*`** | **1** | **0** | **ABSENT** (was `experiments/align05_titles_200_key.csv`) |
| **`results/worker_map.json`** | 0 | 0 | **ABSENT** |
| `results/registry.json` | 0 | 0 | **ABSENT** |
| every `results/*/metadata.json` | 0 | 0 | **ABSENT** |
| any `results_cpu/*/{worker_map,registry,metadata}.json` | 0 | 0 | **ABSENT** |
| `datasets/cs2023/CS2023_BoK.pdf` | 0 | 0 | **ABSENT** |
| `scripts/verify_reviewer_bundle.sh` | 0 | 0 | **ABSENT** |
| root `LICENSE` | 0 | 0 | **ABSENT** |
| `.aux/.log/.bbl/.blg/.out` artifacts | 0 | 0 | **ABSENT** |

Root `README.md` is *expected* to be present: the builder deletes the
author-named one and copies `scripts/reviewer_README.md` in its place. Verified —
bundle README is 2,490 bytes, byte-identical to `scripts/reviewer_README.md`, and
differs from the repo's 12,221-byte `README.md`.

### Identifier grep re-run on the current bundle

```
== identifier grep over 199 files in .../reviewer_bundle4
   no identifier matches: PASS
== pdf metadata check
   no PDF carries dates, personal fields or non-tool metadata: PASS
   no .git directory: PASS
   excluded paths absent: PASS
exit code: 0
```

Scrub count for this run: **19 files rewritten**, up from 17. Recomputed
independently by exporting both commits, applying the builder's exclusion list
*before* the scrub step (the exclusions delete those files first, so they are
never scrubbed), and testing each survivor for any of the 8 substitution
targets — the method reproduces both reported figures exactly (17 at `0519f8f`,
19 at `HEAD`), so the count is verified rather than inferred:

| file | why it is newly scrubbed |
|---|---|
| `experiments/ALIGN05_PREREG.md` | already shipped in run 3, but only gained an identifier *then* — the A3/A4 amendments name the repository slug, which the `MIHMahmudEli/skill-gap-analysis` substitution added at `59b2cc3` now catches |
| `tests/test_hash_eol_integrity.py` | new to the bundle (one of the four added tests); its docstring names the repository |

No file stopped needing a scrub. `0 file(s) needed a non-UTF-8 read` — the
CP1252 decode path that previously let a handle escape in this file is only
exercised when such bytes exist, and none remain after `eded4e1`.

`results/stray_kernels.json` ships as an empty array (`[]`) and
`results/verification_report.json` is the `verify_claims` output — both pass the
grep.

## Verification result (third run, commit `0519f8f`)

```
bundle source commit: 0519f8f
scrubbed 17 file(s)
== identifier grep over 159 files in .../reviewer_bundle3
   no identifier matches: PASS
== pdf metadata check
   no PDF carries dates, personal fields or non-tool metadata: PASS
   no .git directory: PASS
   excluded paths absent: PASS
bundle ready: .../reviewer_bundle3
```

Bundle: **159 files, 5.2 MB**. Top level: `paper/`, `paper_placement/`, `datasets/`,
`experiments/`, `results/`, `scripts/`, `tests/`, `README.md` (anonymized),
`reproduce_local.py`, `requirements.txt`, `.gitignore`.

The grep covers all 16 host/worker handles from `results/worker_map.json`, the author
identity strings, the contact address, and the national-timezone string that had leaked
into PDF metadata before the anonymity sweep. PDFs are checked with `pdfinfo`: any
`CreationDate`/`ModDate` fails, any non-empty `Title`/`Subject`/`Keywords`/`Author`
fails, and `Creator`/`Producer` must be either empty or the two known tool strings
(`LaTeX with hyperref`, `MiKTeX pdfTeX*`).

## Two real defects found by the first run (both fixed)

1. **Figure PDFs leaked the build machine's timezone.** All seven `paper/figures/*.pdf`
   carried `/CreationDate (D:2026...)` stamped with the author's national time standard,
   plus matplotlib `Creator`/`Producer` strings. `experiments/make_latex.py` now writes
   every figure through `save_figure()` with `FIG_METADATA` suppressing
   `CreationDate`/`Creator`/`Producer`/`Title`/`Author`/`Subject`/`Keywords`/`Trapped`;
   the seven figures were regenerated from committed metrics (values unchanged) and
   `paper/main.pdf` rebuilt (13 pp, no undefined references). Commit `9c7a230`.
2. **The verifier itself was the only "leak"** — it holds the identifier list by design —
   and `pdfinfo` pads empty fields with spaces, so empty `Title`/`Author` fields were
   reported as leaks. The builder now excludes the verifier from the export and the
   verifier trims values before testing. A third defect was mine: the new figure comment
   named the timezone explicitly, which the grep then found (commit `0519f8f`).

## Not covered / for the author

- The bundle is built from the committed tree; raw datasets are not redistributed
  (manifest + checksums + licences are, so a reviewer can refetch them).
- `tests/test_reproducibility.py` skips its two audit/registry-dependent tests inside the
  bundle (those paths are excluded); the other tests run.
- The manuscript claim-verification layer (`audit/verify_claims.py`, 103 checks) is
  withheld with `audit/`; the reviewer README states it is available to editors on request.
  If you would rather ship it, say so and I will add a sanitized copy plus a
  handle-free ledger.
