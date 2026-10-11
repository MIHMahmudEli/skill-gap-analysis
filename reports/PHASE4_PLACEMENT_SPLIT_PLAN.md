# Phase 4 — Placement Split: File-by-File Plan (PREPARED, NOT EXECUTED)

Date: 2026-10-12 · Branch: `q1-revision` · Status: **awaiting author approval —
no file in this plan has been touched.** This plan prepares Option A of
`reports/Q1_REVISION_PLAN.md` Phase 4 (move RQ4/RQ5 + placement models to a
companion `paper_placement/`), incorporating what the real-vs-synthetic audit
(`reports/REAL_VS_SYNTHETIC_FINDINGS.md`) now establishes: every placement
cohort is synthetic, so the split also removes the paper's only synthetic-data
*findings* from the gap-measurement paper.

## 0. Rulings needed from the author before execution

| ID | Decision | Recommendation |
|---|---|---|
| D1 | **RQ5 geography** (GEO01, 1.35M *real* postings, Fig. 6a "85.2% US") is a market-topography result, not a placement result. Move with RQ5, or keep in the main paper (folded into RQ1)? | **Keep in main paper** (real data, gap-relevant context); RQ5 renames to "Cross-Cohort Placement Dynamics" inside `paper_placement/`. |
| D2 | **Table I Tier 2 rows** (421K synthetic student records): move to the placement paper, or stay in the main Table I as provenance inventory? | **Stay** — Table I is the corpus provenance inventory; usage claims move. Dropping the rows would re-hide the synthetic accounting we just made explicit. |
| D3 | **H4/H5/H6 + signaling-theory hypothesis text**: move entirely, or keep hypotheses in main with "untestable on real data" verdicts? | **Move entirely** — a hypothesis whose only tests are synthetic benchmarks belongs with the benchmark audit. |
| D4 | **RQ numbering** after the split: main paper has RQ1–RQ3; keep original numbers (gaps at RQ4/RQ5) or renumber? | **Keep RQ1–RQ3 as-is** (no renumbering; numbering is stable across versions). |

## 1. What MOVES to `paper_placement/` (from `paper/main.tex`)

| main.tex element | Lines (current) | Notes |
|---|---|---|
| RQ4 bullet + RQ5 bullet (intro RQ list) | 84–85 | Replaced by one sentence: "placement-determinant analyses are reported in the companion paper" |
| Contribution 5 "Model Validation and Diagnostic Audit" | 94 | Moves verbatim |
| Related work §II.C "Machine Learning in Employability Modeling" | 129–132 | Moves |
| Hypotheses H4, H5, H6 (§II.D) | 141–143 | Move (D3); H1–H3 stay |
| Signaling-theory paragraph (§II.B item 2) | 115–124 | Trim: Spence/Screening motivation moves; the project-portfolio clause that grounds a main-paper recommendation stays |
| Methods §IV.D "Predictive Employability Modeling & Validation Protocols" | 299–327 | Moves |
| Methods §IV.C collinearity/VIF portion | 273–298 (partial) | Move the VIF/collinearity part; the generic bootstrap-inference sentence stays (RQ3 CIs use it) — **line-level split decided at execution** |
| Results §V.D RQ4 (all 6 subsubsections) | 489–575 | Moves: descriptives, VIF, logistic, CV comparison, multiseed, tree-audit + external generalization |
| Results §V.E RQ5 placement half | 576–610 (partial) | INTL01 internship figure + PLAC01 cross-country paragraph move; geography panel stays (D1) |
| fig:placement (tab:descriptive + \FigEffectSizes + \FigMeans) | 497–521 | Moves |
| tab:vif, tab:logistic, tab:model_comparison, tab:multiseed | 530, 542, 554, 565 | Move |
| fig:international (\FigInternship) | 605 | Moves |
| Hypothesis verdicts for H4/H5/H6 + Table XIII rows | 616–626 | Move; tab:hypotheses keeps H1–H3 |
| Recommendations: WIL/co-op bullet; regional-observatories bullet | 657, 663 | Move (both cite placement cohorts) |
| Limitations: decision-boundary/synthetic-benchmark item; external-cohort item | ~697–703 | Move (they describe the placement audits) |
| Reproducibility rows: STAT01, STAT02, PLAC01, INTL01 | tab:experiments 683 | Move; row count updates in both papers |
| Conclusion sentence "near-perfect classification scores can mask synthetic threshold rules…" | ~707 | Moves (it is the placement-audit headline) |

## 2. What STAYS in `paper/main.tex` (gap-measurement paper)

RQ1 topography (real HF tokens; trends-half already removed per step 2),
RQ2 + VALID01 + ALIGN04 nested-superset + CURR01, RQ3 + fig:skill_gap,
SENS01 sensitivity surface, ALIGN05 (pending gate), Table I unit-typed
inventory (D2), H1–H3 + reframed verdicts, the ≥ 60% of limitations about
corpus/proxy/threshold, gap-measurement recommendations, geography panel
(Fig. 6a, D1), reproducibility for ALIGN01–04/SENS01/VALID01/CURR01/ALIGN05.

## 3. New files

| File | Content |
|---|---|
| `paper_placement/main.tex` | Standalone companion paper: intro; employability-modeling related work; H4–H6; methods §IV.D (+ VIF part of §IV.C); RQ4/RQ5 results; discussion (verdicts H4–H6; benchmark-audit framing per step-2 findings: every statistic labelled "synthetic benchmark"); limitations; reproducibility; conclusion |
| `paper_placement/README.md` | Scope, relation to main paper ("methods-audit companion; all cohorts synthetic — `datasets/REAL_VS_SYNTHETIC.csv`"), status (draft; numbers unchanged), build instructions |
| `paper_placement/references.bib` | Copy of needed entries (or shared ../paper/references.bib — decided at execution; prefer copy to keep the two builds independent) |

## 4. Other files touched at execution (ordered)

1. **`figures/tikz_figs.tex`** — keep all macros in place; `paper_placement/main.tex`
   `\input`s the same file (no duplication). `\FigTrends` becomes orphaned
   (panel (b), synthetic — already recommended for removal in step 2) → delete macro at execution.
2. **`experiments/`** — **no moves.** STAT01, STAT02, PLAC01, INTL01 stay
   registered in `results/registry.json`; the companion paper cites the same
   artifacts. TRENDS01 has no consumer after the step-2 removal (registry note only).
3. **`README.md`** — RQ4/RQ5 bullets (lines 22–24) → one line pointing to
   `paper_placement/`; headline counts already unit-typed (step 3).
4. **`audit/verify_claims.py`** — TEX-string checks that will break when text
   moves (repoint to a second TEX handle or move to a placement-paper gate):
   C152-area (`-0.44` H6 verdict strings, line ~298), H6/INTL01 check
   (`"Not supported (STAT01" in TEX`, ~300), H5 checks
   (`"H5 (credential locality) is not supported"`, `"Not supported (PLAC01"`,
   ~310–312), plus readers of `paper/tables/tab_vif.tex` /
   `tab_descriptive.tex` (~228–237) which follow their tables into
   `paper_placement/tables/`. Everything else (C01–C150 family) stays on the
   main TEX unchanged.
5. **`audit/01_claim_evidence_ledger.csv`** — 13 placement rows re-targeted
   (see §5); `audit/build_ledger.py` extended to take a paper path per row.
6. **`reports/Q1_REVISION_PLAN.md`** — Phase 4 rows P4-A/P4-C marked done
   (P4-C is largely already implemented by the step-3 unit-typed accounting);
   P4-B marked "not chosen".

## 5. Effect on the claim ledger (13 rows, all artifact-backed; numbers unchanged)

| Rows | Effect |
|---|---|
| C70, C85, C88, C100, C101, C110, C130, M05, M08, C152, C152b, C153, C75 | `manuscript_location` re-pointed from main-paper sections to `paper_placement/main.tex` sections; `exact_claim`, `ms_value`, `artifact_value`, `evidence_path`, `reproduction_status` all unchanged (nothing recomputed). |
| C100 | Loses its "Abstract" location (main-paper abstract drops the external-AUC sentence in the P2-3 rewrite). |
| New rows | None — the split creates no new claims; the main paper simply stops asserting the 13. |

Net effect on the main paper: **13 claims leave, 0 enter**; every remaining
main-paper claim keeps its existing artifact path. The claim ledger grows a
`paper` column (`main` / `placement`) instead of being forked.

## 6. Sequencing when approved

1. Create `paper_placement/main.tex` by **moving** (cut) the §1 elements; run
   a LaTeX build of both papers (numbers/labels intact).
2. Fix cross-references: main paper gains one pointer sentence (intro +
   limitations); `paper_placement` gains "gap-measurement paper" pointer.
3. Update `figures/tikz_figs.tex` (drop `\FigTrends`), README, ledger, gates.
4. Run gates: pytest 13/13; verify_claims with placement checks repointed
   (same 103 checks — none deleted, only their TEX handle may change);
   LaTeX build of both papers.
5. One commit per sub-step (as in this batch), then report.

Stop conditions: any check that cannot be repointed without deleting it →
STOP and report (a deleted check is a governance change requiring author
consent). Same standing rules: `q1-revision` only, no push, every number from
an artifact.
