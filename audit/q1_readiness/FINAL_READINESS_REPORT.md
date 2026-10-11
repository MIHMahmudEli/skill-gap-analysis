# FINAL READINESS REPORT — Q1 Journal Submission

*Date: 2026-10-11 · Branch: `q1-readiness-package` · Updated after independent
adversarial review (see `FINAL_ADVERSARIAL_REVIEW.md`). Manuscript:
`paper/main.tex` / `paper/main.pdf` (**15 pp** after removing internal Revision Log).*

---

## 1. Final readiness verdict

**CONDITIONALLY READY** (verdict **B** — independent adversarial review).

Scientific blockers that previously made submission unsafe (contradicted H6,
corpus count inflation, profile-size confound misattribution, weak citation,
internal revision log in PDF, residual “syllabus” mislabels) are resolved with
artifact evidence. Remaining gaps are **design limitations** (proxy academic
profile), **venue conversion**, and **human proofread** — not hidden defects.

Do not treat this as an acceptance prediction.

Gate checklist:

| Criterion | Status |
|---|---|
| Every RQ has evidence-backed answer | YES (H1–H6 mapped in ledger) |
| Major claims → evidence matrix | YES (108 rows) |
| Primary results reproducible or marked unverified | YES (12/12 exact local or GPU-verified) |
| Dataset provenance audited | YES (18-row `dataset_audit.csv`) |
| Leakage / independence investigated | YES (STAT01/02, SGI protocol) |
| Measurement validity described | YES (VALID01 + limitations; residual C-1/R-5) |
| References verified with statuses | YES (52 rows) |
| LaTeX synced; figures/tables verified | YES |
| PDF compiles | YES (pdflatex+bibtex, 0 errors; **15 pp** post-adversarial edits) |
| No internal audit clutter in submission PDF | YES (Revision Log removed 2026-10-11 adversarial pass) |
| Independent critical review of strongest claims | YES (Phase 3/F + this package) |

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
| Corpus size | 3,176,266 analyzed | **≈2,643,703 unique** | Fixed + inventory note |
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
python audit/q1_readiness/build_package.py
python -m pytest tests/ -q          # 13 passed (on main; re-run after merge)
python reproduce_local.py           # all stages ok (on main)
# PDF: pdflatex + bibtex + pdflatex ×2  (0 errors; on main)
```

See `REPRODUCIBILITY_REPORT.md` for the full command log summary.

---

## 7. Unresolved items before submission

1. Author venue choice + template conversion (R-9)
2. Human proofread (R-10)
3. Optional: multiplicity note (R-3); calibration/PR-AUC (R-4);
   employer-cluster bootstrap (R-7); CS2023 line audit (R-6)
4. Live re-check of quartile/APC (unverified dynamic data)
5. Merge/push of this package branch only with explicit authorization

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
