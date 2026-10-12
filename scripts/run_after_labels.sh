#!/usr/bin/env bash
# Label-ready pipeline (batch 3, step 5). One command per study, to be run
# ONCE the author's labels exist:
#
#   bash scripts/run_after_labels.sh curr02   [LABELLING_DIR]
#   bash scripts/run_after_labels.sh align05  [LABELLING_DIR]
#
# Fixed order:
#   1. labelling/score_labels.py   -> the pre-specified gate
#   2. if (and only if) the gate PASSES: the registered experiment
#   3. experiments/verify.py
#   4. experiments/make_latex.py --check
#   5. audit/verify_claims.py
#
# A gate FAILURE stops the pipeline before any experiment runs and prints the
# observed metric next to the pre-specified revision rule. A partial label fill
# also stops: the gate is not determined until every row is labelled.
#
# Nothing under labelling/ is ever written. Pass a scratch directory as $2 to
# dry-run against simulated labels (reports/LABEL_READY_PIPELINE.md).
#
# Gates are the scorer's, unchanged:
#   curr02  precision >= 0.90                     (score_labels.py [1] bar line)
#   align05 precision >= 0.90 AND recall >= 0.90  (score_labels.py [3] GATE line)

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

STUDY="${1:-}"
LAB="${2:-labelling}"

if [[ "$STUDY" != "curr02" && "$STUDY" != "align05" ]]; then
  echo "usage: bash scripts/run_after_labels.sh {curr02|align05} [LABELLING_DIR]" >&2
  exit 2
fi
if [[ ! -d "$LAB" ]]; then
  echo "ERROR: labelling directory '$LAB' not found" >&2
  exit 2
fi

DRYRUN=0
if [[ "$LAB" == "labelling" || "$LAB" == "./labelling" ]]; then
  echo "NOTE: scoring the real labelling/ package (read-only)."
else
  DRYRUN=1
  echo "NOTE: dry-run against scratch labels at '$LAB' (labelling/ untouched)."
fi

echo "========================================================================"
echo "  LABEL-READY PIPELINE - study: ${STUDY}   (labels dir: ${LAB})"
echo "========================================================================"

# ---------------------------------------------------------------- stage 1: gate
echo
echo "--- stage 1/5: score_labels.py gate -------------------------------------"
# The ALIGN05 sealed key lives OUTSIDE the repo. Honour an explicit 3rd arg,
# else ALIGN05_KEY from the environment, else the ../sealed_keys/ default.
if [[ "$STUDY" == "align05" ]]; then
  if [[ -n "${3:-}" ]]; then
    export ALIGN05_KEY="$3"
  fi
  KEY_PATH="${ALIGN05_KEY:-$ROOT/../sealed_keys/align05_titles_200_key.csv}"
  if [[ ! -f "$KEY_PATH" ]]; then
    echo "ERROR: ALIGN05 sealed key not found at: $KEY_PATH"
    echo "It lives OUTSIDE the repository by design. Pass it as the 3rd argument or"
    echo "export ALIGN05_KEY=<path>. Never commit a key - see"
    echo "archive/align05_titles_200_key_RETIRED.md for why."
    exit 3
  fi
  echo "sealed key: $KEY_PATH (read-only; never printed)"
fi
SCORER_OUT="$(mktemp)"
if ! LABELLING_DIR="$LAB" ALIGN05_KEY="${KEY_PATH:-}" python labelling/score_labels.py >"$SCORER_OUT" 2>&1; then
  echo "ERROR: score_labels.py did not run. Output:"
  cat "$SCORER_OUT"
  rm -f "$SCORER_OUT"
  exit 3
fi

# The scorer output carries at least one non-UTF8 byte (a box-drawing dash in its
# docstring), so every grep below forces text mode with -a. Context counts are
# bounded so one section's context cannot overrun into the next section's header.
section() { grep -a -A "${2:-6}" -- "$1" "$SCORER_OUT"; }

GATE_PASS=0
OBSERVED=""

if [[ "$STUDY" == "curr02" ]]; then
  section "^\[1\] curriculum precision" 3
  section "^\[2\] curriculum recall" 6

  hdr1=$(grep -a -m1 "^\[1\] curriculum precision" "$SCORER_OUT")
  filled_p=$(echo "$hdr1" | sed -E 's|.* ([0-9]+)/([0-9]+) rater_label.*|\1|')
  total_p=$(echo "$hdr1"  | sed -E 's|.* ([0-9]+)/([0-9]+) rater_label.*|\2|')
  bar_line=$(grep -a -m1 "bar: >= 0.90 ->" "$SCORER_OUT")
  recall_line=$(grep -a -m1 "estimated recall =" "$SCORER_OUT")
  precision=$(grep -a -m1 "    precision = " "$SCORER_OUT" | sed -E 's|.*precision = ([0-9.]+).*|\1|')
  recall=$(echo "$recall_line" | sed -E 's|.*recall = ([0-9.]+).*|\1|')

  echo
  if [[ "${filled_p:-0}" != "${total_p:-0}" || -z "$precision" ]]; then
    echo "STOP: curriculum labels incomplete (${filled_p:-0}/${total_p:-0} precision rows scored)."
    echo "      The gate is not determined until every row is labelled."
    echo "      Complete labelling/curriculum_precision_100.csv and"
    echo "      labelling/curriculum_recall_100.csv, or waive explicitly."
    rm -f "$SCORER_OUT"; exit 4
  fi

  OBSERVED="precision = ${precision} (bar >= 0.90); estimated recall = ${recall:-n/a} (design-weighted)"
  if [[ "$bar_line" == *"PASS"* ]]; then
    GATE_PASS=1
    echo
    echo "GATE: PASS - ${OBSERVED}"
  else
    echo
    echo "GATE: FAIL - ${OBSERVED}"
    echo
    echo "Pre-specified consequence (datasets/curriculum/LABELLING_BRIEF.md, 'What happens"
    echo "after' item 2): the >= 0.90 precision bar is not cleared, so CURR02 is NOT"
    echo "registered and NOT run on this corpus. There is no auto-revision rule for"
    echo "CURR02; the decision is the author's, and the documented options are:"
    echo "  (a) waive with disclosure -- the extraction-recall limitation is stated in"
    echo "      the manuscript and the enumerated yes_keep items are reported honestly;"
    echo "  (b) revise the extractor (version bump, amendment note listing every changed"
    echo "      rule), re-extract, draw a FRESH validation sample with the same design"
    echo "      (seed 42), and re-label. The gate is then re-applied from scratch."
    echo "No CURR02 run, no table, and no manuscript number may be produced until one"
    echo "of those two paths is taken and recorded."
    rm -f "$SCORER_OUT"; exit 5
  fi
else  # align05
  if [[ "$DRYRUN" == "1" ]]; then
    # Print the gate section but STOP before the per-row disagreement listing:
    # those rows show the sealed key's predictions (pred=tech/non-tech), and the
    # author must not see them before labelling.
    awk '/ALIGN05 title gate/{p=1}
         p && /disagreement rows/{print "    [disagreement rows withheld: dry-run output must not reveal the sealed key]"; exit}
         p{print}' "$SCORER_OUT"
  else
    section "^\[3\] ALIGN05 title gate" 12
  fi

  hdr3=$(grep -a -m1 "^\[3\] ALIGN05 title gate" "$SCORER_OUT")
  filled_a=$(echo "$hdr3" | sed -E 's|.* ([0-9]+)/([0-9]+) author_label.*|\1|')
  total_a=$(echo "$hdr3"  | sed -E 's|.* ([0-9]+)/([0-9]+) author_label.*|\2|')
  gate_line=$(grep -a -m1 "GATE: precision" "$SCORER_OUT")
  a_precision=$(grep -a -m1 "design-weighted TECH precision = " "$SCORER_OUT" | sed -E 's|.*precision = ([0-9.]+).*|\1|')
  a_recall=$(grep -a -m1 "design-weighted TECH recall" "$SCORER_OUT" | sed -E 's|.*recall.*= ([0-9.]+).*|\1|')

  echo
  if [[ "${filled_a:-0}" != "${total_a:-0}" || -z "$a_precision" ]]; then
    echo "STOP: ALIGN05 labels incomplete (${filled_a:-0}/${total_a:-0} author_label filled)."
    echo "      The gate is not determined until all 200 rows are labelled."
    echo "      Complete labelling/align05_titles_200.csv without opening"
    echo "      experiments/align05_titles_200_key.csv, or waive explicitly."
    rm -f "$SCORER_OUT"; exit 4
  fi

  OBSERVED="precision = ${a_precision}, recall = ${a_recall} (both bars >= 0.90)"
  if [[ "$gate_line" == *"PASS"* ]]; then
    GATE_PASS=1
    echo
    echo "GATE: PASS - ${OBSERVED}"
  else
    echo
    echo "GATE: FAIL - ${OBSERVED}"
    echo
    echo "Pre-specified revision rule (experiments/ALIGN05_PREREG.md 5.4, verbatim):"
    echo "  revise the rule set (version bump, amendment note listing every changed"
    echo "  rule), re-validate on a FRESH stratified 200-title sample; at most two"
    echo "  revisions, then the author decides (waive with disclosure or defer"
    echo "  ALIGN05)."
    echo "The already-drawn 200-title sample may not be re-used for a revised rule:"
    echo "the rule has now seen it. ALIGN05 does not run, and no precision/recall"
    echo "figure may be reported, until the gate passes on a fresh sample or the"
    echo "gate is waived and the waiver recorded in metrics.json"
    echo "(validation_waived: true) with your dated instruction quoted."
    rm -f "$SCORER_OUT"; exit 5
  fi
fi

# ------------------------------------- stage 2: the registered experiment
echo
echo "--- stage 2/5: registered experiment ------------------------------------"
case "$STUDY" in
  curr02)  EXP_SCRIPT="experiments/exp_scripts/curr02_curriculum_sgi.py"
           EXP_ID="CURR02_curriculum_sgi" ;;
  align05) EXP_SCRIPT="experiments/exp_scripts/align05_title_validation.py"
           EXP_ID="ALIGN05_title_validation" ;;
esac

if [[ ! -f "$EXP_SCRIPT" ]]; then
  echo "GATE PASSED, but the registered experiment module for ${STUDY} does not exist yet:"
  echo "    ${EXP_SCRIPT}"
  echo "It is written and registered only now that the gate has cleared, so that no"
  echo "analysis code could have been shaped by unlabelled data. Write it against the"
  echo "frozen design (${STUDY} prereg), register it in results/registry.json, then"
  echo "re-run this command; stages 3-5 will execute automatically."
  rm -f "$SCORER_OUT"; exit 6
fi
mkdir -p "results/${EXP_ID}"
echo "running ${EXP_SCRIPT} -> results/${EXP_ID}/"
SKILLGAP_OUTPUT_DIR="results/${EXP_ID}" python "$EXP_SCRIPT" || { rm -f "$SCORER_OUT"; exit 7; }

# ---------------------------------------------------------------- stage 3: verify
echo
echo "--- stage 3/5: experiments/verify.py ------------------------------------"
python experiments/verify.py || { rm -f "$SCORER_OUT"; exit 8; }

# ------------------------------------------------- stage 4: table regeneration
echo
echo "--- stage 4/5: experiments/make_latex.py --check -------------------------"
python experiments/make_latex.py --check || { rm -f "$SCORER_OUT"; exit 9; }

# --------------------------------------------------------- stage 5: claims
echo
echo "--- stage 5/5: audit/verify_claims.py -----------------------------------"
python audit/verify_claims.py || { rm -f "$SCORER_OUT"; exit 10; }

rm -f "$SCORER_OUT"
echo
echo "========================================================================"
echo "  ${STUDY}: gate PASS, experiment run, all four checks green."
echo "========================================================================"
exit 0
