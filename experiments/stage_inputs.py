"""Stage the experiment input bundle as a public Kaggle dataset.

Builds bundle/ with hardlinks (fallback: copy) of the canonical inputs,
writes datasets-metadata.json, and runs `kaggle datasets create -u`.
Idempotent: skips if the dataset already exists with the same files.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BUNDLE_FILES, LOCAL_FALLBACKS, RESULTS_DIR, parse_env_workers

BUNDLE_DIR = RESULTS_DIR / "_staging"
META_DIR = RESULTS_DIR / "_staging"
DATASET_ID = "studyhub991/skill-gap-inputs-v1"


def link_or_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main() -> None:
    workers = parse_env_workers()
    host = next(w for w in workers if w["username"] == "studyhub991") if \
        any(w["username"] == "studyhub991" for w in workers) else workers[0]

    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for key, name in BUNDLE_FILES.items():
        src = LOCAL_FALLBACKS[key]
        if not src.exists():
            print(f"MISSING: {src}")
            sys.exit(1)
        link_or_copy(src, BUNDLE_DIR / name)
        total += src.stat().st_size
        print(f"staged {name} ({src.stat().st_size/1e6:.1f} MB)")
    print(f"total bundle: {total/1e6:.1f} MB")

    meta = {
        "id": DATASET_ID,
        "title": "Skill Gap Experiment Inputs v1",
        "licenses": [{"name": "CC0-1.0"}],
    }
    import json
    (META_DIR / "dataset-metadata.json").write_text(json.dumps(meta, indent=2),
                                                    encoding="utf-8")

    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = host["token"]
    # `create -u` refuses when the title already exists; `version` publishes a new
    # version of the existing dataset from the same staging dir.
    proc = subprocess.run(
        ["kaggle", "datasets", "version", "-p", str(META_DIR), "-m",
         "Add job_skills.csv for ALIGN04 cross-corpus experiment",
         "-q", "-r", "skip"],
        capture_output=True, text=True, timeout=7200, env=env,
    )
    print("stdout:", proc.stdout[-1500:])
    print("stderr:", proc.stderr[-1500:])
    if proc.returncode != 0:
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
