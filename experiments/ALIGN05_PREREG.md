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
   *(column layout amended 2026-10-12, A2: labelling CSV blinded to
   `sample_id, job_title, author_label` only, row order shuffled seed 42;
   design columns sealed in `experiments/align05_titles_200_key.csv`.)*
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

### A2 — 2026-10-12 (author instruction; pre-run, labelling-package hygiene)

1. **The author-facing validation CSV is blinded.**
   `labelling/align05_titles_200.csv` now carries exactly three columns —
   `sample_id, job_title, author_label` — with `author_label` blank. All
   prediction/design columns (`stratum, sampling_weight, rule_matched,
   predicted_soc, predicted_tech`) moved to a sealed key file,
   `experiments/align05_titles_200_key.csv`, which the author must not open
   until labelling is finished. This supersedes the §5.1 column list.
2. **Row order randomized** with a fresh seed-42 draw, and `sample_id`s
   assigned *in the shuffled order* (A5T001…A5T200), so neither column set
   nor ID ranges reveal stratum membership.
3. **Sampling design unchanged:** same 100+100 SRS per stratum, same frame,
   same weights (92.37 / 2,552.79), same frozen rule set v1 (SHA-256
   `09bc778e…7e36`), same estimators, same gate (≥ 0.90 precision AND
   recall), same ≤ 2 revision rule. Only the presentation of the sample to
   the rater changed; `experiments/build_align05_validation_sample.py`
   regenerates both files deterministically (both seeded with 42).
4. `labelling/score_labels.py` joins the blinded CSV to the key on
   `sample_id` at scoring time; nothing about the estimators changed.


### A3 - 2026-10-12 (author instruction; pre-run; RETIRES the v1 sample and key)

**Trigger.** The v1 sealed key, `experiments/align05_titles_200_key.csv`, was
committed to a **public** GitHub repository (`MIHMahmudEli/skill-gap-analysis`,
`main`) before a single `author_label` existed. Publishing the key voids the
blinded status of the validation gate: any labelling done afterwards could have
been shaped by it. The author elected option 2 (re-draw) over waiving.

**Verified state at retirement (no contamination).**

- `labelling/align05_titles_200.csv` `author_label` was, and remains, **fully
  blank** — checked in the working tree and at the pushed commit `0aa1ac2`
  (200/200 blank).
- **No scoring** ever ran against the v1 key: no ALIGN05 `metrics.json` or result
  artifact exists anywhere in history.
- **No rule revision** was informed by it: `align05_title_rules_v1.json` was
  touched in exactly one commit (`9a6f030`, sample creation) and is byte-identical
  since, SHA-256
  `9F0410507C23313C99517CEC9D40A1CC0697CD29192A89357F0E321234F1429D`.
  The builder now hard-fails if this hash changes.
- **History is untouched**: no force-push, no rebase, no filter-branch. The old
  key was moved out of the active path by an ordinary commit to
  `archive/align05_titles_200_key_RETIRED.csv` with a dated note. It remains
  reachable in public history and is retained only as a record of the leak; it is
  **not** a valid key and must never be used to score ALIGN05.

**Replacement sample (v2).** Same frame (distinct normalized titles over the
519,814-posting primary corpus), same two strata (predicted-tech /
predicted-nontech), same **frozen** v1 rule set (hash verified above, unchanged),
same 100-per-stratum equal allocation, same weights (92.37 / 2,552.79), same
blinded 3-column format (`sample_id, job_title, author_label`, `author_label`
blank, rows shuffled, ids assigned in shuffled order).

**Changes, and only these:**

1. **Seed.** `SEED_V2 = 20261013` replaces 42 for both the stratum draws and the
   shuffle. Seed 42 is burned: it produced the retired sample and is not reused
   for a draw the author will label against.
2. **ID prefix.** `A5U001`-`A5U200` replaces `A5T001`-`A5T200`, so the two
   samples cannot be confused and no retired id can be re-used accidentally.
3. **Key location.** The v2 key is written **outside the repository** to
   `../sealed_keys/align05_titles_200_key.csv` (mode 0600 where honoured), and
   `.gitignore` now rejects `*_key*.csv`, `*key*.csv.bak`, `sealed/`, `sealed*/`
   and `**/sealed_keys/`. The builder refuses to write a key inside the repo.
4. **Key access.** `labelling/score_labels.py` and `scripts/run_after_labels.sh`
   read the key from `ALIGN05_KEY` (or an explicit argument); both fail with an
   explanatory message if it is absent rather than falling back to an in-repo
   path. The key is never printed or opened by either.
5. **Guards.** `tests/test_no_tracked_secrets.py` and the pre-push hook
   `scripts/pre-push` fail if any *tracked* file matches the sealed-key patterns,
   with a single explicit allowlist entry for the retired archive copy (already
   public, retained for the record).

**Unchanged (reaffirmed).** The estimators, the gate (design-weighted tech
precision >= 0.90 **and** recall >= 0.90), the <= 2 revision rule, the analysis
in 56, and the non-goals in 58 are all unchanged. This amendment alters only
*which* 200 titles are labelled and *where the key lives*. The 200-title sample
drawn under seed 42 is retired and may not be re-used for any purpose.

### A4 - 2026-10-12 (agent correction; pre-run; corrects the record, changes nothing)

**What A2 said.** A2 cites the frozen rule set as `SHA-256 09bc778e...7e36`.
Batch 3's step-1 note and this file's A3 instead quote
`9F0410507C23313C99517CEC9D40A1CC0697CD29192A89357F0E321234F1429D`, and the
batch-3 report flagged the mismatch as an unexplained discrepancy. **That flag
was wrong: A2 was correct.** A3 and the retired-key note recorded the wrong
value. No edit is made to A2 or A3 - amendments are append-only - this block
supersedes the hash cited in A3.

**The two hashes are the same file, differing only in line endings.**

| | SHA-256 | CRLF newlines | Bytes |
|---|---|---|---|
| (a) working-tree raw bytes, Windows `core.autocrlf=true` | `9F0410507C23313C99517CEC9D40A1CC0697CD29192A89357F0E321234F1429D` | 55 | 4,863 |
| (b) working-tree, LF-normalised | `09BC778E67C884ECE38EDEC81B57DF70123EBE331F932D9441D6A12DBFCB7E36` | 0 | 4,808 |
| (c) git blob at `9a6f030` (`git cat-file blob`) | `09BC778E67C884ECE38EDEC81B57DF70123EBE331F932D9441D6A12DBFCB7E36` | 0 | 4,808 |

**(b) == (c), and both equal A2's `09bc778e...7e36`.** The blob is pure LF;
`core.autocrlf=true` rewrites its 55 LF newlines to CRLF when checking out on
Windows, so hashing the bytes on disk gives `9F0410...`. A2 recorded the
canonical, machine-independent value; the batch-3 note recorded a
Windows-artifact one. The committed blob object id is
`42ac2df209a2426c45ae32b7de2e212281496fa6`.

**Correction applied.** `experiments/build_align05_validation_sample.py` now
LF-normalises before hashing and expects `09BC778E...`, so the guard passes on
Windows, Linux and macOS alike. (Its batch-3 form hashed raw bytes against the
CRLF value: correct on this laptop, guaranteed to fail on a Linux clone for a
perfectly unchanged file - the inverse of the reproducibility the guard exists
to provide.)

`.gitattributes` is added, forcing `eol=lf` on every file whose content hash is
recorded here, in `datasets/input_checksums.sha256`, or in any metrics file
(`align05_title_rules_v1.json`, `input_checksums.sha256`, plus `*.json`,
`*.sha256`, `*.yaml/toml/cfg/ini` and the source/prose types). This closes the
gap from the other side: the working tree becomes byte-identical to the blob on
every platform. `tests/test_hash_eol_integrity.py` (7 tests) pins the invariant.

**Scope of the same bug elsewhere - audited 2026-10-12.** Every recorded
SHA-256 in the repository was re-verified:

- `datasets/input_checksums.sha256`, all 9 canonical inputs: **match, no
  exposure**. Their targets are *untracked* (gitignored), so git never
  normalises their EOLs and the recorded hash is of stable raw bytes. The test
  asserts they stay untracked (or gain `eol=lf`) so this cannot regress.
  Four of the nine are CRLF-terminated files on disk (hf_skill_gap_skills,
  hf_job_skill_set, student_career_success, global_placement, plus
  international_graduates) - that is their content as shipped, not a
  conversion, and the hashes were computed over exactly those bytes.
- `results/registry.json` and every `results/*/metrics.json`: **zero** recorded
  64-hex hashes. Nothing to normalise.
- `tests/test_common.py`: a hash of a synthetic `b"hello"` fixture written with
  `write_bytes`; not EOL-sensitive.
- `requirements.txt` `--require-hashes`: hashes of PyPI release artifacts,
  fetched over the network, never subject to this repo's EOL policy.

So `align05_title_rules_v1.json` was the **only** recorded hash exposed to EOL
normalisation, and it is now pinned.

**Nothing else changes.** Sampling design, strata, weights, seed `20261013`,
the `A5U` prefix, the sealed-key location and access rules, the estimators and
the gate are all untouched. The v1 rule set's *content* is byte-identical;
only the encoding of its newlines in the working tree, and the form of the
hash check, changed. This amendment changes no label, no number and no
registered decision.