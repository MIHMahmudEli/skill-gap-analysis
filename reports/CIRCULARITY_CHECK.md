# Circularity check — reference profile vs. market corpus

Author instruction 2026-10-12 (batch 3, step 1). **Descriptive audit, not a registered
experiment**: nothing here feeds a manuscript number, nothing was written to `results/`,
and the registry is untouched. Purpose: rule the "same postings on both sides" objection
in or out before deciding whether a leave-out robustness experiment is worth registering.

Inputs: `datasets/hf_job_skill_set.csv` (reference profile, 1,167 postings) and the
primary market corpus `datasets/hf_skill_gap_jobs.csv` +
`datasets/hf_skill_gap_skills.csv` (519,814 postings, all with `got_summary` ∧ `got_ner`).
Extraction for the vocabulary counts is byte-for-byte the ALIGN01 rule
(strip brackets, drop apostrophes, split on comma, lower-case).

## (a) Do any of the 1,167 profile postings appear in the market corpus?

The profile carries no `job_link`, so the join falls back to title matching, then
requires the **skill sets to corroborate** the match. Title-only matching is not
evidence: generic titles such as "Human Resources Manager" occur 287 times in the
market corpus by construction.

| Match rule | Hits |
|---|---|
| Normalized exact title | 575 / 1,167 (49.3%) |
| Title **and** skill-set Jaccard ≥ 0.5 | **1 / 1,167** |
| Title and skill-set Jaccard ≥ 0.9 | **0 / 1,167** |

The one ≥0.5 hit is `retail sales manager` (11 profile skills vs 16 market skills,
9 shared). Every shared skill is generic — *leadership, problem solving, interpersonal
skills, flexibility, motivation, sales management, sales strategy execution, action plan
development, performance analysis*. Jaccard distribution over the 575 title matches:
**0 at ≥0.9**, 1 at 0.5–0.9, 410 at 0.1–0.5, 164 at <0.1.

**Verdict: no posting-level overlap.** The reference profile is a separate, curated set
of five occupational categories with employer-derived skill sets; the market corpus is a
2024 LinkedIn scrape. They share vocabulary only in the way any two English job corpora
do.

## (b) How much of the market top-K comes from profile postings?

Taking the **loosest possible bound** — crediting not the 1 corroborated posting but all
41 market postings sharing its title — so the true figure is an upper bound:

| Quantity | Value |
|---|---|
| Market skill tokens (top-100 occurrences) | 2,231,621 |
| … contributed by the 41 title-matched postings | 301 (**0.0135%**) |
| Market skill tokens (top-500 occurrences) | 3,833,198 |
| … contributed by the 41 title-matched postings | 480 (**0.0125%**) |
| All market tokens | 10,794,213 |
| … from the 41 title-matched postings | 771 (0.0071%) |

Using the strict corroborated set (1 posting) the contribution is 16 tokens of
10,794,213 = **0.00015%**. Either way the market top-100/top-500 is not materially
sourced from profile postings; the 9/100 top-100 skills the loose bound "touches" are
generic skills that would rank in the top-100 from the other 519,773 postings alone.

## (c) How much of the profile vocabulary is in the market top-K?

| | |
|---|---|
| Profile skill vocabulary | 20,970 tokens → **5,047 unique** |
| … in market top-100 | 71 (**1.41%** of profile vocab) |
| … in market top-500 | 281 (**5.57%**) |
| … in market top-1000 | 452 (**8.96%**) |
| … appearing anywhere in the 1.44M-skill market vocabulary | 3,963 (78.52%) |

This asymmetry *is* the measured phenomenon: the profile's vocabulary is 78.5% present in
the market at large but only 1.41% inside its head — the lexical divergence ALIGN01/02
quantify. It is not an artefact of shared postings.

## Proposed leave-out design (NOT run; needs your go-ahead to register)

Overlap is ~0, so the experiment is a **falsification test whose expected result is
"no change"** — that is exactly why it is worth registering, but it is also why it can
wait. Proposed protocol, reusing the SENS01 grid and the existing pipeline:

1. **Exclusion set.** The 575 title-matched market postings (the loose bound), removed
   from the 519,814-posting primary corpus → 519,239 postings. A stricter variant
   removes only the 1 corroborated posting; both are reported.
2. **Recompute** the lexical SGI and the semantic SGI at τ ∈ {0.4, 0.5, 0.6, 0.7} with
   the same tokenizer, `all-MiniLM-L6-v2`, seed 42, 1,000 bootstrap resamples — i.e. the
   SENS01 grid on the reduced corpus.
3. **Report** ΔSGI = SGI_leaveout − SGI_published at each τ, with the bootstrap CI of the
   difference. Pre-specified interpretation: |Δ| ≤ 1.0 pp → "overlap does not drive the
   result"; larger → the headline is partly self-referential and must be restated.
4. **Cost:** one SENS01-class run (~3 min CPU, ~1 min GPU). No new labels, no downloads.

**Draft limitation wording** (to be added only if the experiment is registered and run):

> *Potential corpus overlap.* The employer-derived reference profile and the market
> corpus are drawn from different sources, and a posting-level join finds no shared
> postings: of the 1,167 profile postings, none matches a market posting on both title
> and skill set at Jaccard ≥ 0.9 (one generic-title collision at ≥ 0.5), and even the
> loosest title-only bound attributes ≤ 0.014% of the market top-100 skill occurrences
> to profile postings. The lexical and semantic gap indices are therefore not driven by
> the same postings appearing on both sides of the comparison.

If the leave-out experiment is later run, this paragraph gains its ΔSGI sentence and the
numbers move into Table I's provenance block.
