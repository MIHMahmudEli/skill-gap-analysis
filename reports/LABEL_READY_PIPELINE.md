# Label-ready pipeline — `scripts/run_after_labels.sh`

Author instruction 2026-10-12 (batch 3, step 5). One command per study, to be run
**once labels exist**, so that a single invocation carries a study from its gate to
green checks with no human sequencing:

```
bash scripts/run_after_labels.sh curr02   [LABELLING_DIR]
bash scripts/run_after_labels.sh align05  [LABELLING_DIR]
```

Fixed order, identical for both studies:

1. `labelling/score_labels.py` — the pre-specified gate
2. **if and only if the gate PASSES** — the registered experiment
3. `experiments/verify.py`
4. `experiments/make_latex.py --check`
5. `audit/verify_claims.py`

A gate **failure stops the pipeline before any experiment runs**, printing the
observed metric next to the pre-specified revision rule. A **partial label fill
also stops**: the gate is not determined until every row is labelled, so a
half-filled file cannot silently produce a provisional figure that reads as final.
Nothing under `labelling/` is ever written; `LABELLING_DIR` defaults to `labelling`
and accepts a scratch directory for dry-runs.

## The two gates (the scorer's own, unchanged)

| Study | Gate | Source |
|---|---|---|
| CURR02 | precision ≥ 0.90 | `score_labels.py` `[1]` bar line |
| ALIGN05 | design-weighted tech precision ≥ 0.90 **AND** recall ≥ 0.90 | `score_labels.py` `[3]` GATE line |

CURR02's recall is **reported with its design-weighted estimate and stratified-bootstrap
CI but carries no numeric bar** — `LABELLING_BRIEF.md` "What happens after" item 2 fixes
the bar at ≥ 0.90 precision and requires recall errors to be *reviewed individually*.
The pipeline prints recall and its CI for that review and gates on precision alone,
which is what the pre-specification says.

## Revision rules printed on failure

**ALIGN05** (`experiments/ALIGN05_PREREG.md` §5.4, quoted verbatim in the output):
revise the rule set — version bump, amendment note listing every changed rule — and
re-validate on a **fresh** stratified 200-title sample; at most two revisions, then the
author decides (waive with disclosure or defer ALIGN05). The already-drawn sample may
not be reused for a revised rule, because the rule has now seen it. The output states
that no precision/recall figure may be reported until the gate passes on a fresh sample
or the gate is waived and the waiver recorded in `metrics.json`
(`validation_waived: true`) with the author's dated instruction quoted.

**CURR02** has **no auto-revision rule** — the bar's failure means CURR02 is not
registered and not run on that corpus, and the decision is the author's. The output
states the two documented options: (a) waive with disclosure, the extraction-recall
limitation stated in the manuscript and the enumerated `yes_keep` items reported
honestly; (b) revise the extractor (version bump, amendment note), re-extract, draw a
**fresh** validation sample with the same design (seed 42), re-label, and re-apply the
gate from scratch.

## After the gate: the experiment module does not exist yet

Neither study has an `exp_scripts/` module today — both are label-gated and absent from
`results/registry.json`. That is deliberate: the analysis code is written **only after
the gate clears**, so no code could have been shaped by unlabelled data. The pipeline
therefore stops at stage 2 with the exact path it expects
(`experiments/exp_scripts/curr02_curriculum_sgi.py`,
`experiments/exp_scripts/align05_title_validation.py`) and the instruction to register
it, after which stages 3–5 run automatically. A gate PASS with no module is reported as
such rather than as a completed study.

## Dry-run evidence (scratch copies; `labelling/` never touched)

Three simulated scenarios, each a full copy of the three CSVs plus a scratch
`LABELLING_DIR`. Simulated labels only; no label file was edited in place.

| # | Scenario | Expected | Observed | Exit |
|---|---|---|---|---|
| 1 | CURR02, all kept phrases real + all drops correct | precision 1.000 → PASS, stop at missing module | `GATE: PASS - precision = 1.000 … estimated recall = 1.000`, then stage-2 stop naming the absent module | 6 |
| 2 | ALIGN05, 120/200 filled | incomplete → STOP before the gate | `STOP: ALIGN05 labels incomplete (120/200 …)` | 4 |
| 3 | ALIGN05, 200/200 filled all `tech` | precision 1.000, recall 0.035 → FAIL + revision rule | `GATE: FAIL - precision = 1.000, recall = 0.035`, then §5.4 verbatim | 5 |

Exit codes are distinct per failure class (3 scorer failure, 4 incomplete, 5 gate fail,
6 no module, 7–10 stage failures), so a wrapper can branch on the cause.

### Blinding preserved in dry-run output

ALIGN05's scorer prints per-row disagreement listings that reveal the **sealed key's**
predictions (`pred=tech/non-tech` per `sample_id`). Because the author has not labelled
yet, showing those in a dry-run would leak the answer key. In scratch mode the pipeline
cuts the output at the `disagreement rows` header and prints a withheld notice; the
full listing is available on a real run, when labelling is already complete.

### Two defects found and fixed during the dry-runs

1. **Header parse bypassed the incomplete-fill STOP.** The scorer's header reads
   `…(align05_titles_200.csv): 120/200 author_label filled` — colon-space, not
   slash-space — so the original `s|.*/ ([0-9]+)/…|` pattern never matched, both
   `filled` and `total` captured the whole line, compared equal, and the STOP was
   silently skipped. Caught because dry-run 1 only passed by luck (its fill was
   complete). Both studies' patterns fixed to `s|.* ([0-9]+)/…|`; dry-run 2 now exits 4.
2. **Section context overrun.** `grep -A 6` on the `[1]` header reached into the `[2]`
   header, printing that block twice; context is now per-call (`[1]` gets 3 lines).
   The scorer's output also carries a non-UTF8 box-drawing dash, so every `grep` forces
   text mode with `-a`.

## What this does not do

It does not run CURR02, ALIGN05 or ALIGN06 — no label exists, and the author has
excluded them. It does not write to `labelling/`, `results/`, or the registry. It adds
no number to any manuscript. It is sequencing and gating only.
