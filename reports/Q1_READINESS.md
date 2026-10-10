# Q1-Readiness Assessment

*Assessment date: 2026-10-10 (post-VALID01) · Artifact: `paper/main.pdf`
(13 pp) + `experiments/` (10 registered GPU experiments) + HF archive.*

## Verdict: **READY** for submission to a mid-tier Q1 venue

The residual risk that previously topped the register (no human validity
evidence) was closed by VALID01: the matcher now carries κ = 0.737 and
AUC = 0.961 against a *published* expert gold standard — a stronger
credential than typical self-annotation, because the standard is
third-party and the annotation protocol is peer-reviewed.

## Evidence Checklist

| Criterion | Status | Evidence |
|---|---|---|
| Every number traceable to an executed experiment | ✅ | 10/10 experiments `USED_IN_MANUSCRIPT`; all tables/figures auto-generated from `results/<EXP_ID>/` |
| GPU execution as source of truth | ✅ | Kaggle kernels; refs in Table X |
| Reproducible environment | ✅ | `requirements.txt` = verified stack; seeds 42 / 0–9; immutable Kaggle input bundle |
| Results archived persistently | ✅ | HF `MoshinAli/skill-gap-experiments` (incl. VALID01 pair-level results) + Kaggle `studyhub991/skill-gap-inputs-v1` |
| Statistical rigor | ✅ | Bootstrap CIs (1,000×) for SGI/deficits/effects/κ; Wald CIs; VIF; effect sizes; χ²+Cramér's V; multi-seed CV |
| Honest negative/null results | ✅ | Internship ns (p=0.62); external AUC corrected down to 0.576; tree near-perfection diagnosed as label artifact; lexical κ=0.11 reported against our own lexical baseline |
| **Human validation of the matcher** | ✅ | **VALID01: κ=0.737 [0.711, 0.760], acc 87.9%, AUC 0.961 vs expert SkillSpan→ESCO mappings; ESCO grounding 91%/99% of top-100** |
| Theoretical grounding | ✅ | HCT, Signaling, Constructive Alignment, SBTC tied to specific findings |
| Build integrity | ✅ | 13 pp, 0 LaTeX errors, 0 undefined refs, 0 BibTeX errors, 48 citations |

## Risk Register (updated)

| # | Risk | Severity | Status / Mitigation |
|---|------|----------|---------------------|
| 1 | ~~No human gold-standard for the matcher~~ | ~~High~~ | **RESOLVED** by VALID01 (external expert gold, κ=0.737) |
| 2 | Domain-gap deficits small & corpus not CS-specific | Medium | Limitations 7–8; relative severity rule; conditional-demand framing; optional ALIGN04 sensitivity |
| 3 | Tier-2 benchmarks semi-deterministic (k-of-n labels) | Medium | Fully disclosed; tree audit (99.92%) + external validation; framed as a contribution |
| 4 | External AUC modest (0.768 / 0.576) | Medium | Discussed as domain shift with in-sample refs for context |
| 5 | Geographic concentration (85.2% US) | Low–Med | Limitation 6 |
| 6 | Validity is external-gold, not in-house corpus labels | Low | Limitation 4 states this explicitly; a reviewer-requested in-house κ (300 pairs, 2 raters) is a ~1-day follow-up |

## Journal Fit Notes

- **Strong fits:** *Computers & Education: AI*, *Education and Information
  Technologies*, *Interactive Learning Environments*, *Smart Learning
  Environments*; stretch: *Computers & Education* / *IEEE Trans. Education*.
- 13 pages IEEEtran ≈ 10 KPI words; mechanical conversion for
  Elsevier/Springer targets (~½ day).
- Selling points: (i) dual lexical–semantic instrument with bootstrap CIs;
  (ii) externally validated matcher (κ, AUC vs expert gold); (iii) complete
  provenance chain Kaggle→HF→auto-generated LaTeX; (iv) honest benchmark
  diagnostics (k-of-n audit).

## Pre-Submission To-Do

1. Choose target journal; convert template; write cover letter.
2. Optional: in-house double-annotation (300 pairs) if targeting top Q1.
3. Optional: ALIGN04 CS-corpus sensitivity appendix.
4. Optional: Zenodo/OSF DOI for the code archive alongside HF/Kaggle.
