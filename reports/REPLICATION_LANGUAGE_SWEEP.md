# Replication / Independence Language Sweep

Date: 2026-10-12 · Branch: `q1-revision` · Patterns: `replicat`, `independent`,
`confirm`, `cross-corpus`, `corroborat` (+ `both corpora`, `two corpora`) over
`paper/main.tex`, `README.md`, `reports/*.md`. **Nothing was edited** — rewrites
apply only after author OK. Line numbers refer to the current tree.

## Part A — main.tex sentences that still imply independent evidence (rewrite proposals)

**A1 (the H1 domain-deficit replication sentence — flagged by the author).**
`main.tex:616` — "H1 (constructive alignment) is supported **in both corpora**:
technical categories carry the only nonzero deficits while soft skills are fully
covered."
→ "H1 (constructive alignment) is supported on the primary corpus and **persists
on the nested LinkedIn superset (one scrape family)**: technical categories
carry the only nonzero deficits while soft skills are fully covered."

**A2 (H3 verdict — independence + leftover pre-reframing ordering claim).**
`main.tex:616` — "H3 (instrument robustness) is supported by strictly positive
SGI with **the invariant lexical-above-semantic ordering on LinkedIn**, and
more strongly still by the matched-profile sensitivity showing identical SGI
**on both corpora** at equal academic covering-set size."
→ "H3 (instrument robustness) is supported by strictly positive SGI and
magnitude persistence on the nested LinkedIn superset (the lexical-above-semantic
ordering is retained only as a sanity check, since exact match ⇒ cosine 1.0 ≥ τ
guarantees it — `reports/H2H3_BY_CONSTRUCTION.md`), and more strongly still by
the matched-profile sensitivity showing identical SGI **on both nested samples
of the scrape family** at equal academic covering-set size."
*Note:* this verdict clause was missed by the step-3 H3 reframing (which rewrote
the hypothesis statements); A2 fixes both defects at once.

**A3 (H2 "three times over").**
`main.tex:616` — "H2 (terminology divergence) is supported **three times over**—
ALIGN01/02 ($0.52$ vs.\ $0.32$), ALIGN04 ($0.37$ vs.\ $0.14$), and CURR01 …"
→ "H2 (terminology divergence) is supported by the primary ALIGN01/02 contrast
($0.52$ vs.\ $0.32$), **echoed within the same scrape family** by the nested
ALIGN04 check ($0.37$ vs.\ $0.14$), and **independently attested on curricular
vocabulary** by CURR01 (lexical $0$--$2.4\%$ vs.\ semantic $30.4\%$)."

**A4 (CURR01 "independently replicating H2").**
`main.tex:436` — "Exact lexical coverage is near zero for every Area
(0--2.4\%), **independently replicating H2 a third time** on a third vocabulary."
→ "…, **consistent with H2 on a third, genuinely independent vocabulary**
(curricular guidelines, not postings)."
(CS2023 is a real independent source — the word "independently" survives, but
"replicating" overstates: CURR01 measures profile-vs-curricula coverage, not
the lexical-vs-semantic contrast H2 tests.)

**A5 (INTL01 "external descriptive replication").**
`main.tex:143` — "…with INTL01 as an **external descriptive replication** on
international graduates …"
→ "…with INTL01 as an **external descriptive check on a separate (synthetic)
international-graduate benchmark** …"

**A6 (abstract).**
`main.tex:54` — "…accompanied by decision-boundary diagnostics and **independent
external validation**."
→ covered by the P2-3b draft (`reports/Q1_REVISION_PLAN.md`): drop "independent";
external cohorts are synthetic benchmarks of one generative family.

**A7 (STAT02 first mention).**
`main.tex:323` — "…we train … on the College Placement benchmark ($N = 10,000$)
and evaluate it on **the independent Student Career Success cohort** …"
→ "…and evaluate it on **a held-out Student Career Success benchmark (synthetic
cohort)** …"

**A8 (STAT02 results).**
`main.tex:574` — "**To evaluate performance on an independent sample**, the
logistic regression model was tested on the Student Career Success dataset …"
→ "**To evaluate performance on a held-out synthetic benchmark**, the logistic
regression model was tested on the Student Career Success dataset …"

**A9 (limitations, matched-profile).**
`main.tex:702` — "…shows SGI levels shifting from $0.52/0.32$ ($P = 100$) to
$0.37/0.14$ ($P = 500$) **on both corpora** …"
→ "… **on both nested corpora of the scrape family** …"

**A10–A11 ("confirming" softening; within-corpus, not independence).**
`main.tex:466` — "**confirming** that vocabulary divergence accounts for a
substantial share of the raw lexical gap" → "**consistent with** vocabulary
divergence accounting for …".
`main.tex:468` — "…while **confirming** that deficit magnitudes are
corpus-conditional" → "…while **indicating** that deficit magnitudes are
corpus-conditional".

## Part B — main.tex: correct as written (keep)

| Line | Sentence (trimmed) | Why keep |
|---|---|---|
| 92 | "re-check both gap indices on a nested-superset robustness sample … (a sample-size extension, not an independent replication)" | Step-1 wording, explicit disclaimer |
| 418 | "…functions as a nested-superset robustness check … not an independent replication…" | Step-1 wording |
| 131 | "…performance on independent external cohorts" (related work) | About the *literature*, not our data |
| 376 | "validated against an independent, human-annotated gold standard" (VALID01) | SkillSpan→ESCO genuinely independent |
| 392 | "the near-chance lexical κ **independently corroborates** this" | Metric-level (different measurement), not corpus-level |
| 503, 525 | "chi-square tests **confirm**…"; "**confirming** that multicollinearity does not affect…" | Statistical-sense confirmation (relabel per synthetic-data findings, not here) |
| 537 | "contributes **independent signal**" | Regression sense |
| 701 | "**independent-rater** annotation … remains future work" | Rater sense |
| 164 | table label `tab:crosscorpus` | LaTeX label kept to avoid breakage (already noted in `PROVENANCE_AUDIT.md` §C.14); cosmetic only |

## Part C — README.md

`README.md:169–170` — "superset of the primary 519K corpus, same scrape family;
**not an independent replication**" — correct; keep. No other hits.

## Part D — reports/ with stale pre-audit independence language (propose banner or reword)

| File:line | Text (trimmed) | Proposed action |
|---|---|---|
| `reports/MISSING_WORK.md:23` | "cross-corpus replication on 1.29M LinkedIn postings…" | Reword → "nested-superset check (same scrape family)" |
| `reports/MISSING_WORK.md:50` | "✅ **Cross-corpus replication** → ALIGN04…" | Reword → "✅ Nested-superset robustness check → ALIGN04…" |
| `reports/Q1_READINESS.md:7,23,36,52` | "on 1.29M **independent** LinkedIn postings; ordering + τ-monotonicity **replicate**" | Reword (2 spots) + note that ordering is now sanity-check only (A2) |
| `reports/EXPERIMENT_REPORT.md:43,90–91` | "**Cross-corpus** SGI + domain gaps"; "ALIGN04 **replicates** both SGI variants" | Reword → "nested-superset"; "re-checks" |
| `reports/Q1_REVISION_PLAN.md:73,86–88` | "replication compares market top-100…"; `metrics.json::matched_profile_replication` | Prose → "matched-profile comparison"; **artifact key names stay** (identifiers) |
| `reports/SENS01_FOLLOWUP.md`, `reports/PROVENANCE_AUDIT.md`, `reports/H2H3_BY_CONSTRUCTION.md` | quote the old wording | **Keep** — they are the correction record |

## Apply order (after author OK)

1. A1–A5, A9–A11 in one pass (main.tex verdicts/hypotheses/limitations).
2. A6–A8 together with the approved abstract replacement (P2-3) and the step-2
   synthetic-data relabelling (they touch the same sentences).
3. Part D banners/rewords (reports only; no numbers change anywhere).
All rewrites preserve every registered number; no gate check depends on the
affected phrasings (verify_claims keys on numbers, not these words).
