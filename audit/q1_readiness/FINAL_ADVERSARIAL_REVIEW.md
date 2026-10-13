# FINAL ADVERSARIAL REVIEW

*Date: 2026-10-11 · Independent re-verification on branch `q1-readiness-package` ·
Starting commit claim: `19a2308` · Role: skeptical reviewer / statistical auditor.
Prior audit claims were treated as untrusted until re-checked against artifacts.*

---

## A. Phase 1 — Verification of the previous audit

| Claim under test | Independent check | Result |
|---|---|---|
| Branch `q1-readiness-package`, commit `19a2308` | `git rev-parse HEAD` | **CONFIRMED** `19a23086fa8767…` |
| Audit package exists | `audit/q1_readiness/*` | **CONFIRMED** (10 files) |
| 13 tests pass | `pytest tests/ -q` | **CONFIRMED** 13 passed (re-run after manuscript edits) |
| 12/12 experiments `USED_IN_MANUSCRIPT` + artifacts | `registry.json` + `verification_report.json` + `metrics.json` existence | **CONFIRMED** all 12 metrics present, `all_verified: true` |
| Local reruns vs artifact-only | ALIGN01/02/04, CURR01, STAT01, STAT02: prior local CPU re-runs + this session H6 recompute from raw CSV | **CONFIRMED** H6 independently recomputed: RD **−0.4442 pp**, 16.3219% vs 16.7661% |
| PDF compiles | pdflatex+bibtex×2 | **CONFIRMED** — **16 pages** at the 2026-10-13 recheck (15 before the Appendix A demand-share table was added), 0 errors / 0 undefined / 0 overfull |
| PDF ↔ current sources | recompile overwrites `main.pdf` from current `main.tex` | **CONFIRMED** (post-edit rebuild) |
| 107 reproduced / 1 partial / 0 contradicted | ledger + matrix tallies | **CONFIRMED** (partial = M06 VALID01 metadata quirk only) |
| Numerical corrections in abstract/body/tables | grepped `main.tex` for 2.64M, 519,814, 1,167, −0.44, profile-size 2×2 | **CONFIRMED** present and consistent |

### Discrepancies found during independent verification

| # | Severity | Finding | Disposition |
|---|---|---|---|
| V-1 | **HIGH (submission hygiene)** | Manuscript still contained a full **Revision Log** section referencing `audit/` paths — internal material in the submission PDF | **CORRECTED** this session (section removed; PDF 16→15 pp) |
| V-2 | **MEDIUM (construct wording)** | Residual **“syllabus”** labels in Algorithm 1, §III-B embedding definition, RQ2 body, and Discussion (“academic syllabi often describe…”) overstated the job-derived academic profile | **CORRECTED** this session (reference-profile wording) |
| V-3 | MEDIUM | Contribution bullet still said “curriculum descriptors” for the multi-source corpus | **CORRECTED** → “job-derived academic reference profile” |
| V-4 | MEDIUM | Discussion asserted domain deficits “reflect institutional constraints in curriculum adaptation” (causal-sounding from a proxy measurement) | **NARROWED** → “are consistent with---though do not by themselves establish---” |
| V-5 | LOW | Ledger C143: manuscript Cloud share range “47.1–53.9%” vs artifact min 47.05 / max 53.85 | **ACCEPTED** — ordinary 1-dp rounding of 47.05→47.1, 53.85→53.9; not a scientific error |
| V-6 | LOW | Ledger C120: 85.2 vs 85.23 etc. | **ACCEPTED** — display rounding |
| V-7 | MEDIUM | M06: VALID01 `n_positive_by_type` hard/random negatives stored as 0 while `n_negative=1769` | **OPEN (non-blocking)** — pair CSV intact; manuscript-facing κ/AUC unaffected |

**No historical experiment output or raw data file was modified.**

---

## B. Phase 2 — Challenge of the main scientific claims

### B1. SGI 52% → 32% (lexical vs semantic, ALIGN01/02)

| Attack | Evidence | Verdict |
|---|---|---|
| Numbers fabricated? | `ALIGN01…/metrics.json` sgi=0.52 [0.42,0.63]; `ALIGN02…/metrics.json` τ=0.5 SGI=0.32 [0.23,0.41]; prior local re-run exact | **SURVIVES** |
| Lower SGI = better instrument? | VALID01 κ_lex=0.112 vs κ_sem=0.737; precision 0.919 / recall 0.757 at τ=0.5 | **SURVIVES as measurement property of matching**, not “truer curriculum gap” |
| Different denominators? | Both use top-K market tokens K=100, academic P=100 | **SURVIVES** |
| Overclaim of curriculum truth? | Pre-edit text still said “syllabi” in places | **WAS WEAK → CORRECTED** (V-2). Current text: “apparent” gap + proxy language |

### B2. H6 internship effect (college cohort)

| Attack | Evidence | Verdict |
|---|---|---|
| Sign/magnitude wrong? | Independent recompute from `college_student_placement_dataset.csv`: RD=−0.4442 pp; Welch p≈0.56; logistic OR=1.0194 p=0.62 | **SURVIVES as null / slightly negative** |
| Confused with INTL01 +15.3 pp? | Manuscript explicitly separates populations/estimands (H5 vs H6) | **SURVIVES** |
| Causal overreach? | Limitation 10 observational non-causal; H6 “not supported” | **SURVIVES** |

### B3. Matched-profile 2×2 / ALIGN04 confound

| Attack | Evidence | Verdict |
|---|---|---|
| Profile-size confound real? | Code paths P=100 (ALIGN01/02) vs P=500 (ALIGN03/04); audit 2×2 JSON | **SURVIVES** |
| Manuscript still claiming identical procedures / vocabulary story? | §IV-B2 rewritten; Limitation 5 discloses P-sensitivity | **SURVIVES after prior fix** |
| 2×2 is audit-only not registered GPU? | Disclosed in `audit/03_sgi_validation.md`; text reports as sensitivity | **ACCEPTABLE** if kept as sensitivity (current) |

### B4. External validation AUC 0.768 / 0.576

| Attack | Evidence | Verdict |
|---|---|---|
| Leakage? | STAT02 protocol: zero-shot, no target in features (prior audit + metrics present) | **SURVIVES** |
| Presented as strong generalization? | Limitation 2 explicitly attenuation/domain shift | **SURVIVES** |
| Calibration missing? | Not reported | **OPEN optional** (Phase D) |

### B5. Domain deficits (Cloud 2.45 / 0.94 pp; soft skills 0.00)

| Attack | Evidence | Verdict |
|---|---|---|
| Absolute magnitudes tiny / corpus is healthcare-heavy? | Limitation 7 discloses corpus composition; severity is relative-to-median | **SURVIVES as conditional coverage**, not economy-wide demand |
| Soft-skill “fully covered” = curriculum teaches soft skills? | Soft-skill coverage is market vs **job-derived profile** | **NARROWED by proxy language**; still easy to misread — residual risk LOW–MEDIUM for reviewers |

### B6. χ² binning & AUC rounding

| Item | Verdict |
|---|---|
| χ²-projects 721.47 vs older 719.82 | Documented binning difference; not silent |
| CV AUC 0.9407 vs 0.9406 | Rounding; accepted |

**Claims that require narrower wording (done or residual):** B1 syllabus labels (done); B5 soft-skill curriculum reading (mitigated); title “Academic–Industry Skills Misalignment” remains ambitious but is bounded by Limitations 1–3–7 — acceptable if venue expects systems/empirical framing.

---

## C. Phase 3 — Academic-profile construct limitation (substantive)

**What is measured:** alignment between (i) top market skill tokens from posting corpora and (ii) a **job-derived reference profile** (1,167 postings, 5 occupational categories), with CS2023 as an external curriculum **anchor** (CURR01), not as the profile itself.

**What cannot be established:** national/global university curriculum deficiency; what any specific CS program teaches; causal educational failure.

**Manuscript status after this review:**
- Table I: proxy description present  
- §III-B: proxy + CURR01 quantification  
- Limitations 1 & 3: explicit  
- Algorithm/method terms: fixed (V-2)  
- CURR01: 30.4% applied coverage / weak theoretical core — honest bound  

**Verdict:** Limitation retained and defensible within the design. New syllabus collection is a **future extension**, not a gate for this paper’s narrower contribution (measurement instrument + multi-source replication + placement association audit).

---

## D. Phase 4 — Optional statistical hardening

| Item | Necessity for current RQs | Action |
|---|---|---|
| 1. Calibration (placement) | Useful if claiming probabilistic utility; not required for ranking/OR narrative | **Optional** — need raw prediction dumps; not blocking |
| 2. PR-AUC / baselines | Useful given 16.6% base rate; ROC-AUC already reported with baseline acc 0.834 | **Optional high-value** if predictions archived |
| 3. Employer-clustered bootstrap (domain CIs) | Ideal for posting dependence; employer IDs largely unavailable in HF skills extract | **Recommended future**; not implementable cleanly without new fields |
| 4. Multiplicity discussion | One-sentence already enough for interval-based posture | **Optional LOW** |
| 5. SGI τ-sweep | Already in Table sensitivity + Limitation 5 | **Done** |
| 6. Alternative χ² binning | Documented; no result flip | **Done as documentation** |
| 7. Independent curriculum validation | CURR01 is partial; true multi-institution syllabus gold = future data | **Future work** |

No optional analysis was added solely to inflate methods count. No result-changing analysis was skipped that was both feasible and necessary.

---

## E. Phase 5 — Reference re-audit (focus on PARTIAL)

| Status class (n) | Independent verdict |
|---|---|
| VERIFIED (31) | Crossref DOI/title/year — unchanged |
| PARTIALLY — dataset URL citations (Kaggle/HF) | **Legitimate dataset cites** with official repo URLs; not peer-reviewed articles — correctly not forced to “VERIFIED article” |
| PARTIALLY — seminal no-DOI (Becker, Schultz, WEF) | **Legitimate** foundational/institutional sources |
| PARTIALLY — schlippe / cuckov / scandurra | Metadata quirks documented; DOIs resolve or issue-year choice defensible |
| PARTIALLY — daberao claim support | Metadata OK; manuscript now cites as **profile-matching precedent**, not curriculum validation |
| INCORRECT / RETRACTED | **None found** |

No bibliography entry deleted or replaced. `reference_audit.csv` retained with statuses; claim_support field left conservative.

---

## F. Phase 6 — Journal re-check

| Journal | Scope fit | Format evidence (2026-10-11) | Quartile evidence (system + year) | Decision |
|---|---|---|---|---|
| **BJET** (Wiley/BERA) | Ed-tech empirical/methodological — strong fit for instrument + higher-ed workforce alignment | Official: free format; original articles typically **≤6,000 words excl. references**; **double-anonymous**; CiteScore **23.1** on journal page | Scopus **CiteScore Q1** Education (journal page); SCImago SJR Education **Q1** (SCImago listing ~2025) | **PRIMARY** |
| IEEE ToE | Strong CS-education fit | 8–10 pages structured abstract requirements (prior verified) | SCImago Education **Q1** (2024–2025 history) | Alternative if page cut accepted |
| IJETHE | Higher-ed TEL, Diamond OA | Research articles 4,500–8,000 words; abstract 150–250 | SCImago Education **Q1** top SJR (~7.95, 2025 list) | Alternative if OA/APC OK |

**Primary recommendation remains BJET**, contingent on word-budget pass (current body ~6.6k excl. tables is slightly over 6k — needs compression at conversion). Do **not** convert template until owner selects venue.

---

## G. Phase 7 — Submission-version preparation (this session)

| Step | Status |
|---|---|
| Correct unsupported claims | DONE (syllabus→reference profile; causal curriculum adaptation narrowed) |
| Abstract/conclusion consistency | Rechecked; H6 null, 52→32, proxy limits consistent |
| Title overstatement | Retained “misalignment” framing; bounded by limitations — **acceptable**, optional title softener left to owner |
| Remove revision log / audit notes from article | **DONE** (Revision Log removed) |
| Limitations retained | YES (items 1–10) |
| Figures/tables/refs resolve | Clean compile; 15 pp |
| Metrics traceable | 12 registered experiments |
| Anonymization | Authors redacted; no audit paths remain in PDF body |
| Journal template | **NOT applied** (awaiting owner choice) |
| Final PDF | Rebuilt 15 pp, 918 018 bytes |

---

## H. Phase 8 — Regression

| Check | Result |
|---|---|
| `pytest` | 13 passed |
| Experiment artifacts untouched | git status: only manuscript + audit package files |
| Tables still match verified metrics | crosscorpus/gap/sensitivity unchanged; no `make_latex` clobber |
| Citations | bibtex Done; no undefined |
| Secrets | none added; `.env` gitignored |

---

## I. Category summary (required distinctions)

| Category | Items |
|---|---|
| **Confirmed errors (pre-fix)** | H6 sign; corpus inflation; profile-size confound story; Table I counts; bib DOIs; weak daberao support |
| **Corrected errors (incl. this session)** | Above + V-1 revision log, V-2 syllabus labels, V-3 contribution wording, V-4 causal curriculum phrasing |
| **Claims that survived challenge** | SGI 52/32; H6 null; matched 2×2 stability; STAT02 AUCs; CURR01 metrics; VALID01 κ |
| **Claims that need narrower wording** | Soft-skill “coverage” (done via proxy language); title ambitiveness (residual, owner call) |
| **Limitations requiring new data** | True multi-institution syllabi; employer IDs for clustered CIs; calibration prediction dumps |
| **Optional analyses** | PR-AUC, calibration, multiplicity sentence, multi-syllabus gold |
| **Unresolved submission blockers** | (1) Owner venue selection + BJET word cut; (2) human proofread; (3) explicit merge/push authorization |

---

## J. Final decision

### **B. CONDITIONALLY READY**

**Why not A:** No critical scientific or reproducibility failure remains. Central numbers re-derive from artifacts (and H6 from raw data). Zero contradicted ledger claims. Clean compile. Construct limitation is disclosed and bounds the claims.

**Why not C:** (1) Venue-specific format conversion and **~6k-word BJET pass not done**; (2) full human proofread not done; (3) residual reviewer-facing risk that soft-skill/domain “curriculum” language will be over-read despite proxy disclaimers; (4) optional but valuable PR-AUC/calibration not in place; (5) owner has not authorized final template/merge.

**Conditions to upgrade toward C after owner actions:** select venue → pass word/page budget → final proofread → re-run `pytest` + compile on submission branch.

---

## K. Concise owner report

| Field | Value |
|---|---|
| Work completed | Independent re-verification; manuscript hygiene + construct-wording fixes; adversarial review doc; reports updated |
| Tests | **13 passed** |
| Compilation | **15 pp**, 0 errors / undefined / overfull; Revision Log removed |
| Unresolved issues | M06 metadata quirk; optional PR-AUC/calibration; employer-cluster CI; venue conversion; proofread |
| Recommended journal | **BJET** (primary); IEEE ToE; IJETHE |
| Exact next action | **Owner: confirm venue (or accept BJET path), authorize format pass, then authorize merge/push of `q1-readiness-package`.** |
