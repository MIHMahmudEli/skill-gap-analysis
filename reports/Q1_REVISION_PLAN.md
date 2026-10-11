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
| P2-1 | Experiment **SENS01**: SGI grid K∈{50,100,200,500} × P∈{100,250,500,1000} × τ∈{0.4,0.5,0.6,0.7} × lexical/semantic × HF + LinkedIn; seed 42 | Script written (`experiments/exp_scripts/sens01_sgi_sensitivity.py`); smoke validating, full run pending |
| P2-2 | Dual bootstrap: skill-list resample **and** posting resample; report both CIs with interpretation | Implemented in script (B_SKILL=1000, B_POST=500; posting CI = joint market-P + academic-1167 resample; NaN at P=all anchors) |
| P2-3 | Heatmap/surface figure + sensitivity table; replace abstract "52%→32%" with range + SENS01 result | Script emits figure + tables; abstract rewrite pending full-run numbers |
| P2-4 | Register in `results/registry.json`; extend `experiments/verify.py` | verify.py SENS01 checks written (held uncommitted until results exist, so the baseline gate stays green); registry entry lands with the run |

**Finding (2026-10-11, surfaced by SENS01's anchor check):** the published
experiments do not share one definition of the academic reference profile.
ALIGN01/ALIGN02 compare market top-100 against academic **top-100**
(symmetric — this is the headline "52% → 32%" instrument), but ALIGN04's
LinkedIn replication compares market top-100 against academic **top-500**
(`most_common(PROFILE_N)` with no `.head(TOP_N)` — asymmetric). Under the
symmetric instrument LinkedIn lexical SGI@K=100 is **0.52**, not the
published 0.37; the 0.37 reproduces exactly only under ALIGN04's asymmetric
definition (coverage 0.63 vs 0.48). Consequences:

1. SENS01's grid is symmetric (K vs K) — internally consistent, matching the
   headline instrument; its LinkedIn column is a fresh consistent-instrument
   result, **not** a failed reproduction of 0.37/0.14.
2. The script validates both paths: HF anchors must reproduce 0.52/0.32
   (symmetric), and a dedicated `align04_asymmetric_replication` block must
   reproduce 0.37/0.14 (asymmetric) — both are hard assertions.
3. **Author decision at P2-3 manuscript edit:** the cross-corpus claim
   ("replicates on LinkedIn: 0.37/0.14") is partly an artifact of the larger
   academic profile. Options: (a) report both definitions in ALIGN04's row
   with a footnote, (b) restate the cross-corpus claim on the symmetric
   instrument (HF 0.52 vs LinkedIn 0.52 lexical — a *stronger* consistency
   result, τ-dependent for semantic), or (c) leave ALIGN04 as-is and add the
   definition discrepancy to limitations. Not decided yet.

---

## Phase 3 — Domain-gap credibility (ALIGN05)

| ID | Task | Status |
|---|---|---|
| P3-1 | Experiment **ALIGN05**: stratify/filter postings by occupation family (tech vs non-tech); rerun domain deficits on tech-relevant subset | Pending |
| P3-2 | Drop or externally anchor Critical/Moderate/Mild labels; report effect sizes + CIs | Pending |

---

## Phase 4 — Placement section (STOP for author choice)

| ID | Task | Status |
|---|---|---|
| P4-A | **Option A:** move RQ4/RQ5 + placement models to `paper_placement/`; remove from main paper | **BLOCKED — awaiting author choice** |
| P4-B | **Option B:** keep as clearly labelled "illustrative benchmark audit"; remove real-graduate OR claims; drop synthetic datasets from headline count | **BLOCKED — awaiting author choice** |
| P4-C | Correct headline scale: report only the nine experiment-feeding sources; list the rest in appendix | Pending after choice |

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
