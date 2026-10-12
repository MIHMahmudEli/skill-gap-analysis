# Skill Gap Analysis

A data-driven framework for quantifying the gap between employer skill
requirements and an employer-derived academic reference profile (a proxy for
curricula, not institutionally collected syllabi) using NLP, statistics, and
machine learning — with **every reported number traceable to a registered,
GPU-executed experiment**.

## Overview

The project analyzes 15 publicly available open datasets (**3,163,517 raw rows**,
de-duplicating to **2,123,889 unique rows** — a row total that pools four
incompatible row units, not an all-purpose record count), acquired from
LinkedIn, Kaggle, and HuggingFace. The main article answers three research
questions (RQ1–RQ3); the placement component is audited in a companion
benchmark-audit article (`paper_placement/`):

- **1,349,621 real web-scraped posting rows** — the LinkedIn 2024 scrape
  (1,348,454; root of the scrape family) plus a 1,167-posting posting-derived
  academic reference. The HuggingFace jobs and skills tables share an identical
  set of 519,814 `job_link` identifiers (a linked posting–skill pair, counted
  once), and that entire pair is a strict subset of the LinkedIn 2024 postings
  table — verified pairwise in `datasets/OVERLAP_AUDIT.csv` — so it contributes
  **0** new postings (its 519,814 skill-pair rows vanish on de-duplication).
- **316,279 aggregated title × skill count rows** — the USA job-market file,
  whose source scrape is **unverifiable** (aggregate rows, not postings).
- **457,989 synthetic rows** — the AI job series (10,345), the AI salary file
  (15,000), India skills profiles (12,000; its own README states "generated,
  not collected"), and **420,644 generated student/alumni records** (all seven
  placement/graduate benchmarks; generator evidence in
  `datasets/REAL_VS_SYNTHETIC.csv`).

The headline gap-measurement results (RQ2/RQ3: SGI 52% → 32%) rest entirely on
the real posting family; `reports/REAL_VS_SYNTHETIC_FINDINGS.md` documents the
generator-signance evidence, and the RQ4/RQ5 placement material now lives in the
companion benchmark audit (`paper_placement/`).

- **RQ1** — market skill topography
- **RQ2** — lexical vs. semantic (Sentence-BERT) reference-profile alignment (SGI)
- **RQ3** — eight-category domain-level skill gaps with bootstrap CIs
- The former **RQ4/RQ5** placement analyses (employability determinants,
  cross-cohort dynamics; STAT01/STAT02/PLAC01/INTL01) are reported in the
  companion benchmark-audit article `paper_placement/` (no real-world claims
  about graduates; tier-flagged benchmark provenance). RQ1 also carries the
  geographic distribution of postings (GEO01).

## Project Structure

```
.
├── experiments/               # Reproducible experiment suite (source of truth)
│   ├── common.py              # Seeds, taxonomy, env helpers, worker parsing
│   ├── kaggle_client.py       # Kaggle CLI wrapper (push/poll/download, UTF-8)
│   ├── scheduler.py           # Dependency-aware registry loop + watchdog
│   ├── stage_inputs.py        # Builds/pushes input bundle to Kaggle dataset
│   ├── verify.py              # Schema + sanity checks -> VERIFIED
│   ├── sync_to_hf.py          # Uploads verified results to HuggingFace
│   ├── make_latex.py          # Generates paper/tables/*.tex + figures/*.pdf
│   └── exp_scripts/           # One self-contained script per experiment
│       ├── align01_lexical.py
│       ├── align02_semantic.py
│       ├── align03_domain_gap.py
│       ├── align04_crosscorpus.py
│       ├── curr01_cs2023_anchor.py
│       ├── stat01_placement_core.py
│       ├── stat02_external_valid.py
│       ├── geo01_linkedin.py
│       ├── trends01_ai.py
│       ├── intl01_internship.py
│       ├── plac01_global_country.py
│       └── valid01_esco_gold.py
├── results/
│   ├── registry.json          # Experiment lifecycle status (see below)
│   └── <EXP_ID>/              # Downloaded metrics.json + CSV artifacts
├── paper/
│   ├── main.tex, references.bib, main.pdf
│   ├── tables/*.tex           # AUTO-GENERATED from verified CSVs
│   └── figures/*.pdf          # AUTO-GENERATED from verified CSVs
├── datasets/                  # Local data copies + legacy analysis scripts
├── audit/                     # Q1-readiness audit (Phases 0–12; claim ledger, fixes)
├── tests/                     # Unit + integration tests (pytest)
├── reproduce_local.py         # Single local entry point (env→checksums→verify→claims→stats→citations)
├── reports/                   # Experiment / gap / Q1-readiness reports
├── requirements.txt           # Verified execution environment
└── .env                       # Kaggle/HF credentials (git-ignored)
```

## Quick Start (local reproduction)

```bash
pip install -r requirements.txt pytest
python -m pytest tests/ -q          # 13 tests; requires results/ + optional raw CSVs
python reproduce_local.py           # full local gate (skippable stages via --skip)
# PDF: cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```

Kaggle GPU re-runs: see `experiments/scheduler.py` and `archive/EXPERIMENT_REPORT.md` (superseded pre-audit record).

## Experiment Lifecycle

Each experiment moves through
`PENDING → RUNNING → COMPLETED → VERIFIED → USED_IN_MANUSCRIPT`
(with `FAILED`/`RETRY` on error). Statuses live in `results/registry.json`;
manuscript tables/figures are generated only from `VERIFIED` outputs.

| ID | Task | Kernel (Kaggle GPU) | Status |
|----|------|---------------------|--------|
| ALIGN01 | Lexical alignment + SGI bootstrap | nihanshadman/sg-align01-lexical-a1 | USED_IN_MANUSCRIPT |
| ALIGN02 | SBERT semantic alignment, τ sweep | nihanshadman/sg-align02-semantic-a3 | USED_IN_MANUSCRIPT |
| ALIGN03 | Eight-category domain gap | nihanshadman/sg-align03-domaingap-a2 | USED_IN_MANUSCRIPT |
| STAT01 | Placement statistics + CV | nihanshadman/sg-stat01-placement-a2 | USED_IN_MANUSCRIPT |
| STAT02 | External validation | leyamridha/sg-stat02-external-a1 | USED_IN_MANUSCRIPT |
| GEO01 | Geographic shares | sadmanhasanmiraj/sg-geo01-linkedin-a1 | USED_IN_MANUSCRIPT |
| TRENDS01 | AI trends 2020–2026 | nishat1156/sg-trends01-ai-a1 | VERIFIED (registry; not used in manuscript — strong generator signatures; corpus excluded from the manuscript) |
| INTL01 | Internship effect (archived; not reported per Phase 4 D3) | afrojahaqueshornaly/sg-intl01-internship-a1 | USED_IN_MANUSCRIPT |
| PLAC01 | Placement by country | abdullahalsayfan/sg-plac01-global-a1 | USED_IN_MANUSCRIPT |
| VALID01 | External gold-standard matcher validation (SkillSpan/ESCO) | nihanshadman/sg-valid01-gold-a1 | USED_IN_MANUSCRIPT |
| ALIGN04 | Nested-superset SGI robustness check (LinkedIn, 1.29M postings) | tasnimjenny/sg-align04-crosscorpus-a4 | USED_IN_MANUSCRIPT |
| CURR01 | CS2023 curriculum anchor (computational embedding coverage; 2,197 topics) | rssiam/sg-curr01-cs2023-a2 | USED_IN_MANUSCRIPT |

## Usage

```bash
pip install -r requirements.txt

# 1. (one-off) stage inputs and publish the Kaggle input dataset
python experiments/stage_inputs.py

# 2. run the scheduler (pushes -> polls -> downloads; watchdog on errors)
python experiments/scheduler.py

# 3. verify outputs (schema + sanity + cross-checks)
python experiments/verify.py

# 4. archive verified results to HuggingFace
python experiments/sync_to_hf.py

# 5. regenerate all manuscript tables and figures from verified CSVs
python experiments/make_latex.py

# 6. compile the manuscript
cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

Experiment scripts accept `SKILLGAP_INPUT_DIR` / `SKILLGAP_OUTPUT_DIR` for
local smoke tests; on Kaggle they read the mounted bundle
`/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1/`.

## Key Verified Results

- **Skill Gap Index** (primary 519K corpus): lexical **52%** (95% CI [42, 63]);
  semantic **32%** at
  τ = 0.5 (95% CI [23, 41]); 46% at τ = 0.7
- **Domain gaps** (postings, pp): Cloud & Infrastructure **2.45** (Critical),
  Programming **1.69**, Data Science **1.20**; semantic alignment cuts each by
  up to 74%; Soft Skills fully covered
- **Placement model** (statsmodels MLE, standardized; companion benchmark
  audit, tier-flagged benchmark provenance): Communication OR = 6.55 [5.86, 7.31],
  CGPA OR = 6.28, IQ OR = 5.16, Projects OR = 3.20 (all p < 0.001); CV accuracy
  90.11% ± 0.74%, ROC-AUC 0.9406
- **External validation** (companion): ROC-AUC 0.768 (Student Career Success,
  N = 50k), 0.576 (Global Placement)
- **Internship association**: the +15.34 pp international-graduate contrast
  (INTL01) is archived but **not reported as a finding** in either manuscript
  (Phase 4 D3: generated file, no claim about graduates); in the separate
  college cohort (N = 10,000) the internship risk difference is **−0.44 pp**
  (null; OR 1.02, p = 0.62; companion audit)
- **Credential locality (H5)**: **untested** — its registered test (PLAC01) is
  a benchmark of unverified provenance (moderate generator signatures), so the cross-country similarity it shows
  (India 63.2% … Germany 60.0%) is a benchmark property, not evidence about
  graduates (companion)
- **Geographic**: USA 85.2%, UK 8.4%, Canada 4.2%, Australia 2.2% (N = 1.35M)
- **Matcher validity** (VALID01 vs expert SkillSpan→ESCO mappings, 2,907
  pairs): SBERT τ = 0.5 agreement **κ = 0.737** [0.711, 0.760], accuracy
  87.9%, ROC-AUC 0.961; lexical exact-match κ = 0.112
- **Nested-superset robustness check** (ALIGN04, LinkedIn N = 1.29M — a strict
  superset of the primary 519K corpus, same scrape family; not an independent
  replication): lexical SGI **0.37** [0.28, 0.47], semantic SGI **0.14**
  [0.07, 0.21] — both intervals exclude zero; lexical > semantic ordering and
  τ-monotonicity reproduce the primary corpus exactly
- **CS2023 anchor** (CURR01, computational embedding coverage of 2,197 topics /
  17 knowledge areas; no human line-by-line audit): the academic profile covers
  **30.4%** [28.5, 32.4] of the curricular Body of Knowledge at τ = 0.5
  (HCI/DM best ≥ 52%; Algorithmic Foundations 12.6%, Math 10.0%), with 49.6%
  of profile skills grounded in the guidelines

## Data & Artifact Archives

- **Input bundle (Kaggle)**: https://www.kaggle.com/datasets/studyhub991/skill-gap-inputs-v1
- **Experiment outputs (HuggingFace)**: https://huggingface.co/datasets/MoshinAli/skill-gap-experiments
- **Manuscript**: `paper/main.pdf` (16 pp, IEEEtran; anonymized for double-blind review)
- **Companion manuscript**: `paper_placement/main.pdf` (benchmark audit, IEEEtran)

Large source datasets (>10 MB) are not committed; see
`datasets/DATASET_MANIFEST.csv` and `datasets/download_kaggle.py`.

## Environment

Python 3.14.6 with pandas 3.0.5, numpy 2.5.1, scipy 1.18.1,
scikit-learn 1.9.0, statsmodels 0.15.0, sentence-transformers 6.0.1
(all-MiniLM-L6-v2), matplotlib 3.11.1, kaggle 2.2.4, huggingface_hub 1.29.0.
All splits/bootstrap resamples use seed 42 (multi-seed robustness: seeds 0–9).

## Contributing

Read [reports/CONTRIBUTING.md](reports/CONTRIBUTING.md) before changing anything.
Two rules are enforced mechanically, not by convention:

- **No push without the author's explicit written approval.** `scripts/pre-push`
  refuses every push unless `ALLOW_PUSH=1` is set. Install the hook once per clone
  with `git config core.hooksPath scripts`.
- **Sealed labelling keys never enter this repository.** They live outside it
  (e.g. `../sealed_keys/`) and are read via `ALIGN05_KEY`. `.gitignore` and
  `tests/test_no_tracked_secrets.py` both reject `*_key*.csv` and `sealed*/`.

These exist because a sealed key was published before labelling on 2026-10-12,
which voided the pre-registered ALIGN05 blinded gate and forced a sample re-draw
under a new seed — see `archive/align05_titles_200_key_RETIRED.md`.

## Citation

```bibtex
@software{skill_gap_analysis,
  title={Skill Gap Analysis: Academic-Industry Skills Gap Quantification},
  year={2026},
  url={https://github.com/MIHMahmudEli/skill-gap-analysis}
}
```

## License

MIT — see [LICENSE](LICENSE).
