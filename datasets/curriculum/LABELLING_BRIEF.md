# Labelling Brief — CURR02 Validation Samples (author gate)

*2 files, 200 short decisions, ~25–35 minutes. Fill only the `rater_label`
column (and `rater_notes` when unsure). Leave the files' row order untouched.*

Both files are in `datasets/curriculum/extracted/`. No analysis is computed
until you finish or explicitly waive; CURR02 stays blocked either way.

## File 1 — `validation_precision_100.csv` (extracted phrases)

Question per row: **"Is this phrase genuine curriculum skill/content text
from the course (a topic, learning outcome, prerequisite skill, or syllabus
statement)?"**

| `rater_label` | Use when |
|---|---|
| `yes` | Real curriculum content: "Topics: C/C++ Data Types...", "Students should know Python", "Module 3. Selection", "Dynamic programming and greedy algorithms" |
| `no` | Boilerplate the extractor should not have kept: instructor bios, grading logistics ("midterm will be worth 30%"), cookie/nav text, license text, file listings ("1-rsg.zip"), page furniture |

Notes:
- Short topic items ("Programming Languages", "04. Divide and conquer") → `yes` if they name a skill/topic.
- Prerequisite sentences ("Prospective students should know C++") → `yes` (deliberately kept: they carry skill content).
- Phrases starting with `Topics:` are recovered Stanford lists → judge the list, not the marker.

## File 2 — `validation_recall_100.csv` (dropped sentences)

Question per row: **"Should the extractor have kept this sentence as curriculum
content?"** (i.e., did a filter wrongly drop real content?)

| `rater_label` | Use when |
|---|---|
| `yes_keep` | The dropped sentence was actually curriculum content (e.g. a real topic lost to a filter) |
| `no_drop` | The drop was correct: junk/too short/boilerplate ("Recitation.", "Prof. Strang", instructor bio, department list) |

The `drop_reason` column tells you which rule fired — the study checks each
rule:
- `too_short` (< 12–40 chars): mostly fragments → usually `no_drop`, but a real short topic ("Binary search trees") is `yes_keep`.
- `metadata_section` / `duplicate`: instructor bios, department names → almost always `no_drop`.
- `assessment_logistics` / `enrollment_logistics`: grading/admin text → `no_drop` unless it embeds real topics.

## What happens after

1. I compute: precision (design-weighted), recall (design-weighted using cell
   sizes in `extraction_summary.json`), and per-rule error rates.
2. If precision/recall clear the bar (>= 0.90 precision; recall errors reviewed
   individually), CURR02 gets registered and run with the same (K, P, τ) as
   ALIGN01/02, seed 42.
3. Any `yes_keep` dropped items are enumerated in the paper (they quantify the
   extraction-recall limitation honestly — they are not silently re-added).

If you disagree with any `no`/`no_drop` while labelling, just flip the label —
the rater column is yours; my filter opinions do not override it.
