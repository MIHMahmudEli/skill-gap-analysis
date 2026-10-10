# Q1-Readiness Assessment

*Assessment date: 2026-10-10 · Artifact assessed: `paper/main.pdf` (12 pp) +
`experiments/` + `results/registry.json` + HF archive.*

## Verdict: **CONDITIONALLY READY** (2–4 days of remaining work)

The empirical and reproducibility core now meets Q1 standards; the residual
work is packaging (commit, license, journal format) and one recommended
methodological strengthening (human agreement sample).

## Evidence Checklist

| Criterion | Status | Evidence |
|---|---|---|
| Every number traceable to an executed experiment | ✅ | 9/9 experiments `USED_IN_MANUSCRIPT`; `make_latex.py` emits all tables/figures from `results/<EXP_ID>/` |
| GPU execution as source of truth | ✅ | All kernels on Kaggle GPU/CPU instances; refs in Table X of the manuscript |
| Reproducible environment | ✅ | `requirements.txt` = verified stack; seeds fixed (42; 0–9 multi-seed); input bundle on Kaggle |
| Results archived persistently | ✅ | HF `MoshinAli/skill-gap-experiments` + Kaggle `studyhub991/skill-gap-inputs-v1` |
| Statistical rigor | ✅ | Bootstrap CIs (1,000×) for SGI/deficits/effects; Wald CIs for ORs; VIF; effect sizes; chi-square + Cramér's V; multi-seed CV |
| Honest negative/null results | ✅ | Internship ns in College model (p=0.62) reported; external AUC corrected *down* to 0.576; tree near-perfection diagnosed as label artifact |
| Theoretical grounding | ✅ | HCT, Signaling, Constructive Alignment, SBTC connected to specific findings |
| Build integrity | ✅ | 12 pp, 0 LaTeX errors, 0 undefined refs, 0 BibTeX errors, 45 citations |
| Human validation of NLP labels | ❌ | No Cohen's κ — see Risk 1 |
| Data representativeness | ⚠️ | Soft-skill/healthcare-heavy corpus; US-centric LinkedIn — see Risks 2–3 |

## Risk Register

| # | Risk | Severity | Mitigation in manuscript | Recommended action |
|---|------|----------|--------------------------|--------------------|
| 1 | No human gold-standard for skill extraction/matching | High (reviewer magnet) | Limitation 4 acknowledges it | Annotate ~300 skill pairs with 2 raters, report κ, add one subsection (½ day) |
| 2 | Domain-gap deficits small & corpus not CS-specific | Medium | Limitations 7–8; relative severity rule; conditional-demand framing | Optional `ALIGN04` sensitivity on LinkedIn/USA corpus as appendix (1 day) |
| 3 | Tier-2 benchmarks semi-deterministic (k-of-n labels) | Medium | Fully disclosed; tree audit (99.92%) and external validation included | Keep as a *feature* of the contribution (diagnostic framing) — it already is |
| 4 | External AUC modest (0.768 / 0.576) | Medium | Discussed as domain shift; in-sample refs (0.782/0.714) shown for context | Add calibration/decision-curve note in rebuttal if pressed |
| 5 | Geographic concentration (85.2% US) | Low–Med | Limitation 6 | Optional: add India/APAC Tier-1 sensitivity later |
| 6 | Single-corpus SGI (no cross-corpus replication) | Low | Top-100 dual-profile design + τ sweep | Position SGI as a measurement instrument; replicate in future work |

## Journal Fit Notes

- **Strong fits:** *Computers & Education* (empirical, large-scale, theory-informed),
  *Computers & Education: AI*, *Education and Information Technologies*,
  *IEEE Transactions on Education* (methodological framing).
- 12 pages IEEEtran double-column ≈ 9–10 KPI words — likely requires
  reformatting for Elsevier/Springer targets (mechanical, ~½ day).
- Title/abstract emphasize the dual lexical–semantic instrument and the
  diagnostic ML audit; both are defensible novelty claims vs. the
  curriculum-alignment literature cited in §II.

## Pre-Submission To-Do (in order)

1. Commit the working tree (22 changed files) — awaiting owner approval.
2. Add `LICENSE` (MIT) — referenced by README, currently missing.
3. (Recommended) Human agreement sample → κ subsection + limitation update.
4. Choose target journal; convert template; write cover letter.
5. Optional: `ALIGN04` corpus-sensitivity appendix; archive code on
   Zenodo/OSF with a DOI to cite alongside the HF/Kaggle artifacts.
