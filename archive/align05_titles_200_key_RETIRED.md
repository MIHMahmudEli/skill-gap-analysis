# RETIRED — ALIGN05 validation-sample key (v1, seed 42)

**Status: retired, not secret.** This file is retained only because it is already in
public git history; it is not a valid validation key and must never be used to score
ALIGN05.

## Why it was retired

The key was committed to a **public** GitHub repository (`MIHMahmudEli/skill-gap-analysis`,
`main`) on 2026-10-12 **before a single `author_label` existed**. It carries, per
`sample_id`, the stratum, sampling weight, matched rule, predicted SOC code and predicted
class — i.e. the answer key for the 200-title blinded labelling sample.

Once public, the ALIGN05 pre-registered gate (design-weighted tech precision ≥ 0.90 **and**
recall ≥ 0.90, `experiments/ALIGN05_PREREG.md` §5.4) can no longer be interpreted as a
*blinded* validation: any labelling done afterwards could have been shaped by this file,
consciously or not. Deleting it from a later commit does not restore blinding — the blobs
remain reachable in history, and GitHub's CDN cache and any forks retain copies. The only
honest repair is a **fresh sample drawn under a new seed, with its key held outside the
repository**.

## What was and was not done with it

| | |
|---|---|
| Labels made against it | **none** — `labelling/align05_titles_200.csv` was and is fully blank |
| Scoring run with it | **none** — no ALIGN05 metrics.json or result artifact was ever committed |
| Rule revision informed by it | **none** — `experiments/align05_title_rules_v1.json` is byte-identical to its first commit (SHA-256 `9F0410507C23313C99517CEC9D40A1CC0697CD29192A89357F0E321234F1429D`), touched once, at sample creation |
| Git history rewritten | **no** — moved out of the active path by an ordinary commit; no force-push, no rebase, no filter-branch |

## Replaced by

A new stratified 100 + 100 sample, same frame, same strata, same frozen v1 rule set,
drawn with a **new seed recorded in `experiments/ALIGN05_PREREG.md`** (not 42). Its key is
written to a path **outside the repository** (`../sealed_keys/`, gitignored), and
`labelling/score_labels.py` plus `scripts/run_after_labels.sh` read it from an environment
variable (`ALIGN05_KEY`) or explicit argument. Repository guards (a test and a pre-push
hook) now fail on any tracked `*_key*.csv`, `sealed*/`, or sealed-key path pattern, so this
class of leak cannot recur silently.

Retired 2026-10-12 by author instruction, on the record.
