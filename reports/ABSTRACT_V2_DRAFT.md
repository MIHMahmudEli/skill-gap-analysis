# Abstract v2 — DRAFT ONLY (2026-10-12, batch-2 step 3)

**Status: not applied.** `paper/main.tex` still carries the current abstract (with the
minimal A6 fix from step 1). This file holds the author's requested v2 draft for
review. Title is **not** changed (`main.tex` line 36 still reads "Bridging the Higher
Education--Workforce Divide: ... Natural Language Processing and Machine Learning").

## Constraints (author instruction 2026-10-12)

- [x] No mention of placement (no cohorts, no classifiers, no benchmark outcomes)
- [x] No mention of synthetic data (silent — neither "synthetic" nor "generated")
- [x] No "15 datasets" headline (corpus described only as the real LinkedIn-family
      posting data + the curriculum corpus)
- [x] States that until CURR02 the reference profile is posting-derived
- [x] States that all gap results rest on one scrape family
- [x] Ranges in bracket notation `[0.52, 0.74]` and `[0.26, 0.42]`
- [x] 2–3 candidate titles conditional on the CURR02 outcome (below); current title kept

## Abstract v2 draft

Disparities between higher-education curricula and labor-market skill demands are
widely reported, yet large-scale empirical studies that link hiring requirements with
what curricula actually teach remain limited. We measure academic--industry skill
alignment from two sources: a real job-posting corpus from the LinkedIn family
(1,348,454 postings acquired in 2024, including a nested 519,814-posting
skill-annotated subset — a single scrape family) and a curriculum corpus (the CS2023
curricular guidelines together with a 26-unit modern course reading set). Until the
registered curriculum-precision study (CURR02) completes, academic skill requirements
are proxied by an employer-derived, *posting-derived* reference profile (1,167 postings
across five occupational categories) rather than by institutionally collected syllabi,
and every skill-gap result reported here rests on that one scrape family. Grounded in
Human Capital Theory, Job-Market Signaling, and Constructive Alignment, the analysis
combines: (1) n-gram skill extraction across an eight-category taxonomy; (2) semantic
vector alignment via Sentence-BERT (`all-MiniLM-L6-v2`) across four cosine-similarity
thresholds (τ ∈ {0.4, 0.5, 0.6, 0.7}); and (3) registered sensitivity analysis with
1,000-fold bootstrap confidence intervals, an expert-gold validation on published ESCO
mappings (κ = 0.737), and a computational anchor to the CS2023 guidelines. Exact string
matching yields an apparent Skill Gap Index (SGI) of 0.52 (registered range
[0.52, 0.74]); dense semantic alignment reduces the estimate to 0.32 at τ = 0.5 (95%
bootstrap CI [0.23, 0.41]; registered range [0.26, 0.42]), a 20-point reduction.
Deficits concentrate in emerging technical areas — Cloud Infrastructure (2.45 pp
lexical, 0.94 pp after semantic alignment) and Programming & Development (1.69 pp
lexical) — while soft-skill requirements are fully covered, indicating that a
substantial share of the apparent gap is vocabulary divergence between academic
descriptors and recruitment postings rather than absent coverage.

**Number provenance:** 1,348,454 / 519,814 / 1,167 = `datasets/DATASET_MANIFEST.csv`
(one scrape family per `datasets/OVERLAP_AUDIT.csv`); 0.52 / 0.32 / [0.23, 0.41] =
`results/ALIGN01_lexical_bootstrap`, `ALIGN02_semantic_sbert`; ranges [0.52, 0.74] /
[0.26, 0.42] = `results/SENS01_sgi_sensitivity`; κ = 0.737 =
`results/VALID01_esco_gold`; 2.45 / 0.94 / 1.69 pp = `results/ALIGN03_domain_gap`;
26-unit curriculum set = `datasets/curriculum/SELECTION_PROTOCOL.md` §9d.

**Known tension to resolve at CURR02:** the curriculum corpus is described in the
corpus sentence, but its *reference-profile* role depends on CURR02 passing the
precision/recall gate — which is exactly what the "posting-derived until CURR02"
sentence discloses.

## Candidate titles (conditional on CURR02 outcome — do NOT apply yet)

**Strong** (CURR02 passes the ≥0.90 precision/recall gate and curriculum reference
corroborates the posting-derived deficits):

> From Lexicon to Embeddings: A Replicable Measure of the Academic–Industry Skill Gap
> from Job Postings and Curricular Guidelines

**Mixed** (curriculum attestation partial — corroboration on some domains, divergence
on others):

> Vocabulary or Competence? Separating Lexical Divergence from Skill Gaps in
> Academic–Industry Alignment

**Weak** (CURR02 fails its gate, is waived, or the curriculum reference cannot be
corroborated — measurement-first, no gap-existence claim):

> An Audit of Skill-Gap Measurement: Reference-Profile Provenance and Threshold
> Sensitivity in Academic–Industry Alignment

Current title (kept until the CURR02 ruling):

> Bridging the Higher Education–Workforce Divide: A Large-Scale Empirical Analysis of
> Academic–Industry Skills Misalignment Using Natural Language Processing and Machine
> Learning
