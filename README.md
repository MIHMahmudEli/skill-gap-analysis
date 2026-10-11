# Skill Gap Analysis

A data-driven framework for quantifying the gap between academic curricula and
industry skill requirements using NLP, statistics, and machine learning — with
**every reported number traceable to a registered, GPU-executed experiment**.

## Overview

The project analyzes 15 publicly available open datasets (2.64M unique records;
raw file row-sum 3.18M includes a linked HF posting–skill pair counted once)
from LinkedIn, Kaggle, and HuggingFace and answers five research questions (RQ1–RQ5):

- **RQ1** — market skill topography and 2020–2026 trends
- **RQ2** — lexical vs. semantic (Sentence-BERT) curriculum alignment (SGI)
- **RQ3** — eight-category domain-level skill gaps with bootstrap CIs
- **RQ4** — graduate placement determinants, CV benchmarks, tree-rule audit,
  external validation
- **RQ5** — geographic concentration and internship/cohort effects

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

Kaggle GPU re-runs: see `experiments/scheduler.py` and `reports/EXPERIMENT_REPORT.md`.

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
| TRENDS01 | AI trends 2020–2026 | nishat1156/sg-trends01-ai-a1 | USED_IN_MANUSCRIPT |
| INTL01 | Internship effect | afrojahaqueshornaly/sg-intl01-internship-a1 | USED_IN_MANUSCRIPT |
| PLAC01 | Placement by country | abdullahalsayfan/sg-plac01-global-a1 | USED_IN_MANUSCRIPT |
| VALID01 | External gold-standard matcher validation (SkillSpan/ESCO) | nihanshadman/sg-valid01-gold-a1 | USED_IN_MANUSCRIPT |
| ALIGN04 | Cross-corpus SGI replication (LinkedIn, 1.29M postings) | tasnimjenny/sg-align04-crosscorpus-a4 | VERIFIED |
| CURR01 | CS2023 curriculum anchor validation (2,197 topics) | rssiam/sg-curr01-cs2023-a2 | VERIFIED |

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

- **Skill Gap Index**: lexical **52%** (95% CI [42, 63]); semantic **32%** at
  τ = 0.5 (95% CI [23, 41]); 46% at τ = 0.7
- **Domain gaps** (postings, pp): Cloud & Infrastructure **2.45** (Critical),
  Programming **1.69**, Data Science **1.20**; semantic alignment cuts each by
  up to 74%; Soft Skills fully covered
- **Placement model** (statsmodels MLE, standardized): Communication
  OR = 6.55 [5.86, 7.31], CGPA OR = 6.28, IQ OR = 5.16, Projects OR = 3.20
  (all p < 0.001); CV accuracy 90.11% ± 0.74%, ROC-AUC 0.9406
- **External validation**: ROC-AUC 0.768 (Student Career Success, N = 50k),
  0.576 (Global Placement)
- **Internship effect**: +15.34 pp employment (95% CI [14.99, 15.73]),
  N = 300,000
- **Geographic**: USA 85.2%, UK 8.4%, Canada 4.2%, Australia 2.2% (N = 1.35M)
- **Matcher validity** (VALID01 vs expert SkillSpan→ESCO mappings, 2,907
  pairs): SBERT τ = 0.5 agreement **κ = 0.737** [0.711, 0.760], accuracy
  87.9%, ROC-AUC 0.961; lexical exact-match κ = 0.112
- **Cross-corpus replication** (ALIGN04, LinkedIn N = 1.29M): lexical SGI
  **0.37** [0.28, 0.47], semantic SGI **0.14** [0.07, 0.21] — both intervals
  exclude zero; lexical > semantic ordering and τ-monotonicity reproduce the
  primary corpus exactly
- **CS2023 anchor** (CURR01, 2,197 topics / 17 knowledge areas): academic
  profile covers **30.4%** [28.5, 32.4] of the curricular Body of Knowledge
  at τ = 0.5 (HCI/DM best ≥ 52%; Algorithmic Foundations 12.6%, Math 10.0%),
  with 49.6% of profile skills grounded in the guidelines

## Data & Artifact Archives

- **Input bundle (Kaggle)**: https://www.kaggle.com/datasets/studyhub991/skill-gap-inputs-v1
- **Experiment outputs (HuggingFace)**: https://huggingface.co/datasets/MoshinAli/skill-gap-experiments
- **Manuscript**: `paper/main.pdf` (15 pp, IEEEtran)

Large source datasets (>10 MB) are not committed; see
`datasets/DATASET_MANIFEST.csv` and `datasets/download_kaggle.py`.

## Environment

Python 3.14.6 with pandas 3.0.5, numpy 2.5.1, scipy 1.18.1,
scikit-learn 1.9.0, statsmodels 0.15.0, sentence-transformers 6.0.1
(all-MiniLM-L6-v2), matplotlib 3.11.1, kaggle 2.2.4, huggingface_hub 1.29.0.
All splits/bootstrap resamples use seed 42 (multi-seed robustness: seeds 0–9).

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
