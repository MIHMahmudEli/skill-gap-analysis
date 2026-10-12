# Abstract v4 — two branches (print-only; NOT applied to `paper/main.tex`)

Author instruction 2026-10-12 (batch 3, step 2). Constraints applied to both branches:
no "15 datasets", no "2.12M unique records"; the corpus described by unit (1.35M real
LinkedIn postings, one scrape family) with the nested subset and the superset named; the
reference profile described as what it is (1,167 employer-derived postings across five
occupational categories) plus the new step-1 independence result; **no recommendation
sentence at all**; Cloud/Programming/soft-skill figures labelled **reference-profile**
deficits, not curricular. Kept as required: the 20-percentage-point reduction with its
CI, κ with precision/recall and the gold-set skew caveat, "consistent with" for the
vocabulary-divergence reading, and the nested-superset (same scrape family) wording.

Every number comes from a committed artifact: `results/ALIGN01_lexical_bootstrap`,
`ALIGN02_semantic_sbert`, `ALIGN04_linkedin_superset`, `VALID01_esco_gold/metrics.json`,
`reports/CIRCULARITY_CHECK.md`.

---

## v4a — CURR02 completed (curricular gap size quotable)

> Disparities between what computing curricula teach and what employers demand are widely
> reported, yet studies that measure both sides at scale remain limited. We compare a
> 1.35-million-posting LinkedIn corpus — a single scrape family — against an
> employer-derived reference profile of 1,167 job postings across five occupational
> categories. Analyses run on a 519,814-posting nested subset of that corpus, and both gap
> indices are re-checked on a 1.29-million-posting superset from the same family; a
> posting-level check finds no near-duplicate postings between the reference profile and the
> market corpus (title--skill Jaccard $\geq$ 0.9). N-gram skill extraction over an eight-category taxonomy is combined with
> Sentence-BERT alignment at four cosine thresholds (τ ∈ {0.4, 0.5, 0.6, 0.7}; 1,000-fold
> bootstrap intervals). Exact string matching yields a Skill Gap Index (SGI) of 52.0%;
> semantic alignment reduces this by 20 percentage points to 32.0% at τ = 0.5 (95% CI
> [23.0%, 41.0%]). Against the measured curricula the semantic SGI is
> [CURR02_SGI_SEMANTIC]% (lexical [CURR02_SGI_LEXICAL]%). Reference-profile deficits
> concentrate in Cloud Infrastructure (2.45 pp lexical, 0.94 pp semantic) and Programming
> & Development (1.69 pp lexical), while soft-skill requirements are fully covered by the
> profile. The matcher agrees with published expert ESCO mappings at κ = 0.737 (precision
> 91.9%, recall 75.7%), though the gold set is skewed toward software-development
> mentions; the size of the lexical-to-semantic reduction is consistent with vocabulary
> divergence accounting for part of the gap.

~245 words. Fill-ins: `CURR02_SGI_SEMANTIC`, `CURR02_SGI_LEXICAL` (plus the corpus size
if you want it in the sentence).

---

## v4b — CURR02 not completed or waived (no curricular gap size claimed)

> Disparities between what computing curricula teach and what employers demand are widely
> reported, yet studies that measure both sides at scale remain limited. We compare a
> 1.35-million-posting LinkedIn corpus — a single scrape family — against an
> employer-derived reference profile of 1,167 job postings across five occupational
> categories. Analyses run on a 519,814-posting nested subset of that corpus, and both gap
> indices are re-checked on a 1.29-million-posting superset from the same family; a
> posting-level check finds no near-duplicate postings between the reference profile and the
> market corpus (title--skill Jaccard $\geq$ 0.9). N-gram skill extraction over an eight-category taxonomy is combined with
> Sentence-BERT alignment at four cosine thresholds (τ ∈ {0.4, 0.5, 0.6, 0.7}; 1,000-fold
> bootstrap intervals). Exact string matching yields a Skill Gap Index (SGI) of 52.0%;
> semantic alignment reduces this by 20 percentage points to 32.0% at τ = 0.5 (95% CI
> [23.0%, 41.0%]). The profile covers 30.4% of the CS2023 curricular Body of Knowledge by
> embedding coverage — a computational anchor, not a human curriculum audit — so no
> curricular gap size is claimed. Reference-profile deficits concentrate in Cloud
> Infrastructure (2.45 pp lexical, 0.94 pp semantic) and Programming & Development (1.69
> pp lexical), while soft-skill requirements are fully covered by the profile. The matcher
> agrees with published expert ESCO mappings at κ = 0.737 (precision 91.9%, recall 75.7%),
> though the gold set is skewed toward software-development mentions; the size of the
> lexical-to-semantic reduction is consistent with vocabulary divergence accounting for
> part of the gap.

~250 words. No fill-ins; apply-ready once ruled on.

---

## What changed vs. v3

| v3 | v4 |
|---|---|
| "15 open datasets (2.12M unique records…)" | "a 1.35-million-posting LinkedIn corpus — a single scrape family" |
| corpus/provenance described at dataset level | nested 519,814 subset + 1.29M same-family superset named explicitly |
| independence not stated | "a posting-level check finds no near-duplicate postings between profile and market (title--skill Jaccard >= 0.9)" (step 1) |
| "academic–industry alignment" framing | "what computing curricula teach and what employers demand" |
| "modular technical coursework…" recommendation | **removed entirely** (per instruction) |
| "Soft-skill requirements are fully covered by the reference profile" kept but Cloud/Programming implied curricular | all three explicitly labelled **reference-profile deficits** |
