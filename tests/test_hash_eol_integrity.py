"""Hash/EOL integrity: a recorded SHA-256 must verify on every machine.

Motivated by the A2/A3 hash puzzle (ALIGN05_PREREG amendment A4). The frozen
rule set ``experiments/align05_title_rules_v1.json`` is cited by SHA-256 in a
pre-registration and hard-checked by the sample builder. Because the repo is
cloned on Windows with ``core.autocrlf=true``, Git rewrites its LF newlines to
CRLF in the working tree, so hashing the bytes on disk yields one hash
(``9F0410...``) while hashing the LF-normalised bytes -- what the blob stores
and what A2 cites -- yields another (``09BC778E...``). Both are "right"; only
the LF form is reproducible across platforms.

These tests pin the invariant: every recorded hash is compared against
LF-normalised bytes, and the files that carry hashes are forced to ``eol=lf``
so the two forms converge. They also re-verify the canonical input checksums,
which are immune to this bug only because their targets are untracked.

No network, no key access, no labels read.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RULES = ROOT / "experiments" / "align05_title_rules_v1.json"
BUILDER = ROOT / "experiments" / "build_align05_validation_sample.py"
CHECKSUMS = ROOT / "datasets" / "input_checksums.sha256"
GITATTRIBUTES = ROOT / ".gitattributes"

# The canonical (LF-normalised) SHA-256, as cited in ALIGN05_PREREG A2 and A4.
CANONICAL_RULES_SHA = "09BC778E67C884ECE38EDEC81B57DF70123EBE331F932D9441D6A12DBFCB7E36"
# The CRLF working-tree SHA-256 -- NOT canonical, recorded only so this test can
# prove the two are being distinguished rather than conflated.
CRLF_RULES_SHA = "9F0410507C23313C99517CEC9D40A1CC0697CD29192A89357F0E321234F1429D"


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest().upper()


def lf_norm(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def git_blob(rev_path: str) -> bytes:
    return subprocess.run(["git", "show", rev_path], cwd=ROOT,
                          capture_output=True, check=True).stdout


def test_rules_hash_is_canonical_under_lf_normalisation():
    """The frozen rule set's LF-normalised hash must equal the recorded value."""
    assert sha256(lf_norm(RULES.read_bytes())) == CANONICAL_RULES_SHA


def test_blob_and_working_tree_agree():
    """The committed blob must be LF and must hash to the same canonical value.

    This is what makes the recorded hash reproducible on a Linux/macOS clone as
    well as on a Windows one: the blob is the machine-independent reference.
    """
    blob = git_blob("HEAD:experiments/align05_title_rules_v1.json")
    assert b"\r" not in blob, "committed blob must be pure LF"
    assert sha256(blob) == CANONICAL_RULES_SHA
    assert blob == lf_norm(RULES.read_bytes()), (
        "working tree differs from the blob after EOL normalisation -- the "
        "file's content changed, not just its line endings"
    )


def test_builder_checks_lf_normalised_bytes_not_raw():
    """The builder must normalise EOLs and expect the canonical hash.

    Regression guard for the exact bug: a raw-bytes ``read_bytes()`` hash would
    pass on Linux and fail on Windows for an unchanged file.
    """
    src = BUILDER.read_text(encoding="utf-8")
    assert 'replace(b"\\r\\n", b"\\n")' in src, (
        "builder must LF-normalise before hashing; hashing raw working-tree "
        "bytes makes the check platform-dependent"
    )
    assert CANONICAL_RULES_SHA in src, "builder must expect the canonical hash"
    # The CRLF hash must NOT be the expected value.
    m = re.search(r"EXPECTED_RULES_SHA\s*=\s*\(?\"([0-9A-F]+)\"", src)
    assert m, "could not locate EXPECTED_RULES_SHA in the builder"
    assert m.group(1) == CANONICAL_RULES_SHA, (
        f"builder expects {m.group(1)}, which is not the canonical LF hash"
    )


def test_gitattributes_forces_lf_for_hash_recorded_files():
    """.gitattributes must pin eol=lf on every file that carries a recorded hash."""
    text = GITATTRIBUTES.read_text(encoding="utf-8")
    for f in ("experiments/align05_title_rules_v1.json", "datasets/input_checksums.sha256"):
        pat = re.compile(rf"^{re.escape(f)}\s+.*eol=lf", re.M)
        assert pat.search(text), f".gitattributes must force eol=lf for {f}"


def test_gitattributes_has_no_invalid_attribute_lines():
    """git must be able to parse .gitattributes without complaining.

    An indented '# comment' continuation line is parsed as a pattern, not a
    comment, and git emits 'is not a valid attribute name'.
    """
    proc = subprocess.run(["git", "check-attr", "-a", "--", "README.md"],
                          cwd=ROOT, capture_output=True, text=True)
    combined = proc.stdout + proc.stderr
    assert "is not a valid attribute name" not in combined, combined


def test_canonical_input_checksums_still_verify():
    """Every recorded input checksum must match the file's bytes on disk.

    These are safe from the CRLF/LF bug only because their targets are
    *untracked* (gitignored) and so never pass through EOL normalisation. This
    test pins that assumption: if a hashed input ever became tracked, a CRLF
    checkout would silently break its recorded hash.
    """
    assert CHECKSUMS.exists()
    tracked = set(subprocess.run(["git", "ls-files"], cwd=ROOT,
                                 capture_output=True, text=True,
                                 check=True).stdout.split())
    ok = 0
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("MISSING"):
            continue
        m = re.match(r"([0-9a-fA-F]{64})\s+(.+?)(?:\s+\(.*)?$", line)
        if not m:
            continue
        rec, path = m.group(1).upper(), m.group(2).strip()
        p = ROOT / path
        assert p.exists(), f"recorded input missing locally: {path}"
        assert path not in tracked, (
            f"{path} is hashed in input_checksums.sha256 AND tracked; a CRLF "
            "checkout would then change its bytes and break the recorded hash. "
            "Either untrack it or add eol=lf for it in .gitattributes."
        )
        assert sha256(p.read_bytes()) == rec, f"checksum mismatch for {path}"
        ok += 1
    assert ok >= 9, f"expected to verify the 9 canonical inputs, saw {ok}"


# ---------------------------------------------------------------------------
# Text encoding: a stray non-UTF-8 byte makes a file silently un-scrubbable.
# ---------------------------------------------------------------------------
# Why this test exists (batch 4, step 5). `scripts/make_reviewer_bundle.sh`
# removed identifiers from the bundle by reading each file as UTF-8, and its
# scrub loop used to `continue` on `UnicodeDecodeError`. Three markdown files
# carried isolated CP1252 bytes (em dash 0x97, multiplication sign 0xd7,
# section sign 0xa7) that PowerShell here-strings had written, so those files
# were undecodable and were skipped WITHOUT a word - which is exactly how the
# GitHub handle survived in `experiments/ALIGN05_PREREG.md` and reached a
# bundle that then had to be rejected by verify_reviewer_bundle.sh. The scrub
# now tolerates such bytes, but the repository should not contain them at all.
# ---------------------------------------------------------------------------

BINARY_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".gz", ".zip",
                   ".pkl", ".npy", ".npz", ".pt", ".bin"}


def test_tracked_text_files_are_valid_utf8():
    """Every tracked non-binary file must decode as UTF-8.

    A single CP1252 byte (from a Windows console write) makes the file
    undecodable, which previously caused the reviewer-bundle scrub to skip it
    silently and let an identifier through.
    """
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.split()
    bad = []
    for f in tracked:
        p = ROOT / f
        if not p.is_file() or p.suffix.lower() in BINARY_SUFFIXES:
            continue
        try:
            p.read_bytes().decode("utf-8")
        except UnicodeDecodeError as e:
            bad.append(f"{f}: byte 0x{e.object[e.start]:02x} at offset {e.start}")
    assert not bad, (
        "tracked text files that are not valid UTF-8 (write files as UTF-8, "
        "not via a CP1252 console here-string):\n  " + "\n  ".join(bad)
    )


def test_reviewer_bundle_scrub_tolerates_non_utf8_bytes():
    """The bundle scrub must not silently skip an undecodable file.

    Regression guard for the leak: the loop used to `continue` on
    UnicodeDecodeError, so a file with one stray byte was never scrubbed and
    carried its identifiers into the bundle unnoticed.
    """
    src = (ROOT / "scripts" / "make_reviewer_bundle.sh").read_text(encoding="utf-8")
    body = src[src.index('python - "$OUT" <<\'PY\''):src.index("\nPY\n")]
    assert "surrogateescape" in body, (
        "the bundle scrub must read with errors='surrogateescape' so a file "
        "with non-UTF-8 bytes is still scrubbed rather than silently skipped"
    )
    assert "except (UnicodeDecodeError, OSError):\n        continue" not in body, (
        "the bundle scrub silently skips undecodable files; this is how the "
        "GitHub handle reached a bundle (see ALIGN05_PREREG.md, batch-4 step 5)"
    )
    # and the GitHub handle must be among the identifiers it scrubs
    for ident in ("MIHMahmudEli", "mdmohsin11222"):
        assert f'("{ident}"' in body, f"bundle scrub does not replace {ident}"



def test_no_recorded_hash_is_the_crlf_variant_in_new_code():
    """New/edited code must not cite the CRLF variant as if it were canonical.

    The retired-key note and pre-reg A3 legitimately quote 9F0410... as
    historical evidence of the confusion; the builder and any live check must
    not.
    """
    live = [BUILDER, ROOT / "labelling" / "score_labels.py",
            ROOT / "scripts" / "run_after_labels.sh"]
    for f in live:
        src = f.read_text(encoding="utf-8")
        assert CRLF_RULES_SHA not in src, (
            f"{f} cites the CRLF working-tree hash {CRLF_RULES_SHA}; the "
            f"canonical value is {CANONICAL_RULES_SHA} (see ALIGN05_PREREG A4)"
        )


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all hash/EOL integrity checks pass")
