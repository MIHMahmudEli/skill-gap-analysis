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
3. **Footgun F-5 — FIXED 2026-10-12 (P5-4).** `python experiments/make_latex.py`
   regenerates all 14 tables; `tab_crosscorpus.tex` is now a genuine generator
   product (byte-identical to the audited table), and figure PDFs are **not**
   written unless you pass `--figures`. Before compiling you can confirm
   nothing would change with the side-effect-free check:
   ```powershell
   python experiments/make_latex.py --check   # exit 0 = all tables identical
   ```
   `tests/test_make_latex_regeneration.py` runs that check in CI, so a
   hand-edited table or a drifting generator fails the test suite.
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


---

## 13. Running the 5 Sentence-BERT experiments on a machine where `torch` loads

**STATUS 2026-10-13: CLOSED — all 5 were verified on a CPU-only Kaggle kernel.**
`reports/CPU_VS_COMMITTED.md` records that 8 of 13 experiments were re-executed on
CPU and reproduced all 288 compared numeric fields exactly, but that **5 experiments
could not be re-run on the author's laptop**: `ALIGN02_semantic_sbert`,
`ALIGN03_domain_gap`, `ALIGN04_crosscorpus_linkedin`, `CURR01_cs2023_anchor` and
`VALID01_esco_gold` each `import torch`, and that import fails there with
`ImportError: DLL load failed while importing _C: An Application Control policy has
blocked this file` — the same local policy that blocks `statsmodels` in
`reproduce_stats.py`. Their committed values were reported as **unchanged but
unverified on CPU**, not as agreeing.

That gap is now closed by `scripts/kaggle_cpu_verify.py`, which pushed the 5 to a
CPU-only Kaggle kernel owned by the account that holds the input bundle, pinned the
kernel to the commit GitHub served, and gated the downloaded output against the
committed artifacts:

| | |
|---|---|
| Kernel | `studyhub991/cpu-verify-embedding-5` (private, CPU, internet on for pip + the HF model + VALID01's pinned upstream annotations) |
| Runtime | 1065 s total (ALIGN02 58.8 s, ALIGN03 194.6 s, ALIGN04 547.1 s, CURR01 27.6 s, VALID01 175.1 s) |
| Environment | Python 3.13.15, `torch` 2.11.0+cpu, `sentence-transformers` 6.0.1, AMD EPYC 7B12, `pip_mode: pinned` |
| Comparison | `reports/CPU_VS_COMMITTED_KAGGLE.md` Part 1 - 614 `metrics.json` numeric fields, 0 beyond tolerance, largest `\|diff\|` **0.000e+00**. Part 2 - 14 CSV artifacts, 17,796 numeric cells, 2,445 differing (per-pair cosines only), largest **1.0e-04**; headline metrics agree at reported precision |
| Headline gate | 113 headline fields (SGI, CI bounds, domain deficits, CS2023 coverage, κ, precision, recall, AUC) checked at the decimals the manuscript reports — 0 mismatches |
| Archive | `MoshinAli/skill-gap-cpu-verification` (22 files: `results_cpu_kaggle/`, the comparison report, `run_info.json`) |

Two pitfalls the driver now guards, both hit on the way:

1. **Kaggle's CLI uploads only a kernel's `code_file`.** An extra `repo.tar.gz` in
   the kernel folder never reaches the machine (first run died with
   `FATAL: repo.tar.gz not shipped with the kernel`). The kernel now clones the
   public repository and then *pins itself*, asserting the clone's HEAD equals the
   commit recorded at build time and checking that commit out if GitHub's tip has
   moved.
2. **`results_cpu/` is tracked, so the clone already contained the 8 committed
   non-embedding experiments.** Leaving them would have made the comparison
   circular. The driver deletes the cloned `results_cpu/` before running, so from
   that point it can only hold fresh output; the 8 cloned copies that did land in
   the first download were moved out of `results_cpu_kaggle/` before the gate ran.

Nothing here changes a committed artifact under `results/`: outputs go to
`results_cpu_kaggle/`, and `results/registry.json` is not touched.

The remaining sections describe the manual procedure this driver automates, and are
kept so the same run can be repeated on any CPU-only Linux machine.

### 13.1 Prerequisites

- Linux (Ubuntu 22.04/24.04 or similar) with Python 3.12 or 3.14.
- ~6 GB free disk (the input bundle is 1.4 GB; embeddings dominate the rest).
- No GPU required — these runs are CPU-only and single-threaded by design.
- Network only for staging inputs and the model; go offline afterwards.

### 13.2 Stage the environment

```bash
git clone https://github.com/MIHMahmudEli/skill-gap-analysis.git
cd skill-gap-analysis
python -m venv .venv && source .venv/bin/activate
pip install --require-hashes -r requirements.txt   # or: pip install -r requirements.txt
python -c "import torch, sentence_transformers; print(torch.__version__)"
# must print a version, not ImportError. If it fails, fix the environment first.
```

### 13.3 Stage the raw inputs

Route A (frozen bundle, §4) is what the committed artifacts were produced from:

```bash
export KAGGLE_USERNAME=... KAGGLE_KEY=...
kaggle datasets download -d studyhub991/skill-gap-inputs-v1 -p _bundle --unzip
export SKILLGAP_INPUT_DIR="$PWD/_bundle"
sha256sum -c datasets/input_checksums.sha256
```

### 13.4 Re-run the 5 experiments, offline, single-threaded

`scripts/run_cpu_rerun.py` pins every BLAS thread to 1, forces `PYTHONHASHSEED=42`,
and routes each experiment's output to `results_cpu/<EXPERIMENT_ID>` via
`SKILLGAP_OUTPUT_DIR`, so nothing under `results/` is written.

```bash
# go offline now: no further network is needed or used
python scripts/run_cpu_rerun.py --only \
  ALIGN02_semantic_sbert ALIGN03_domain_gap ALIGN04_crosscorpus_linkedin \
  CURR01_cs2023_anchor VALID01_esco_gold
```

Each of the 5 prints `OK <seconds>` and writes `results_cpu/<ID>/metrics.json`.
To a different tree (recommended, so this run cannot be confused with the
author's), set the output root by copying the runner's output dir afterwards, or
run from a clone and keep its `results_cpu/`.

Expected wall time on 1 CPU core: ALIGN02 ~10 min, CURR01 ~10 min, VALID01 ~20 min,
ALIGN03 ~45 min, ALIGN04 ~2--4 h (it embeds ~1.29M postings). Total ~3--5 h.

### 13.5 Compare against the committed artifacts

```bash
python scripts/compare_cpu_results.py \
  --cpu-dir results_cpu --ref-dir results \
  --report reports/LINUX_VS_COMMITTED.md
echo "exit=$?"     # 0 = every field within tolerance
```

The comparison walks every numeric leaf of each `metrics.json` recursively, with
`max(1e-9, 1e-6 * |value|)` tolerance. Fields that legitimately vary between a GPU
and a CPU run are excluded by construction (`runtime_sec`, `device`, seeds,
statuses, timestamps, kernel slug, package versions) — they carry no claim.

**What to expect, and why it is not necessarily zero.** For the 8 experiments that
already re-ran on the author's CPU, every difference was exactly `0`: those use
integer counts, rounded proportions and seeded-bootstrap percentiles that do not
depend on the arithmetic's order. The 5 embedding experiments are different in
kind — `SentenceTransformer.encode` accumulates float32 dot products in an order
that depends on BLAS threading and the SIMD code path, so a GPU encoding and a CPU
encoding of the same string can differ in the last bits, and those bits propagate
into cosine similarities and hence into threshold decisions at $\tau$.

Therefore:

- A **small number of fields differing within $10^{-6}$ relative** (cosine
  similarities, SGI at a threshold, bootstrap percentiles) is the expected and
  acceptable outcome, and is exactly what `--report` quantifies. Record it; do not
  hide it, and do not round it away.
- A **headline SGI differing beyond $1e-6$ relative** is a stop condition. Report
  it with both values, the diff, and the threshold at which the divergence
  appears, and do not update the manuscript or the registry — the author decides
  whether the divergence is a tolerance artefact or a genuine non-determinism
  finding.
- **Structural fields must not differ at all**: `n_rows`, token/vocabulary counts,
  the number of pairs above threshold at every $\tau$, and any integer count.
  A difference there is a bug in the re-run or a changed input, not float noise.

To attribute a divergence to threading rather than to the data, re-run one
experiment twice with a different thread count and compare those two runs to each
other first:

```bash
OMP_NUM_THREADS=1  python scripts/run_cpu_rerun.py --only ALIGN02_semantic_sbert
mv results_cpu/ALIGN02_semantic_sbert results_cpu_t1/ALIGN02_semantic_sbert
OMP_NUM_THREADS=4  python scripts/run_cpu_rerun.py --only ALIGN02_semantic_sbert
python scripts/compare_cpu_results.py --cpu-dir results_cpu_t1 --ref-dir results_cpu
```

If the two CPU runs already differ from each other beyond tolerance, the cause is
BLAS threading, and the committed GPU values remain the reported ones with the
divergence disclosed.

### 13.6 What to do with the result

**DONE 2026-10-13 — the all-5-within-tolerance branch was taken.** The manuscript
sentence in §Reproducibility and Data Availability was strengthened to name the
completed CPU verification (288 + 614 = 902 compared `metrics.json` numeric
fields, all zero difference), and `reports/CPU_VS_COMMITTED_KAGGLE.md` plus
`reports/cpu_kaggle_gate.json` were committed as the evidence. The row-level CSV
artifacts are a **separate** comparison and are not bit-identical for the 5:
headline metrics agree at reported precision; per-pair cosine similarities differ
by at most 1e-4 (CPU vs GPU float differences). Part 2 of that report and
`reports/cpu_kaggle_csv_diff.json` carry the counts and maxima (14 CSV files,
5,985 rows, 17,796 numeric cells, 2,445 differing, largest 1.0e-04). The branches
below are kept for anyone repeating the run.

- If all 5 are within tolerance: the manuscript sentence in
  §Reproducibility and Data Availability may be strengthened from "not claimed
  here as verified" to name the completed CPU verification. That edit is the
  author's to make and requires a commit; it is not automatic.
- If any headline metric exceeds tolerance: stop, write the comparison into
  `reports/`, and escalate. Do not silently adopt the CPU value.
- Either way, do not overwrite anything under `results/`, and do not regenerate
  `results/verification_report.json` as a side effect — `experiments/verify.py`
  writes it, so run it only if you intend to.