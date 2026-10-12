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
