# Clean-room reproduction (fresh clone + fresh venv)

**Purpose.** Run on a *separate machine* to confirm that every number in the two
manuscripts can be regenerated or verified without touching this working copy.

- Branch reproduced: `q1-revision`
- Written: 2026-10-12 (batch-3 step 5)
- Reference machine (author): Windows 11, Python 3.14.6, MiKTeX pdfTeX 1.40.28
- Everything below is **read-only with respect to the two papers** except the
  LaTeX build outputs. Commands that write artifacts say so explicitly.

---

## 0. What "reproduced" means here (three levels)

| Level | Needs raw data? | What it proves |
|---|---|---|
| **L1 — Verification** | No | Every committed artifact is internally consistent, the registry is complete, and all 103 manuscript claims still match their evidence. |
| **L2 — Re-derivation** | Yes (≈950 MB of CSVs) | The headline statistics (STAT01/INTL01 logistic + Welch/Cohen), the corpus accounting, and the generator-signature checks can be recomputed from raw files. |
| **L3 — Full re-execution** | Yes + Kaggle GPU | The registered GPU kernels (ALIGN01–04, GEO01, VALID01, CURR01, STAT01/02, PLAC01, INTL01) run end-to-end. Not part of the clean-room run below; documented in `README.md`. |

L1 is the acceptance criterion for a clean-room run. L2 is optional. L3 needs
Kaggle credentials and GPU quota and is intentionally out of scope.

---

## 1. Prerequisites

```text
git            any recent
Python         3.14.x (3.14.6 used here)
pip            latest
TeX            MiKTeX or TeX Live with IEEEtran (papers are IEEEtran two-column)
network        only for stage "citations" and for raw-data download
```

Windows note: **always run tests as `python -m pytest`.** A bare `pytest`
hangs on the reference machine (the `pytest` launcher does not return control
after the suite). This is an environment quirk, not a repo defect.

---

## 2. Stage 0 — clone

```powershell
git clone <repo-url> skill-gap-repro
cd skill-gap-repro
git checkout q1-revision
git log --oneline -1        # expect the anonymity-sweep commit (Step 4)
```

Verify the tree is clean before starting:

```powershell
git status --porcelain      # expect empty
```

---

## 3. Stage 1 — fresh virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

POSIX: `python -m venv .venv && . .venv/bin/activate`.

`requirements.txt` pins the verified environment (pandas 3.0.5, numpy 2.5.1,
scipy 1.18.1, scikit-learn 1.9.0, statsmodels 0.15.0, matplotlib 3.11.1,
sentence-transformers 6.0.1, huggingface-hub 1.29.0, requests 2.34.2,
python-dotenv 1.2.3, kaggle 2.2.4).

---

## 4. Stage 2 — raw data (needed only for L2; skip for a pure L1 run)

Two routes. **Route A is recommended** (it is the exact frozen input bundle the
kernels consumed). **Route B** re-downloads the upstream sources and is the
independent check that the bundle really is what it claims to be.

### Route A — the frozen Kaggle input bundle (9 canonical files)

```powershell
# Kaggle CLI token: ~/.kaggle/kaggle.json  (or KAGGLE_USERNAME/KAGGLE_KEY env vars)
kaggle datasets download -d studyhub991/skill-gap-inputs-v1 -p _bundle --unzip
$env:SKILLGAP_INPUT_DIR = (Resolve-Path _bundle).Path
```

The nine canonical names (`experiments/common.py`, `BUNDLE_FILES`):

```text
hf_skill_gap_skills.csv      market_skills        (HF Skill Gap corpus, skills)
hf_job_skill_set.csv         academic_skills      (academic reference profile)
linkedin_job_postings.csv    linkedin_postings    (1,348,454 rows)
job_skills.csv               linkedin_skills
college_student_placement_dataset.csv   college_placement
student_career_success_dataset.csv      student_career
global_placement.csv         global_placement
ai_job_market_2020_2026.csv  ai_trends
international_graduates_dataset.csv     international_grads
```

### Route B — upstream sources (provenance check)

`datasets/DATASET_MANIFEST.csv` is authoritative: 15 sources, each with
`source`, `download_date`, `version_or_identifier`, `records`.

- 12 Kaggle datasets → `kaggle datasets download -d <owner/slug> -p datasets/kaggle/<slug> --unzip`
  (slugs are the `version_or_identifier` column).
- 3 HuggingFace corpora (`skill-gap-analytics/jobs-corpus`,
  `skill-gap-analytics/skills-corpus`, `skill-gap-analytics/academic-reference`)
  → download with `huggingface-cli download` and place as
  `datasets/hf_skill_gap_jobs.csv`, `datasets/hf_skill_gap_skills.csv`,
  `datasets/hf_job_skill_set.csv`.

Everything under `datasets/kaggle/` and `datasets/*.csv` is gitignored, so
neither route dirties the tree.

### Verify the inputs are bit-identical

```powershell
python datasets/compute_checksums.py     # rewrites datasets/input_checksums.sha256
git diff --exit-code datasets/input_checksums.sha256
```

`input_checksums.sha256` is tracked; an empty `git diff` means the raw inputs
are byte-identical to the ones the experiments used. If a file is missing the
script prints `MISSING <key>` instead of failing.

---

## 5. Stage 3 — `reproduce_local.py` (the one-command L1+L2 run)

```powershell
python reproduce_local.py
# optional: python reproduce_local.py --skip citations --skip stats
```

Stages run in this order; exit code is non-zero if any stage fails. `verify`
and `claims` are hard stops (the runner aborts after a failure in either).

| # | Stage key | Command | Checks | Raw data needed |
|---|---|---|---|---|
| 1 | `env` | inline | every pin in `requirements.txt` is installed at the pinned version (import-name mapped) | no |
| 2 | `checksums` | `datasets/compute_checksums.py` | SHA-256 of the nine canonical inputs matches the tracked `datasets/input_checksums.sha256` | **yes** |
| 3 | `verify` | `experiments/verify.py` | every registered experiment directory exists, has the required artifacts, and passes schema/sanity checks | no |
| 4 | `claims` | `audit/verify_claims.py` | 103 claim checks: manuscript constants vs `results/` artifacts, plus presence checks over `paper/main.tex` **and** `paper_placement/main.tex` | no |
| 5 | `stats` | `audit/reproduce_stats.py` | re-derives STAT01/INTL01 statistics (logistic regression, Welch's *t*, Cohen's *d*) from the raw placement CSVs and writes `audit/05_stat_reproduction.json` | **yes** |
| 6 | `citations` | `audit/verify_citations.py` | every DOI in `references.bib` is checked against Crossref (title/year/first-author); writes `audit/07_citation_check.csv` | network |

Artifacts written: `datasets/input_checksums.sha256`,
`audit/05_stat_reproduction.json`, `audit/07_citation_check.csv`,
`results/verification_report.json`. All are tracked; use
`git checkout --` to discard re-runs that differ only in timestamps.

Expected summary on a clean machine (L1 run, no raw data):

```text
env          ok
checksums    ok              (or MISSING lines if raw data absent)
verify       ok
claims       ok
stats        FAIL(rc=1)      <- environment-specific, see §9
citations    ok
```

---

## 6. Stage 4 — unit tests

```powershell
python -m pytest -q          # expect: 23 passed
```

| Test file | What it pins down |
|---|---|
| `tests/test_common.py` | input resolution (`SKILLGAP_INPUT_DIR`, `/kaggle/input` roots), bundle file naming, hashing |
| `tests/test_reproducibility.py` | registry hygiene (every experiment is `USED_IN_MANUSCRIPT`, staged-only-if-verified, or not-used with a recorded reason); `verify.py`'s required keys all have directories; manifest row counts match local CSVs **when present** (skipped otherwise); the claim ledger has zero contradicted claims; the checksum file is well-formed |
| `tests/test_synthetic_checks.py` | the generator-signature checkers behave on synthetic fixtures, and the committed artifact `datasets/synthetic_checks_output.json` is structurally complete (10 datasets, 5 check families, recorded thresholds) |

Without raw data, `test_manifest_counts_match_local_files_when_present` skips
(it is the only test that reads raw CSVs), so expect **23 passed** or
**22 passed + 1 skipped**.

---

## 7. Stage 5 — artifact verification alone

```powershell
python experiments/verify.py     # expect "all_verified": true
```

Writes `results/verification_report.json`. This is the gate that guarantees no
table/figure in either paper is hand-transcribed: every number comes from a
`results/<EXP>/` artifact that passed schema checks.

---

## 8. Stage 6 — claim verification alone

```powershell
python audit/verify_claims.py    # expect: checks=103 matched=103 mismatched=0
```

Two manuscript handles are checked (`TEX` = `paper/main.tex`,
`TEXP` = `paper_placement/main.tex`, `ALLTEX` = both):

- `add(...)` checks compare a manuscript constant to a value computed from
  `results/` (tolerance `1e-6 + 1e-9 * max(|ms|, |art|)`).
- presence checks assert that specific strings (and, where relevant, that
  specific *superseded* strings do **not** appear) in the right paper.

Writes `audit/01_claim_verification.json` and refreshes
`audit/01_claim_evidence_ledger.csv` (113 rows; `paper` column = `main` /
`placement` / `none (artifact retained)` / `main+placement`).

---

## 9. Stage 7 — compile both papers

```powershell
# IMPORTANT: do not re-run experiments/make_latex.py first (footgun F-5, see §11)
cd paper
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex     # second pass for cross-references
cd ..\paper_placement
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Expected:

| Paper | Pages | Notes |
|---|---|---|
| `paper/main.pdf` | 13 | gap-measurement article, RQ1–RQ3 / H1–H3 |
| `paper_placement/main.pdf` | 7 | benchmark-audit companion, H4–H6 |

Both must build with **no undefined references**:

```powershell
Select-String -Path paper\main.log,paper_placement\main.log -Pattern "undefined"
# expect: no output
```

The preamble of both papers sets `\pdfinfoomitdate=1`, `\pdfsuppressptexinfo=-1`
and `\pdftrailerid{}`, so `pdfinfo` on the built PDFs must show **no
CreationDate/ModDate** (the timestamp would otherwise leak the build machine's
time zone). `pdfinfo paper/main.pdf` should show empty `Title`/`Author`.

Optional re-generation of tables/figures (NOT recommended before compiling —
see §11):

```powershell
python experiments/make_latex.py
```

Optional regeneration of the generator-signature artifact (deterministic;
should reproduce `datasets/synthetic_checks_output.json` byte-for-byte):

```powershell
python datasets/synthetic_checks.py
git diff --exit-code datasets/synthetic_checks_output.json
```

---

## 10. Acceptance criteria (paste-able)

```powershell
python -m pytest -q
python experiments/verify.py          | Select-String all_verified
python audit/verify_claims.py         | Select-String "checks=103 matched=103 mismatched=0"
git status --porcelain                # expect: only generated build artifacts
```

If those four lines hold, the clean-room run is a pass at level L1.

---

## 11. Known environment issues and footguns

1. **`pytest` hangs; use `python -m pytest`.** (Reference machine, Windows.)
2. **`stats` stage / `audit/reproduce_stats.py` fails on the reference
   machine**: `ImportError: DLL load failed while importing _arma_innovations:
   An Application Control policy has blocked this file.` This is an OS
   Application Control (WDAC/AppLocker) block on the statsmodels compiled
   extension, not a repository defect; the same statistics are independently
   checked by `audit/verify_claims.py` (C87–C90, C152/C152b) against the
   committed STAT01 artifacts. On a clean machine with the pinned
   `statsmodels==0.15.0` this stage is expected to pass.
3. **Footgun F-5: `python experiments/make_latex.py` regenerates
   `paper/tables/tab_crosscorpus.tex` and the figure PDFs with
   non-authoritative versions** (they are hand-audited). If you re-run it,
   restore before compiling:
   ```powershell
   git checkout -- paper/figures paper/tables/tab_crosscorpus.tex
   ```
   Fix is tracked as plan item **P5-4** (pending).
4. **`reproduce_local.py` overwrites tracked audit artifacts.** Re-run the
   stages you need, then `git checkout -- audit results` if you want the
   committed versions back.
5. **Double-blind**: the Kaggle/HuggingFace namespaces are redacted in the two
   papers and in the generated experiment tables (`anon/<kernel-slug>`); the
   real `namespace/slug` pairs live in `results/registry.json` and
   `results/worker_map.json`, which are **not** part of a paper submission.

---

## 12. What a clean-room run cannot reproduce (by design)

| Item | Why | Where it is documented |
|---|---|---|
| GPU kernel execution (L3) | needs Kaggle GPU quota + credentials | `README.md`, `results/registry.json` (attempts, kernel refs) |
| CURR02 (curriculum gold check) | blocked on author labelling of `labelling/curriculum_precision_100.csv` / `curriculum_recall_100.csv` | `datasets/curriculum/SELECTION_PROTOCOL.md` §9 |
| ALIGN05 (title-level precision/recall) | blocked on blinded author labelling of `labelling/align05_titles_200.csv` (do **not** open `experiments/align05_titles_200_key.csv` first) | `experiments/ALIGN05_PREREG.md` |
| ALIGN06 (O\*NET/BLS external demand profile) | pre-registered only; §9 license checklist must be signed before any download | `experiments/ALIGN06_PREREG.md` |
| SENS01 first-run byte identity | unresolved determinism question; results are still reported with their recorded seeds | `reports/SENS01_DETERMINISM.md` |
| Raw curriculum corpus (`datasets/curriculum/raw/`) | gitignored; needed only for CURR02 | `datasets/curriculum/SELECTION_PROTOCOL.md` |
