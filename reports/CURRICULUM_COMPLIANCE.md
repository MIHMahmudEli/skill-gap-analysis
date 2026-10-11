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
