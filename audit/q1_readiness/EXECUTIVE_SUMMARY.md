# EXECUTIVE SUMMARY — Q1 Journal Readiness Audit

*Date: 2026-10-11 · Branch: `q1-readiness-package` (from `main` = `41223eb`).
Package consolidates evidence from Phases 0–12 (`audit/00`–`12`) into the
master-prompt deliverable layout under `audit/q1_readiness/`.*

---

## Overall readiness verdict

**CONDITIONALLY READY for Q1-tier submission after a venue-specific format
pass and a full human proofread.**

- No unresolved **critical** scientific blocker remains in the claim ledger
  (**0 contradicted / 107 reproduced / 1 partially reproduced** of 108 claims).
- All 12 registered experiments are artifact-verified
  (`results/verification_report.json` → `all_verified: true`).
- Manuscript compiles clean (16 pp IEEEtran; 0 errors / 0 undefined / 0 overfull).
- The work is **not** labelled “submission-ready without caveats”: construct
  validity of the academic reference (proxy, not observed syllabi), venue
  reformatting, and human proofread remain author-owned.

## Strongest contributions (evidence-backed)

1. **Registered, GPU-traceable pipeline** for skill-gap measurement across
   lexical + semantic matching, domain-level alignment, placement prediction,
   and external validation (12/12 `USED_IN_MANUSCRIPT`).
2. **Expert-anchored matcher validity** (VALID01 vs SkillSpan/ESCO gold;
   precision ~91.9% / recall ~75.7% at τ=0.5).
3. **CS2023 curriculum anchor** (CURR01; bit-exact reproduction of 2,197-topic
   coverage metrics) separating market skill lists from occupational profiles.
4. **Honest negative / corrective findings** retained: internship RD −0.44 pp
   (not a positive effect); matched-profile 2×2 showing SGI level is governed
   by academic covering-set size, not market corpus choice.

## Critical blockers found and resolved (historical → current)

| ID | Severity (pre) | Issue | Status |
|---|---|---|---|
| D-1 | CRITICAL | H6 internship effect misstated (+0.08 pp; wrong test attribution) | **RESOLVED** (−0.44 pp; STAT01) |
| D-2 | HIGH | Corpus “3,176,266 analyzed” overstated unique records | **RESOLVED** (2.64M unique + inventory note) |
| D-3 | HIGH | LinkedIn / HF / academic-ref counts wrong in Table I | **RESOLVED** |
| D-4 | HIGH | Profile-size confound misread as corpus-composition effect | **RESOLVED** (matched 2×2 in §IV-B2) |
| L-1 | MEDIUM | `daberao2025resumeinsight` weak claim support | **RESOLVED** (wording) |
| B-1…B-5 | MEDIUM | Bib DOI/year/title defects | **RESOLVED** (Crossref) |

## Work completed (this package + prior audit branches)

- Dependency map, claim ledger (108), dataset provenance, SGI validity,
  CURR01, STAT01/INTL01/STAT02 reproduction, citation Crossref audit,
  reproducibility infra (tests/CI/checksums/entry point), manuscript fixes,
  figure/table consistency, journal-format verification (ToE/BJET/IJETHE),
  and this structured deliverable set.

## Remaining limitations (do not overclaim)

1. Academic reference profile is **1,167 employer-style job-skill postings in
   5 categories**, not university syllabi; national curriculum gap claims must
   stay proxy-qualified (Limitation + CURR01).
2. CS2023 2,197-topic extraction **not hand-audited line-by-line**.
3. Bootstrap CIs for SGI quantify **skill-list composition**, not market
   sampling error.
4. Placement benchmarks are **semi-synthetic**; RF AUC=1.0 is non-generalizable.
5. Journal quartiles are **time-varying**; evidence below is SCImago/Scopus
   snapshot ~2025 and must be re-checked at submission.

## Recommended next steps (author)

1. Choose venue (primary recommendation: **BJET** if content-centered Q1;
   **IEEE ToE** if CS-education format fit and page cut are acceptable;
   **IJETHE** if OA/high-SJR and abstract ≤250 words). See
   `FINAL_READINESS_REPORT.md` §Journal fit.
2. Run venue template conversion + word/page budget.
3. Full human proofread of `paper/main.tex` → PDF.
4. Optional Phase-5/6 hardening (employer-clustered bootstrap; calibration /
   PR-AUC).
5. Merge `q1-readiness-package` only after author review; push only with
   explicit authorization.
