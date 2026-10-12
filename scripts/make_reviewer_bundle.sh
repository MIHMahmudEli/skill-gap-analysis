#!/usr/bin/env bash
# Build a history-free, identifier-free reviewer bundle from a CLEAN tree.
#
# Usage:  bash scripts/make_reviewer_bundle.sh [output_dir]
# Default output dir: ./reviewer_bundle (never committed; add to .gitignore).
#
# The bundle is a plain directory: no .git, no history, no account handles.
# After building, scripts/verify_reviewer_bundle.sh greps every file for the
# known identifiers and checks every PDF for metadata leaks, and fails loudly.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
OUT="${1:-$ROOT/reviewer_bundle}"

if [ -n "$(git -C "$ROOT" status --porcelain)" ]; then
    echo "REFUSING: working tree is not clean. Commit or stash first so the" >&2
    echo "bundle is reproducible from a single commit." >&2
    exit 2
fi
HEAD_SHA="$(git -C "$ROOT" rev-parse --short HEAD)"
echo "bundle source commit: $HEAD_SHA"

rm -rf "$OUT"
mkdir -p "$OUT"
git -C "$ROOT" archive HEAD | tar -x -C "$OUT"

# ---------------------------------------------------------------- 1. exclusions
# History is already absent (git archive).  These paths are removed because they
# carry account handles, third-party material we may not redistribute, or
# pre-publication working files that reviewers should not see.
rm -rf "$OUT"/audit "$OUT"/archive "$OUT"/reports "$OUT"/labelling "$OUT"/.github
rm -f  "$OUT"/LICENSE "$OUT"/README.md
rm -f  "$OUT"/scripts/verify_reviewer_bundle.sh   # holds the identifier list by design
rm -f  "$OUT"/datasets/cs2023/CS2023_BoK.pdf        # third-party copyright
rm -f  "$OUT"/results/worker_map.json "$OUT"/results/registry.json   # namespaces
find "$OUT"/results -name metadata.json -delete                        # kernel/user handles
find "$OUT" \( -name '*.aux' -o -name '*.log' -o -name '*.bbl' \
              -o -name '*.blg' -o -name '*.out' \) -delete

# ---------------------------------------------------------------- 2. README
cp "$ROOT"/scripts/reviewer_README.md "$OUT"/README.md

# ---------------------------------------------------------------- 3. scrub code
# Two account strings live inside executable code as default values / comments
# (the Kaggle input-bundle slug and the output-archive slug).  They are replaced
# by placeholders in the BUNDLE ONLY; the repository keeps them so the pipeline
# still runs on the original hosts.  Everything else is byte-identical.
python - "$OUT" <<'PY'
import pathlib, sys
out = pathlib.Path(sys.argv[1])
SUBS = [
    ("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1", "/kaggle/input/<INPUT_BUNDLE>"),
    ("studyhub991/skill-gap-inputs-v1", "<INPUT_BUNDLE>"),
    ("MoshinAli/skill-gap-experiments", "<OUTPUT_ARCHIVE>"),
    ("studyhub991", "<ACCOUNT>"),
    ("MoshinAli", "<ACCOUNT>"),
    # The GitHub handle was NOT in this list before batch-4 step 5, so the
    # bundle leaked it: experiments/ is retained (unlike archive/, reports/,
    # audit/ and labelling/, which are removed), and the ALIGN05 pre-reg
    # amendments A3/A4 name the repository as MIHMahmudEli/skill-gap-analysis
    # while explaining why the sealed key was retired. Caught by
    # verify_reviewer_bundle.sh, which already grepped for this identifier -
    # the scrub simply had to catch up with the verifier.
    ("MIHMahmudEli/skill-gap-analysis", "<REPO_SLUG>"),
    ("MIHMahmudEli", "<ACCOUNT>"),
    ("mdmohsin11222", "<EMAIL_LOCALPART>"),
]
n = 0
for p in out.rglob("*"):
    if not p.is_file():
        continue
    try:
        s = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    orig = s
    for a, b in SUBS:
        s = s.replace(a, b)
    if s != orig:
        p.write_text(s, encoding="utf-8", newline="\n")
        n += 1
print("scrubbed %d file(s)" % n)
PY

# ---------------------------------------------------------------- 4. verify
bash "$ROOT"/scripts/verify_reviewer_bundle.sh "$OUT"

echo "bundle ready: $OUT"
