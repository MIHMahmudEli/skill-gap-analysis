# Labelling Package — 3 files, 400 decisions

*Consolidated 2026-10-12 (author instruction). Nothing here is filled in;
only the author (or author-appointed raters) label. No analysis, CURR02, or
ALIGN05 run happens until these are labelled or explicitly waived.*

Fill the designated label column **in place** (Excel / LibreOffice / any text
editor), keep row order and all other columns untouched, save as CSV (UTF-8).
Vocabulary is given per file below; the scorer also accepts 1/0.

---

## 1. `curriculum_precision_100.csv` (100 rows) — curriculum detail sheet:
   `datasets/curriculum/LABELLING_BRIEF.md` §File 1

Question per row: *Is this phrase genuine curriculum skill/content text from
the course?*

- `yes` — real content (topic, learning outcome, prerequisite, syllabus line)
- `no` — boilerplate the extractor should not have kept (instructor bios,
  grading logistics, nav/cookie text, file listings, page furniture)

Fill `rater_label`. A second rater may fill `rater2_label` **blind and
independent** (same rules); this yields an inter-rater Cohen's kappa.
Optional `rater_notes` whenever unsure.

## 2. `curriculum_recall_100.csv` (100 rows) — detail sheet: same brief §File 2

Question per row: *Should the extractor have kept this dropped sentence?*

- `yes_keep` — wrongly dropped curriculum content
- `no_drop` — drop was correct (fragment, metadata, duplicate, logistics)

Fill `rater_label`. `drop_reason` shows which rule fired — judge the text,
not the rule. Dropped-but-real items are enumerated in the paper as the
recall limitation; they are **not** silently re-added.

## 3. `align05_titles_200.csv` (200 rows) — ALIGN05 title classifier gate

Question per row: *Does this **job title** denote a computing/IT occupation?*

- `tech` — a role in the ALIGN05 SOC list (computing/IT: software, QA, web,
  database, network/systems admin, IT support, security, CS research, data
  scientist/ML, or IT management such as CTO/CIO/IT director)
- `non-tech` — anything else, **including** engineering outside computing
  (civil, mechanical, electrical hardware, chemical), sciences, analysts
  without a computing role, business/sales/marketing, healthcare, etc.

Judge **the title only** — skills text is off-limits by the pre-registration
firewall (`experiments/ALIGN05_PREREG.md` §2). `rule_matched` /
`predicted_soc` / `predicted_tech` show what the frozen v1 rule set predicted;
ignore them as evidence, label the title yourself. Fill `author_label`.

---

## After labelling

Run `python labelling/score_labels.py`. It reports, per file, the filled
counts, then:

- **Curriculum:** extraction precision with Wilson 95% CI; design-weighted
  extraction recall with stratified-bootstrap CI (cell sizes from
  `datasets/curriculum/extracted/extraction_summary.json`); per-drop-reason
  error rates; rater1-vs-rater2 Cohen's kappa when `rater2_label` is filled.
  Gate per `LABELLING_BRIEF.md`: precision ≥ 0.90, recall errors reviewed
  individually → CURR02 may then be registered (still pre-specified; nothing
  runs automatically).
- **ALIGN05:** design-weighted tech precision AND recall (stratified
  estimator per `ALIGN05_PREREG.md` §5.3) with bootstrap CIs; F1; Cohen's
  kappa vs the rule predictions; every disagreement row listed. Gate:
  precision ≥ 0.90 **and** recall ≥ 0.90 → PASS, else the ≤2-revision rule
  applies (version bump + fresh sample, never relabel in place).
