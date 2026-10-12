# Abstract v3 — two alternatives (print-only drafts; NOT applied to `paper/main.tex`)

Author instruction 2026-10-12 (batch 2, step 3). Both drafts are 200–250 words and obey
the stated rules: "pre-specified" instead of "registered"; no pending-study language; no
26-unit curriculum set unless CURR02 results exist; the lexical-to-semantic change written
as "20 percentage points"; soft-skill coverage attributed to the *reference profile*; the
vocabulary-divergence reading stated as "consistent with", with VALID01 precision/recall
and the gold-set distribution caveat; one scrape family stated explicitly.

Every number below comes from a committed results artifact:
`results/VALID01_esco_gold/metrics.json` (κ, precision, recall, AUC),
`results/ALIGN01_lexical_gap/metrics.json` + `results/ALIGN02_semantic_gap/metrics.json`
(52.0% → 32.0%, CIs, 20 percentage points), `results/ALIGN04_linkedin_superset/metrics.json`
(37%/14%), `results/CURR01_cs2023_anchor/metrics.json` (30.4%), and the domain-deficit
rows of the ALIGN03 artifact (Cloud 2.45/0.94 pp, Programming 1.69 pp).

---

## v3a — CURR02 *completed*, gap measured against real curricula

> Disparities between higher-education curricula and labor-market skill demands are widely
> reported, yet large-scale studies that link hiring requirements with what curricula
> actually teach remain limited. We examine academic--industry alignment using 15 open
> datasets (2.12M unique records after removing linked-table and nested-corpus duplication);
> every posting corpus comes from one scrape family (a 2024 LinkedIn scrape and its nested
> HuggingFace subset), and academic skill requirements are proxied by an employer-derived
> occupational reference profile (1,167 job postings across five occupational categories)
> and, for the curricular comparison, by \[N\_COURSES] course descriptions from
> \[N\_PROGRAMMES] computing programmes. N-gram skill extraction over an eight-category
> taxonomy is combined with Sentence-BERT alignment across four cosine thresholds
> ($\tau \in \{0.4, 0.5, 0.6, 0.7\}$; 1,000-fold bootstrap intervals). Exact string matching
> yields a Skill Gap Index (SGI) of 52.0\%; semantic alignment reduces this by 20 percentage
> points to 32.0\% at $\tau = 0.5$ (95\% CI [23.0\%, 41.0\%]). Against the measured
> curricula the semantic SGI is \[CURR02\_SGI\_SEMANTIC] (lexical \[CURR02\_SGI\_LEXICAL]).
> Soft-skill requirements are fully covered by the reference profile, while residual
> deficits concentrate in Cloud Infrastructure (2.45 pp lexical, 0.94 pp semantic) and
> Programming \& Development (1.69 pp lexical). The matcher agrees with published expert
> ESCO mappings at $\kappa = 0.737$ (precision 91.9\%, recall 75.7\%, ROC-AUC 0.961), and
> both gap indices re-check on the nested superset (37\%/14\%). The magnitude of the
> lexical-to-semantic reduction is consistent with vocabulary divergence accounting for part
> of the gap, given that precision and recall are measured on a gold set skewed toward
> software-development mentions. Findings support modular technical coursework in fast-moving
> toolchains.

**Fill-ins required before this can be applied** (all from CURR02 artifacts that do not yet
exist): `N_COURSES`, `N_PROGRAMMES`, `CURR02_SGI_SEMANTIC`, `CURR02_SGI_LEXICAL`. If CURR02
lands under the pre-specified gate, the third sentence can also name the curriculum set
explicitly; if it lands above it, this draft must not be used and v3b applies instead.

---

## v3b — CURR02 *not completed* or waived (no curricular gap size claimed)

> Disparities between higher-education curricula and labor-market skill demands are widely
> reported, yet large-scale studies that link hiring requirements with what curricula
> actually teach remain limited. We examine academic--industry alignment using 15 open
> datasets (2.12M unique records after removing linked-table and nested-corpus duplication);
> every posting corpus comes from one scrape family (a 2024 LinkedIn scrape and its nested
> HuggingFace subset), and academic skill requirements are proxied by an employer-derived
> occupational reference profile (1,167 job postings across five occupational categories)
> rather than by institutionally collected syllabi. N-gram skill extraction over an
> eight-category taxonomy is combined with Sentence-BERT alignment across four cosine
> thresholds ($\tau \in \{0.4, 0.5, 0.6, 0.7\}$; 1,000-fold bootstrap intervals). Exact
> string matching yields a Skill Gap Index (SGI) of 52.0\%; semantic alignment reduces this
> by 20 percentage points to 32.0\% at $\tau = 0.5$ (95\% CI [23.0\%, 41.0\%]), and to 46.0\%
> ([37.0\%, 56.0\%]) at $\tau = 0.7$. Soft-skill requirements are fully covered by the
> reference profile, while residual deficits concentrate in Cloud Infrastructure (2.45 pp
> lexical, 0.94 pp semantic) and Programming \& Development (1.69 pp lexical). The matcher
> agrees with published expert ESCO mappings at $\kappa = 0.737$ (precision 91.9\%, recall
> 75.7\%, ROC-AUC 0.961), and both gap indices re-check on the nested superset (37\%/14\%).
> Coverage of the reference profile against the CS2023 curricular Body of Knowledge is 30.4\%
> by embedding coverage, a computational anchor rather than a human curriculum audit, so no
> curricular gap size is claimed. The magnitude of the lexical-to-semantic reduction is
> consistent with vocabulary divergence accounting for part of the gap, given that precision
> and recall are measured on a gold set skewed toward software-development mentions. Findings
> support modular technical coursework in fast-moving toolchains.

**No fill-ins.** This draft is apply-ready once the author rules on it; it contains no
pending-study language, no 26-unit set, and claims no curricular gap size.

---

## Applied change in this step (main.tex)

Only the wording fix was applied to `paper/main.tex` (abstract): the phrase
"independent 1.29M-posting LinkedIn corpus" is now "a nested LinkedIn superset drawn from
the same scrape family (1.29M postings)", and "replication" is now "a re-check" — matching
the §IV-B statement that ALIGN04 is "a sample-size extension within one scrape family, not
an independent replication".
