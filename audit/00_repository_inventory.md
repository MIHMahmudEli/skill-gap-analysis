# Phase 0 — Repository Inventory and Safety Record

*Audit date: 2026-10-11 · Auditor: automated Q1-readiness audit · Working dir: `D:\Research\2. Complete\Gap-between acadimic and industry`*

## 0.1 Starting State (recorded before any edits)

| Item | Value |
|---|---|
| Branch at start | `main` |
| Commit at start | `abbff839f99cfd3070c2ef50bff2cc3aad431779` (`abbff83`) |
| Working tree | **Clean** (0 modified, 0 untracked) |
| Remote | `origin/main` = `abbff83` (pushed) |
| Audit branch | `q1-readiness-audit` (created from `abbff83`; `main` untouched) |
| Python | 3.14.6 (Windows, local) |
| LaTeX | MiKTeX pdflatex/bibtex at `D:\MiKTeX\miktex\bin\x64\` |
| Credentials | `.env` present, **gitignored**; keys observed by name only (16× Kaggle worker pairs + 1× HF token). Never read or printed values. |

## 0.2 What This Repository Is

A skills-gap research pipeline: 15 public datasets → 12 registered GPU/CPU
experiments (`experiments/scheduler.py` → Kaggle kernels) → verified artifacts
in `results/<EXP_ID>/` → auto-generated LaTeX tables/figures
(`experiments/make_latex.py`) → IEEEtran manuscript `paper/main.tex` (15 pp PDF
at `abbff83`).

## 0.3 Authoritative Manuscript Source

- **Source of truth:** `paper/main.tex` (90,366 bytes) + `paper/references.bib`
  (52 entries) + auto-generated `paper/tables/*.tex` (9 files) and
  `paper/figures/*.pdf` (7 files).
- **Build process:** `pdflatex main && bibtex main && pdflatex ×2` in `paper/`.
  Last build (2026-10-14): 17 pages, 795,918 bytes, 0 errors, 0 undefined
  references (verified in `paper/main.log`).
- **Tables/figures are generated**, not hand-authored: `experiments/make_latex.py`
  reads `results/<EXP_ID>/*.csv` + `metrics.json` only.

## 0.4 Directory Map (tracked vs generated vs external)

| Path | Role | Git |
|---|---|---|
| `experiments/*.py` | Pipeline (scheduler, verify, sync, make_latex, stage_inputs) | tracked |
| `experiments/exp_scripts/*.py` | 12 self-contained experiment scripts | tracked |
| `results/<EXP_ID>/` | Downloaded kernel outputs (metrics.json, CSVs, metadata.json) | tracked (small) |
| `results/registry.json` | Experiment lifecycle registry (12 entries) | tracked |
| `results/_kernels/`, `results/_staging/` | Kernel build snapshots / staging | **ignored** |
| `paper/main.tex`, `references.bib` | Manuscript source | tracked |
| `paper/main.pdf`, `*.aux/*.log/...` | Build artifacts | pdf tracked, rest ignored |
| `datasets/*.csv` (hf_*, table*) | Local copies of HF inputs + stale derived tables | manifest + derived_matrices tracked; raw `datasets/*.csv` ignored |
| `datasets/kaggle/**` | 17 raw Kaggle CSVs (~6.6 GB) present **locally only** | **ignored** |
| `datasets/cs2023/` | CS2023 BoK PDF + extracted topics (curriculum anchor) | tracked (3.6 MB PDF) |
| `datasets/DATASET_MANIFEST.csv` | 15-dataset provenance manifest | tracked |
| `reports/` | Experiment/readiness reports | tracked |
| `README.md`, `requirements.txt`, `LICENSE` | Docs / pinned env / MIT | tracked |
| `.env` | Credentials | **ignored, never committed** |
| `audit/` | This audit (new) | new on audit branch |

**External storage:** Kaggle input bundle `studyhub991/skill-gap-inputs-v1`
(1,404 MB, 9 CSVs); HF results archive `MoshinAli/skill-gap-experiments`;
Kaggle kernels per registry. No Git LFS.

## 0.5 Data Inventory (local files, not in Git)

Raw CSVs exist on disk under `datasets/kaggle/` (gitignored) and
`datasets/hf_*.csv` (gitignored). Local presence verified 2026-10-11:

| File | MB | In manifest? |
|---|---|---|
| `kaggle/1-3m-linkedin-jobs-and-skills-2024/job_summary.csv` | 4,865.7 | as linked dir (manifest lists dir size 641.5 = job_skills only?) |
| `kaggle/1-3m-linkedin-jobs-and-skills-2024/job_skills.csv` | 641.6 | yes (ALIGN04 input) |
| `kaggle/1-3m-linkedin-jobs-and-skills-2024/linkedin_job_postings.csv` | 396.1 | yes |
| `hf_skill_gap_jobs.csv` | 140.4 | yes (HF Skill Gap Jobs) |
| `hf_skill_gap_skills.csv` | 257.7 | yes (HF Skill Gap Skills; ALIGN01–03 market corpus) |
| `hf_job_skill_set.csv` | 4.7 | yes (HF academic reference) |
| `kaggle/usa-job-market-skills-and-title-analysis/usa_job_posting_dataset.csv` | 13.5 | yes |
| `kaggle/international-graduates-employment-dataset/dataset.csv` | 28.4 | yes |
| `kaggle/student-career-success-prediction-dataset/student_career_success_dataset.csv` | 8.0 | yes |
| `kaggle/data-science-job-postings-and-skills/*` (3 files) | 61.5 | **NOT in manifest; no experiment references found** → orphan, flagged Phase 2 |
| 8 more placement/trend CSVs | ≤3.8 each | yes |

**Reproducibility caveat:** a clean clone cannot run experiments without
re-downloading Kaggle/HF sources; `datasets/download_kaggle.py` exists but is
not version-pinned per file (no checksums recorded anywhere).

## 0.6 Dependency and Environment Pinning

- `requirements.txt`: 12 packages, fully pinned (pandas 3.0.5, numpy 2.5.1,
  scipy 1.18.1, sklearn 1.9.0, statsmodels 0.15.0, sentence-transformers 6.0.1
  → all-MiniLM-L6-v2, matplotlib 3.11.1, huggingface-hub 1.29.0, requests 2.34.2,
  python-dotenv 1.2.3, kaggle 2.2.4).
- Missing pins: Python minor version (3.14.x), CUDA/torch stack (transitive via
  sentence-transformers), LaTeX distribution version.

## 0.7 Test Infrastructure

**None found.** No `tests/`, no `pytest`/`unittest` files, no CI workflows
(no `.github/`). `experiments/verify.py` is a data/schema sanity gate, not a
unit test suite. → Phase 8 deliverable.

## 0.8 Claim-Support Surface (quick map; full ledger Phase 1)

| Manuscript claim cluster | Primary evidence |
|---|---|
| SGI 52% lexical / 32% semantic (CIs) | `results/ALIGN01_lexical_bootstrap/metrics.json`, `ALIGN02_semantic_sbert/metrics.json` |
| Domain deficits (Cloud 2.45 pp …) | `results/ALIGN03_domain_gap/metrics.json` + CSVs |
| Cross-corpus SGI (0.37 / 0.14) | `results/ALIGN04_crosscorpus_linkedin/*` |
| CS2023 coverage 30.4% / reverse 49.6% | `results/CURR01_cs2023_anchor/*` |
| Matcher κ=0.737, AUC 0.961 | `results/VALID01_esco_gold/*` |
| Logistic ORs, CV 90.11%, AUC 0.9406 | `results/STAT01_placement_core/*` |
| External AUC 0.768 / 0.576 | `results/STAT02_external_validation/metrics.json` |
| Internship +15.34 pp | `results/INTL01_internship_effect/metrics.json` |
| Geography 85.2% US | `results/GEO01_linkedin_shares/metrics.json` |
| AI trends shares | `results/TRENDS01_ai_longitudinal/metrics.json` |
| Placement by country | `results/PLAC01_global_by_country/metrics.json` |
| Dataset counts (15 datasets, 3,176,266 records) | `datasets/DATASET_MANIFEST.csv` sum — **to be recomputed Phase 2** |

## 0.9 Safety Checks Performed

- No secrets staged or printed (`.env` names only; `git status` clean).
- No raw datasets committed (`datasets/kaggle/`, `datasets/*.csv` ignored).
- Audit work isolated on `q1-readiness-audit`; `main` remains at `abbff83`.

## 0.10 Initial Risk Register (pre-verification; refined per phase)

| # | Risk | Sev | Note |
|---|---|---|---|
| R1 | No unit/integration tests for SGI/matching code | Major | Phase 8 |
| R2 | No data checksums; local raw data ~6.6 GB not reproducible from clone alone | Major | Phase 2 |
| R3 | Manifest vs local files mismatch (orphan `data-science-job-postings`, LinkedIn dir size) | Moderate | Phase 2 |
| R4 | India Skills Intelligence dataset documented as **synthetic** (manifest) — must not be described as real observations | Moderate | Phase 2/5 |
| R5 | SGI estimand validity (proxy academic reference; τ choice) | Major | Phase 3–4 |
| R6 | Causal language risk on observational placement/internship data | Major | Phase 5/9 |
| R7 | IEEEtran used without declared target journal | Moderate | Phase 11 |
| R8 | External AUC 0.576 (near-chance) must remain fully disclosed | Minor | Phase 6 |

*Phase 0 complete. Next: Phase 1 claim-to-evidence ledger.*
