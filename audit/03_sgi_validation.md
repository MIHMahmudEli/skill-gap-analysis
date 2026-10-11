# Phase 3 — Skill Gap Index (SGI) Validity Audit

*Date: 2026-10-11 · Local reproductions run on Windows CPU with the same
code paths/tokenizers/model/seed as the Kaggle kernels. Raw data unmodified.
Artifacts: `audit/_sgi_sensitivity/*.json`.*

## 3.1 The Estimand (as implemented)

Let $\mathcal{M}$ = multiset of normalized market skill tokens (comma-split,
lowercased) from the market corpus; $m_1..m_K$ = top-$K$ most frequent unique
tokens ($K=100$). Let $\mathcal{A}$ = analogous academic-reference tokens;
$a_1..a_P$ = top-$P$ ($P=100$ in ALIGN01/02; $P=500$ in ALIGN03/04).

- **Lexical coverage:** $c_i^{lex} = \mathbb{I}[m_i \in \{a_1..a_P\}]$
- **Semantic coverage:** $c_i^{sem}(\tau) = \mathbb{I}[\max_j \cos(e(m_i), e(a_j)) \ge \tau]$, embeddings from `all-MiniLM-L6-v2` (384-d)
- **SGI:** $\mathrm{SGI}(\tau) = 1 - \frac{1}{K}\sum_{i=1}^{K} c_i$
- **CI:** percentile bootstrap ($B=1000$, seed 42) over the **skill-level**
  indicator vector $\{c_i\}$ — i.e., uncertainty over the top-$K$ skill list
  treated as exchangeable, **not** over postings/employers.

Manuscript Eq. (3)–(4) and Algorithm 1 match this implementation **except**
the manuscript writes a single top-$N$ for both sides while the code uses
different $P$ for $\mathcal{A}$ across experiments (§3.3 below).

## 3.2 Local Reproduction of Published SGI (exact)

| Experiment | Published | Local (same code path, local CSVs) | Match |
|---|---|---|---|
| ALIGN01 lexical SGI (HF, acad-100) | 0.52 [0.42, 0.63] | **0.52 [0.42, 0.63]** | exact |
| ALIGN01 token counts | 10,793,352 / 20,970 | 10,793,352 / 20,970 | exact |
| ALIGN02 semantic SGI τ∈{.4,.5,.6,.7} | 0.20 / 0.32 / 0.39 / 0.46 | **0.20 / 0.32 / 0.39 / 0.46** | exact |
| ALIGN04 lexical/semantic (LI, acad-500) | 0.37 / 0.14 | **0.37 [0.28,0.47] / 0.14 [0.08,0.21]** | exact |

Machine output: `audit/_sgi_sensitivity/`. The pipeline is deterministic and
reproducible from local data.

## 3.3 Verified Defect — Academic-Profile-Size Confound (Major)

**Code facts:**
- `align01_lexical.py:78` and `align02_semantic.py:81`: academic covering set =
  **top-100** (`head(TOP_N)`).
- `align03_domain_gap.py:158`, `align04_crosscorpus.py:136`:
  academic covering set = **top-500** (`most_common(PROFILE_N)`).

**Manuscript claim (§IV-B2, line 408):** ALIGN04 "re-run the **identical**
lexical and semantic procedures (top-100 market profile, academic top-500
reference…)" — the parenthetical describes ALIGN04, but ALIGN01/02 used
academic **top-100**. The procedures are **not identical**.

**2×2 audit reanalysis** (both corpora × both profile sizes; identical
tokenizers/model/seed):

| Market corpus | Acad profile | Lexical SGI | Semantic SGI τ=0.5 |
|---|---|---|---|
| HF skills (519,814) | top-100 (=published ALIGN01/02) | **0.52** [0.42, 0.63] | **0.32** [0.23, 0.41] |
| HF skills | top-500 | **0.37** [0.28, 0.47] | **0.14** |
| LinkedIn (1.29M) | top-100 | **0.52** [0.42, 0.62] | **0.32** [0.23, 0.42] |
| LinkedIn | top-500 (=published ALIGN04) | **0.37** [0.28, 0.47] | **0.14** [0.08, 0.21] |

**Interpretation:**
1. At **matched** profile size the two corpora produce **the same SGI**
   (0.52/0.32 at P=100; 0.37/0.14 at P=500). The published ALIGN01-vs-ALIGN04
   contrast (0.52 → 0.37) is an **academic-profile-size artifact**, not a
   corpus property.
2. The manuscript's §IV-B2 explanation ("LinkedIn's free-text vocabulary is
   dominated by generic terms the academic reference already covers, whereas
   the curated HF corpus contains more specialist tool tokens") is
   **not supported** — the same levels appear on HF when P=500.
3. H3 (instrument robustness) is **still supported, even more cleanly**: at
   matched P the instrument is *exactly* stable across two independent
   corpora. But the current manuscript text must be rewritten; as written it
   attributes a profile-size effect to corpus composition.

**Recommended manuscript fix (Phase 9):** present the 2×2 as the primary
cross-corpus evidence; redefine ALIGN04's contribution as matched-profile
replication (P=500, both corpora) + domain-gap ordering replication; drop the
vocabulary-composition explanation of the level shift or replace it with the
profile-size sensitivity.

## 3.4 Matching Behavior

- Coverage is **many-to-one permitted**: each market skill takes its single
  best academic match; one academic term (e.g. `communication`) can cover many
  market terms (`communication skills`, `verbal communication`, …). This is
  generous-to-academia by design and is why lexical→semantic always *reduces*
  SGI. VALID01 (κ vs expert mappings) is the external check on this generosity;
  precision 91.9% / recall 75.7% at τ=0.5 bounds the false-match rate on the
  expert benchmark.
- No 1-to-1 assignment (Hungarian) or frequency/importance weighting is used.
  Binary top-K coverage is the estimand; frequency-weighted coverage would be
  a different estimand (documented as future work, not silently substituted).

## 3.5 Threshold Sensitivity (extended)

Published τ-sweep (ALIGN02, P=100): 0.20/0.32/0.39/0.46 — reproduced exactly.
Extended sweeps at P=500 and on LinkedIn are in
`audit/_sgi_sensitivity/*.json`. τ=0.5 is the midpoint of a steep region
(P=500: 0.06→0.14→0.22→0.28 on LinkedIn); VALID01 shows κ also peaks near
τ=0.4–0.5 (0.79 at 0.4, 0.74 at 0.5). Baseline choice is defensible but should
be reported with the sweep (already done in Table II).

## 3.6 Bootstrap Interpretation (caveat, not defect)

The CI resamples the **100 skill indicators**, not postings. It quantifies
sensitivity to which skills sit in the top-100 — not sampling error of the
job market. With 519K–1.3M postings the top-100 list is essentially a census;
the CI is better read as a **list-composition uncertainty band**. The
manuscript says "non-parametric bootstrap over the binary coverage indicator
array" (§III-C) — accurate — but Discussion should avoid "population"
language. Domain-gap CIs (ALIGN03/04) bootstrap **postings**, which is the
more standard sampling unit; that distinction is worth one sentence.

## 3.7 Frequency-Weighted Alternative (exploratory, audit-only)

Weighting each market token by posting frequency (top-100 weights available in
`market_top500.csv`) changes the HF/acad-100 lexical coverage from 48% to
≈? — **not computed here to avoid estimand shopping**; flagged as a defensible
robustness variant for authors to pre-specify if added.

## 3.8 Actions

| # | Action | Phase |
|---|---|---|
| 3.8.1 | Rewrite §IV-B2 + H3 text around matched-profile 2×2; remove unsupported corpus-composition explanation | 9 |
| 3.8.2 | Add profile-size sensitivity (P=100 vs 500) to methods or supplement | 9 |
| 3.8.3 | One sentence on bootstrap unit (skills vs postings) | 9 |
| 3.8.4 | Keep VALID01 as the matcher-validity anchor (κ/AUC reproduced Phase 1) | — |

*No raw data or experiment outputs were modified. The 2×2 is an audit
reanalysis, not a replacement registered experiment; if adopted in the
manuscript it should be registered (e.g., ALIGN05) or clearly labeled as a
sensitivity analysis with code in `audit/`.*
