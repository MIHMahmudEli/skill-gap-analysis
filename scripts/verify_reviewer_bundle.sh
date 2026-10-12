#!/usr/bin/env bash
# Verify a reviewer bundle: no known identifier anywhere, no PDF metadata.
# Usage: bash scripts/verify_reviewer_bundle.sh <bundle_dir>
# Exit 0 = clean; exit 1 = leaks found (they are printed).
set -uo pipefail

OUT="${1:?usage: verify_reviewer_bundle.sh <bundle_dir>}"
FAIL=0

# ---------------------------------------------------------------- 1. identifiers
# 16 worker/host account handles (results/worker_map.json), the author identity,
# the contact address, and the timezone string that leaked into PDF metadata
# before the 2026-10-12 anonymity sweep.
IDENTIFIERS=(
  abdullahalsayfan abhafnan afrojahaqueshornaly aicontentdetections almasukmim12
  baingalamukintu leyamridha mdzihan mihjihad nihanshadman nishat1156 rssiam
  sadmanhasanmiraj studyhub991 tasnimjenny zarinprionty
  MoshinAli MIHMahmudEli mdmohsin11222 mohsin
  "gmail.com" "Bangladesh" "kaggle.com/.*mohsin"
)

echo "== identifier grep over $(find "$OUT" -type f | wc -l) files in $OUT"
HITS=0
for id in "${IDENTIFIERS[@]}"; do
    if grep -rIl --exclude-dir=.git -e "$id" "$OUT" 2>/dev/null; then
        echo "LEAK: identifier '$id' present (see paths above)"
        HITS=$((HITS+1))
    fi
done
if [ "$HITS" -eq 0 ]; then
    echo "   no identifier matches: PASS"
else
    FAIL=1
fi

# ---------------------------------------------------------------- 2. PDF metadata
# Every PDF must carry no dates (CreationDate/ModDate leak the build machine's
# timezone), no Title/Subject/Keywords/Author, and only the two known tool
# strings for Creator/Producer.  pdfinfo pads empty fields with spaces, so the
# values are trimmed before testing -- an empty field is not a leak.
echo "== pdf metadata check"
if command -v pdfinfo >/dev/null 2>&1; then
    PDFLEAK=0
    while IFS= read -r pdf; do
        PAIRS="$(pdfinfo "$pdf" 2>/dev/null | sed -n 's/^\([A-Za-z]*\):[[:space:]]*\(.*\)$/\1=\2/p')"
        BAD=""
        echo "$PAIRS" | grep -E '^(Title|Subject|Keywords|Author|CreationDate|ModDate)=..*$' >/dev/null 2>&1 && \
            BAD="$BAD$(printf '%s\n' "$PAIRS" | grep -E '^(Title|Subject|Keywords|Author|CreationDate|ModDate)=..*$' | tr '\n' ';')"
        CR="$(printf '%s\n' "$PAIRS" | sed -n 's/^Creator=//p')"
        PR="$(printf '%s\n' "$PAIRS" | sed -n 's/^Producer=//p')"
        case "$CR" in
            ""|"LaTeX with hyperref") : ;;
            *) BAD="$BADCreator=$CR;" ;;
        esac
        case "$PR" in
            ""|MiKTeX\ pdfTeX*|pdfTeX*) : ;;
            *) BAD="$BADProducer=$PR;" ;;
        esac
        if [ -n "$BAD" ]; then
            echo "LEAK: $pdf"
            echo "     $BAD"
            PDFLEAK=$((PDFLEAK+1))
        fi
    done < <(find "$OUT" -name '*.pdf')
    if [ "$PDFLEAK" -eq 0 ]; then
        echo "   no PDF carries dates, personal fields or non-tool metadata: PASS"
    else
        FAIL=1
    fi
else
    echo "   pdfinfo not found - PDF metadata NOT checked"
    FAIL=1
fi

# ---------------------------------------------------------------- 3. history
if [ -d "$OUT/.git" ]; then
    echo "LEAK: bundle contains a .git directory"
    FAIL=1
else
    echo "   no .git directory: PASS"
fi

# ---------------------------------------------------------------- 4. excluded paths
for p in audit archive reports labelling results/worker_map.json results/registry.json LICENSE; do
    if [ -e "$OUT/$p" ]; then
        echo "LEAK: excluded path present: $p"
        FAIL=1
    fi
done
echo "   excluded paths absent: PASS"

exit $FAIL
