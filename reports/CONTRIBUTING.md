# Contributing / agent operating rules

Binding rules for anyone or anything working in this repository — human or agent.
They exist because of two incidents in October 2026; each rule below is pointed at
the damage it prevents.

## 1. No push without explicit author approval — hard rule

**Do not `git push` to any remote without the author's explicit written approval
in the current conversation.** Not "probably fine", not after a green gate run —
explicit, in writing, for that push.

Why: on 2026-10-12 a push to `main` published
`experiments/align05_titles_200_key.csv`, the sealed key for the pre-registered
ALIGN05 blinded validation gate, **before a single label existed**. That voided
the gate: once public, any labelling done afterwards could have been shaped by
the key, so the ≥0.90 precision-and-recall bar could no longer be interpreted as
blinded. Deleting the file does not fix it — history, GitHub's CDN cache and any
forks retain it. The only repair was to retire the sample and redraw under a new
seed (`experiments/ALIGN05_PREREG.md` amendment A3;
`archive/align05_titles_200_key_RETIRED.md`).

Enforcement: `scripts/pre-push` refuses every push unless `ALLOW_PUSH=1` is set,
**and** independently refuses if any tracked file matches a sealed-key pattern.
Set `ALLOW_PUSH=1` only on the author's explicit go-ahead:

```
ALLOW_PUSH=1 git push origin <branch>
```

Install the hook once per clone:

```
git config core.hooksPath scripts
```

## 2. Sealed keys never enter this repository

A sealed key is any file that tells a rater what the right answer is — strata,
sampling weights, rule predictions, gold labels. Rules:

- Keys live **outside** the repository directory, e.g. `../sealed_keys/`.
- They are read via an environment variable (`ALIGN05_KEY`) or an explicit
  argument, never via a repo-relative path.
- `.gitignore` rejects `*_key*.csv`, `*key*.csv.bak`, `sealed/`, `sealed*/` and
  `**/sealed_keys/`.
- `tests/test_no_tracked_secrets.py` fails the suite if a tracked file matches
  those patterns. There is exactly one allowlist entry — the already-public
  retired key kept as a leak record. **Do not add to it.**
- Never print, `cat`, `head`, or paste a key into a transcript, a report, a
  commit message or a log. "I only read the header" is still a leak.

If a key does get published: **do not rewrite history.** Report it, then repair by
redrawing the sample under a fresh seed with the new key held outside the repo.

## 3. Labels are the author's; gates are mechanical

- Never fill, edit, infer or "clean up" a file under `labelling/`. They are blank
  by design until the author (or an author-appointed rater) labels them.
- Never open the sealed key before labelling is finished — including in a
  dry-run, including "just to check the schema".
- A gate failure **stops** the pipeline. Print the observed metric and the
  pre-specified revision rule; do not proceed, do not soften the bar, do not
  re-run on a fresh sample to chase a pass.
- Partial label fills are not results. The gate is undetermined until every row
  is labelled.

## 4. Every number comes from a committed artifact

- No manuscript number may be hand-transcribed. Tables and figures are generated
  from `results/`, and `experiments/make_latex.py --check` asserts all 14 tables
  regenerate byte-identically.
- Registered experiments write only under `results/<EXPERIMENT_ID>/` via
  `SKILLGAP_OUTPUT_DIR`. Never overwrite a committed artifact to "fix" a value —
  if a number changes, that is a finding, and it is reported, not quietly applied.
- `reproduce_stats.py` and the five Sentence-BERT experiments do not run on the
  author's laptop (a local Application Control policy blocks `statsmodels` and
  `torch`). Do not claim full CPU reproducibility in the manuscript; the
  committed text says 8 of 13 re-ran bit-exactly and 5 are unverified on CPU.

## 5. Do not run what is gated

`CURR02`, `ALIGN05` and `ALIGN06` are blocked on author input (labels; a licence
checklist). Do not run them, do not download their inputs, and do not create
`results/` entries for them. `scripts/run_after_labels.sh` is the only sanctioned
path, and it stops at the gate until labels exist.

## 6. Branches and scope

- Work happens on `q1-revision`. Do not merge, rebase away, or force-push.
- Commit each unit of work separately, with gates green after every commit.
- A stop-point must be honored, not talked around: a gate failing for a
  non-mechanical reason, a registered number that would change, or any step that
  would require labels, downloads, or running a gated study.
