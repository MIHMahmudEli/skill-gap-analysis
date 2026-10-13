# AUTHOR READING GUIDE — every section, its change since baseline, and its claim rows

Read in the order below. Line numbers are **current** line numbers at `HEAD`,
so they can be pasted into an editor as-is.

- **Baseline:** `9ca13e2` (the author-tagged baseline for this revision).
- **Claim ledger:** `audit/01_claim_evidence_ledger.csv`, 113 rows, mapped
  from its `manuscript_location` column (`Abstract`, `Sec.I`, `Sec.III-A`,
  `Sec.IV-B2`, `Limit.3`, `Tab.I`, `paper_placement Sec.IV-E`, …) and its
  `paper` column (`main` 78, `placement` 31, `none (artifact retained)` 3,
  `main+placement` 1).
- A row with several tokens — `C01` is `Abstract; Sec.I; Sec.III-A; Tab.I` —
  is credited to **every** section it names, not just the first match.
- **49 of 113** rows map to at least one section, **54** are marked `various` (location deliberately not section-specific), and **10** carry a token the mapper cannot resolve (a table number or free text). All three groups appear in full at the end, so no row is dropped silently.

---

## `paper/main.tex`

557 lines at `HEAD`; baseline had 715; **98 line(s) differ**.

| # | Level | Section | Start | Change since baseline | Claim-ledger rows |
|---|---|---|---:|---|---|
| 0 | *front* | **Abstract** | 69 | 1 line(s) changed: circularity check reordered to primary, SENS01 range scoping, escaping: % -> \%, escaping: & -> \&, reference-profile qualifier, C159 computational-anchor wording | `C01`, `C01a`, `C10`, `C11`, `C12`, `C20`, `C50` |
| 1 | **§** | Introduction | 80 | 9 line(s): reference-profile qualifier; RQ wording; dataset-count claim (still flagged) | `C01`, `C01a`, `M07` |
| 2 | **§** | Related Work and Theoretical Foundations | 118 | no change since baseline | — |
| 3 | ↳ | &nbsp;&nbsp;↳ Conceptualizations of the Skills Gap | 121 | no change since baseline | — |
| 4 | ↳ | &nbsp;&nbsp;↳ Theoretical Framework | 127 | 2 line(s): escaping: & -> \& | — |
| 5 | ↳ | &nbsp;&nbsp;↳ Natural Language Processing for Curriculum Analytics | 136 | no change since baseline | — |
| 6 | ↳ | &nbsp;&nbsp;↳ Testable Hypotheses | 140 | 4 line(s): local text edits | — |
| 7 | **§** | Methodology | 153 | no change since baseline | — |
| 8 | ↳ | &nbsp;&nbsp;↳ Data Corpus and Provenance Architecture | 156 | 28 line(s): escaping: & -> \&; reference-profile qualifier; dataset-count claim (still flagged) | `C01`, `C01a`, `C157`, `M03`, `M04`, `M10` |
| 9 | ↳ | &nbsp;&nbsp;↳ Taxonomy Construction and Skill Extraction | 204 | 2 line(s): circularity check reordered to primary; reference-profile qualifier | — |
| 10 | ↳ | &nbsp;&nbsp;↳ Semantic Vector Alignment via Sentence-BERT | 250 | 1 line(s): local text edits | — |
| 11 | ↳ | &nbsp;&nbsp;↳ Statistical Inference | 279 | 2 line(s): escaping: % -> \% | — |
| 12 | **§** | Empirical Results | 286 | no change since baseline | — |
| 13 | ↳ | &nbsp;&nbsp;↳ RQ1: Labor Market Skill Topography | 289 | 10 line(s): escaping: % -> \%; RQ wording | `C02b`, `C120` |
| 14 | ↳ | &nbsp;&nbsp;↳ RQ2: Lexical vs. Semantic Reference-Profile Alignment | 310 | 1 line(s): corpus qualifier on table/caption | `C10`, `C11`, `M02` |
| 15 | ↳↳ | &nbsp;&nbsp;↳↳ External Validation Against Expert Gold Standards (VALID01) | 338 | no change since baseline | `C50`, `M01`, `M06` |
| 16 | ↳↳ | &nbsp;&nbsp;↳↳ Nested-Superset Robustness Check on LinkedIn (ALIGN04) | 381 | 3 line(s): SENS01 range scoping | `C156`, `C30`, `M09` |
| 17 | ↳↳ | &nbsp;&nbsp;↳↳ Curriculum Anchor Validation against CS2023 (CURR01) | 399 | 1 line(s): escaping: % -> \%; escaping: & -> \&; reference-profile qualifier | `C41` |
| 18 | ↳ | &nbsp;&nbsp;↳ RQ3: Domain-Level Skill Gap Quantification | 415 | 2 line(s): escaping: % -> \%; escaping: & -> \&; reference-profile qualifier | `C155`, `C20` |
| 19 | **§** | Discussion | 458 | no change since baseline | — |
| 20 | ↳ | &nbsp;&nbsp;↳ Theoretical Implications | 461 | 1 line(s): escaping: % -> \% | — |
| 21 | ↳ | &nbsp;&nbsp;↳ Institutional Factors in Curriculum Adaptation | 485 | no change since baseline | — |
| 22 | ↳ | &nbsp;&nbsp;↳ Implications and Recommendations | 494 | 4 line(s): escaping: % -> \%; reference-profile qualifier | — |
| 23 | ↳ | &nbsp;&nbsp;↳ Reproducibility and Data Availability | 510 | 3 line(s): local text edits | — |
| 24 | ↳ | &nbsp;&nbsp;↳ Threats to Validity and Limitations | 528 | 5 line(s): circularity check reordered to primary; Threats scope note (unswept superset); escaping: % -> \%; escaping: & -> \&; reference-profile qualifier; RQ wording | `C157`, `C41` |
| 25 | **§** | Conclusion | 546 | 1 line(s): escaping: % -> \%; escaping: & -> \&; reference-profile qualifier; dataset-count claim (still flagged) | — |

*Index Terms at line **73**; abstract lines **69–71**; front matter lines 1–79.*

*Abstract: **248 words** at HEAD vs **454** at baseline (limit 250).*

---

## `paper_placement/main.tex`

**New since baseline** — this file does not exist at `9ca13e2`, so
every section below is new. The `Change` column therefore records only
the section start, and the table exists to give you the reading order
and line numbers. 378 lines at `HEAD`.

| # | Level | Section | Start | Change since baseline | Claim-ledger rows |
|---|---|---|---:|---|---|
| 0 | *front* | **Abstract** | 61 | new since baseline (file created after baseline) | — |
| 1 | **§** | Introduction | 72 | new since baseline | — |
| 2 | **§** | Related Work and Theoretical Foundations | 92 | new since baseline | — |
| 3 | ↳ | &nbsp;&nbsp;↳ Machine Learning in Employability Modeling | 95 | new since baseline | — |
| 4 | ↳ | &nbsp;&nbsp;↳ Theoretical Grounding of H4--H6 | 99 | new since baseline | — |
| 5 | ↳ | &nbsp;&nbsp;↳ Hypotheses H4--H6 (Restated) | 108 | new since baseline | — |
| 6 | **§** | Methodology | 121 | new since baseline | — |
| 7 | ↳ | &nbsp;&nbsp;↳ Benchmarks and Provenance | 124 | new since baseline | `C113` |
| 8 | ↳ | &nbsp;&nbsp;↳ Statistical Inference \& Collinearity Diagnostics | 129 | new since baseline | — |
| 9 | ↳ | &nbsp;&nbsp;↳ Predictive Modeling \& Validation Protocols | 155 | new since baseline | — |
| 10 | **§** | Benchmark Audit Results | 184 | new since baseline | `C100`, `C70`, `C77` |
| 11 | ↳ | &nbsp;&nbsp;↳ RQ4: Employability Determinants \& Cross-Validation Benchmarks | 187 | new since baseline | `C70`, `C71`, `C72`, `C73`, `C74`, `C75`, `C76`, `C85`, `C86` |
| 12 | ↳↳ | &nbsp;&nbsp;↳↳ Univariate \& Descriptive Findings | 191 | new since baseline | — |
| 13 | ↳↳ | &nbsp;&nbsp;↳↳ Multicollinearity Diagnostics | 224 | new since baseline | — |
| 14 | ↳↳ | &nbsp;&nbsp;↳↳ Standardized Logistic Regression | 236 | new since baseline | — |
| 15 | ↳↳ | &nbsp;&nbsp;↳↳ 5-Fold Cross-Validation Model Comparison | 248 | new since baseline | `C77`, `C80`, `C81`, `C83`, `C84` |
| 16 | ↳↳ | &nbsp;&nbsp;↳↳ Diagnostic Audit of Tree Ensembles \& External Generalization | 271 | new since baseline | `C100`, `C101`, `C102`, `C78`, `C79`, `C82`, `M08` |
| 17 | ↳ | &nbsp;&nbsp;↳ RQ5: Cross-Cohort Placement Dynamics | 277 | new since baseline | `C130` |
| 18 | **§** | Discussion | 287 | new since baseline | `C130` |
| 19 | ↳ | &nbsp;&nbsp;↳ Hypothesis Verdicts (as Benchmark Properties) | 290 | new since baseline | `C152`, `C152b`, `C161`, `M05` |
| 20 | ↳ | &nbsp;&nbsp;↳ Recommendations | 319 | new since baseline | — |
| 21 | ↳ | &nbsp;&nbsp;↳ Threats to Validity and Limitations | 333 | new since baseline | `C157`, `C41` |
| 22 | ↳ | &nbsp;&nbsp;↳ Reproducibility and Data Availability | 346 | new since baseline | `M07` |
| 23 | **§** | Conclusion | 367 | new since baseline | — |

*Index Terms at line **65**; abstract lines **61–63**; front matter lines 1–71.*

*Abstract: **289 words** (no baseline to compare — new file).*

---

## What the `paper/main.tex` abstract says now that it did not say at baseline

| # | Addition | Commit |
|---|---|---|
| 1 | **Corpus scoping** of the SENS01 ranges: "on the primary corpus, sweeping (K, P) keeps lexical SGI in [0.52, 0.73] and semantic SGI at τ = 0.5 in [0.26, 0.42]" — nested-superset ranges [0.53, 0.74] live in the body once | `9b456cb` |
| 2 | **Title-free circularity promoted to primary**: "a title-free skill-set join on the primary market subset finds no profile/market pairs at Jaccard ≥ 0.7 (max 0.667)" | `8bf3499` |
| 3 | **Escaping repairs**: 8 × `%` → `\%`, 1 × `&` → `\&`, so the abstract renders in full instead of truncating after "52.0" | `fbe9122` |
| 4 | **C159** reworded to "a computational anchor, not a human audit" (confirmed in place; no file change in this batch) | — |

---

---

## Claim-ledger rows in reading order

Rows are listed once per section that names them. **54 `various` rows are deliberately not section-specific** and are given as one block.

### `various` — 54 rows (location deliberately not section-specific)

`C01b`, `C03`, `C04`, `C10b`, `C10c`, `C11b`, `C12b`, `C12c`, `C20b`, `C21`, `C22`, `C23`, `C24`, `C25`, `C26`, `C31`, `C31b`, `C32`, `C32b`, `C40`, `C40b`, `C41b`, `C42`, `C43`, `C44`, `C45`, `C46`, `C47`, `C48`, `C49`, `C50b`, `C51`, `C52`, `C53`, `C54`, `C55`, `C55b`, `C55c`, `C56`, `C57`, `C58`, `C59`, `C60`, `C61`, `C140`, `C141`, `C142`, `C143`, `C150`, `C151`, `C154`, `C158`, `C159`, `C160`

### Unmapped — 10 rows (of the 64 unmapped, 54 are the `various` rows above)

These carry a token the mapper cannot resolve (a table number or free text, or a location referring to material removed from the manuscripts). Listed so nothing disappears:

| claim | paper | manuscript_location |
|---|---|---|
| `C02` | main | Tab.I |
| `C05` | main | Tab.I |
| `C110` | none (artifact retained) | removed from both manuscripts 2026-10-12 (Phase 4 D3: internship-effect claim dropped; … |
| `C111` | none (artifact retained) | removed from both manuscripts 2026-10-12 (Phase 4 D3: internship-effect claim dropped; … |
| `C112` | none (artifact retained) | removed from both manuscripts 2026-10-12 (Phase 4 D3: internship-effect claim dropped; … |
| `C153` | placement | paper_placement tab:hypotheses |
| `C87` | placement | paper_placement tab:vif (was main tab:vif) |
| `C88` | placement | paper_placement tab:descriptive |
| `C89` | placement | paper_placement tab:descriptive |
| `C90` | placement | paper_placement tab:descriptive |

### Mapped — 49 distinct rows, credited to 66 section slots

`C01`, `C01a`, `C02b`, `C10`, `C100`, `C101`, `C102`, `C11`, `C113`, `C12`, `C120`, `C130`, `C152`, `C152b`, `C155`, `C156`, `C157`, `C161`, `C20`, `C30`, `C41`, `C50`, `C70`, `C71`, `C72`, `C73`, `C74`, `C75`, `C76`, `C77`, `C78`, `C79`, `C80`, `C81`, `C82`, `C83`, `C84`, `C85`, `C86`, `M01`, `M02`, `M03`, `M04`, `M05`, `M06`, `M07`, `M08`, `M09`, `M10`

---

## Counts

- `paper/main.tex`: **25** headings = 6 sections + 16 subsections + 3 subsubsections; 557 lines at HEAD.
- `paper_placement/main.tex`: **23** headings = 6 sections + 12 subsections + 5 subsubsections; 378 lines at HEAD.
- Claim ledger: **113** rows → **49** mapped to at least one section (66 credits in total), **54** `various`, **10** other-unmapped. 49 + 54 + 10 = 113.

*Generated by `guide_build.py`; regenerate rather than hand-editing, since line numbers move whenever the manuscript changes.*
