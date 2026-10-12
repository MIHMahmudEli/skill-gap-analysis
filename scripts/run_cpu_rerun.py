"""Re-run every registered experiment on CPU into results_cpu/ (batch 3, step 3).

Implements reports/CPU_RERUN_PLAN.md: single-thread BLAS, seed 42 (pinned in
each script), outputs isolated under results_cpu/<EXPERIMENT_ID> via
SKILLGAP_OUTPUT_DIR so nothing under results/ is ever touched.

    python scripts/run_cpu_rerun.py --only geo01_linkedin
    python scripts/run_cpu_rerun.py --skip-embedding
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results_cpu"

# experiment_id -> script, whether it loads Sentence-BERT
EXPERIMENTS = {
    "ALIGN01_lexical_bootstrap": ("align01_lexical.py", False),
    "GEO01_linkedin_shares": ("geo01_linkedin.py", False),
    "INTL01_internship_effect": ("intl01_internship.py", False),
    "PLAC01_global_by_country": ("plac01_global_country.py", False),
    "STAT01_placement_core": ("stat01_placement_core.py", False),
    "STAT02_external_validation": ("stat02_external_valid.py", False),
    "TRENDS01_ai_longitudinal": ("trends01_ai.py", False),
    "ALIGN02_semantic_sbert": ("align02_semantic.py", True),
    "ALIGN03_domain_gap": ("align03_domain_gap.py", True),
    "ALIGN04_crosscorpus_linkedin": ("align04_crosscorpus.py", True),
    "CURR01_cs2023_anchor": ("curr01_cs2023_anchor.py", True),
    "SENS01_sgi_sensitivity": ("sens01_sgi_sensitivity.py", True),
    "VALID01_esco_gold": ("valid01_esco_gold.py", True),
}

ENV = dict(os.environ,
           OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
           NUMEXPR_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1",
           PYTHONHASHSEED="42", TOKENIZERS_PARALLELISM="false")


def run_one(exp_id: str, script: str) -> tuple:
    out_dir = OUT / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(ENV, SKILLGAP_OUTPUT_DIR=str(out_dir))
    t0 = time.time()
    p = subprocess.run([sys.executable, str(ROOT / "experiments" / "exp_scripts" / script)],
                       cwd=str(ROOT), env=env, capture_output=True, text=True)
    dt = time.time() - t0
    ok = p.returncode == 0 and (out_dir / "metrics.json").exists()
    return ok, dt, (p.stderr or p.stdout)[-400:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--skip-embedding", action="store_true")
    args = ap.parse_args()

    todo = {k: v for k, v in EXPERIMENTS.items()
            if (args.only is None or k in args.only)
            and not (args.skip_embedding and v[1])}
    if not todo:
        print("nothing to run")
        return 1

    failures = []
    for exp_id, (script, emb) in todo.items():
        print(f"[{exp_id}] {'embedding' if emb else 'cpu-native'} {script} ...",
              flush=True)
        ok, dt, tail = run_one(exp_id, script)
        print(f"    {'OK  ' if ok else 'FAIL'} {dt:7.1f}s", flush=True)
        if not ok:
            failures.append(exp_id)
            print("    " + tail.replace("\n", "\n    "), flush=True)
    print("\nran %d, failed %d %s" % (len(todo), len(failures), failures or ""))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
