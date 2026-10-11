# FINAL READINESS REPORT — Q1 Journal Submission

*Date: 2026-10-11 · Branch: `main` @ `db3d2b6` (= origin/main, origin/q1-readiness-package; clean tree before this pass) · Updated after independent adversarial review and final repository reconciliation (H5 construct fix, proxy disclosure, CS2023 characterization). Manuscript: `paper/main.tex` / `paper/main.pdf` (**16 pp**; Revision Log absent).*

---

## 1. Final readiness verdict

**CONDITIONALLY READY** (verdict **B**).

Scientific blockers that previously made submission unsafe (contradicted H6,
corpus count inflation, profile-size confound misattribution, weak citation,
internal revision log in PDF, residual “syllabus” mislabels, **H5 misattribution
of the INTL01 internship association as a domestic training premium**) are
resolved with artifact evidence. Remaining gaps are **design limitations**
(proxy academic profile, CS2023 computational-only anchor), **venue
conversion**, and **human proofread** — not hidden defects.

Do not treat this as an acceptance prediction.

Gate checklist:

| Criterion | Status |
|---|---|
| Every RQ has evidence-backed answer | YES (H1–H6 mapped; H5 now PLAC01 = not supported) |
| Major claims → evidence matrix | YES (108 rows + F-1 correction recorded) |
| Primary results reproducible or marked unverified | YES (12/12 exact local or GPU-verified) |
| Dataset provenance audited | YES (18-row `dataset_audit.csv`; manifest sum 3,163,517 / unique 2,643,703) |
| Leakage / independence investigated | YES (STAT01/02, SGI protocol) |
| Measurement validity described | YES (VALID01 expert κ=0.737 + CURR01 computational anchor, labeled as such; residual C-1/R-5) |
| References verified with statuses | YES (52 rows; 0 unresolved) |
| LaTeX synced; figures/tables verified | YES (TikZ figures; hand-audited crosscorpus table preserved) |
| PDF compiles | YES (pdflatex+bibtex, 0 errors / 0 undefined / 0 overfull; **16 pp**) |
| No internal audit clutter in submission PDF | YES (Revision Log removed 2026-10-11 adversarial pass) |
| Independent critical review of strongest claims | YES (Phase 3/F + this package) |
| Claim checker green after edits | YES (**103/103** `audit/verify_claims.py`) |
| Tests green after edits | YES (**13/13** pytest) |
| Local reproduction gate | YES (`reproduce_local.py` env/checksums/verify/claims/citations ok; stats skipped this pass) |

**Do not treat “conditionally ready” as acceptance prediction.** Q1 acceptance
depends on reviewers, editor fit, and authorship decisions outside this audit.

---

## 2. Construct-validity statement (Phase 3 master requirement)

- The academic side of SGI is **`hf_job_skill_set.csv`**: **1,167 job-skill
  postings in 5 occupational categories** (IT, BD, Finance, Sales, HR) —
  an **employer-style reference profile**, not scraped university syllabi.
- CURR01 anchors the analysis to **CS2023** (2,197 topics / 17 KAs) but covers
  only a minority of market top-skills (~30.4% topic coverage regime).
- **SGI estimand:** binary top-K market-token coverage by the academic profile
  (lexical exact match or SBERT cosine ≥ τ); SGI = 1 − coverage.
- **52% (lex) → 32% (sem, τ=0.5)** verified exactly; the decrease reflects
  **many-to-one semantic coverage** under a fixed top-100 academic set, not
  proof that the “true” gap is smaller.
- Matched-profile 2×2: at fixed P, HF and LinkedIn SGI **identical**;
  level shifts when P changes 100↔500. Lower SGI ≠ more accurate instrument
  without an external standard; VALID01 is that standard for the matcher.
- Permitted interpretation: **alignment between market skill demand lists and
  a job-derived reference profile, curriculum-anchored where CS2023 applies.**
  Not permitted: “national university curriculum gap established.”

---

## 3. Numerical discrepancies and resolutions

| Claim | Pre-audit | Artifact truth | Resolution |
|---|---|---|---|
| Internship RD (H6) | +0.08 pp | **−0.44 pp** (STAT01) | Manuscript fixed |
| H5 credential locality | “Supported (INTL01) +15.3 pp domestic premium” | **Not supported** — INTL01 is an internship association (+15.34 pp, international cohort); PLAC01 placement rates similar across countries (India 63.2% … Germany 60.0%, overlapping CIs) | Retargeted H5 to PLAC01; verdict flipped; INTL01 kept only as descriptive context (F-1) |
| Corpus size | 3,176,266 analyzed | **≈2,643,703 unique** (manifest sum 3,163,517 − 519,814 linked pair) | Fixed + inventory note |
| LinkedIn postings | 1,348,510 | 1,348,454 | Fixed |
| HF jobs row count | 519,841 | 519,814 (linked pair) | Fixed; unique total counts once |
| Academic ref | 13,833 taxonomy | **1,167 postings** | Fixed Table I + construct text |
| ALIGN01 vs ALIGN04 SGI gap | “corpus vocabulary” | **profile-size artifact** | 2×2 rewrite |
| χ²-projects | 719.82 | 721.47 (binning) | Documented, not silent |
| CV AUC LR | 0.9406 | 0.9407 | Rounding; documented |

---

## 4. Experiments (12/12)

All registered GPU experiments: registry `USED_IN_MANUSCRIPT`, artifact
`verified`. Local CPU re-runs: exact for ALIGN01/02/04, CURR01, STAT01,
STAT02 (see `experiment_audit.csv`). ALIGN03 domain CIs match manuscript
tables. VALID01 metrics present in pair artifacts; metadata quirk R-8 open.

---

## 5. Journal fit (Phase 9) — evidence snapshot 2025–2026

Rankings are **not permanent**. Evidence: SCImago SJR / Scopus / publisher
pages checked 2026-10-11. Quartile ≠ acceptance probability.

| Journal | Indexing evidence (snapshot) | Scope fit | Format gap vs current draft | Trade-off |
|---|---|---|---|---|
| **British Journal of Educational Technology** (Wiley) | SCImago **Q1** Education (SJR ~3.83, 2025); Scopus CiteScore ~23 Q1; ABDC **A**; WoS SSCI | High (ed-tech + analytics) | Free format; **5–6k word** budget likely needs cut; class away from IEEEtran | Strong Q1 brand; word surgery |
| **IEEE Trans. Education** | SCImago **Q1** Education (SJR ~0.966, 2025); CiteScore ~5.9 | High (CS education + methods evidence) | **8–10 journal pages**; structured abstract | Best LaTeX class match; heavy compression |
| **Int. J. Educational Technology in Higher Education** (Springer, Diamond OA) | SCImago **Q1** Education (SJR ~7.95, 2025; top of Education list) | Moderate–high (higher-ed TEL) | Abstract ≤250 words; OA APC logistics | High SJR; OA cost decision |

**Primary recommendation (content fit + Q1 evidence):** **BJET** after a
word-budget pass — educational-technology readership matches the curriculum–
industry measurement story; methods depth survives free-format submission.

**Strong alternatives:** IEEE ToE (if CS-education audience and page cut are
acceptable); IJETHE (if Diamond-OA readership and APC policy are acceptable).

**Not recommended solely for “Q1-ness”:** do not chase quartile without
scope fit. Re-verify quartiles and APCs on live pages at submission time.

---

## 6. Validation commands executed (this package)

```
python audit/verify_claims.py       # checks=103; matched=103; mismatched=0
python -m pytest tests/ -q          # 13 passed
python reproduce_local.py --skip stats   # env/checksums/verify/claims/citations ok
python experiments/verify.py        # all_verified: true
# PDF: pdflatex + bibtex + pdflatex ×2  (0 errors / 0 undefined / 0 overfull; 16 pp)
```

See `REPRODUCIBILITY_REPORT.md` for the full command log summary.

---

## 7. Unresolved items before submission

1. Author venue choice + template conversion (R-9 / A-6 BJET word budget)
2. Author/journal metadata: names redacted placeholder; owner decision (F-6)
3. Human proofread (R-10)
4. Optional strengtheners: multiplicity note (R-3); calibration/PR-AUC (R-4);
   employer-cluster bootstrap (R-7); CS2023 human line audit (R-6, now
   labeled computational-only — do not claim audit exists)
5. Live re-check of quartile/APC (unverified dynamic data)
6. Merge/push of this package only with explicit authorization

---

## 8. Deliverable index

| File | Role |
|---|---|
| `EXECUTIVE_SUMMARY.md` | Verdict, blockers, next steps |
| `ISSUE_REGISTER.md` | Severity-tagged issue log |
| `dataset_audit.csv` | Provenance / counts / roles |
| `reference_audit.csv` | 52 bib entries + verification status |
| `experiment_audit.csv` | 12 experiments + reproduction status |
| `claim_evidence_matrix.csv` | 108 claims ↔ artifacts |
| `CHANGELOG.md` | Scientific/editorial change log |
| `FINAL_READINESS_REPORT.md` | This document |
| `REPRODUCIBILITY_REPORT.md` | Commands, tests, compilation |
| `build_package.py` | Regenerates CSV deliverables |
