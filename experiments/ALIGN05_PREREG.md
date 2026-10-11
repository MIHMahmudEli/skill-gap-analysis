# ALIGN05 pre-registration — job-family stratification of the domain-gap deficits

**Status:** PRE-REGISTERED, NOT RUN. This file is committed before any ALIGN05
execution, per the revision protocol (`reports/Q1_REVISION_PLAN.md`, Phase 3)
and the author's instruction of 2026-10-11. Amendments after this commit must
be appended as dated, reasoned amendment blocks — never by silent edit.

## 1. Question

Does the H1 category-deficit structure (ALIGN03: Programming & Development
carrying the largest semantic deficit; Soft Skills fully covered) survive when
the market side is restricted to postings from *technically relevant job
families*? ALIGN03's demand shares are computed over an economy-wide corpus in
which technical postings are a minority (Programming demand 3.97% of all
postings); the objection under test is that deficit magnitudes are driven by
corpus composition rather than by curricular coverage.

## 2. Circularity firewall (binding)

1. **Job family is derived from `job_title` / occupation fields only — never
   from `job_skills`, skill tokens, taxonomy hits, embeddings, or any
   quantity entering the SGI or deficit computation.** The tech/non-tech label
   must be statistically independent of the measurement instrument given the
   title.
2. The rule set (§4) may not contain any term from the eight-category skill
   taxonomy used by ALIGN03, nor any of the academic/market top-100 profile
   skills. **Verification step (pre-run):** intersect the rule-set term list
   with the taxonomy skill list and the published top-100 profiles; report the
   intersection; every intersecting term is dropped or replaced before the
   classifier is frozen. The check output is recorded in `metrics.json`.
3. Deficits are computed with the unchanged ALIGN03 pipeline; ALIGN05 adds
   only a *row filter* over postings. No SGI/coverage code is modified.

## 3. Data

- Primary corpus: `datasets/hf_skill_gap_jobs.csv` (519,814 postings;
  `job_title`, `company`, `job_level`, `job_type`, `search_position`) joined to
  `datasets/hf_skill_gap_skills.csv` by `job_link` (the ALIGN03 instrument's
  market side; posting-skill pair as in ALIGN03).
- Known provenance fact (established 2026-10-11, `reports/SENS01_FOLLOWUP.md`
  §A2): this corpus is a strict subset of the Kaggle 1.3M LinkedIn corpus.
  ALIGN05 makes no cross-corpus independence claims.
- No new data acquisition. No external model calls at run time; the O*NET-SOC
  mapping is a local rule set (§4).

## 4. Job-family classifier (primary: external standard)

**Primary standard: O\*NET-SOC detailed occupations** (US Department of Labor
occupational classification framework). *License record:* O*NET-SOC content is in the
**public domain** (US Government work; O*NET center, `onetcenter.org`). The
exact framework release (e.g., O*NET-SOC 2019) and source URL are recorded in
`metrics.json` at run time.

**Mapping mechanism:** a transparent, versioned keyword rule set
(`experiments/align05_title_rules_v1.json`) mapping `job_title` strings to
O\*NET-SOC **detailed** codes via ordered, documented patterns (case-folded
regex; negations first; first-match-wins; explicit `unmatched`/default
bucket). The file is frozen at **SHA-256
`09bc778e67c884ece38edec81b57df70123ebe331f932d9441d6a12dbfcb7e36`**
(version `v1`, 2026-10-12). Rule changes require a version bump and are listed
as amendments.

**Tech definition (amended 2026-10-12; supersedes the major-group definition
below):** *tech* = titles mapping to **computing/IT occupations — O\*NET-SOC
15-12xx computer occupations, data scientists, and selected IT management**.
Exact SOC 2018 detailed codes (crosswalk to the recorded O\*NET-SOC release
re-verified at run time):

| Code | Occupation |
|---|---|
| 15-1211 | Computer Systems Analysts |
| 15-1212 | Information Security Analysts |
| 15-1213 | Computer Network Support Specialists |
| 15-1216 | Database Administrators |
| 15-1221 | Computer and Information Research Scientists |
| 15-1231 | Computer Network Architects |
| 15-1241 | Network and Computer Systems Administrators |
| 15-1244 | Network and Communications Analysts |
| 15-1251 | Computer Programmers |
| 15-1252 | Software Developers |
| 15-1253 | Software Quality Assurance Analysts and Testers |
| 15-1254 | Web Developers |
| 15-1255 | Web and Digital Interface Designers |
| 15-1256 | Computer Occupations, All Other |
| 15-2051 | Data Scientists |
| 11-3021 | Computer and Information Systems Managers |

*non-tech* = every other mapped code or default; *unmatched* = no rule fires.
Unmatched postings are **excluded from the tech-only stratum** (they cannot be
asserted tech) and **kept in the full-corpus stratum**; the unmatched share is
reported.

**Superseded definition (kept for the record, demoted to secondary robustness
mapping):** the broad O\*NET-SOC major-group definition — *tech* = major groups
**15 (Computer and Mathematical), 17 (Engineering and Architecture), 19
(Life, Physical, and Social Science)** — is run as a *secondary robustness
mapping only* (same pipeline, reported alongside, never the headline). The
broad definition inflates the tech stratum with non-computing engineering and
science roles, which dilutes the very composition effect ALIGN05 tests.

**Secondary robustness mapping:** the dataset's own nearest-to-category field,
`search_position` (the search query that surfaced the posting). It is not an
occupational category — this is recorded as a measurement caveat, not hidden —
and is used only to cross-check the primary stratification (Spearman
correlation of category deficit vectors under the two mappings). The
`job_level`/`job_type` fields play no role.

## 5. Validation gate (blocking — ALIGN05 may not run before this passes)

1. *(amended 2026-10-12 — stratified design; supersedes simple random
   sampling)* Draw a **stratified sample of 200 distinct titles**: 100 from the
   rule set's predicted-tech stratum and 100 from predicted-non-tech (frame:
   264,516 distinct normalized titles in `datasets/hf_skill_gap_jobs.csv`;
   N_tech = 9,237 / N_nontech = 255,279 under frozen rules v1; SRS without
   replacement per stratum, seed 42, deterministic sorted frame order).
   Saved as **`labelling/align05_titles_200.csv`** (moved from
   `datasets/align05_validation/` to the unified labelling package; columns:
   `sample_id, stratum, sampling_weight, job_title, rule_matched,
   predicted_soc, predicted_tech, author_label` — prediction columns filled
   from frozen rules v1; `author_label` left blank). **Sampling weight per
   row:** `w_h = N_h / n_h` (92.37 for predicted-tech, 2,552.79 for
   predicted-non-tech), making design-weighted precision *and* recall
   estimable from the labelled sample (the SRS design could not identify
   recall, since true tech outside the predicted-tech stratum was never
   sampled).
2. The author hand-labels all 200 rows (`author_label ∈ {tech, non-tech}`,
   judged per §4's occupational definition: does the *title* denote a
   computing/IT role in the SOC list above).
3. Report **precision, recall, F1 for the tech class** (author label as gold)
   with 95% CIs, plus the confusion matrix and every disagreement row.
   *Estimators (fixed now):* precision = design-weighted TP / design-weighted
   predicted-positive = plain mean over the predicted-tech stratum (SRS
   within stratum); recall via the two-stratum design-weighted estimator
   `recall = (w_T·TP̂_T) / (w_T·TP̂_T + w_N·FP̂_N)` where `TP̂_T` = # labelled
   tech in the predicted-tech stratum and `FP̂_N` = # labelled tech in the
   predicted-non-tech stratum (each × its weight); CIs by stratified
   bootstrap over the 200 labelled titles (B = 1,000, seed 42). Wilson CIs
   retained for the stratum-conditional precision as a cross-check.
4. **Pass criterion (unchanged):** design-weighted tech-class precision ≥
   0.90 **and** recall ≥ 0.90. On failure: revise the rule set (version bump,
   amendment note listing every changed rule), re-validate on a **fresh**
   stratified 200-title sample; at most two revisions, then the author
   decides (waive with disclosure or defer ALIGN05).
5. A waived gate is recorded in `metrics.json` (`validation_waived: true`)
   with the author's dated instruction quoted.

## 6. Analysis (fixed after the gate passes)

Strata: **full corpus** (all postings, as ALIGN03) and **tech-only** (§4).
Identical taxonomy, academic covering set (P = 500), τ = 0.5 baseline,
MiniLM-L6-v2 embeddings cached from ALIGN03/04 (no re-embedding).

**Reporting (replaces the relative-to-median labels):**

1. Per category × stratum: demand share (pp), lexical coverage, semantic
   coverage @ τ=0.5, **deficit in pp with 95% posting-bootstrap CIs**
   (B = 1000, seed 42, percentile method as ALIGN03).
2. **Effect size:** tech-only minus full-corpus deficit per category, with a
   paired posting-bootstrap CI (resample postings once per replicate, compute
   both strata's deficits on the same resample, take the difference).
3. **Headline framing (binding):** full-corpus deficits remain the headline
   (they are the registered ALIGN03 result). **Tech-only deficits are larger
   by construction** — conditioning on technical postings raises technical
   demand shares — and are reported as a composition-robustness check of the
   *ordering* (Spearman ρ between category deficit vectors, both match types),
   never as an enlarged headline gap.
4. If the manuscript retains Critical/Moderate/Mild labels anywhere, their
   anchoring rule is fixed here: *Critical* = deficit CI lower bound > 2× the
   full-corpus median category deficit; *Moderate* = deficit point estimate ≥
   that median; *Mild* = below. Labels computed on the full-corpus stratum
   only; tech-only stratum never labelled.
5. Unmatched-title share, rule-file hash, taxonomy-intersection check output
   (§2.2), O*NET-SOC release/URL, sample sizes per stratum → `metrics.json`.

## 7. Registration, seed, artifacts

- **Registered in `results/registry.json` before execution** (entry
  `ALIGN05_jobfamily_deficit`, `run_mode` local, `seed` 42, dependencies
  ALIGN03 + this prereg; status flips to COMPLETED only with artifacts on
  disk). Tests and `experiments/verify.py` treat an unregistered ALIGN05 run
  as failure.
- Seed 42 for: the validation sample draw and every posting bootstrap.
- Artifacts: `results/ALIGN05_jobfamily_deficit/{metrics.json,
  table_domain_gap_by_stratum.csv, table_effect_sizes_tech_vs_full.csv,
  figure optionally}`; verification extension in `experiments/verify.py`;
  manuscript edit limited to the domain-gap subsection + limitations.

## 8. Explicit non-goals

No re-tuning of the taxonomy, covering set, τ, or embedding model. No
per-cell significance testing (single pre-registered contrast per category).
No claims of corpus independence (§3). No placement/outcome data involved.

## 9. Amendments (dated blocks; appended, never silent)

### A1 — 2026-10-12 (author instruction; pre-run, sampling only)

1. **Primary tech definition narrowed** from broad major groups 15/17/19 to
   *computing/IT occupations*: O\*NET-SOC 15-12xx computer occupations + data
   scientists (15-2051) + IT management (11-3021); exact SOC 2018 detailed
   codes recorded in §4. The broad 15/17/19 definition is demoted to a
   *secondary robustness mapping* (same pipeline; never headline).
2. **Rule set frozen:** `experiments/align05_title_rules_v1.json` v1,
   SHA-256 `09bc778e67c884ece38edec81b57df70123ebe331f932d9441d6a12dbfcb7e36`
   (negations first — sales/marketing/recruiter/product-project-program
   management force non-tech; 18 ordered rules; default non-tech). Written to
   *enable* the stratified sampling; it is the candidate classifier whose
   precision/recall the §5 gate must still establish. Classification stats on
   the frame (title-level): predicted-tech 9,237 of 264,516 distinct titles
   (3.5%).
3. **Validation sample stratified** (replaces SRS): 100 predicted-tech +
   100 predicted-non-tech distinct titles, seed 42, weights
   `w_h = N_h/n_h` = 92.37 / 2,552.79, design-weighted precision *and*
   recall estimators with stratified-bootstrap CIs fixed in §5.3. Gate
   threshold (≥ 0.90 both) and ≤ 2 revision rule unchanged.
4. **Sample generated (sampling only; no ALIGN05 run, no deficit computed):**
   `labelling/align05_titles_200.csv` (200 rows; `author_label` blank;
   builder `experiments/build_align05_validation_sample.py`). Path changed
   from `datasets/align05_validation/` to the unified `labelling/` package
   (author instruction, same date).
5. §2 firewall unchanged: title-only input; skills/taxonomy never enter the
   classifier; the taxonomy-intersection verification step (§2.2) remains
   binding at run time (rule *patterns* are occupational-title terms, not
   taxonomy skills; the check is still executed and recorded).
