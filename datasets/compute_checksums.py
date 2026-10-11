#!/usr/bin/env python3
"""Compute SHA-256 checksums for the nine canonical input-bundle files.

Writes datasets/input_checksums.sha256 (tracked). Files themselves remain
gitignored; checksums let any machine verify it has bit-identical inputs.
Missing files are listed as MISSING (not hashed).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
from common import BUNDLE_FILES, LOCAL_FALLBACKS, resolve_input  # noqa: E402

out_lines = [
    "# SHA-256 checksums of canonical experiment inputs (audit Phase 8, 2026-10-11)",
    "# Verify with: python -c \"import hashlib,pathlib,sys; ...\" or sha256sum -c",
]
ok = 0
for key in BUNDLE_FILES:
    try:
        path = resolve_input(key)
    except FileNotFoundError:
        out_lines.append(f"MISSING  {key}  ({BUNDLE_FILES[key]})")
        continue
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    out_lines.append(f"{h.hexdigest()}  {rel}  ({key})")
    ok += 1

dest = ROOT / "datasets" / "input_checksums.sha256"
dest.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
print(f"wrote {dest} ({ok}/{len(BUNDLE_FILES)} files hashed)")
for ln in out_lines[2:]:
    print(" ", ln[:120])
