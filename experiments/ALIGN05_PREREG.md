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

**Primary standard: O\*NET-SOC major groups** (US Department of Labor
occupational classification framework). *License record:* O*NET-SOC content is in the
**public domain** (US Government work; O*NET center, `onetcenter.org`). The
exact framework release (e.g., O*NET-SOC 2019) and source URL are recorded in
`metrics.json` at run time.

**Mapping mechanism:** a transparent, versioned keyword rule set
(`experiments/align05_title_rules_v1.json`) mapping `job_title` strings to
O*NET-SOC major groups via ordered, documented patterns (case-folded substring
/ regex; first-match-wins; explicit `unmatched` bucket). Every rule carries a
one-line rationale. The rule file hash (SHA-256) is recorded in
`metrics.json`; rule changes require a version bump and are listed as
amendments.

**Tech definition (pre-registered):** *tech* = titles mapping to O*NET-SOC
major groups **15 (Computer and Mathematical), 17 (Engineering and
Architecture), 19 (Life, Physical, and Social Science)**; *non-tech* = all
other mapped groups; *unmatched* = no rule fires. Unmatched postings are
**excluded from the tech-only stratum** (they cannot be asserted tech) and
**kept in the full-corpus stratum**; the unmatched share is reported.

**Secondary robustness mapping:** the dataset's own nearest-to-category field,
`search_position` (the search query that surfaced the posting). It is not an
occupational category — this is recorded as a measurement caveat, not hidden —
and is used only to cross-check the primary stratification (Spearman
correlation of category deficit vectors under the two mappings). The
`job_level`/`job_type` fields play no role.

## 5. Validation gate (blocking — ALIGN05 may not run before this passes)

1. Draw a **simple random sample of 200 postings** from the primary corpus's
   distinct titles (seed 42), saved as
   `datasets/align05_validation/title_validation_sample_200.csv`
   (columns: `sample_id, job_title, search_position, predicted_family,
   predicted_tech`; prediction columns filled from the frozen v1 rule set;
   a blank `author_label` column for hand-labelling; labelling brief alongside
   defining tech/non-tech per §4).
2. The author hand-labels all 200 rows (`author_label ∈ {tech, non-tech}`).
3. Report **precision, recall, F1 for the tech class** (author label as gold)
   with 95% Wilson CIs, plus the confusion matrix and every disagreement row.
4. **Pass criterion:** tech-class precision ≥ 0.90 **and** recall ≥ 0.90.
   On failure: revise the rule set (version bump, amendment note listing every
   changed rule), re-validate on a **fresh** 200-posting sample; at most two
   revisions, then the author decides (waive with disclosure or defer ALIGN05).
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
