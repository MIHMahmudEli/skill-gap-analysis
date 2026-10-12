"""Compare a CPU re-run tree against the committed artifacts.

Used by the clean-room procedure for the 5 Sentence-BERT experiments that could
not be re-run on the author's laptop (reports/CLEAN_ROOM_REPRO.md §13;
reports/CPU_VS_COMMITTED.md).

    python scripts/compare_cpu_results.py                      # results_cpu/ vs results/
    python scripts/compare_cpu_results.py --cpu-dir results_linux --report reports/Linux_vs_committed.md

Compares every numeric leaf of each metrics.json recursively. Environment-dependent
fields are excluded by construction (runtime, device, seeds, statuses, timestamps,
kernel slugs) because they legitimately differ between a GPU and a CPU run.

Tolerance is max(1e-9, 1e-6 * |value|) - the author's 1e-6 relative rule. A GPU
embedding run and its CPU re-run can differ in the last bits of a float because the
encoder accumulates in a different order; that is expected and is quantified here
rather than hidden. Any difference beyond tolerance is printed as a FAILURE.

Exit codes: 0 all within tolerance, 1 a difference exceeded tolerance,
2 a requested directory or metrics.json was missing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL_TOL, ABS_TOL = 1e-6, 1e-9

# Fields that legitimately vary between machines/runs and carry no claim.
EXCLUDE = {
    "runtime_sec", "runtime_seconds", "device", "verified_utc", "generated_utc",
    "kernel_slug", "usage_status", "status", "seed", "seed_used", "bootstrap_n",
    "torch_version", "sentence_transformers_version", "python_version",
    "platform", "hostname", "cuda_available",
}


def leaves(obj, path=""):
    """Yield (dotted_path, value) for every scalar in a nested structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, obj


def numeric_leaves(obj):
    return {p: v for p, v in leaves(obj)
            if isinstance(v, (int, float)) and not isinstance(v, bool)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu-dir", default=str(ROOT / "results_cpu"))
    ap.add_argument("--ref-dir", default=str(ROOT / "results"))
    ap.add_argument("--report", default=None,
                    help="optional path to write a Markdown report")
    args = ap.parse_args()

    cpu_dir, ref_dir = Path(args.cpu_dir), Path(args.ref_dir)
    if not cpu_dir.is_dir():
        print(f"ERROR: CPU results dir not found: {cpu_dir}", file=sys.stderr)
        return 2

    rows, missing, compared_dirs = [], [], 0
    for d in sorted(p for p in cpu_dir.iterdir() if p.is_dir()):
        exp = d.name
        cpu_m, ref_m = d / "metrics.json", ref_dir / exp / "metrics.json"
        if not cpu_m.exists():
            missing.append((exp, "no metrics.json in the CPU run"))
            continue
        if not ref_m.exists():
            missing.append((exp, "no committed metrics.json to compare against"))
            continue
        a = numeric_leaves(json.loads(ref_m.read_text(encoding="utf-8")))
        b = numeric_leaves(json.loads(cpu_m.read_text(encoding="utf-8")))
        compared_dirs += 1
        for k in sorted(set(a) & set(b)):
            if any(x in k for x in EXCLUDE):
                continue
            va, vb = float(a[k]), float(b[k])
            diff = abs(va - vb)
            tol = max(ABS_TOL, REL_TOL * max(abs(va), abs(vb)))
            rows.append((exp, k, va, vb, diff, tol, diff <= tol))
        for k in sorted(set(a) - set(b)):
            missing.append((f"{exp}:{k}", "in committed, absent in the CPU run"))

    n_bad = sum(1 for r in rows if not r[6])
    max_diff = max((r[4] for r in rows), default=0.0)

    def fmt(v):
        return ("%g" % v) if abs(v) < 1e5 else ("%.6g" % v)

    print(f"experiments compared : {compared_dirs}")
    print(f"numeric fields       : {len(rows)}")
    print(f"beyond tolerance     : {n_bad}")
    print(f"largest |diff|       : {max_diff:.3e}")
    print(f"tolerance rule       : max({ABS_TOL:g}, {REL_TOL:g} * |value|)")
    if missing:
        print("\nmissing:")
        for e, why in missing:
            print(f"  {e}: {why}")
    bad = [r for r in rows if not r[6]]
    if bad:
        print("\nFAILURES (beyond tolerance):")
        for exp, k, va, vb, diff, tol, _ in bad:
            print(f"  {exp} :: {k}  committed={fmt(va)} cpu={fmt(vb)} "
                  f"diff={diff:.3e} tol={tol:.1e}")

    if args.report:
        lines = ["| Experiment | Metric | Committed | CPU | abs diff | tol | ok |",
                 "|---|---|---|---|---|---|---|"]
        for exp, k, va, vb, diff, tol, ok in rows:
            lines.append(f"| {exp} | `{k}` | {fmt(va)} | {fmt(vb)} | "
                         f"{diff:.3e} | {tol:.1e} | {'yes' if ok else '**NO**'} |")
        Path(args.report).write_text(
            "# CPU vs committed artifacts\n\n"
            f"experiments compared: {compared_dirs} | numeric fields: {len(rows)} | "
            f"beyond tolerance: {n_bad} | largest |diff|: {max_diff:.3e}\n\n"
            + "\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nwrote {args.report}")

    return 1 if n_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
