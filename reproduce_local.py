#!/usr/bin/env python3
"""Single local entry point for the reproducibility package (audit Phase 8).

Runs, in order, with per-stage status lines:
  1. Environment pin check (requirements.txt vs installed)
  2. Input checksum verification (if datasets/input_checksums.sha256 present)
  3. Registry + artifact verification (experiments/verify.py)
  4. Claim-ledger reproduction (audit/verify_claims.py)
  5. Statistical reproduction (audit/reproduce_stats.py) — requires local CSVs
  6. Citation check (audit/verify_citations.py) — requires network

Each stage is independently skippable via --skip. Exit code is non-zero if
any non-skipped stage fails. GPU/Kaggle stages are intentionally excluded
(results/ already contains the verified GPU outputs; re-running requires
Kaggle credentials and is documented in README.md).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STAGES = [
    ("env", "Environment pin check", [sys.executable, "-c", r"""
import sys
from pathlib import Path
IMPORT_NAME = {
    'scikit-learn': 'sklearn',
    'python-dotenv': 'dotenv',
    'pillow': 'PIL',
    'pyyaml': 'yaml',
}
missing = []
for line in Path('requirements.txt').read_text().splitlines():
    line=line.strip()
    if not line or line.startswith('#') or '==' not in line: continue
    name, ver = line.split('==',1)
    mod_name = IMPORT_NAME.get(name, name.replace('-','_'))
    try:
        mod = __import__(mod_name)
        have = getattr(mod,'__version__',None)
        if have and have != ver:
            print(f'VERSION MISMATCH {name}: pinned {ver}, installed {have}')
            missing.append(name)
    except ImportError:
        print(f'MISSING {name} (pinned {ver})')
        missing.append(name)
print('env_ok' if not missing else f'env_issues={len(missing)}')
sys.exit(1 if missing else 0)
"""]),
    ("checksums", "Input checksums", [sys.executable, "datasets/compute_checksums.py"]),
    ("verify", "Registry/artifact verification", [sys.executable, "experiments/verify.py"]),
    ("claims", "Claim ledger reproduction", [sys.executable, "audit/verify_claims.py"]),
    ("stats", "Statistical reproduction", [sys.executable, "audit/reproduce_stats.py"]),
    ("citations", "Citation Crossref check", [sys.executable, "audit/verify_citations.py"]),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip", action="append", default=[],
                    choices=[s[0] for s in STAGES], help="stage name(s) to skip")
    ap.add_argument("--only", action="append", default=[],
                    choices=[s[0] for s in STAGES], help="run only these stages")
    args = ap.parse_args()

    results = []
    for key, title, cmd in STAGES:
        if args.only and key not in args.only:
            continue
        if key in args.skip:
            print(f"[SKIP] {title}")
            results.append((key, "skipped", 0.0))
            continue
        print(f"[RUN ] {title} ...")
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=str(ROOT))
        dt = time.time() - t0
        status = "ok" if proc.returncode == 0 else f"FAIL(rc={proc.returncode})"
        print(f"[{status:6s}] {title} ({dt:.1f}s)")
        results.append((key, status, dt))
        if proc.returncode != 0 and key in ("verify", "claims"):
            # hard-stop on core integrity stages
            break

    print("\n==== reproduce_local summary ====")
    for k, s, dt in results:
        print(f"  {k:12s} {s:12s} {dt:6.1f}s")
    hard_fail = any(s.startswith("FAIL") for _, s, _ in results)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
