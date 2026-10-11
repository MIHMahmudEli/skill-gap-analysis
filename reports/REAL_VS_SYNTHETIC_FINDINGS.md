# Real vs. Synthetic Dataset Audit — Findings and Claim Inventory

Date: 2026-10-12 · Branch: `q1-revision` · Artifact: `datasets/REAL_VS_SYNTHETIC.csv`
(generator: `audit/real_vs_synthetic.py`). **No claims were edited in this step** — this
report lists every claim that must change, with a proposed action, for author approval.

## 1. Headline finding

Of the 15 manifest datasets (14 audit rows; the HF jobs+skills pair is one linked unit):

- **REAL (web-scraped): 3 units — all one scrape family.** LinkedIn 2024 (1,348,454),
  HF Skill Gap pair (519,814 nested inside LinkedIn), academic reference (1,167, from the
  same scrape). Organic evidence: 584,544 distinct LinkedIn titles with a realistic long
  tail, messy casing/typos.
- **UNVERIFIED provenance: 1 unit.** USA Job Market Skills — 316,279 rows are *aggregate*
  (title × skill keyword × count) triples over only 6,328 titles; the underlying scrape
  source is unstated and unverifiable.
- **SYNTHETIC: 10 units, 457,989 rows** — every student/placement/graduate benchmark
  (college 10,000; global placement 10,000; career success 50,000; international graduates
  300,000; career change 38,444; NGESS 7,200; fresher 5,000; = 420,644 student rows) plus
  the AI market series (10,345), the AI salary file (15,000), and India Skills (12,000,
  whose own local README states: "12,000 **synthetic** professional profiles… Every value
  in this dataset is **generated, not collected**").

Generator evidence (per-file detail in the CSV, now backed by the executable checker
suite `datasets/synthetic_checks.py` → `datasets/synthetic_checks_output.json`):
uniform-consistent draws on *many* low-cardinality categoricals (ratios 1.00–1.07 —
not all: e.g. SCS `Company_Tier` and NGESS `Gender`/`Religion` reject uniformity),
coin-flip binary columns, balanced pseudo-longitudinal years (7 years × ~1,470),
sequential IDs (`AI00001`, `IN-PROF-######`, `ST######`, `NGR######`), 16 generic
company names over 15,000 rows, missing-as-equal-class blanking in the career-change
file, and fabricated name pools. **Corrections (2026-10-12, after making the checks
executable):** the earlier informal note of a "1:1 mapping between `experience_level`
and `remote_type` (99.5% of rows)" is **refuted** (Cramér's V = 0.015, independent);
"100 College_IDs × 100 students" is **refuted** (36 IDs, 75–133 students each); the
India file's categories are **not** uniform (calibrated, consistent with its declared
provenance); and fresher `degree`/`age` are not uniform draws. The inferred
classification therefore rests on the surviving families only, and NGESS is marked
**low confidence** (sequential ID + template schema only).

**Paper treatment today:** only India Skills is labelled synthetic anywhere (Table I).
Everywhere else the paper treats these as real postings, real graduate cohorts, or a
"longitudinal" series.

## 2. Claims that must change (applied 2026-10-12 — author OK'd the list; see §6 addendum)

### A. RQ1 trends — computed on a synthetic generator → **remove or demote to "generator behaviour"**

| Location | Sentence / element | Proposed action |
|---|---|---|
| `main.tex:333` | "Longitudinal tracking across 10,345 AI and data science postings from 2020 through 2026 … Python appeared in 47.5\% to 52.2\% of postings across years …" | **Remove.** These percentages are properties of a uniform random generator (skills ~50% by construction); they are not market evidence. |
| `main.tex:583,586` | Fig. 6b "AI skill demand trajectories, 2020--2026 (TRENDS01)"; "(b) Longitudinal share of AI/data-science postings requiring core technologies" | **Drop panel (b)** (keep (a), real 1.35M geography), or relabel "synthetic benchmark series — not market data". |
| `main.tex:81` | RQ1: "…how have core technical skills evolved from 2020 through 2026?" | **Re-scope** to topography on real postings; the time-evolution half has no real data source. |
| `main.tex:154` | "…including a multi-year AI job market series (2020--2026)…" | **Relabel**: "a synthetic AI job-market series (2020–2026, generated benchmark)". |
| `main.tex:181` (Table I) | "Longitudinal AI/data science job postings" | **Relabel**: "Synthetic AI/data-science job series (generated benchmark)". |
| `main.tex:178` (Table I) | AI Job Market Trends 15,000 — "Global AI job market and salary distribution", listed Tier 1 | **Relabel synthetic + fix Tier** (it is not postings evidence). |
| `main.tex:90` | Contribution: "…combining online job postings … covering 2020 through 2026" | **Reword** to drop the implied real longitudinal span. |
| `README.md` | RQ1/trend descriptions of TRENDS01 | Same relabel/remove as above. |

### B. Tier framing prose — unverified + synthetic sources presented as evidence

| Location | Sentence / element | Proposed action |
|---|---|---|
| `main.tex:158` | Tier 1: "…USA Job Market dataset (316K records)… direct observations of employer skill specifications." | **Reword**: USA file is aggregated title×skill counts of unverifiable provenance; no posting-level observation. |
| `main.tex:159` | Tier 2: "These tabular records provide academic, behavioral, and placement indicators used for statistical testing…" | **Add**: "all seven Tier 2 files are synthetic benchmarks (datasets/REAL_VS_SYNTHETIC.csv)". |
| `main.tex:175–177, 182–185` (Table I) | International Graduates "alumni employment outcomes"; College "placement classification benchmark"; Global "multi-national university placement benchmark"; NGESS "National graduate employment survey cohort"; fresher "Entry-level engineering recruitment outcomes"; career change "transition records" | **Mark each "synthetic"** in the description column (only India, L180, is marked today). |

### C. Placement/statistical claims computed on synthetic data → **relabel as benchmark illustration; verdicts demoted**

| Location | Claim | Proposed action |
|---|---|---|
| `main.tex:483,494,511,528,532,555` | STAT01 descriptive stats, χ², logistic ORs (Communication OR 6.55, CGPA 6.28, IQ 5.16, projects 3.20) on the 10,000-row college benchmark | **Relabel throughout**: "on a synthetic placement benchmark with a near-deterministic label rule". |
| `main.tex:607,622` | "H4 (signaling hierarchy) is supported: …" / Table: "Supported (STAT01)" | **Demote**: "supported on the synthetic benchmark (illustrative)". |
| `main.tex:607,623` | "H5 … not supported: placement rates are statistically similar across the five countries … (PLAC01)" | **Demote**: PLAC01 country cells are uniform synthetic draws (rates 60–63% by construction); the hypothesis is untested on real data. |
| `main.tex:624` | "H6 … not supported (STAT01 …)" | **Demote** same as H4. |
| `main.tex:565,94` | External validation: "tested on the Student Career Success dataset (N=50,000)… ROC-AUC = 0.768"; contribution "test generalization on an external 50,000-student cohort" | **Reword**: both train and external cohorts are synthetic; "independent external validation" overstates. |
| `main.tex:590,595,607,657` | INTL01: internship → +15.34 pp employment (57.6% vs 42.3%) on 300,000 international graduates | **Relabel**: synthetic cohort; keep only as benchmark illustration or remove from Recommendations. |
| `main.tex:663` | "…regional variation in placement rates…" (PLAC01) | **Relabel/drop** (synthetic country cells). |

### D. Corpus-level sentences — fixed by the pending abstract replacement (P2-3) + Table I restructure

| Location | Sentence | Proposed action |
|---|---|---|
| `main.tex:54` | Abstract: "…2.12M unique records… collected from LinkedIn, HuggingFace, and public benchmark repositories spanning 2020 through 2026… independent external validation" | Covered by the draft abstract replacement in `reports/Q1_REVISION_PLAN.md` (updated in step 3 of this batch). |
| `main.tex:707` | Conclusion: "Across 15 open datasets (2.12M unique records) spanning 2020 through 2026…" | **Reword** with unit-typed counts (step 3) and drop the real-sounding time span. Note: the conclusion's existing phrase "synthetic threshold rules" refers to decision boundaries, not data — keep but avoid confusion with actual synthetic data. |
| `README.md:11–12` | "3,163,517 raw rows … de-duplicate to 2,123,889 unique records" | **Extend** with the unit-type breakdown (step 3) and synthetic labels. |

### E. What survives untouched

All headline gap results — SGI 52% → 32%, SENS01 ranges, ALIGN01–04, VALID01 (κ=0.737),
CURR01, GEO01 geography (1.35M real postings), RQ1 **topography** (`main.tex:324`, real
HF skill tokens: 148,765 communication postings etc.) — rest **entirely on real data**.
The synthetic exposure is: the RQ1 trends half, all of Tier 2 placement/statistics,
PLAC01 country cells, and INTL01.

## 3. Recommended overall framing (for author decision)

1. **RQ1:** keep topography (real), remove the trends half or re-run it later on a real
   longitudinal source (e.g., USAJOBS feed — `reports/INDEPENDENT_SOURCES.md` B1).
2. **Tier 2:** present as a "synthetic benchmark audit" of *methods* (decision-boundary
   masking, domain-shift degradation) — not as findings about graduates. H4/H5/H6 verdict
   table relabelled accordingly.
3. **USA 316K:** excluded from evidence statements; retained as inventory with
   unverifiable-provenance label.
4. Abstract/conclusion get the unit-typed corpus description (step 3) plus one explicit
   synthetic-data disclosure sentence.

## 6. Execution addendum (2026-10-12, batch-2 step 2)

Applied under the author's "APPLY the synthetic removal/demotion list" ruling:

1. **Declared vs inferred.** `datasets/REAL_VS_SYNTHETIC.csv` gained `synthetic_basis`
   (`declared (source states it)` / `inferred (generator signatures)` / `n/a`) and
   `signature_checks` columns; classifications now read `SYNTHETIC (inferred)`,
   `SYNTHETIC (declared by source)`, `SYNTHETIC (inferred; low confidence)` for NGESS.
   No certainty is asserted for the inferred group.
2. **Executable checks.** `datasets/synthetic_checks.py` implements the five
   generator-signature families (categorical uniformity chi-square, binary balance,
   cross-field Cramér's-V coupling, ID-sequence templating, missing-as-equal-class);
   outputs saved to `datasets/synthetic_checks_output.json` and cited in the claim
   ledger (row M10) and in §III-A/Table I of `paper/main.tex`.
   `tests/test_synthetic_checks.py` (10 tests) guards the checker logic and the
   artifact. Four informal claims above were refuted/corrected by these checks.
3. **H5 = untested.** Verdict sentence and hypotheses-table row now read
   "untested / Untested (PLAC01 benchmark apparently synthetic; no verdict)";
   `verify_claims` C158 repointed to the new strings.
4. **RQ1 trends removed.** Deleted: the longitudinal paragraph (old `main.tex:342`),
   Fig. 6b panel (`\FigTrends` subfigure + caption + macro), the RQ1 "and Trends"
   title halves (bullet + subsection), the "Adaptive Curriculum Guidelines"
   trend-evidence attribution, and every "spanning 2020 through 2026" phrasing
   (abstract, contribution, §III-A, conclusion). RQ1 is topography only.
5. **TRENDS01 marked not-used.** Registry entry: `status: VERIFIED`,
   `manuscript_use: not_used_in_manuscript` + reason, history event appended;
   `tests/test_reproducibility.py` gained a `NOT_USED_IN_MANUSCRIPT` set requiring
   a recorded reason; README + `paper/tables/tab_experiments.tex` updated;
   ledger M07 rewritten; `verify_claims` C04/C140–C143 relabelled
   "(artifact only; removed from manuscript 2026-10-12)".
6. **Declared/inferred wording in main.tex.** §III-A accounting, contribution 1,
   Tier-2 bullet, Table I caption + section headers + rows now say
   "apparently synthetic" with the declared/inferred split (445,989 inferred +
   12,000 declared) spelled out; "Eight of the 15 sources" → "Seven".
7. **Deferred to step 4 (Phase 4 split):** H4/H6 verdict reframing, INTL01/STAT01/STAT02
   sentences, PLAC01 country cells, and the Table I synthetic rows → appendix
   (they move to `paper_placement/` under the benchmark-audit reframing, rulings D2/D3).
