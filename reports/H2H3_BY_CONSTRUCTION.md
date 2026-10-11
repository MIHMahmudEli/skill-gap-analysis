# H2/H3 by Construction — Code Check (Q1 Revision — Step 3)

Date: 2026-10-12 · Branch: `q1-revision` · Question: does the semantic matcher count exact string matches as matches (cosine 1.0 ≥ τ), making semantic coverage ≥ lexical coverage **by construction**?

## 1. Code evidence

**Lexical matcher** (`experiments/exp_scripts/sens01_sgi_sensitivity.py`, `lexical_coverages`, lines 245–259; same design in `align01_lexical.py`): coverage = exact skill-**string** intersection between the market top-K profile and the academic top-P profile (`acd_sets[k].intersection(m)` on normalized strings).

**Semantic matcher** (same file, lines 376–418; same design in `align02_semantic.py` lines 92–107):

- Line 382–384: embeddings are keyed by the skill **string** — `if s not in str2row: str2row[s] = len(all_strings)` — so *identical strings share one embedding row* in both profiles.
- Lines 386–388: `emb = model.encode(...)` then L2-normalisation.
- Lines 411–417: `S = M @ A.T` (cosine matrix); a market skill is covered at τ iff `S[:k,:k].max(axis=1) >= t`.
- `align02_semantic.py` lines 92–107: `sim = cosine_similarity(market_emb, academic_emb); max_sims = np.max(sim, axis=1); covered = max_sims >= tau`.

**Containment:** a market skill that exactly string-matches an academic skill maps to the *same* embedding row on both sides; a unit vector's cosine with itself is 1.0 (up to float rounding ≈1e-7), which satisfies `>= t` for every τ in the grid (τ ≤ 0.7). Therefore

```
lexically covered ⊆ semantically covered   at every (K, P, τ)
⇒ SGI_semantic(τ) ≤ SGI_lexical           at every grid cell, by construction.
```

The lexical-above-semantic **ordering is not an empirical hypothesis** — it is guaranteed by the matcher definitions. (H3's original "preserve the lexical > semantic ordering" wording therefore had an empty test; it was removed from the manuscript in Step 1 and is replaced here.)

## 2. Numerical confirmation (committed artifacts)

`results/SENS01_sgi_sensitivity/table_sensitivity_grid.csv`, all 160 paired (corpus, K, P, τ) cells:

- violations of `SGI_semantic ≤ SGI_lexical`: **0**
- minimum paired lexical−semantic margin: **0.04** (at τ = 0.7; margins 0.32 / 0.16 / 0.10 / 0.04 at τ = 0.4 / 0.5 / 0.6 / 0.7 — consistent with `reports/sens01_paired_h3_test.csv`)

The same containment holds in ALIGN01/02/03/04 (identical matcher design), so the observed ordering in every one of those experiments carries no independent evidential weight; what carries evidential weight is the **magnitude** of the reduction and the **validity** of the added matches.

## 3. Reframing

**H2 (was: "semantic must yield systematically smaller gap estimates"; ordering) → magnitude + validity:**

> If a share of the reported gap is vocabulary mismatch rather than absent competence, dense semantic matching should remove a substantial share of the lexically measured gap, and the matches it adds beyond exact string matching should be predominantly valid. Because every exact string match is also a cosine match at τ ≤ 0.7, the *direction* of the change is guaranteed by construction; the hypotheses concern the *magnitude* of the reduction (with bootstrap confidence intervals) and the validity of the added matches. Tests: ALIGN01 vs. ALIGN02 (magnitude: 52%→32% [0.23, 0.41] at τ = 0.5); ALIGN04 (nested superset) and CURR01 (a third vocabulary) for the same question; VALID01 (expert gold) for validity of the added matches.

**H3 (was: "remain strictly positive and preserve ordering on an independent corpus"; then Step-1 nested-superset positivity) → positivity + magnitude persistence + validity:**

> If the Skill Gap Index measures a property of the profile–market pair rather than of one sample of it, both variants of SGI should remain strictly positive and the magnitude of the semantic reduction should persist when the market sample is extended from the 519K-posting primary corpus to a nested superset of the same posting-scrape family. Test: ALIGN04 (LinkedIn nested superset, N = 1.29M postings).

Supporting validity numbers (VALID01, expert SkillSpan→ESCO gold, 2,907 pairs, `results/VALID01_esco_gold/metrics.json`):

| Matcher | precision | recall | κ |
|---|---|---|---|
| lexical exact | 1.000 | 0.094 | 0.112 |
| SBERT τ = 0.4 | 0.861 | 0.885 | 0.790 |
| SBERT τ = 0.5 | 0.919 | 0.757 | 0.737 |
| SBERT τ = 0.6 | 0.957 | 0.589 | 0.614 |
| SBERT τ = 0.7 | 0.985 | 0.394 | 0.436 |

The additional matches admitted by semantic alignment (recall 0.39–0.88 beyond exact's 0.094) are **86–98% valid** at every τ — the extra coverage is predominantly genuine, which is the substantive content the ordering claim had been standing in for.

## 4. Edits made in this step

1. `paper/main.tex` H2 (terminology-divergence hypothesis): rewritten as magnitude + validity; the by-construction status of the direction is stated explicitly; tests extended to VALID01 for added-match validity.
2. `paper/main.tex` H3 (instrument robustness): "remain strictly positive" → "remain strictly positive **and the magnitude of the semantic reduction should persist**" under the nested-superset extension (positivity alone is weak; the reduction magnitude is the registered quantity).
3. `reports/SENS01_FOLLOWUP.md` §A3: the tau-specific ordering draft is superseded by the reframed H3 above (ordering recorded as trivially true; margin table kept as a sanity check).
4. `reports/Q1_REVISION_PLAN.md`: status lines updated to record the by-construction finding as the governing interpretation.

No numbers were added to the manuscript beyond quantities already published there or in committed artifacts; the 52%→32% figure is the abstract's own headline and VALID01's precision values are quoted in the reframing reports, not (yet) in the manuscript.
