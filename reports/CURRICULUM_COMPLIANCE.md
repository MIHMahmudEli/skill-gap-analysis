# Curriculum Compliance Report (Q1 Revision — Step 5)

Date: 2026-10-12 · Branch: `q1-revision` · Corpus: `datasets/curriculum/` · No CURR02 run; no SGI value exists on this corpus.

The author asked for an honest report against four bars: (i) legacy pooled into "primary", (ii) institution cap (MIT 15 / TU Delft 14 vs ≤8), (iii) only 2 countries, (iv) extraction before author review of counts. Facts below are computed from `datasets/curriculum/MANIFEST.csv` and `extracted/curriculum_phrases.csv`.

## 1. Ground truth (recomputed 2026-10-12)

**Full extracted corpus: 41 units** — MIT 15 / TU Delft 14 / Stanford 6 / Harvard 6.

| | legacy | modern (2019+) | total |
|---|---|---|---|
| MIT | 9 | 6 | 15 |
| TU Delft | 0 | 14 | 14 |
| Stanford | 6 | 0 | 6 |
| Harvard | 0 | 6 | 6 |
| **total** | **15** | **26** | **41** |

Modern (26 units) by stratum: applied 18 / theory 8. By country: US 12 (MIT 6 + Harvard 6), NL 14.
Modern phrases: 437 extracted phrases (424 distinct after normalisation), per course min 6 / median 14 / max 63 / mean 16.8.

**Committed primary set (`PRIMARY_SET.md`, n = 20):** modern only, ≤8/institution cap applied (TU Delft 14 → 8, manifest-order rule): MIT 6 / TU Delft 8 / Harvard 6; strata 6 theory / 14 applied. Legacy group (15 units, MIT 9 + Stanford 6) is defined as a separate vintage-sensitivity group.

## 2. Honest assessment against the four bars

**(i) "Legacy pooled into primary" — NOT so in the committed record.** Protocol §6b (author-approved 2026-10-11, frozen before download) defines the primary analysis set as material year ≥ 2019 only, with legacy "reported separately; not pooled into the primary SGI". `PRIMARY_SET.md` §2/§6 implements this: primary = 20 modern units; the 15 legacy units (MIT OCW pre-2019 + all of Stanford SEE) are the vintage-sensitivity group. The "MIT 15 / TU Delft 14 / Stanford 6 / Harvard 6" figure describes the **full extracted corpus**, not the primary set — an earlier status message used the phrase "primary set" loosely for the extracted corpus; the record is corrected here. No legacy unit has ever been in a primary designation.

**(ii) Institution cap — applied to the analysis set, not the corpus (no violation as registered).** The ≤8/institution bar (§6b) bounds the *primary analysis set*: TU Delft was trimmed 14 → 8 by the author-confirmed deterministic rule (first 8 rows in MANIFEST file order, §9b), giving primary n = 20 with max 8 per institution. The corpus itself deliberately retains all 41 units (trimming "only bounds the primary analysis set" — `PRIMARY_SET.md` §1.3). So MIT 15 / TU Delft 14 in the manifest are corpus facts, not cap breaches. **However**, per the author's 2026-10-12 instruction, subsampling is removed from the *main* result going forward (amendment 9d): the main CURR02 comparison will use all 26 modern units with institution-aware inference, and the ≤8 capped subsample becomes a sensitivity analysis only.

**(iii) Only 2 countries — TRUE, and the binding deviation.** Modern set: US (12) + NL (14). Legacy adds only US units (MIT 9, Stanford 6), so the full corpus is still 2 countries. The protocol's ≥3-region hard bar (§4) FAILed; the author waived to ≥2 regions on 2026-10-11 (§9a) with a required manuscript limitation: the third region was license-blocked (NPTEL/SWAYAM TOU, Helsinki all-rights-reserved, both excluded at plan stage), not overlooked. This remains a genuine limitation: two countries of open courseware, both Western.

**(iv) Extraction before author review of counts — TRUE.** All 41 units were extracted on 2026-10-11; the author's count review and rulings (region waiver §9a, cap rule §9b) came the same day *after* extraction, and this compliance review follows. Mitigating facts on record: the selection protocol, institution list, and strata targets were frozen pre-download; no SGI or phrase-based analysis output existed before the author's rulings (CURR02 has not run); the region-bar failure was surfaced by the pre-analysis bar check in `PRIMARY_SET.md`, not after results. The sequencing deviation is disclosed here and in amendment 9d.

**STOP-condition check (author's instruction):** can the modern set support ≥20 courses across ≥3 institutions? Yes — 26 modern units across TU Delft, MIT, Harvard (even after the ≤8 trim: 20 across the same 3). No STOP triggered; CURR02 may proceed to registration once the labelling gate clears.

## 3. Amendment (§9d) — summary of what changes

Recorded in `datasets/curriculum/SELECTION_PROTOCOL.md` §9d (full text there):

1. Primary = all **26 modern (2019+) units**; legacy 15 = sensitivity group (unchanged principle, expanded primary from the capped 20).
2. **No post-hoc subsampling for the main result.** Main CURR02 uses every modern unit with institution-aware inference: institution-clustered bootstrap (B = 1000, seed 42; CI flagged indicative — only 3 clusters), institution-weighted SGI (equal institution weight, reported alongside course-weighted), and leave-one-institution-out (3 runs).
3. The **≤8/institution capped subsample** (first 8 modern units per institution in MANIFEST file order — deterministic, no RNG; seed 42 covers all CURR02 resampling) is registered **now** as a sensitivity analysis only; it no longer bounds the main result.
4. **Matched covering-set size P** for the curriculum-vs-proxy comparison (added to CURR02 design): report phrase counts per course (registered: 437 phrases / 424 distinct; min 6 / median 14 / max 63 / mean 16.8) and use P = min(curriculum-profile size, proxy-profile size) capped at 500, with sensitivity at P ∈ {100, 500} to mirror ALIGN01/02 vs ALIGN03/04; the exact P used must be stated in results.
5. Required manuscript limitations (reaffirmed): two countries (US + NL), open-courseware material, elite-institution skew, syllabus text ≠ course content.

`PRIMARY_SET.md` carries a dated banner noting the supersession (its n = 20 set is retained as the registered capped-subsampling sensitivity).

---

## §E — TU Delft unit listing and new pre-run amendments (2026-10-12, author instruction; no CURR02 run)

### E.1 The 14 TU Delft units

**One-programme flag: YES.** All 14 units come from a **single programme/source** —
the TU Delft OpenCourseWare catalogue (`ocw.tudelft.nl`, site-wide CC BY-NC-SA 4.0,
one platform, one license). Within it they span four subject groupings (inferred
from course titles; MANIFEST does not record department names) and two course
levels. Material years are page-visible years recorded at extraction.

| unit_id | Course title | Subject grouping (inferred) | Level | Stratum | Material year | Phrases |
|---|---|---|---|---|---|---|
| TUD-ALG | Algoritmiek (Algorithms) | CS theory | upper | theory | 2023 | 11 |
| TUD-DS | Unix Tools: Data, Software and Production Engineering | Software engineering | upper | applied | 2020+ | 23 |
| TUD-AI1 | AI skills for engineers: Data creation and collection | AI/ML | intro | applied | 2023 | 20 |
| TUD-AI2 | AI skills for Engineers: Supervised Machine Learning | AI/ML | intro | applied | 2023 | 29 |
| TUD-QI | Quantum Information Processing | Quantum | upper | theory | 2023 | 17 |
| TUD-TOC | Theory of Computation | CS theory | upper | theory | 2020+ | 15 |
| TUD-AST | Automated Software Testing: Advanced Skills for Java Developers | Software engineering | upper | applied | 2019+ | 12 |
| TUD-AST2 | Automated Software Testing: Practical Skills for Java Developers | Software engineering | intro | applied | 2019+ | 14 |
| TUD-GSE | Global Software Engineering | Software engineering | upper | applied | 2020+ | 19 |
| TUD-FP | Introduction to Functional Programming | CS theory | upper | theory | 2020+ | 21 |
| TUD-QC | Quantum Cryptography | Quantum | upper | theory | 2023 | 26 |
| TUD-SV | System Validation | Software engineering | upper | applied | 2023 | 15 |
| TUD-AIP | AI in Practice: Applying AI | AI/ML | intro | applied | 2022+ | 17 |
| TUD-AI3 | AI skills — Unsupervised, Deep and Reinforcement Learning | AI/ML | upper | applied | 2023 | 26 |

Totals: 14 units / 265 phrases (61% of the modern set's 437); subject split
software engineering 5, AI/ML 4, CS theory 3, quantum 2; level split 4 intro /
10 upper; strata 9 applied / 5 theory. All 14 are modern (≥ 2019) and all enter
the §9d main set (n = 26); the 6 units beyond the old ≤8 cap are back in the
main set under §9d.

**Limitation to carry to the manuscript:** the NL half of the corpus is one
programme on one platform with a site-wide license — intra-institution
diversity at TU Delft is course-level only (four subject groupings), not
programme-level; this strengthens, not weakens, the §9f requirement to treat
per-institution SGI as descriptive.

### E.2 New pre-run amendments (registered in `SELECTION_PROTOCOL.md`)

- **§9e — minimum phrase floor ≥ 5 phrases per unit** (extraction-completeness
  rule, fixed before any CURR02 SGI). Below floor: MIT-1806 (2 phrases, legacy
  landing-page fragment). MIT-6046 (5) passes at the floor; all 26 modern units
  pass (minimum 6). A stricter ≥ 6 cut would additionally drop MIT-6046 —
  registered value is ≥ 5.
- **§9f — inference hierarchy:** per-institution SGI = descriptive;
  institution-clustered bootstrap (3 clusters) = **unreliable, never headline**;
  headline CIs = posting-level bootstrap (market side) + phrase-level bootstrap
  (curriculum side), B = 1000, seed 42; leave-one-institution-out and
  institution-weighted SGI = descriptive robustness checks. This supersedes the
  "CI flagged indicative" role written in §d item 2 above.
