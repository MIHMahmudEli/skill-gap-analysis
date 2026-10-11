# Phase 1 — Claim-to-Evidence Ledger (Summary)

*Full ledger: `audit/01_claim_evidence_ledger.csv` (103 rows). Machine checks:
`audit/verify_claims.py` → `audit/01_claim_verification.json` (95 automated checks;
86 exact matches, 2 rounding-only, 7 presence/provenance rows).*

## 1.1 Method

Every quantitative constant in `paper/main.tex` was matched against the
authoritative artifact under `results/<EXP_ID>/` (metrics.json, CSVs, or
auto-generated `paper/tables/*.tex`). A claim is **reproduced** only when the
manuscript value equals (or correctly rounds) the artifact value. Raw data were
not modified. The H6 internship figure was independently recomputed from the
source CSV.

## 1.2 Classification Totals

| Status | Count | Meaning |
|---|---|---|
| reproduced | 96 | Manuscript value == artifact value (incl. correct rounding) |
| partially reproduced | 3 | Core number OK; context/unit/metadata caveat |
| contradicted | 4 | Manuscript number or attribution wrong (all one cluster: H6) |
| not reproduced | 0 | — |

## 1.3 Verified Defects (contradicted)

### D-1 (Major) — H6 internship risk difference "+0.08 pp" is unsupported and the experiment is misattributed

- **Location:** `paper/main.tex:592` (hypothesis-verdict paragraph) and
  Table XIII (`tab:hypotheses`, line 609: `H6 & ... & Not supported (INTL01; $p = 0.62$)`).
- **Manuscript claims:** H6 not supported, "risk difference +0.08 pp, p = 0.62",
  attributed to INTL01.
- **Evidence:**
  - Computed from
    `datasets/kaggle/college-student-placement/college_student_placement_dataset.csv`
    (2026-10-11): P(placed|internship)=16.32% (n=3,964) vs 16.77% (n=6,036)
    → **univariate RD = −0.44 pp** (not +0.08).
  - `results/STAT01_placement_core/metrics.json`: multivariate
    Internship_Binary OR=1.0194, p=0.6197 (ns) — this is the correct test for H6.
  - `results/INTL01_internship_effect/metrics.json`: RD=**+15.34 pp** [14.99, 15.73],
    χ² p≈0 — INTL01 is *significant* and cannot be the "not supported" citation.
- **Why it matters:** a fabricated-looking number in the hypothesis-verdict
  table is exactly what a statistical reviewer will pounce on; the
  misattribution also contradicts the paper's own H5 evidence.
- **Action (Phase 9):** rewrite as "Not supported (STAT01: OR = 1.02, p = 0.62;
  univariate RD = −0.44 pp on the College Placement cohort)". Update
  Table XIII cell to `(STAT01)`.

### D-2 (Moderate) — Corpus headline "3,176,266 records / 15 datasets, we analyze"

- **Location:** Abstract, §I, §III-A, Table I.
- **Evidence:** manifest sum = 3,176,266 ✓ arithmetic; but:
  1. **Linked-table double count:** HF Skill Gap Jobs (519,841) and Skills
     (519,814) are posting-level and skill-row views of the same corpus
     (join on `job_id`). Unique postings ≈ 519.8K, not 1.04M.
  2. **Inventory-only datasets:** of the 15 archived datasets, only ~9 feed a
     registered experiment (see Phase 2 usage map). USA Job Market, Career
     Change, AI 15K, India Skills Intelligence (synthetic), NGESS, and India
     Fresher contribute zero computed results — "we analyze 15 datasets" overstates.
  3. **Unit mixing:** job postings, skill rows, and student records summed into one N.
- **Action:** restate precisely in §III-A/abstract: e.g. "15 archived public
  datasets; primary analyses use 9 (≈2.7M posting-level records + 420,644
  student records)". Document the linked-table relationship.

### D-3 (Minor) — LinkedIn record count mismatch

- Table I: 1,348,510 (manifest). GEO01 processed 1,348,454 rows
  (`results/GEO01.../metrics.json`). Δ = 56 rows (header/parse).
- **Action:** Phase 2 root-cause; state "1,348,454 parsed (file lists 1,348,510)".

### D-4 (Minor) — ALIGN03 posting count vs RQ1 denominator

- RQ1 text: "Among the 519,814 skill requirements…" (matches skills table rows).
- ALIGN03 `n_postings` = 518,953 (postings with ≥1 parsed skill after filtering).
- **Action:** one-sentence clarification in §IV-C or §IV-B1.

## 1.4 Key Reproduced Headlines (sample; see CSV for all)

| Claim | MS | Artifact |
|---|---|---|
| Lexical SGI 52% [42, 63] | 0.52 [0.42, 0.63] | ALIGN01 ✓ |
| Semantic SGI τ=0.5 32% [23, 41] | 0.32 [0.23, 0.41] | ALIGN02 ✓ |
| Cloud deficit 2.45→0.94 pp | matches | ALIGN03 ✓ |
| Cross-corpus SGI 0.37 / 0.14 | matches | ALIGN04 ✓ |
| CS2023 coverage 30.4% / reverse 49.6% | matches | CURR01 ✓ |
| κ=0.737, AUC 0.961, n=2,907 | matches | VALID01 ✓ |
| Comm OR 6.55 [5.86, 7.31] | matches (raw 6.5471) | STAT01 ✓ |
| CV LR 90.11%, AUC 0.9406; RF 99.99% | matches | STAT01 ✓ |
| External AUC 0.768 / 0.576 | matches (0.7680/0.5757) | STAT02 ✓ |
| Internship +15.34 pp [14.99, 15.73] | matches | INTL01 ✓ |
| Geo US 85.2% | matches (85.23) | GEO01 ✓ |
| RQ1 top-6 token counts | exact match | ALIGN01 market_top500.csv ✓ |
| Semantic pair cos 0.6122 / 0.2937 | exact | ALIGN02 matches CSV ✓ |
| VIF ≤ 1.001 | max 1.001 | tab_vif ✓ |
| k-of-n audit 99.92% | 0.9992 | STAT01 tree_audit ✓ |
| Multi-seed LR 90.12±0.04% | matches | STAT01 ✓ |
| ESCO inventory 13,896 | file has 13,896 lines | VALID01 upstream ✓ |

## 1.5 Notes on Borderline Items

- **Canada 4.2% vs raw 4.15%** and **Cloud min 47.1% vs raw 47.05%**: correct
  1-dp rounding; not defects.
- **VALID01 `n_positive_by_type` all zeros** while `n_negative=1,769`: metrics
  metadata bug (type histogram not filled). Pair-level CSV exists; no
  manuscript number depends on it. Optional fix in verify/sync.
- **RQ1 counts vs independent recount:** naive exact-token recount on local
  `hf_skill_gap_skills.csv` gives communication 147,123 vs artifact 148,765
  (−1.1%). Registered artifact is authoritative; difference is tokenizer detail
  (documented here; not a manuscript error).

## 1.6 Changes Made This Phase

- Added `audit/verify_claims.py`, `audit/build_ledger.py` (read-only vs raw data).
- Added `audit/00_repository_inventory.md`, `audit/01_claim_evidence_ledger.{csv,md}`,
  `audit/01_claim_verification.json`.
- **No manuscript or data edits yet.**

## 1.7 Blocked / Next

- Phase 2 will recount raw files, resolve the 56-row LinkedIn delta, map
  dataset usage, and check HF jobs/skills linkage (`job_id` overlap).
- D-1 will be fixed in the manuscript revision phase (not now, to keep the
  ledger describing the *original* state).
