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
