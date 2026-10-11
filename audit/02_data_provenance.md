# Phase 2 — Data Provenance and Quality Audit

*Date: 2026-10-11 · Tools: `audit/validate_data.py` → `audit/02_data_quality.csv`
(22 files) + `audit/02_data_quality_summary.json`; targeted probes recorded below.
Raw data unmodified (read-only access).*

## 2.1 Headline Corrections (verified against local files)

| Manuscript / manifest claim | Local ground truth | Delta |
|---|---|---|
| 15 datasets, **3,176,266 records** | Unique records ≈ **2,643,703** | **−532,563 (−16.8%)** |
| HF Skill Gap **Jobs** 519,841 | 519,814 rows; job_link set **identical** to skills file | −27; **linked table** |
| HF Skill Gap **Skills** 519,814 | 519,814 ✓ | — |
| HF Job Skill Set ("academic reference") **13,833** | **1,167 rows** | **−12,666** |
| LinkedIn postings **1,348,510** | **1,348,454** | −56 |
| LinkedIn job_skills (ALIGN04 input) 1,296,381 | 1,296,381 ✓ | — |
| College placement 10,000 | 10,000 ✓ (Placement Yes=1,659/No=8,341 ✓) | — |
| All other manifest counts (USA 316,279; intl 300,000; SCS 50,000; career 38,444; AI15K 15,000; India skills 12,000; AI trends 10,345; college 10,000; global 10,000; NGESS 7,200; fresher 5,000) | ✓ match local | — |

**Root cause of the 3,176,266 headline** (exact arithmetic):
519,814 (HF skills counted again after jobs) + 12,666 (academic ref overcount)
+ 56 (LinkedIn) + 27 (HF jobs) = **532,563**.

Recomputed unique inventory (unit-aware):

| Unit | N | Datasets |
|---|---|---|
| Job postings (HF jobs≡skills) | 519,814 | 1 unique corpus, 2 files |
| LinkedIn postings | 1,348,454 | asaniczka (skills subset 1,296,381) |
| USA postings | 316,279 | batuhanklac |
| AI/other postings | 25,345 | trends 10,345 + AI15K 15,000 |
| Synthetic profiles | 12,000 | India skills (**synthetic**, disclosed) |
| Academic-reference postings | 1,167 | skill-gap-analytics/academic-reference |
| Student/person records | 420,644 | 7 Tier-2 datasets |
| **Total unique records** | **≈ 2,643,703** | (vs 3,176,266 claimed) |

## 2.2 Dataset Usage Map (which files actually feed experiments)

| Dataset (local file) | Used by | Role |
|---|---|---|
| `hf_skill_gap_skills.csv` (519,814) | ALIGN01, ALIGN02, ALIGN03 | **Market corpus** |
| `hf_job_skill_set.csv` (1,167) | ALIGN01–04, CURR01 | **Academic reference profile** |
| LinkedIn `job_skills.csv` (1,296,381) | ALIGN04 | Cross-corpus market |
| LinkedIn `linkedin_job_postings.csv` (1,348,454) | GEO01 | Geography |
| `college_student_placement_dataset.csv` | STAT01 | Placement model |
| `student_career_success_dataset.csv` | STAT02 | External cohort A |
| `global_placement.csv` | STAT02, PLAC01 | External cohort B / countries |
| intl graduates `dataset.csv` (300,000) | INTL01 | Internship contrast |
| AI trends 2020–2026 (10,345) | TRENDS01 | Longitudinal shares |
| SkillSpan upstream (VALID01 `_upstream/`) | VALID01 | Expert gold |
| CS2023 PDF/topics | CURR01 | Curriculum anchor |
| `hf_skill_gap_jobs.csv` | **none** (≡skills keys) | inventory only |
| USA job market (316,279) | **none** | inventory only |
| Career change (38,444) | **none** | inventory only |
| AI Job Market 15,000 | **none** | inventory only |
| India skills (12,000, **synthetic**) | **none** | inventory only |
| NGESS (7,200), fresher (5,000) | **none** | inventory only |
| `data-science-job-postings-and-skills/*` (12,217) | **none**; **not in manifest** | orphan local files |
| `job_summary.csv` (48.2M rows) | **none** | unused raw |
| `ai_job_dataset.csv` ≡ `ai_job_dataset1.csv`? | need flag | two copies 15,000 each |

**Implication:** the sentence "we analyze 15 datasets totaling 3,176,266 records"
(abstract, §I, §III-A) is **not accurate as written**. Primary analyses use ~9
sources. Fix in Phase 9 with unit-aware counts.

## 2.3 The Academic Reference Profile (critical construct finding)

`hf_job_skill_set.csv` (the academic side of every SGI number):

- **1,167 rows**, each a full job posting (title, description, skill list).
- **5 categories only:** IT 240, Business Development 239, Finance 236,
  Sales 232, HR 220.
- **Not** course syllabi, NOT a CS curriculum extract, NOT 13,833 taxonomy entries.
- `academic_top500.csv` frequency "communication 1092" = 1,092/1,167 postings (93.6%).

The manuscript already hedges ("standardized curriculum reference profiles
rather than scraped syllabi", §III-B; Limitation 3 + CURR01 anchor), but
**Table I's description "Curriculum-domain skill taxonomy reference,
13,833 records" is contradicted by the data** and must be corrected to
"curated business/IT job-skill reference postings (N = 1,167)". CURR01's
30.4% CS2023 coverage is consistent with this weakly-curricular profile —
the anchor experiment is what keeps the SGI interpretable, and its
limitation must be stated even more plainly.

## 2.4 Quality Signals (from `02_data_quality.csv`)

| File | n_rows | dup_rows | mean missing% | Notes |
|---|---|---|---|---|
| college placement | 10,000 | 0 | low | **College_ID unique only 100** (9,900 duplicate IDs!) — benchmark reuses IDs; no effect on models (ID unused) but flags synthetic benchmark structure |
| hf skills/jobs | 519,814 each | 0 | 0% on keys | identical key sets |
| linkedin postings | 1,348,454 | see CSV | — | 56-row gap vs manifest |
| linkedin job_skills | 1,296,381 | — | — | 52,073 postings without skills rows (3.9%) |
| job_summary | 48,219,736 | — | — | unused; enormous |
| ai_job_dataset vs ai_job_dataset1 | 15,000 each | compare | — | possible duplicate copies (same source dir) |
| India skills | 12,000 | — | — | **synthetic by construction** (provider README) |
| data-science-job-postings | 12,217 ×3 | — | — | orphan, not in manifest, unused |

Per-file schemas, checksums (SHA-256 of first 1 MB), and duplicate counts:
`audit/02_data_quality.csv`.

## 2.5 Provenance Fields Unresolved (documented, not inferred)

| Item | Status |
|---|---|
| Exact collection dates behind Kaggle mirrors | Not in repo; only download_date 2026-09-06 recorded |
| Licenses per dataset | Manifest asserts CC0/CC-BY/ODbL; **not independently re-verified from provider pages in this audit** (network not used for license scraping) |
| LinkedIn "2024" snapshot window | Provider slug only |
| Whether HF `academic-reference` was curated by the HF uploader as intended curriculum proxy | Upstream intent unverified; content audited here |
| Employer/ad clustering | job_link unique per posting; employers available in jobs table but not exploited (no cluster-robust inference at employer level) |

## 2.6 Changes Made

- Added `audit/validate_data.py` (re-runnable; read-only).
- Added `audit/02_data_quality.csv`, `audit/02_data_quality_summary.json`,
  this file.
- **No raw data modified. No manuscript edits yet.**

## 2.7 Actions Picked Up by Later Phases

1. **Phase 9 (manuscript):** correct Table I (academic ref N=1,167 + honest
   description); restate corpus totals unit-aware (~2.64M unique); disclose
   HF jobs/skills linkage; keep synthetic label for India dataset.
2. **Phase 8:** record per-file SHA-256 in manifest; fix manifest counts
   (jobs 519,814; academic 1,167; LinkedIn 1,348,454).
3. **Phase 5/6:** treat College_ID duplication + k-of-n labels as evidence the
   placement benchmarks are semi-synthetic (already partially disclosed).
