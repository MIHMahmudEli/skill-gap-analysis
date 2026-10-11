# Curriculum Corpus Selection Protocol (CURR02 / Phase 1)

*Fixed before extraction or any SGI result on this corpus was computed.*
*Date frozen: 2026-10-11 · Branch: `q1-revision`*

---

## 1. Purpose

Build a small, legally reusable corpus of **course-level curriculum units**
(syllabi, course descriptions, learning outcomes) so that experiment **CURR02**
can compute the Skill Gap Index (SGI) on **real curriculum text** and compare it
to the job-derived academic reference profile used in ALIGN01/02.

CS2023 Body of Knowledge remains a **separate anchor** (CURR01). Its 2,197
topics are **not** pooled with the course set.

---

## 2. Inclusion criteria

A curriculum unit is included only if **all** of the following hold:

1. **Explicit reuse terms** at retrieval time, per item: CC BY, CC BY-SA,
   CC BY-NC-SA, CC0, or a clear institutional open-curriculum / OCW policy that
   states reuse permission in the license text.
2. **License snapshot** saved (page URL + license text excerpt) under
   `datasets/curriculum/license_snapshots/` at retrieval.
3. **Robots/ToS**: site `robots.txt` does not disallow the URL path; terms do
   not prohibit educational reuse of the page content. If terms prohibit bulk
   download or scraping, the source is **excluded** even if free to view.
4. **Unit type**: a discrete course (or OCW course page) with identifiable
   title, institution, and either syllabus / learning outcomes / course
   description text sufficient for skill extraction.
5. **Subject**: computing-related (CS, SE, AI/ML, data, systems, security,
   theory, or closely adjacent EE courses that carry CS skill content).
6. **Language**: English (to match market corpus language).

## 3. Exclusion criteria

Exclude and log (`extraction_status=excluded`) when any of:

1. No explicit reuse license (e.g. standard university catalogs: Duke, UCSB,
   Cal State, CUNY, etc.).
2. “All rights reserved” / personal-use-only / anti-scraping terms
   (e.g. **NPTEL/SWAYAM** — TOU prohibits bulk download and reserves all
   rights; **Elements of AI / University of Helsinki** — all rights reserved).
3. Mixed third-party content with no clear unit-level license statement
   (e.g. OpenLearn or CMU OLI pages whose learning outcomes are clear but whose
   embedded third-party materials lack a unit-level CC line — only the
   clearly licensed outcome/description text may be extracted; if the unit’s
   primary pedagogical text is mixed, exclude).
4. Non-CC items inside otherwise CC collections (e.g. Stanford “Introduction
   to Logic” on SEE is explicitly not CC).
5. Full-text books/textbooks used as stand-alone “programs” (wrong unit of
   analysis).

## 4. Sampling frame and stratified targets

**Unit of analysis:** one course = one curriculum unit.

**Minimum bar (hard stop):** ≥ **20 courses** from ≥ **3 institutions** and
≥ **3 regions** (regions: North America; Europe; other). If the bar is not met
after extraction, **STOP** and report; do not run CURR02 on a thin corpus.

**Stratified targets** (approximate balance; fill in order of license clarity):

| Stratum | Definition | Target share |
|---|---|---|
| Theory-heavy | Algorithms, automata/theory of computation, discrete math / mathematical foundations, programming-language theory, logic (where CC) | ~50% of courses |
| Applied | Databases, cloud/distributed systems, software engineering, data engineering, ML/AI systems, security, HCI systems, web/mobile | ~50% of courses |
| Intro level | Intro to CS/programming, intro ML, intro databases, survey courses | ~40–50% |
| Upper-level | Advanced algorithms, distributed systems, compilers, ML theory/systems, security | ~50–60% |
| Vintage modern | Material year ≥ 2019 (or latest clearly stated revision ≥ 2019) | Prefer; primary analysis |
| Vintage legacy | Material year < 2019 | Include as **labelled vintage-sensitivity group only**; report SGI with and without |

**Material year:** recorded per item (course offering year, last syllabus
revision year, or OCW publication year — whichever is most specific). If year
is unknown → treat as vintage-sensitive and flag; do not count toward the
“prefer 2019+” primary set.

**Stanford SEE note:** SEE is a fixed historical pilot (mostly late 2000s–early
2010s materials). All SEE units are tagged vintage; primary analysis reports
results **with and without pre-2019 materials**.

## 5. Region and institution diversity

Approved institutions / sources (license-verified at plan stage):

| Institution | Region | Source program | License (site / unit) |
|---|---|---|---|
| MIT | North America | OpenCourseWare | CC BY-NC-SA 4.0 |
| Stanford | North America | Engineering Everywhere (SEE) | CC BY-NC-SA 4.0 (except Logic) |
| Harvard | North America | CS50 OpenCourseWare | CC BY-NC-SA 4.0 |
| Carnegie Mellon | North America | Open Learning Initiative | CC BY-NC-SA 4.0 (site); unit-level third-party content excluded if mixed |
| TU Delft | Europe (NL) | OpenCourseWare | CC BY-NC-SA 4.0 (site-wide) |
| The Open University | Europe (UK) | OpenLearn Digital & Computing | CC (NC-SA variants); unit-level check required |

**Excluded at plan stage (logged):**

| Source | Region | Reason |
|---|---|---|
| NPTEL / SWAYAM | India | TOU: all rights reserved; prohibits scraping/bulk download |
| University of Helsinki / Elements of AI | Finland | All rights reserved; contact for licensing |
| Standard US catalogs (Duke, UCSB, etc.) | North America | No explicit CC/open-reuse terms |
| Stanford Intro to Logic (SEE) | North America | Explicitly not CC-licensed |

## 6. Pre-registration statement

This protocol, the candidate list in `MANIFEST.csv`, and the stratified targets
were **fixed before** any curriculum text was downloaded and before any SGI
value was computed on this corpus. Extraction scripts, skill parsers, and
CURR02 parameters (K, P, τ grid, seed 42) are registered after the human
precision/recall validation step required by the author.

## 6b. Backup swap rule (author-approved 2026-10-11; fixed before download)

A `backup_*` row may replace a `pending` row **only if** that pending row’s
**license check or download fails**. Swap order is the fixed order already
listed in `MANIFEST.csv` (backup rows appear after their primary peers in the
file). Every swap is logged in `datasets/curriculum/SWAP_LOG.md` with:
`timestamp, replaced_unit_id, backup_unit_id, reason, evidence_url`.

**Forbidden:** rebalancing strata, preferring modern over legacy, or swapping
any item based on extracted skill counts, SGI values, or any analysis output.

**Primary vs vintage split (author-approved):**
- **Primary analysis set** = courses with material year **≥ 2019**, verified
  from the course page/syllabus (evidence URL + excerpt logged).
- **Hard bar for primary set:** ≥ 20 courses, ≥ 3 institutions, **≤ 8 courses
  per institution**. If primary cannot reach 20, **STOP**; do not relax the bar.
- **Vintage-sensitivity group** = material year **&lt; 2019**. Reported separately;
  **not** pooled into the primary SGI.
- Region reporting uses **countries**: US, NL, UK (not “global”).
- Manuscript limitation (required): Western open-courseware sample, skewed
  toward elite institutions; not representative of world curricula.

## 7. Extraction and validation pipeline (post-approval)

1. Download only units with `extraction_status=pending` after author approval
   of this manifest.
2. Save raw HTML/text under `datasets/curriculum/raw/` (gitignored).
3. Extract skill / learning-outcome phrases → `datasets/curriculum/extracted/`
   (committed; no full course prose).
4. **Human validation (author-gated):** random sample of **100** extracted
   items labelled for precision (and a complementary sample for recall);
   CSV with rater columns; **CURR02 does not run until the author labels or
   waives**.
5. CURR02: SGI at same (K, P, τ) as ALIGN01/02; bootstrap CIs; seed 42;
   stratified by theory/applied, vintage, institution; leave-one-institution-out;
   registered in `results/registry.json`.

## 8. Known limitations (for manuscript)

- Open-courseware sample is **not** a representative sample of degree programs.
- Skewed toward well-known / elite institutions with mature OCW programs.
- Syllabus/outcome text ≠ full course content; skill extraction is approximate.
- Vintage mix (especially SEE) requires sensitivity reporting.

## 9. Amendments (dated, author-approved; CURR02 registration-time)

All amendments below were decided **after extraction but before any CURR02
computation** (no SGI value exists on this corpus), and are logged here rather
than silently editing the frozen sections.

### 9a. 2026-10-11 — Region bar waived (author decision)

The corpus reaches only **2 regions** (North America, Europe) against the §4
bar of ≥ 3. Root cause: the approved-institution list (§5) never contained a
license-eligible source outside NA/Europe — NPTEL/SWAYAM (India) and
Helsinki/MinnaLearn were license-excluded at plan stage, and Open University
(UK) 403'd at retrieval (Europe in any case). The bar was therefore
unattainable from the frozen frame; this was surfaced by the pre-CURR02 bar
check in `PRIMARY_SET.md`, not after seeing results.

**Author ruling:** waive to ≥ 2 regions. CURR02 proceeds on the 20-course
primary set. Required manuscript statement: the corpus is two-region
(US + NL) open courseware, and the absent third region is **license-blocked,
not overlooked**; region composition listed in limitations.

### 9b. 2026-10-11 — Primary-set cap rule confirmed (author decision)

The ≤ 8/institution hard bar (§6b) required trimming TU Delft's 14 modern
units to 8. Deterministic rule confirmed by the author: **first 8 rows in
MANIFEST file order** (same pre-download convention as the §6b swap order).
Resulting primary set: 20 courses (MIT 6 / TU Delft 8 / Harvard 6), strata
6 theory / 14 applied. The deviation from the ~ 50/50 stratified target is
a frame property (Harvard CS50 is entirely applied; ceiling = 8/20 theory)
and is reported as a limitation (`PRIMARY_SET.md` §7), not corrected by
post-freeze discretion.

### 9c. 2026-10-11 — Recall-sample design fixed (pre-labelling)

Recall validation sample uses **equal allocation** across
(vintage_group × drop_reason) cells over the full drop population
(N = 699; cell sizes in `extracted/extraction_summary.json::
recall_design.stratum_population_sizes`), so every drop rule receives
validation coverage. Design-weighted recall is computable from the CSV plus
cell sizes alone. Precision sample stays proportional over
(vintage_group × stratum) cells. Both seeded with SEED = 42; sampling
design was fixed before any rater label existed.

### 9d. 2026-10-12 — Main-result design: modern-only primary, no subsampling, matched P (author instruction; supersedes the §6b/§9b role of the cap)

Disclosures preceding this amendment (honest record, full report in
`reports/CURRICULUM_COMPLIANCE.md`):

- Legacy units were **never** pooled into any primary designation (§6b,
  `PRIMARY_SET.md` §2/§6); the 41-unit figure that circulated is the full
  extracted corpus (MIT 15 / TU Delft 14 / Stanford 6 / Harvard 6), not the
  primary set.
- The ≤8/institution bar bounded the *analysis set* (TU Delft trimmed
  14 → 8, §9b), not the corpus.
- The corpus reaches **2 countries** (US, NL) only; region bar waived §9a
  with the required limitation statement.
- Extraction of all 41 units occurred **before** the author reviewed counts
  (same day 2026-10-11; rulings §9a/9b followed extraction). No SGI or
  phrase-based analysis output existed at any point before the author's
  rulings, and CURR02 has still not run.

Amendment:

1. **Primary set = all modern (material year ≥ 2019) extracted units:
   n = 26** — TU Delft 14 / MIT 6 / Harvard 6; strata applied 18 / theory 8;
   countries US 12 / NL 14. Legacy (15 units: MIT 9, Stanford 6) remains the
   vintage-sensitivity group, reported separately, never pooled.
2. **No post-hoc subsampling for the main result.** The main CURR02
   comparison uses every modern unit. Institution-aware inference replaces
   the cap as the diversity safeguard:
   (i) **institution-clustered bootstrap** (resample the 3 institutions with
   replacement, taking all their units; B = 1000, seed 42; CIs flagged as
   indicative because 3 clusters are few);
   (ii) **institution-weighted SGI** (each institution equal weight,
   reported alongside the course-weighted SGI);
   (iii) **leave-one-institution-out** (3 runs, reported individually).
3. **Capped subsample = sensitivity analysis only.** The ≤8/institution
   subsample is registered now, rule frozen: *first 8 modern units per
   institution in MANIFEST file order* (deterministic; no RNG — seed 42
   covers all CURR02 resampling). Resulting n = 20 (MIT 6 / TU Delft 8 /
   Harvard 6, the current `PRIMARY_SET.md`). It no longer bounds the main
   result; the §6b hard bar "≤ 8 per institution" is superseded by the
   ≥20-courses-across-≥3-institutions bar on the modern set (met: 26/3).
4. **Matched covering-set size P (added to the CURR02 design).** The
   curriculum-vs-proxy comparison must use the **same P for both covering
   sets**: P = min(curriculum-profile size, proxy-profile size), capped at
   500, with sensitivity at P ∈ {100, 500} to mirror ALIGN01/02 (P = 100)
   and ALIGN03/04 (P = 500). CURR02 must report phrase counts per course
   (registered from the extraction: 437 phrases / 424 distinct; min 6 /
   median 14 / max 63 / mean 16.8 across 26 modern units) and state the
   exact P used in the results table.
5. **Required manuscript limitations** (reaffirmed): two countries (US +
   NL); open-courseware material (OCW/SEE/CS50 course pages, not
   institutionally collected syllabi); elite-institution skew; syllabus and
   outcome text ≠ full course content.

CURR02 remains blocked on the author labelling gate (§7 step 4) regardless
of this amendment; nothing here authorises a run.

### 9e. 2026-10-12 — Minimum extraction completeness: ≥ 5 phrases per unit (author instruction; fixed before any CURR02 run)

**Rule:** a curriculum unit contributing fewer than **5** extracted phrases is
excluded from every CURR02 analysis set (main and sensitivity groups); it stays
in the manifest and corpus with `below_phrase_floor` logged. Set on
extraction-completeness grounds, **before any SGI exists on this corpus** —
not on any analysis output.

Rationale:

1. **Noise dominance.** Below 5 phrases, one dropped or mis-extracted phrase
   moves the unit's own profile by ≥ 20%, so per-unit (descriptive) coverage
   contributions are dominated by extraction noise rather than course content.
2. **Page-fragment guard, not content filter.** The threshold is deliberately
   set *below* the observed floor of demonstrably complete extractions
   (modern minimum = 6 phrases) so that no complete extraction is excluded;
   the only unit it ever removes is a thin landing-page fragment (see below),
   where extraction succeeded but the source page carries almost no skill text.
3. **No analysis-driven selection.** At registration time no CURR02 SGI,
   coverage, or phrase-based analysis output exists; the value 5 is fixed on
   the corpus's own extraction statistics alone.

**Units below the floor (current corpus):**

| unit_id | vintage | phrases | note |
|---|---|---|---|
| MIT-1806 (Linear Algebra, Spring 2010) | legacy | 2 | thin OCW landing page; affects vintage-sensitivity group only |

MIT-6046 (5 phrases, legacy) sits exactly at the floor and passes. **All 26
modern units pass** (minimum 6, HARV-CS50AI), so the main result under §9d is
unaffected. Note for the author: a stricter cut of ≥ 6 would additionally
exclude MIT-6046; registered value is ≥ 5.

### 9f. 2026-10-12 — CURR02 inference design: per-institution descriptives, unreliable cluster bootstrap, bootstrap hierarchy (author instruction; supersedes the CI role in §9d(2)(i))

1. **Per-institution SGI** (TU Delft / MIT / Harvard) is reported as
   **descriptive results** — three point estimates with their resampling
   context — not as separate hypothesis tests and not pooled into a headline.
2. **Institution-clustered bootstrap** (§9d(2)(i), B = 1000, seed 42) is
   retained but explicitly **labelled statistically unreliable**: with only
   3 clusters, cluster-bootstrap intervals have essentially no coverage
   guarantee. It is **never used as a headline CI** and may not be cited in
   the abstract or conclusion.
3. **Headline CIs** come from the two resampling schemes with adequate
   resampling units, each reported with its resampling unit stated:
   (a) **posting-level bootstrap** on the market side (same design as
   ALIGN01/02: resample market postings, B = 1000, seed 42); and
   (b) **phrase-level bootstrap** on the curriculum side (resample extracted
   phrases within the analysis set, B = 1000, seed 42).
4. **Leave-one-institution-out** (3 runs) and the **institution-weighted
   SGI** (§9d(2)(ii)–(iii)) remain **descriptive robustness checks**,
   reported individually.
5. Every CURR02 result table must mark which interval is the headline CI and
   which entries are descriptive/unreliable; headline CIs are the only ones
   quotable as the curriculum-result uncertainty.

CURR02 remains blocked on the author labelling gate (§7 step 4) regardless
of these amendments; nothing here authorises a run.
