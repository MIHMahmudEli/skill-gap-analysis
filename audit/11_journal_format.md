# Phase 11 — Target-Journal Verification (Publisher-Neutral)

*Date: 2026-10-11 · Sources: official author pages fetched 2026-10-11.
No target journal is assumed; IEEEtran is a formatting choice, not a venue
commitment. Candidates below were checked for **fit + format feasibility**;
final choice is an author decision.*

## 11.1 Manuscript Profile (this branch)

| Property | Value |
|---|---|
| Class | `IEEEtran` (journal mode) |
| Length | **16 PDF pages** (0 errors / 0 overfull) |
| Abstract | ~370 words (unstructured) |
| Body words (excl. tables/figures/refs, rough) | ~6,600 |
| References | 52 (35 DOI-verified; 17 URL-bearing) |
| Double-blind ready | Yes (authors redacted; revision log anonymized) |
| Data/code | Public bundle + HF archive + `reproduce_local.py` |

## 11.2 Candidate Venues (verified constraints only)

### A. IEEE Transactions on Education (ToE)
- **Scope:** education methods/technology/programs in EE/CE/CS; Boyer areas
  (Discovery / Integration / Application); structured abstracts required;
  scholarship-of-application/discovery submissions **≤ 8 pages**; Integration
  **≤ 10 pages** (ieee-edusociety.org ToE author resources, 2026).
- **Fit:** strong (CS education + industry alignment + measurement).
- **Gap vs current draft:** 16 → 8–10 pages needs major compression
  (likely cut TRENDS/GEO narrative, merge tables, shorten related work);
  convert to structured abstract; add ORCID at submission.
- **Format:** IEEEtran is the correct family; no class change.

### B. British Journal of Educational Technology (BJET)
- **Scope:** theory/methods/applications of digital technologies in
  education (Wiley/BERA author guidelines, 2026).
- **Length:** Original/Review articles **5,000–6,000 words** (includes
  tables/figures/footnotes; excludes references, abstract, practitioner
  notes); free-format submission.
- **Fit:** moderate–strong (ed-tech + analytics); less CS-curriculum
  specificity than ToE.
- **Gap vs current draft:** body ~6.6k + heavy tables may exceed 6k once
  tables counted; convert from IEEEtran to Wiley/BERA template (structure
  roughly portable: Intro→Lit→Method→Results→Discussion→Limitations).
- **Format:** **class change required** (not IEEEtran).

### C. International Journal of Educational Technology in Higher Education (IJETHE)
- **Scope:** technology-enhanced learning in higher education (Springer
  OA, CC-BY; research articles **4,500–8,000 words**, abstract **150–250
  words**; link.springer.com journal 41239 submission guidelines, 2026).
- **Fit:** moderate (higher-ed focus; industry-alignment framing OK).
- **Gap vs current draft:** abstract must shrink ~370 → ≤250 words;
  OA APC applies (check current APC/funding); Springer Nature template.
- **Format:** class change required.

## 11.3 Not Assessed as Primary (recorded, not recommended/rejected)

- *Computers & Education* (Elsevier): previously flagged as needing Tier-C
  expert-panel evidence for the strongest venue tier; not re-verified here.
- Any IEEE magazine: different page budget and audience; not checked.

## 11.4 Recommendation (non-binding)

1. **Closest format match with least rework:** IEEE ToE — but requires
   cutting ~half the pages and a structured abstract.
2. **Closest length match without page surgery:** IJETHE (4.5–8k words)
   after abstract trim + OA logistics.
3. **BJET** viable after word-budget pass and Wiley conversion.

Authors should pick one and re-run a format checklist against the **live**
author page at submission time (guidelines change; URLs above were live
2026-10-11). This audit does **not** name a single “target” journal.

## 11.5 Blocked / Unverified Items

- Exact APCs and current impact metrics not re-fetched (pricing pages
  dynamic) — treat as unverified.
- Single-anonym vs double-anonym policies differ by venue; draft is
  anonymized (safe for double-blind) but single-blind venues may want
  author identities restored at submission.
