# Phase 4 — Curriculum Reference Validity

*Date: 2026-01-11 · Components: (a) academic reference profile construct;
(b) CURR01 CS2023 anchor; (c) local reproduction.*

## 4.1 What the "Academic Reference" Actually Is

From Phase 2: `hf_job_skill_set.csv` = **1,167 job postings** (IT/Business/
Finance/Sales/HR), not syllabi. The manuscript already avoids calling it
observed university teaching ("standardized curriculum reference profiles
rather than scraped syllabi", §III-B) and quantifies the gap to a real
curricular standard via CURR01. That framing is honest **provided Table I's
"13,833 curriculum-domain skill taxonomy" description is corrected** (Phase 2
D-2). CURR01's 30.4% coverage of CS2023 is the number that keeps SGI
interpretable as *job-facing applied-skill coverage*, not full-curriculum
coverage.

## 4.2 CURR01 — Local Reproduction (exact)

Ran `experiments/exp_scripts/curr01_cs2023_anchor.py` on local inputs
(`SKILLGAP_INPUT_DIR=datasets`). **Every field identical** to
`results/CURR01_cs2023_anchor/metrics.json`: n_topics=2,197; n_kas=17;
overall coverage τ=0.5 = 0.3041; reverse = 0.496; full per-KA vector and
sensitivity curve match bit-for-bit.

## 4.3 CS2023 Topic Source

- PDF: `datasets/cs2023/CS2023_BoK.pdf` (ACM Digital Library URL recorded in
  repo history; 3.6 MB).
- Extraction: `datasets/cs2023/extract_topics.py` → 2,197 topic strings,
  17 KAs. Spot-checks: topic strings are real BoK statements (e.g., "Rices
  theorem and its significance", "Pumping Lemma proofs", "Single qubit gates
  for the circuit model…"). Extraction rules (strip lead verbs, drop >90-char
  lines) are lossy but deterministic and documented in the script.
- **Residual risk:** extraction heuristics could drop or merge topics;
  counts (2,197 / 17) match the manuscript; per-KA counts are plausible vs
  the published BoK structure. No independent line-by-line audit of all 2,197
  strings was performed (flagged as unverified at 100% granularity).

## 4.4 Unmatched-Topic Diagnosis (τ = 0.5, n = 2,197)

From `results/CURR01_cs2023_anchor/cs2023_topic_matches.csv`:

| Cause class | Example (cos) | Assessment |
|---|---|---|
| **True absence from job-facing profile** (theoretical core) | "Rices theorem…" (0.17), "Pumping Lemma proofs" (0.20), quantum gates (0.15–0.18), graphics "Subsurface scattering" (0.18) | Dominant in AL/AR/GIT unmatched sets — the profile is applied/business-IT, so theory topics genuinely have no counterpart. This is a **property of the proxy**, not a matcher failure — exactly what Limitation 3 says. |
| **Phrasing/granularity mismatch** (question vs noun phrase) | "Definitions of agents with examples" → "delegation" (0.28); "Overview of AI problems…" → "machine learning" (0.35) | BoK statements are learning-outcome sentences; embedding them against short skill labels systematically depresses cosine. Would improve with outcome→phrase compression (future work). |
| **Possible semantic false positive** | "What is intelligent behavior?" → "emotional intelligence" (0.56 ≥ 0.5) | Sparse; τ=0.5 does not fully protect against topical drift. VALID01 bounds this on expert pairs (precision 91.9%). |

Unmatched mass concentrates in FPL (241), AI (145), GIT (145), SPD (132) —
consistent with theory/design content absent from a job-skill profile.

## 4.5 Sensitivity

CURR01 reports τ ∈ {0.4, 0.5, 0.6, 0.7}: coverage 63.1% / 30.4% / 10.9% /
3.5%. The 30.4% headline is highly τ-dependent (already disclosed). Reverse
coverage 49.6% (τ=0.5) means about half the profile skills find some BoK
topic — the other half are either below-threshold paraphrases or genuinely
non-CS2023 (business/soft skills in the profile).

## 4.6 Sensitivity to Institution/Discipline

Not testable here: no multi-institution syllabus corpus is available.
The audit does **not** simulate one. CS2023 is a single (authoritative)
reference; institution-level variation remains an open limitation
(aligns with manuscript Limitation 3).

## 4.7 Actions

- Phase 9: correct Table I academic-reference description/size; one sentence
  on question-form topics depressing coverage (optional).
- Keep CURR01 as-is (reproduced exactly; appropriately bounded claims).
