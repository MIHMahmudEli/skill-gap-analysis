# ALIGN06 pre-registration — O\*NET × BLS OEWS employment-weighted tech-skill demand profile as an independent market side

**Status:** PRE-REGISTERED, NOT RUN. **No data downloaded, no analysis run, no
registry entry created** by this commit. Written 2026-10-12 per the author's
third Q1-revision batch (step 5) and the independent-source follow-up
(`reports/INDEPENDENT_SOURCES.md`, rows A1 and C1). Amendments after this commit
must be appended as dated, reasoned amendment blocks — never by silent edit.
Every parameter below is fixed *before* any O\*NET or OEWS file exists on disk.

## 1. Question

Does the headline alignment result — lexical SGI 0.52 → semantic SGI 0.32 at
τ = 0.5 (ALIGN01/02; `results/ALIGN01_lexical_bootstrap/metrics.json`,
`results/ALIGN02_semantic_sbert/metrics.json`) — persist when the **market
side** is rebuilt from a source that shares *no collection mechanism* with the
LinkedIn scrape family?

ALIGN06 replaces posting counts with an **occupational technology-skill demand
profile from the O\*NET Database, weighted by BLS OEWS employment**. O\*NET is
an expert/national occupational survey (US DOL/ETA); OEWS is an establishment
survey (US BLS). Neither touches LinkedIn, Kaggle scrapes, or the HF Skill Gap
pair, all of which are nested in one scrape family (`datasets/OVERLAP_AUDIT.csv`,
`reports/PROVENANCE_AUDIT.md` §D). This is the optional independent-source
selection described in `reports/INDEPENDENT_SOURCES.md` §A1 + §C1.

## 2. Non-circularity firewall (binding)

1. **No posting row enters profile construction.** The market side is built
   only from the two files pinned in §3. Postings may be read *only* by the §6.1
   instrument control (which re-runs an already-published anchor) and by the
   descriptive cross-source comparison in §6.4, neither of which can change the
   O\*NET profile.
2. **The measurement instrument is imported, not rewritten.** Academic
   reference profile (1,167 posting-derived rows, top-K), the eight-category
   skill taxonomy, the lexical matcher, the semantic matcher
   (all-MiniLM-L6-v2, cosine ≥ τ), and the SGI definition (`SGI = 1 − coverage`)
   come from the ALIGN01/02/SENS01 code path unmodified. ALIGN06 adds exactly
   one new function: build a market profile from O\*NET + OEWS instead of from
   postings.
3. **The taxonomy never filters the profile.** The eight categories are used
   only for the secondary category-level report (§6.3), exactly as ALIGN03 uses
   them; no skill is added, dropped, or re-weighted because of its category.
4. **No result-dependent choice.** Release, table, string field, weighting,
   stratum, grid, seed, and CIs are all fixed here. Any change is a dated
   amendment made *before* the corresponding computation, and is listed in §11.
5. The existing labelling gates (ALIGN05, CURR02) are unaffected: ALIGN06 reads
   no labelling file and fills none.

## 3. Data — exact files (nothing fetched at prereg time)

**Source A — O\*NET Database, release `db_30_0` (O\*NET 30.0, 2025), text-file
distribution:** `https://www.onetcenter.org/dl_files/database/db_30_0_text.zip`.
Tables used (exact file names inside the archive):

| File | O\*NET table | Role |
|---|---|---|
| `Technology Skills.txt` | 2.B.1.a Technology Skills | **primary** occupation × tool/technology rows (`O*NET-SOC Code`, `Commodity Code`, `Commodity Title`, `Example`, `Hot Technology`) |
| `Occupation Data.txt` | Occupation Data | occupation frame (`O*NET-SOC Code`, `Title`) |
| `Skills.txt` | 2.A.3.a Skills | secondary weighting variant only (§4.5) |
| `Knowledge.txt`, `Abilities.txt` | 2.A.2.a / 2.A.1.a | **not used** — recorded for the audit trail |

*Pinning rule:* `db_30_0` is the release this prereg is written against. At
fetch time the release actually downloaded is verified against that name; if
`db_30_0` is unavailable or has been superseded, **stop and append a dated
amendment (§11) naming the release before downloading**, then record the
release string and archive SHA-256 in `metrics.json`.

**Source B — BLS OEWS national estimates, May 2025 reference period:**
archive `https://www.bls.gov/oes/special-requests/oesm25nat.zip` (national
estimates workbook inside; the inner workbook filename is recorded in
`metrics.json` at fetch time together with the archive SHA-256). Fields used:
`OCC_CODE` (SOC 2018), `OCC_TITLE`, `TOT_EMP`. Suppressed / not-disclosed
employment cells are treated as missing (§4.2), never as zero-imputed without
reporting. *Pinning rule:* as above — if the May 2025 file is not published at
fetch time, the latest published May reference period is adopted by a dated
amendment **before** download.

**Storage and accounting (unchanged project hygiene):** raw archives are kept
outside git (git-ignored) with SHA-256 in `metrics.json`; derived tables live
under `datasets/onet/` (also ignored unless explicitly whitelisted); a license
snapshot per source goes to `datasets/curriculum/license_snapshots/`; a
manifest entry and a `datasets/OVERLAP_AUDIT.csv` row are added, per
`reports/INDEPENDENT_SOURCES.md` §4. **Section 9 must be signed by the author
before any download happens.**

## 4. Profile construction (fixed)

### 4.1 Occupation frame and strata

- **Frame:** distinct `O*NET-SOC Code` in `Occupation Data.txt`, restricted to
  occupations with ≥ 1 row in `Technology Skills.txt` and a matched,
  non-suppressed OEWS `TOT_EMP`.
- **Primary stratum: economy-wide.** The headline SGI's posting side is
  economy-wide (ALIGN01/02/03), so the independent market side must be
  economy-wide to be an apples-to-apples level comparison. Every occupation in
  the frame enters.
- **Secondary stratum (never headline):** computing/IT occupations only — the
  16 SOC 2018 detailed codes frozen in `experiments/ALIGN05_PREREG.md` §4
  (15-12xx computer occupations, 15-2051, 11-3021). Reused verbatim; no new
  code list is authored here.

### 4.2 Employment weight and code crosswalk

`w(o) = TOT_EMP(o)` from the OEWS national file. Crosswalk: truncate the
O\*NET-SOC code to its SOC 2018 six-digit base (`15-1252.00` / `15-1252.01` →
`15-1252`) and join on `OCC_CODE`. Occupations with no OEWS line (suppressed,
military, or non-SOC entries) are **dropped, with the count and the list of
dropped codes reported** in `metrics.json` — never silently zero-weighted.
Employment shares are reported alongside absolute weights.

### 4.3 Skill string normalization (fixed before fetch)

Primary string field = `Example` (the concrete product/technology name), with
fallback to `Commodity Title` when `Example` is empty. Normalization: Unicode
NFKC → case-fold → collapse internal whitespace → strip surrounding
punctuation and trademark markers. Rows are deduplicated on
`(occupation, normalized skill)`. Deterministic ordering: rank by descending
weight, ties broken by ascending normalized string (no first-seen tie-breaking,
because the source file order is not a frequency order).

### 4.4 Demand weight

`D(s) = Σ_{o : s ∈ Tech(o)} w(o)` — the employment mass of occupations that
list skill `s`. Demand share for reporting = `D(s) / Σ_o w(o)` at occupation
level, and `D(s) / Σ_{s'} D(s')` at skill level (both reported; the denominators
are different quantities and are labelled as such).

### 4.5 Fixed robustness variants (reported, never headline)

1. `Commodity Title` strings instead of `Example`;
2. unweighted occupation counts (`w(o) ≡ 1`) — isolates the OEWS weighting;
3. the computing/IT stratum of §4.1;
4. importance-weighted variant using `Skills.txt` importance (Scale ID `IM`)
   multiplied into `w(o)` for O\*NET skill statements rather than technologies —
   reported in the appendix table only, since its vocabulary is statements, not
   tool names.

## 5. Grid (identical shape to SENS01)

```
K      in {50, 100, 200, 500}   profile size: O*NET top-K vs academic top-K (symmetric,
                                ALIGN01/02 definition)
P      in {100, 250, 500, 1000} occupations sampled from the frame to build the profile
                                (plus a P = all anchor row set over the full frame)
tau    in {0.4, 0.5, 0.6, 0.7}  semantic threshold (semantic rows only)
match  in {lexical, semantic}
stratum in {economy-wide (primary), computing/IT (secondary), commodity-title,
            unweighted, importance-weighted}     # §4.5 variants
seed   42 ;  B_SKILL = 1000 ;  B_OCC = 500
```

`P` is the O\*NET analogue of SENS01's market-posting sample size: the unit
sampled is an *occupation*, not a posting, because the source has no postings.
Academic side is always the full 1,167-row corpus (never sub-sampled), as in
SENS01.

**Point estimate per cell:** one seeded draw of `P` occupations, SRS without
replacement from the deterministically sorted frame, seed `42 + 10 × P_index`
(the SENS01 convention with the corpus index dropped — there is one source).
**Two CIs per cell, the SENS01 "dual bootstrap":**

- `CI_skill` — resample of the K coverage indicators (same method as the
  published ALIGN01/02/04 CIs), B = 1000, seed 42;
- `CI_occ` — resample of the P occupations *and* all 1,167 academic rows,
  rebuilding the O\*NET top-K profile per replicate, B = 500, seed 42
  (profile-estimation uncertainty: "which occupations did you happen to
  observe?"). NaN at `P = all` rows, exactly as `CI_post` is NaN there in
  SENS01.

## 6. Instrument control and outputs

### 6.1 Control (blocking — no O\*NET cell is reported until it passes)

The harness must import SENS01's matcher/profile code and reproduce its
already-published control cells through that same path: HF postings,
`P = all`, lexical K = 100 → SGI **0.52** (exact), semantic K = 100, τ = 0.5 →
SGI **0.32** (± 0.02 device tolerance, per SENS01's stated tolerance). A
control failure fails the run; no result is written. This uses only the local
HF corpus that is already on disk — it is a code-path check, not new data
acquisition.

### 6.2 Primary output — SGI grid

Per cell: SGI (`1 − coverage`), coverage, `CI_skill`, `CI_occ`, stratum sizes,
frame/draw sizes. Saved as
`results/ALIGN06_onet_demand_profile/table_sgi_onet_grid.csv`.

### 6.3 Secondary output — taxonomy category report

ALIGN03's category definitions with the posting unit replaced by employment
weight, explicitly relabelled: for category `c`,
`demand_c = 100 · Σ_{o : Tech(o) ∩ S_c ≠ ∅} w(o) / Σ_o w(o)`; coverage and
deficit per ALIGN03's formulas with the academic top-K (lexical) and `A_τ`
(semantic) covering sets; deficit in pp with a `CI_occ` bootstrap (B = 1000,
seed 42) at each τ. Saved as `table_category_gap_onet.csv`. **Never compared
pp-to-pp with posting-derived deficits** without the estimand caveat of §7.1.

### 6.4 Descriptive cross-source comparison

At each K: top-K lexical overlap (Jaccard) and Spearman ρ of the weight vectors
between the O\*NET-weighted profile and the HF postings top-K (and, where the
artifact exists, the LinkedIn top-K). Descriptive only; cannot select any
parameter.

### 6.5 `metrics.json`

Release strings + archive SHA-256 for both sources, inner OEWS workbook
filename, license snapshot paths, frame size, dropped-occupation count and
codes, stratum sizes, normalization statistics (rows before/after dedup,
`Example`-vs-`Commodity Title` fallback counts), vocabulary overlap with the
posting corpus, grid, seeds, control-cell results, and wall-clock.

## 7. Reporting rules and non-goals (binding)

1. **Level comparison, not replacement.** The published headline (52% → 32% @
   τ 0.5, bracket ranges [0.52, 0.74] / [0.26, 0.42]) is unchanged by this
   experiment. ALIGN06 adds an independent-source robustness statement; no
   manuscript headline number is edited from ALIGN06 output.
2. **Estimand caveat (must appear wherever the numbers appear):** the market
   side is employment-weighted occupations from a US expert taxonomy, not
   posting counts from a global scrape — equal SGI levels would be convergence
   across two different estimands, and different levels are not by themselves
   evidence against the posting-based result.
3. **Registered contrasts only:** (a) economy-wide, `P = all`, K = 100 lexical
   SGI vs 0.52; (b) economy-wide, `P = all`, K = 100, τ = 0.5 semantic SGI vs
   0.32; (c) *persistence* claim, permitted only if the `CI_skill` lower bound
   of cell (b) is > 0. The rest of the grid is sensitivity, reported in full —
   no cell is dropped, promoted, or highlighted on the basis of its value.
4. **No re-tuning** of taxonomy, academic covering set, τ grid, embedding
   model, or matchers. No per-cell significance fishing. No claim that O\*NET
   "validates" LinkedIn noise, and no claim of independence beyond the
   documented non-overlap of the sources.
5. **Out of scope:** downloads of any job-posting corpus (the USAJOBS pilot in
   §10 is a separate, separately authorized act); ESCO/Wikidata sources (ESCO
   already anchors VALID01); BLS Employment Projections; any change to
   ALIGN03's taxonomy or to the published domain-gap deficits.

## 8. Registration, seed, artifacts

- **Registered in `results/registry.json` before execution** (entry
  `ALIGN06_onet_demand_profile`, `run_mode` local, `seed` 42, dependencies:
  ALIGN01/ALIGN02 artifacts + this prereg; status flips to COMPLETED only with
  artifacts on disk). Tests and `experiments/verify.py` treat an unregistered
  ALIGN06 run as failure.
- Seed 42 for: every occupation draw and every bootstrap (§5).
- Artifacts: `results/ALIGN06_onet_demand_profile/{metrics.json,
  table_sgi_onet_grid.csv, table_category_gap_onet.csv,
  table_onet_profile_top.csv, figure optionally}`; verification extension in
  `experiments/verify.py`.
- Manuscript edit scope if adopted: one independent-source robustness paragraph
  (limitations / reproducibility) plus, at most, an appendix table. Any edit to
  the abstract or title requires separate author approval and is **not**
  covered by this prereg.

## 9. License and provenance checklist — **author sign-off required before any download**

Licenses below are recorded from established knowledge and marked *re-verify*;
the author initials and dates each row after opening the linked page. An
unsigned §9 blocks all ALIGN06 downloads.

| # | Source | License as understood (re-verify) | Page to open | Snapshot file | Author ✅ / date |
|---|---|---|---|---|---|
| 1 | O\*NET Database (`db_30_0`) | US DOL work, public domain / "may be used without restriction"; citation and citation-of-derivative expectations to confirm | `onetcenter.org/database.html` + `onetcenter.org/dl_files/database/db_30_0_text.zip` | `datasets/curriculum/license_snapshots/onet_db_30_0.txt` | ☐ ____ |
| 2 | BLS OEWS (May 2025 national) | US BLS work, public domain (17 U.S.C. §105); acknowledged-use / "source: BLS OEWS" notice to confirm | `bls.gov/oes/copyright.htm` + `bls.gov/oes/oes_stat.htm` | `datasets/curriculum/license_snapshots/bls_oes_m2025.txt` | ☐ ____ |
| 3 | USAJOBS content + API (only if §10 authorized) | OPM content public domain (17 U.S.C. §105); **API terms of use apply** — rate limits, User-Agent/contact, caching and redistribution limits to confirm | `developer.usajobs.gov` (API guide + terms) and `usajobs.gov/Help/legal` | `datasets/curriculum/license_snapshots/usajobs_api_terms.txt` | ☐ ____ |

Also recorded at fetch time: manifest entry, `datasets/OVERLAP_AUDIT.csv` row
(new-source de-dup accounting), and the SHA-256 of each archive (§3, §6.5).

## 10. Optional pilot — USAJOBS (separate authorization; **not** part of the ALIGN06 primary run)

Purpose: one posting feed with a genuinely different collection mechanism (US
federal vacancy announcements), as `reports/INDEPENDENT_SOURCES.md` B1.

**Preconditions (all binding):** §9 row 3 signed, *and* a dated author go-ahead
in §11. Without both, USAJOBS is not queried at any point.

**Frozen design if authorized:**

1. **Query:** keyword OR over the 16 computing/IT O\*NET-SOC occupation titles
   frozen in `ALIGN05_PREREG.md` §4, United States, nationwide, posted-date
   window fixed to the most recent 12 months at query time. The keyword list is
   **never** edited after the first response is inspected; there is exactly one
   query formulation, recorded verbatim in `metrics.json`.
2. **Hard limits:** ≤ **10,000** announcements retrieved in **one** session;
   ≤ 3 requests/second and full compliance with rate-limit headers and the
   required identifying User-Agent; only the fields actually needed retained
   (position title, agency, location, posted date, requirements/qualification
   text). Raw payloads are stored outside git; a SHA-256 of the raw archive is
   recorded; **no redistribution of raw payloads** until §9 row 3 confirms it.
3. **Feasibility gate (pre-registered):** in the first ≤ 200 announcements,
   ≥ 20% must contain ≥ 1 parseable skill token under the ALIGN01 tokenizer.
   Below that, record `pilot_feasible: false` with the observed share and
   **stop** — no SGI, no taxonomy report, no manuscript text from this pilot.
4. **Analysis if feasible:** identical taxonomy/SGI definitions and matchers;
   grid = K ∈ {50, 100, 200, 500} × τ ∈ {0.4, 0.5, 0.6, 0.7}, `P = all`
   announcements (no `P` subsample grid — there is exactly one corpus);
   `CI_skill` bootstrap B = 1000, seed 42. Reported as a **pilot** with its
   federal-workforce scope caveat; never headline, never merged into the O\*NET
   table of §6.2.

## 11. Amendments (dated blocks; appended, never silent)

*(none yet — this file is the original registration, 2026-10-12)*
