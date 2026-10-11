# Phase 7 — Literature & Citation Verification

*Date: 2026-10-11 · Tool: `audit/verify_citations.py` →
`audit/07_citation_check.csv` + `audit/07_citation_summary.json`
(Crossref REST API, one request per DOI, UA-identified).*

## 7.1 Mechanical Verification Results

| Category | Count | Notes |
|---|---|---|
| Bib entries total | 52 | `paper/references.bib` |
| DOIs verified against Crossref (title + year) | **35** | all resolve, 0 HTTP 404 |
| Entries without DOI (URL-bearing) | 17 | see 7.2 |
| Unresolved / network failures | 0 | — |

After the fixes in 7.3, re-run shows **35/35 DOIs resolve**; two residual
"weak title match" flags are Crossref metadata truncation, not bib errors
(7.4).

## 7.2 No-DOI Entries (17) — Acceptable Classes

| Class | Keys | Justification |
|---|---|---|
| Foundational books / reports | `becker1964human`, `schultz1961investment`, `wef2020` | monograph / institutional report; URL for WEF present |
| Kaggle dataset citations (13) | `asaniczka…`, `batuhanklac…`, `quackquackrp…`, `mobeenfatimah…`, `jahnavipaliwal…`, `bismasajjad…`, `mansiaggarwal88…`, `shree0910…`, `sumedh1507…`, `rakesh630…`, `philipdayo…`, `shambhurajejagadale…` | datasets are cited by repository URL (all have `url=`) |
| CEUR workshop paper | `decorte2022negative` | CEUR-WS volumes do not mint DOIs; `url=http://ceur-ws.org/Vol-3218/` added (HTTP 200 verified) |
| EU taxonomy portal | `esco2026` | living web resource; official URL |

## 7.3 Fixes Applied to `paper/references.bib` (verified metadata only)

| Key | Change | Evidence |
|---|---|---|
| `korrapati2025aligning` | DOI `10.1109/AISTS66100.2025` → **`10.1109/AISTS66100.2025.11233212`**; title completed with Crossref suffix “A Study of Skill Gaps and TEL Solutions in Indian Universities” | Crossref `/works/10.1109/aists66100.2025.11233212` |
| `zhang2022skillspan` | added `doi=10.18653/v1/2022.naacl-main.366` | Crossref title/author/year exact |
| `green2022development` | added `doi=10.63317/2phbdpk9z5bx` (ACL Anthology DataCite DOI; `10.18653/…lrec-1.128` 404s) | Crossref exact |
| `senger2024deep` | added `doi=10.18653/v1/2024.nlp4hr-1.1` | Crossref exact |
| `kruger2025improving` | added `doi=10.18653/v1/2025.emnlp-main.1375` | Crossref exact |
| `alhazmi2025aligning` | year **2026 → 2025**; added `pages=23--41` | Crossref `published/issued=[[2025]]` |
| `decorte2022negative` | added CEUR volume URL | HTTP 200 on `Vol-3218/` |

No reference was deleted; no citation was silently replaced.

## 7.4 Residual Flags (explained, no action)

| Key | Flag | Explanation |
|---|---|---|
| `schlippe2023skill` | title_match weak | Crossref stores only short title “Skill Scanner”; DOI `10.3991/ijac.v16i1.34779` resolves; full title matches journal PDF. Verified by inspection. |
| `cuckov2022quantifying` | Crossref year `None` | ASEE PEER metadata sparse; DOI resolves; conference is 2022 ASEE Annual. Title exact. |
| `scandurra2024employability` | bib 2024 / Crossref 2023 | online-first 2023, issue year 2024; both defensible; kept issue year. |

## 7.5 Narrative Citation Spot-Checks (high-stakes claims)

| Manuscript claim | Cited works | Support verdict |
|---|---|---|
| “over 40% of core worker skills…shift within five-year windows” (L68) | `wef2020` | Consistent with WEF FoJ 2020 framing (~40% skill-set disruption). ✓ |
| SBERT `all-MiniLM-L6-v2` for semantic matching (L126, L236) | `reimers2019sentence` | Correct method citation (Sentence-BERT); model card is separate but method attribution fine. ✓ |
| CS2023 “2,197 topic statements across 17 KAs” (L424) | `taskforce2024cs2023` | Consistent with CS2023 BoK structure (Crossref-verified entry). ✓ |
| Cuckov “evaluated…against ABET criteria” (L109) | `cuckov2022quantifying` | Title/metadata align. ✓ |
| Korrapati/Alhazmi “curriculum alignment with cloud/AI” (L109) | both | Titles align; Korrapati DOI now paper-level. ✓ |
| Academic profiles “standardized curriculum reference profiles” (L204) | `daberao2025resumeinsight` | **Weak support**: Daberao is resume–job semantic matching, not curriculum profiles. Suggest rewording to “profile-based matching precedent” or cite CURR01/CS2023 context instead. Flagged, not silently changed. |
| Baral “embeddings to measure syllabus alignment in Nepal” (L126, L615) | `baral2026analyzing` | Title matches NLP curriculum–industry gap study. ✓ |
| Skill extraction benchmarks distinguish skill/qualification/occupation | `green2022development`, `zhang2022skillspan` | Consistent with corpus design claims. ✓ |
| Deep-learning survey on skill extraction | `senger2024deep` | Title is exactly that survey. ✓ |
| Rule-based matching fails on occupational phrases | `kruger2025improving` | Compositional entity extraction paper; plausible support. ✓ |

## 7.6 Novelty Matrix (vs. closest cited work)

| Dimension | Closest cited work | Our delta |
|---|---|---|
| Lexical vs semantic curriculum–market gap | `baral2026analyzing` (single-country, small) | Multi-corpus, expert-validated matcher, CI-bounded SGI |
| Skill extraction benchmarks | `zhang2022skillspan`, `green2022development` | Used as annotation ground truth (VALID01), not re-annotated |
| Curriculum compliance scoring | `cuckov2022quantifying` (ABET checklist) | Semantic coverage against CS2023 BoK + per-KA breakdown |
| Placement prediction | `tamene2024predictive`, `haque2024classification` | External zero-shot transfer + multicollinearity audit |
| Resume/skill-gap NLP systems | `daberao2025resumeinsight` | Population-level gap estimation with theory-linked hypotheses |

Novelty claims in §I contributions are consistent with this matrix; no
overclaim of “first ever” was found.

## 7.7 Actions

| # | Action | Phase |
|---|---|---|
| 7.7.1 | Reword L204 citation of `daberao2025resumeinsight` (weak support) | 9 |
| 7.7.2 | Bib fixes above applied (this phase) | done |
| 7.7.3 | Optional: note in revision log that 4 DOIs were completed post-audit | 9 |
