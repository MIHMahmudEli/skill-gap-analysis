# Q1 REVISION PLAN

*Date: 2026-10-11 · Branch: `q1-revision` (from `main` @ `9ca13e2` = origin/main) ·
Manuscript: `paper/main.tex` / `paper/main.pdf`*

---

## Phase 0 — Baseline (complete)

| Gate | Result |
|---|---|
| `python -m pytest tests -q` | **13 passed** |
| `python audit/verify_claims.py` | **103/103 matched, 0 mismatched** |
| `python experiments/verify.py` | `all_verified: true` (12/12) |
| pdflatex + bibtex + pdflatex ×2 | **16 pp; 0 errors / 0 undefined / 0 overfull** |
| Working tree | Clean; `main` in sync with `origin/main` @ `9ca13e2` |
| Rough body word count | ~5.7k words (LaTeX-stripped approximation) |
| Registered experiments | 12, all `USED_IN_MANUSCRIPT` |

**Baseline state (10 lines):**
1. Scientific blockers from the prior audit (H6 RD sign, corpus counts, H5 construct misattribution, proxy disclosure, CS2023 characterization) are resolved and pushed.
2. Prior verdict: **CONDITIONALLY READY** — remaining gaps were design limitations (proxy profile), venue, proofread.
3. This revision targets the residual design/credibility gaps that keep the paper below confident Q1 standards.
4. Main residual construct gap: academic side is still 1,167 job postings (proxy), not real curricula — Phase 1 will fix or reframe.
5. SGI is still a single headline "52% → 32%" without K/P/τ/posting-bootstrap sensitivity — Phase 2.
6. Domain deficits still mix non-tech occupations into the denominator — Phase 3.
7. Placement/internship section is semi-synthetic and unlinked to the gap measure — Phase 4 (author choice).
8. Anonymization has residual Kaggle/HF/GitHub usernames in paper/README/audit paths — Phase 5.
9. `make_latex.py` still clobbers hand-audited `tab_crosscorpus.tex` (R-11/F-5) — Phase 5.
10. Venue conversion deferred until author picks a journal — Phase 6 STOP.

---

## Phase 1 — Construct validity (complete; CURR02 gated on author labelling)

| ID | Task | Status |
|---|---|---|
| P1-A | **Option A:** build real curriculum corpus (20–50 programs; MIT OCW / open catalogs; `datasets/curriculum/MANIFEST.csv` with URL+license+retrieval date+ToS notes) + experiment **CURR02** (SGI on real curricula vs proxy) | Corpus **DONE** (2026-10-11): 41 units / 799 phrases extracted; primary set 20 courses / 3 institutions / deterministic ≤8-per-institution cap (`datasets/curriculum/PRIMARY_SET.md`); region bar waived to 2 regions by author (protocol §9a; license-blocked third region, manuscript limitation required); human validation samples ready (`extracted/validation_{precision,recall}_100.csv` + `LABELLING_BRIEF.md`) — **CURR02 blocked until author labels or waives** |
| P1-B | **Option B:** reframe as measurement-methods paper; strip curriculum conclusions from title/abstract/intro/conclusion; rewrite RQs | Not chosen (superseded by Option A) |

---

## Phase 2 — SGI sensitivity (SENS01)

| ID | Task | Status |
|---|---|---|
| P2-1 | Experiment **SENS01**: SGI grid K∈{50,100,200,500} × P∈{100,250,500,1000} × τ∈{0.4,0.5,0.6,0.7} × lexical/semantic × HF + LinkedIn; seed 42 | **Done (2026-10-11).** Full run (188 s CPU, 200 grid rows) in `results/SENS01_sgi_sensitivity/`; registry VERIFIED |
| P2-2 | Dual bootstrap: skill-list resample **and** posting resample; report both CIs with interpretation | **Done.** B_SKILL=1000, B_POST=500 per cell; posting CI = joint market-P + academic-1167 resample; NaN posting CI at P=all anchor rows by design (reported, not an error) |
| P2-3 | Heatmap/surface figure + sensitivity table; replace abstract "52%→32%" with range + SENS01 result | Figure + `table_sensitivity_grid.csv` + `table_sensitivity_summary.csv` emitted; **abstract replacement drafted below — awaiting author review**. Figure polish TODO at manuscript time: bottom-row x-labels collide with subplot titles (data are final; layout only) |
| P2-4 | Register in `results/registry.json`; extend `experiments/verify.py` | **Done.** SENS01 entry VERIFIED (run_mode local, seed 42); `verify.py` gained REQUIRED files + sanity checks (grid shape 200, SGI∈[0,1], skill-CI contains point, τ-monotonicity, no smoke runs, HF anchors, ALIGN04 replication, matched-profile manuscript claims). Gates: pytest 13/13, verify_claims 103/103, verify.py 13/13 all_verified |

**Headline ranges (SENS01, both corpora, over the finite-P grid; anchors in
parens):** lexical SGI HF [0.52, 0.73] (anchor 0.52), LinkedIn [0.53, 0.74]
(anchor 0.52); semantic @τ=0.5 HF [0.26, 0.42] (anchor 0.32), LinkedIn
[0.26, 0.38] (anchor 0.32). SGI is strictly positive in all 200 cells
(min 0.094 @ τ=0.4). **Ordering is by construction, not a finding**
(2026-10-12, `reports/H2H3_BY_CONSTRUCTION.md`): every exact string match is
also a cosine-1.0 match at τ ≤ 0.7, so lexical coverage ⊆ semantic coverage at
every cell by the matcher definitions; H2/H3 are reframed as (i) *magnitude*
of the reduction with CIs and (ii) *validity* of the added matches (VALID01
precision 0.86–0.98 at every τ). The paired cell-by-cell test
(`reports/SENS01_FOLLOWUP.md` §A3, `reports/sens01_paired_h3_test.csv`) is
retained only as a sanity check: lexical SGI > semantic SGI at all 160 paired
cells (min margin 0.32/0.16/0.10/0.04 at τ=0.4/0.5/0.6/0.7). The earlier
cross-grid range comparison (which suggested a τ=0.7 exception by comparing
unpaired extrema) remains superseded; magnitude claims stay at the baseline
threshold.

**Finding (2026-10-11, surfaced by SENS01's anchor check):** the published
experiments do not share one definition of the academic reference profile.
ALIGN01/ALIGN02 compare market top-100 against academic **top-100**
(symmetric — the headline "52% → 32%" instrument), but ALIGN04's LinkedIn
nested-superset check compares market top-100 against academic **top-500**
(`most_common(PROFILE_N)` with no `.head(TOP_N)` — asymmetric). Under the
symmetric instrument LinkedIn lexical SGI@K=100 is **0.52**, not the
published 0.37; the 0.37 reproduces exactly only under ALIGN04's asymmetric
definition (coverage 0.63 vs 0.48).

**Resolved by the full run:** the manuscript already acknowledges this — the
"Profile-size sensitivity" paragraph (`paper/main.tex` §Results) claims that
at matched academic covering-set size **both** corpora give 0.52/0.32 (P=100)
and 0.37/0.14 (P=500). What was missing is a registered artifact backing the
full claim: ALIGN04's `table_crosscorpus_sgi.csv` contains only the LinkedIn
P=500 rows. SENS01 closes this:

1. `metrics.json::matched_profile_replication` holds all four cells
   (corpus × {P=100 symmetric, P=500 asymmetric} × {lexical, semantic@0.5});
   both corpora land on **identical** values 0.52/0.32 and 0.37/0.14, exactly
   as line 411 states. The LinkedIn P=500 cells are hard-asserted against the
   published ALIGN04 numbers; all eight cells are recorded as
   `manuscript_claim_checks` (all ok) and `verify.py` fails the gate if any
   is not reproduced, so a manuscript/artifact mismatch forces a correction
   rather than shipping a contradicted number.
2. SENS01's own grid stays symmetric (K vs K, the headline instrument) and
   internally consistent; its LinkedIn column is a fresh
   consistent-instrument result, **not** a failed reproduction of 0.37/0.14.

**Corpus-independence finding (2026-10-11, `reports/SENS01_FOLLOWUP.md` §A2 —
author decision needed):** the HF skill-gap corpus is a **strict subset of the
Kaggle LinkedIn corpus** (all 519,814 `job_link`s present in both; 99.9% of
sampled skill strings byte-identical). The two market top-K profiles are
therefore identical skills at K ≤ 200 (100% shared; 496/500 at K=500), which
is why the matched cells agree exactly. ALIGN04's numbers all stand; the
manuscript's "independent corpus" framing has been **reworded to
nested-superset robustness language** (Step 1, 2026-10-12 — all edits listed
in `reports/PROVENANCE_AUDIT.md` §C; corpus counts recomputed to 2,123,889
unique records and eight feeding sources there too).

**Execution incident (for the record):** the first full run's
`metrics.json`/summary turned out to disagree with its own
`table_sensitivity_grid.csv` (reported hf lexical range [0.42, 0.71] vs the
grid's actual [0.52, 0.73]; a summary anchor of 0.32 at τ=0.4 vs the grid's
0.20). The grid itself was sound (τ-monotone per cell, anchors exact,
bit-identical SGI across four independent runs). The run was discarded before
committing, a **self-consistency guard** was added to
`sens01_sgi_sensitivity.py` (re-reads the written CSVs and asserts the
reported ranges/anchors equal what is on disk), and the experiment was
re-executed from scratch; the committed artifacts pass the guard and an
independent re-derivation of every range and anchor from the grid CSV.

**P2-3 draft — proposed abstract replacement (author review):** the current
abstract reports the point estimate "52.0% → 32.0%"; replace the sentence

> Exact string matching yields an apparent Skill Gap Index (SGI) of 52.0\%.
> Dense vector alignment reduces this estimated gap to 32.0\% at baseline
> threshold $\tau = 0.5$ (95\% bootstrap CI: [23.0\%, 41.0\%]), rising to
> 46.0\% ... ($\tau = 0.7$).

with (draft, revised 2026-10-12 per author checks A2–A4 + determinism + by-construction steps):

> At the headline configuration (market top-$K{=}100$ vs.\ academic covering
> set $P{=}100$), exact string matching yields an apparent Skill Gap Index
> (SGI) of 52.0\%, which dense vector alignment reduces to 32.0\% at baseline
> threshold $\tau = 0.5$ (95\% bootstrap CI: [23.0\%, 41.0\%]); under a
> stricter criterion ($\tau = 0.7$) the gap rises to 46.0\%. A pre-specified
> $(K, P, \tau)$ sensitivity surface over the headline instrument (200 grid
> cells spanning all combinations of profile size, covering-set size, and
> threshold on two posting corpora, the second a nested superset of the
> first) shows these values are not artifacts of one configuration: the
> lexical SGI stays within [0.52, 0.74] and the semantic SGI at
> $\tau = 0.5$ within [0.26, 0.42] across the surface, every cell remains
> strictly positive, and the reduction persists on the nested superset at
> matched academic covering-set size.

Notes for the author (updated 2026-10-12): (a) the τ=0.7 CI sentence can stay
as-is (the anchor 0.46 is confirmed by SENS01's grid); (b) limitations §L693
should gain one clause pointing at SENS01 as the registered sensitivity
artifact; (c) ~~H3 needs "at the baseline threshold"~~ → ~~ordering claim
stands unqualified~~ **superseded twice**: the paired test removed the τ=0.7
caveat, then the by-construction check (2026-10-12,
`reports/H2H3_BY_CONSTRUCTION.md`) showed the ordering is guaranteed by the
matcher definitions (exact match ⇒ cosine 1.0 ≥ τ), so H2/H3 now concern
magnitude-of-reduction + validity of added matches, not ordering; main.tex H2
and H3 were rewritten accordingly in the same pass. Magnitude-separation
claims stay at the baseline threshold (margin narrows 0.32→0.04 as τ:
0.4→0.7). Reframed draft H3 wording in the follow-up report §A3; (d) the
grid is described as **one sensitivity surface**, never as 200 independent
tests — no per-cell significance language anywhere; (e) "independent
corpora" language **removed from main.tex, README, and manifest on
2026-10-12** (Step 1, all 19+3+4 edits listed in
`reports/PROVENANCE_AUDIT.md` §C) — "nested-superset robustness check on one
scrape family"; (f) "pre-specified", not "pre-registered": the surface was
repository-timestamped *after* the headline values were known, so
"pre-specified" is the accurate term; (g) range notation fixed to
[0.52, 0.74] / [0.26, 0.42]; (h) "reproduces identically on the superset
corpus" removed — the surviving claim is persistence of the reduction at
matched covering-set size (the identical matched values themselves stay in
the ALIGN04 body text, where the P-matched design is stated).

**P2-3b draft — proposed abstract corpus-sentence replacement (author review,
2026-10-12):** the current abstract's opening corpus claim

> We examine academic--industry alignment using 15 open datasets (2.12M unique
> records after removing linked-table and nested-corpus duplication) collected
> from LinkedIn, HuggingFace, and public benchmark repositories spanning 2020
> through 2026.

is the last remaining single all-purpose record count in the abstract
(`paper/main.tex` body, contributions, conclusion, Table I, and README were
replaced with the unit-typed breakdown in this step). Replace with (draft):

> We examine academic--industry alignment using 15 open datasets spanning
> 2020 through 2026: 1.35M real web-mined job postings from a single LinkedIn
> scrape family (with a posting-derived academic reference profile of 1,167
> postings from the same family), 316K aggregated title--skill count rows of
> unverifiable provenance, and 458K synthetic benchmark rows (including 421K
> generated student records used only for the methods-audit analyses). All
> gap-measurement results rest on the real posting family alone.

and the methodological clause "(4) 5-fold stratified cross-validation …
accompanied by decision-boundary diagnostics and independent external
validation" should drop "independent" (external cohorts are synthetic
benchmarks of the same generative family — `reports/REAL_VS_SYNTHETIC_
FINDINGS.md` §C). Nothing applied until author approval.

---

## Phase 3 — Domain-gap credibility (ALIGN05)

| ID | Task | Status |
|---|---|---|
| P3-1 | Experiment **ALIGN05**: stratify/filter postings by occupation family (tech vs non-tech); rerun domain deficits on tech-relevant subset | **Pre-registered (2026-10-11).** `experiments/ALIGN05_PREREG.md` committed before any run. Binding constraints: job family from `job_title`/occupation fields only (circularity firewall + taxonomy-intersection check); primary mapping O*NET-SOC major groups 15/17/19 via versioned keyword rule set (license recorded: US DOL public domain); secondary robustness = dataset's own `search_position` field; **blocking validation gate** — author hand-labels a 200-posting title sample (precision & recall ≥ 0.90 to proceed); both full-corpus and tech-only deficits reported, tech-only explicitly larger-by-construction and not the headline; posting-level bootstrap, seed 42, registered in `results/registry.json` before execution |
| P3-2 | Drop or externally anchor Critical/Moderate/Mild labels; report effect sizes + CIs | **Design fixed in prereg §6.** Primary reporting = deficit pp + 95% posting-bootstrap CIs + paired tech-vs-full effect sizes; if labels are retained anywhere they are full-corpus-only under the pre-registered CI-anchored rule |
| P3-3 | Experiment **ALIGN06**: independent market side — O\*NET technology-skills demand profile weighted by BLS OEWS employment, matched with the unchanged taxonomy/SGI definitions over the (K, P, τ) grid; optional USAJOBS pilot | **Pre-registered (2026-10-12), NOT RUN, no downloads.** `experiments/ALIGN06_PREREG.md`. Pinned sources: O\*NET `db_30_0` (`Technology Skills.txt`, `Occupation Data.txt`, `Skills.txt`) + OEWS May 2025 national (`oesm25nat.zip`); economy-wide stratum primary, computing/IT (ALIGN05 §4 codes) secondary; blocking harness control reproduces the published 0.52/0.32 anchors; headline unchanged + estimand caveat; **§9 license checklist must be signed by the author before any download**; USAJOBS is a separately authorized optional pilot with a 10,000-announcement cap and a pre-registered feasibility gate |

---

## Phase 4 — Placement section (STOP for author choice)

| ID | Task | Status |
|---|---|---|
| P4-A | **Option A:** move RQ4/RQ5 + placement models to `paper_placement/`; remove from main paper | **DONE (2026-10-12).** Author rulings D1–D4 executed. `paper_placement/` created: standalone IEEEtran companion (H4–H6/RQ4–RQ5 labels kept as companion-paper hypotheses; benchmark-audit framing; no real-graduate claims). Main paper: RQ4 block + RQ5 remainder removed, geography folded into RQ1 (GEO01), H4–H6 + items trimmed, RQ/hypothesis numbering contiguous (RQ1–RQ3/H1–H3). Five tables git-mv'd; `make_latex.py` split (main vs `TABP`); `verify_claims.py` 2nd TEX handle; ledger `paper` column (78 main / 31 placement / 3 dropped D3 / 1 both). |
| P4-B | **Option B:** keep as clearly labelled "illustrative benchmark audit"; remove real-graduate OR claims; drop synthetic datasets from headline count | **NOT CHOSEN** (superseded by P4-A per author rulings D1–D4). |
| P4-C | Correct headline scale: report only the nine experiment-feeding sources; list the rest in appendix | **DONE (2026-10-12).** Main intro reports seven experiment-feeding sources (count-free where possible; no "twelve" total), RQ1 trends/TRENDS01 retained-unused marking from Step 2; the full 15-source provenance inventory stays in Table I with synthetic flags and is supplemented by `paper_placement/` corpus table. |

---

## Phase 5 — Anonymization & hygiene

| ID | Task | Status |
|---|---|---|
| P5-1 | Grep author-identifying strings (MIHMahmudEli, MoshinAli, studyhub991, nihanshadman, leyamridha, sadmanhasanmiraj, nishat1156, etc.) across paper/README/reports/audit/figures; replace with neutral placeholders; anonymized artifact plan | Pending |
| P5-2 | Move audit AI-process files (adversarial review, executive summary, changelogs) out of public-facing tree into git-ignored `archive/` or archive branch | Pending |
| P5-3 | Multi-account Kaggle statement in paper + ToS flag to author | Pending |
| P5-4 | Fix **R-8** (VALID01 `n_positive_by_type` metadata zeros), **R-11/F-5** (`make_latex.py` stop overwriting `tab_crosscorpus.tex`) | Pending |

---

## Phase 6 — Venue conversion (STOP until author names journal)

| ID | Task | Status |
|---|---|---|
| P6-1 | Ask author for target journal; convert template; meet word/page/abstract limits; draft cover letter + highlights | **BLOCKED — awaiting venue** |

---

## Phase 7 — Final verification

| ID | Task | Status |
|---|---|---|
| P7-1 | Rerun tests + verify_claims + full compile; regenerate claim ledger for changed claims | Pending |
| P7-2 | `reports/Q1_REVISION_REPORT.md`: changes, new experiment IDs, softened/removed claims, remaining risks, author-only items | Pending |

---

## Recommendations (non-binding; decisions are yours)

1. **Phase 1:** Prefer **Option A** if the goal is a traditional education/CS-education Q1 paper — a real 20–50 program curriculum corpus is the single highest-leverage credibility upgrade. Prefer **Option B** if speed-to-submission matters and the venue is methods-oriented.
2. **Phase 4:** Prefer **Option B** if keeping the paper long enough for BJET/ToE; prefer **Option A** if the placement section is diluting the gap-measurement contribution.
3. After Phases 1–5, expect the abstract headline to change from a single "52%→32%" to a sensitivity range — this is intentional and more defensible.

---

## Rules for this branch

- No push / merge / delete without explicit authorization (current task: commit to `q1-revision` only).
- No edits to `results/` or raw `datasets/` except new experiment IDs and new curriculum corpus under `datasets/curriculum/`.
- Every number must come from a results artifact or a newly registered experiment.
- STOP at Phase 1 and Phase 4 (and Phase 6) for author decisions.
