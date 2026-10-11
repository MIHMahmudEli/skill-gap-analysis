# Phase 10 — Figures, Tables & Visual Consistency

*Date: 2026-10-11 · Build: `paper/main.pdf` 16 pp, clean.*

## 10.1 Inventory (all present)

| Asset | File | Caption / role | Status |
|---|---|---|---|
| Fig.1 | `fig1_top_skills.pdf` | Top market skills (RQ1) | ✓ |
| Fig.2 | `fig2_skill_gap.pdf` | SGI lexical vs semantic + τ-sweep | ✓ |
| Fig.3a/b | `fig3a_geo_shares.pdf`, `fig3b_ai_trends.pdf` | GEO01 shares; TRENDS01 AI trajectories | ✓ |
| Fig.4a/b | `fig4a_placement_effect_sizes.pdf`, `fig4b_placement_means.pdf` | Cohen's *d*; group means (STAT01) | ✓ |
| Fig.5 | `fig5_internship.pdf` | INTL01 internship employment rates | ✓ |
| Tab.I | `tab_datasets` (in main.tex) | Provenance — **corrected counts + linked-pair note** | ✓ Phase 9 |
| Tab.II | `tab_sensitivity` | τ-sweep SGI | ✓ |
| — | `tab_semantic_matches` | Sample SBERT pairs | ✓ |
| Tab.III | `tab_validity` | VALID01 expert agreement | ✓ |
| Tab.IV | `tab_crosscorpus` | **Rewritten as matched-profile 2×2** (audit off-diagonals) | ✓ Phase 9/10 |
| Tab.V | `tab_cs2023` | CURR01 per-KA coverage | ✓ |
| Tab.VI | `tab_gap` | ALIGN03 domain deficits | ✓ |
| Tab.VII–XI | descriptive/VIF/logistic/model_comparison/multiseed | STAT01 chain | ✓ |
| Tab.XII | `tab_experiments` | 12-experiment registry | ✓ |
| Tab.XIII | hypotheses (in main.tex) | **H6 → STAT01, RD −0.44 pp** | ✓ Phase 9 |

## 10.2 `tab_crosscorpus` Manual Override

`make_latex.py` still emits the legacy HF(P=100)-vs-LinkedIn(P=500) table.
The tracked `paper/tables/tab_crosscorpus.tex` was **hand-updated** to the
matched-profile 2×2 (bold = published ALIGN01/02/04 cells; off-diagonals from
`audit/_sgi_sensitivity/`). Regenerating via `make_latex.py` would clobber
this; either port the 2×2 into `make_latex.py` or skip regeneration until
done. **Known footgun — documented here and in 08_reproducibility.md.**

## 10.3 Consistency Checks

- All `\ref` targets resolve (no undefined in log).
- Figure Ns in captions match section narrative (GEO01 1.35M wording uses
  corrected 1,348,454 in Table I; figure caption “1.35M” is fine as rounding).
- Page count 16 (was 15 pre-audit): +revision log + expanded §IV-B2.
- No float barriers crossed badly (placeins + stfloats as before).

## 10.4 Optional Follow-ups (non-blocking)

- Add PR-AUC / majority-baseline column to external-validation table (Phase 6 rec).
- Visual PDF page diff (pdftoppm) spot-check — layout already clean by log.
- Port matched-profile 2×2 into `make_latex.py` for full auto-regen parity.
