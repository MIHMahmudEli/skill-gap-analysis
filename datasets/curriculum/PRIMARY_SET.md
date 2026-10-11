# Primary Analysis Set Determination (CURR02)

> **Superseded in part, 2026-10-12 (protocol amendment §9d):** the *main*
> CURR02 result uses **all 26 modern units** with institution-aware inference
> (institution-clustered bootstrap, institution-weighted SGI,
> leave-one-institution-out). The n = 20 capped set below is retained as the
> pre-registered **≤8/institution subsample sensitivity analysis**
> (deterministic manifest-order rule). Counts and bar checks below are
> unchanged historical record.

*Computed 2026-10-11 · Branch `q1-revision` · Before any SGI value was computed
on this corpus. Rule fixed at extraction time; no analysis output exists yet.*

## 1. Selection rule (deterministic, analysis-independent)

1. Keep MANIFEST rows with `extraction_status == extracted` and
   `vintage_group == modern` (material year >= 2019, per §6b).
2. Apply the ≤8-courses-per-institution cap by keeping the **first 8 rows in
   MANIFEST file order**. MANIFEST order was fixed pre-download and is the
   same deterministic convention §6b uses for backup swaps; no phrase counts,
   skill counts, or SGI values entered this rule.
3. Everything trimmed stays in the corpus for the vintage-sensitivity group;
   trimming only bounds the primary analysis set.

## 2. Primary set (n = 20)

| unit_id | institution | region | stratum | level | material_year |
|---|---|---|---|---|---|
| MIT-6006 | MIT | North America | theory | upper | Spring 2020 |
| MIT-6036 | MIT | North America | applied | upper | Fall 2020 |
| MIT-6100L | MIT | North America | applied | intro | Fall 2022 |
| MIT-18404J | MIT | North America | theory | upper | Fall 2020 |
| MIT-18S191 | MIT | North America | applied | intro | Fall 2022 |
| MIT-1805 | MIT | North America | theory | intro | Spring 2022 |
| TUD-ALG | TU Delft | Europe (NL) | theory | upper | 2023 |
| TUD-DS | TU Delft | Europe (NL) | applied | upper | 2020+ |
| TUD-AI1 | TU Delft | Europe (NL) | applied | intro | 2023 |
| TUD-AI2 | TU Delft | Europe (NL) | applied | intro | 2023 |
| TUD-QI | TU Delft | Europe (NL) | theory | upper | 2023 |
| TUD-TOC | TU Delft | Europe (NL) | theory | upper | 2020+ |
| TUD-AST | TU Delft | Europe (NL) | applied | upper | 2019+ |
| TUD-AST2 | TU Delft | Europe (NL) | applied | intro | 2019+ |
| HARV-CS50 | Harvard | North America | applied | intro | 2026 (CS50x) |
| HARV-CS50AI | Harvard | North America | applied | upper | current edition |
| HARV-CS50PY | Harvard | North America | applied | intro | current edition |
| HARV-CS50SQL | Harvard | North America | applied | intro | current edition |
| HARV-CS50WEB | Harvard | North America | applied | upper | current edition |
| HARV-CS50CYB | Harvard | North America | applied | intro | current edition |

Composition: MIT 6 / TU Delft 8 / Harvard 6 · level 10 intro / 10 upper ·
stratum 6 theory / 14 applied.

Harvard material-year evidence (2026-10-11): unversioned CS50 URLs serve the
current edition (HTTP Last-Modified 2026-10; `/ai/2024/` versioned page exists
-> course active >= 2024). Recorded in MANIFEST notes.

## 3. Bar check (protocol §4 / §6b)

| Bar | Required | Observed | Verdict |
|---|---|---|---|
| Courses in primary set | >= 20 | 20 | PASS |
| Institutions | >= 3 | 3 | PASS |
| Courses per institution | <= 8 | 8 (TU Delft) | PASS |
| Material year | >= 2019 | all modern | PASS |
| **Regions** | **>= 3** | **2 (North America, Europe)** | **FAIL — hard STOP** |

## 4. Region-bar failure (author decision required)

The corpus can only reach two regions:

* North America — MIT, Harvard, Stanford (extracted).
* Europe — TU Delft (extracted); Open University UK 403'd (excluded, §6b).
* "Other" region — no license-eligible source existed in the approved frame:
  NPTEL/SWAYAM (India) excluded at plan stage (all-rights-reserved, TOU
  prohibits bulk download); Helsinki/MinnaLearn excluded (all rights reserved).
  Note that even a working Open University would still be Europe, so the
  ≥3-region bar was **unattainable from the approved-institution list (§5) as
  frozen** — this is a pre-registration design inconsistency, surfaced now
  rather than after extraction.

Protocol §4 mandates STOP-and-report on an unmet bar; CURR02 must not run
until the author chooses one of:

* **(A)** Waive to ≥2 regions via a dated protocol amendment, with the region
  limitation stated in the manuscript (defensible: the missing region is
  license-blocked, not overlooked).
* **(B)** Authorize adding a license-clean "other"-region source (requires a
  source-list amendment + license verification + fetch before CURR02).
* **(C)** Do not run CURR02 (curriculum result reduced to CURR01 CS2023).

## 5. Trimmed by the ≤8 cap (retained in corpus, not in primary)

TUD-GSE (applied), TUD-FP (theory), TUD-QC (theory), TUD-SV (applied),
TUD-AIP (applied), TUD-AI3 (applied) — all TU Delft, rows 9–14 in MANIFEST
order.

## 6. Vintage-sensitivity group (legacy)

15 units: MIT-60001, MIT-60002, MIT-6033, MIT-6034, MIT-6042, MIT-6046,
MIT-6824, MIT-6828 (MIT OCW), plus Stanford SEE CS107, CS229, EE261, EE263,
EE364A, EE364B. Reported separately, never pooled with the primary set.

## 7. Known deviation from the stratified target

§4's approximate ~50/50 theory/applied target is not met by the primary set
under the deterministic rule above: 6 theory / 14 applied (30/70). The binding
constraint is Harvard CS50 (all 6 courses applied). The imbalance is a property
of the frame, not of the trim: any ≤8-cap choice for TU Delft yields at most
8/20 theory, because MIT contributes 3 and Harvard 0. Reported as a corpus
limitation; the trim rule was not adjusted to flatter the target, since doing so
would introduce post-freeze discretion.
