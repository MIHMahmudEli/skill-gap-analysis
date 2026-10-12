"""Guard: no sealed key may ever be tracked in this repository.

Motivated by the 2026-10-12 leak: `experiments/align05_titles_200_key.csv` was
committed to a public GitHub repository before any label existed, which voided the
pre-registered ALIGN05 blinded gate and forced a full sample re-draw under a new
seed (ALIGN05_PREREG amendment A3; archive/align05_titles_200_key_RETIRED.md).

These tests fail if a file matching a sealed-key pattern is tracked, so the same
class of leak cannot recur silently. They are cheap and run with the normal suite.

One explicit allowlist entry exists, for the retired key that is ALREADY public and
is retained deliberately as a record of the leak. Do not add to it.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Patterns that must never match a tracked path.
FORBIDDEN = [
    re.compile(r"(^|/)[^/]*_key[^/]*\.csv$", re.I),   # *_key*.csv
    re.compile(r"(^|/)[^/]*key[^/]*\.csv\.bak$", re.I),
    re.compile(r"(^|/)sealed(/|$)", re.I),            # sealed/ anywhere
    re.compile(r"(^|/)sealed[^/]*/", re.I),           # sealed*/ anywhere
    re.compile(r"(^|/)sealed_keys(/|$)", re.I),
]

# The ONLY tolerated match: already-public, retained as a leak record.
# (path, reason)
ALLOWLIST = {
    "archive/align05_titles_200_key_RETIRED.csv":
        "retired v1 key, already public in git history; kept as a record of the "
        "2026-10-12 leak. Not a valid key - never use it to score ALIGN05.",
}


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]


def test_no_tracked_sealed_key():
    """No tracked path may match a sealed-key pattern, bar the one allowlist entry."""
    offenders = []
    for path in tracked_files():
        if any(p.search(path) for p in FORBIDDEN):
            if path in ALLOWLIST:
                continue
            offenders.append(path)
    assert not offenders, (
        "SEALED KEY TRACKED - these paths must never be committed. Keys live "
        "OUTSIDE the repo (../sealed_keys/) and are read via ALIGN05_KEY. "
        f"Offenders: {offenders}"
    )


def test_allowlist_is_minimal_and_documented():
    """The allowlist must stay a single, explicitly justified entry."""
    assert len(ALLOWLIST) == 1, (
        f"allowlist must hold exactly the one retired key, found {len(ALLOWLIST)}: "
        f"{sorted(ALLOWLIST)}"
    )
    (path, reason), = ALLOWLIST.items()
    assert path.startswith("archive/"), "allowlisted keys must live under archive/"
    assert "RETIRED" in path, "allowlisted key must be named RETIRED"
    assert len(reason) > 40, "allowlist entries need a written justification"


def test_allowlisted_file_is_really_the_retired_key():
    """The allowlisted file must exist and must be the retired v1 key, not a new one."""
    (path, _), = ALLOWLIST.items()
    p = ROOT / path
    assert p.exists(), f"allowlisted retired key missing: {path}"
    header = p.read_text(encoding="utf-8").splitlines()[0]
    assert header.startswith("sample_id,stratum,sampling_weight"), (
        f"unexpected schema for the retired key: {header!r}"
    )


def test_sealed_key_default_path_is_outside_repo():
    """The builder's default key path must resolve outside the repository."""
    src = (ROOT / "experiments" / "build_align05_validation_sample.py").read_text(encoding="utf-8")
    assert "sealed_keys" in src, "builder must default to a sealed_keys/ path"
    assert "is_relative_to(ROOT)" in src or "is_relative_to" in src, (
        "builder must refuse to write a key inside the repo"
    )


def test_scorer_reads_key_from_env_not_repo_path():
    """score_labels.py must resolve the key via ALIGN05_KEY, not a repo-relative default."""
    src = (ROOT / "labelling" / "score_labels.py").read_text(encoding="utf-8")
    assert "ALIGN05_KEY" in src, "scorer must honour ALIGN05_KEY"
    assert 'environ.get("A5_KEY", ROOT / "experiments"' not in src, (
        "scorer must not fall back to an in-repo key path"
    )


def test_gitignore_blocks_key_patterns():
    """.gitignore must reject every sealed-key pattern."""
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pat in ("*_key*.csv", "sealed/", "sealed*/", "**/sealed_keys/"):
        assert pat in gi, f".gitignore missing sealed-key pattern: {pat}"


def test_prepush_hook_present_and_executable():
    """The pre-push hook must exist, and be registered as a hook path or staged."""
    hook = ROOT / "scripts" / "pre-push"
    assert hook.exists(), "scripts/pre-push guard missing"
    text = hook.read_text(encoding="utf-8")
    assert "ls-files" in text, "pre-push hook must inspect tracked files"
    assert "_key" in text, "pre-push hook must check key patterns"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all secret-tracking guards pass")
