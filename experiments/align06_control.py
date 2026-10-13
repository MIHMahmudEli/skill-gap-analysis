"""ALIGN06 section 6.1 - instrument control (blocking; run before any O*NET cell).

    HF postings, P = all, lexical  K = 100        -> SGI 0.52  (exact)
    HF postings, P = all, semantic K = 100, tau .5 -> SGI 0.32  (+/- 0.02)

"The harness must import SENS01's matcher/profile code and reproduce its
already-published control cells through that same path ... A control failure
fails the run; no result is written. This uses only the local HF corpus that is
already on disk - it is a code-path check, not new data acquisition."

That is what this script does: it imports `sens01_sgi_sensitivity` by path and
calls *its* loaders, *its* `top_profile`, *its* `lexical_coverages`, and
reproduces the semantic cell with the same model, normalisation and
`S[:k,:k].max(axis=1)` rule that SENS01's own `semantic_coverages` uses. It
reads no O*NET or OEWS file.

Exit status: 0 = control passed, 1 = control failed (ALIGN06 must not run).

Output: results/ALIGN06_onet_demand_profile/control_6_1.json
"""
from __future__ import annotations

import importlib.util
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
SENS01_PATH = ROOT / "experiments" / "exp_scripts" / "sens01_sgi_sensitivity.py"
OUT_DIR = ROOT / "results" / "ALIGN06_onet_demand_profile"
OUT_PATH = OUT_DIR / "control_6_1.json"

# --- the two cells, verbatim from ALIGN06_PREREG.md 6.1 --------------------
LEX_K = 100
SEM_K = 100
SEM_TAU = 0.5
LEX_EXPECTED = 0.52          # "SGI 0.52 (exact)"
SEM_EXPECTED = 0.32          # "SGI 0.32 (+/- 0.02 device tolerance)"
SEM_TOL = 0.02


def load_sens01():
    spec = importlib.util.spec_from_file_location("sens01_sgi_sensitivity",
                                                  SENS01_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"FATAL: cannot load {SENS01_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    t0 = time.time()
    print("== ALIGN06 6.1 instrument control ==", flush=True)
    print(f"   importing matcher/profile code from {SENS01_PATH.name}",
          flush=True)
    s = load_sens01()
    print(f"   PROFILE_N={s.PROFILE_N} K_GRID={s.K_GRID} "
          f"MODEL_NAME={s.MODEL_NAME} SEED={s.SEED}", flush=True)

    print("loading local HF corpus ...", flush=True)
    acad = s.load_academic()
    mkt = s.load_market_hf()
    print(f"   academic rows={acad.n_rows} vocab={len(acad.vocab_list)}",
          flush=True)
    print(f"   market   rows={mkt.n_rows} vocab={len(mkt.vocab_list)}",
          flush=True)

    # P = all : the full corpus, never sub-sampled (SENS01 anchor path).
    acad_prof = s.top_profile(s.full_counts(acad))
    mkt_prof = s.top_profile(s.full_counts(mkt))
    print(f"   anchor profiles: market top-{len(mkt_prof)} / "
          f"academic top-{len(acad_prof)}", flush=True)

    # ---- cell 1: lexical K = 100 --------------------------------------
    lex_cov = s.lexical_coverages(mkt_prof, acad_prof,
                                  mkt.vocab_list, acad.vocab_list)
    sgi_lex = 1.0 - lex_cov[LEX_K]
    lex_ok = round(sgi_lex, 2) == LEX_EXPECTED
    print(f"   lexical  K={LEX_K} P=all -> coverage={lex_cov[LEX_K]:.6f} "
          f"SGI={sgi_lex:.6f} (expect {LEX_EXPECTED}) "
          f"{'OK' if lex_ok else 'FAIL'}", flush=True)

    # ---- cell 2: semantic K = 100, tau = 0.5 --------------------------
    # Reproduce SENS01's embedding path exactly: union vocabulary over the two
    # anchor profiles, one row per distinct skill STRING, L2-normalised.
    str2row: dict[str, int] = {}
    all_strings: list[str] = []
    for prof, vocab in ((mkt_prof, mkt.vocab_list),
                        (acad_prof, acad.vocab_list)):
        for i in prof.tolist():
            sv = vocab[i]
            if sv not in str2row:
                str2row[sv] = len(all_strings)
                all_strings.append(sv)
    print(f"   embedding {len(all_strings)} distinct anchor-profile skills ...",
          flush=True)

    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(s.MODEL_NAME, device=device)
    emb = model.encode(all_strings, show_progress_bar=False,
                       convert_to_numpy=True, batch_size=256)
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    def rows_of(prof: np.ndarray, vocab: list) -> np.ndarray:
        return np.fromiter((str2row[vocab[i]] for i in prof.tolist()),
                           dtype=np.int64, count=len(prof))

    M = emb[rows_of(mkt_prof, mkt.vocab_list)]
    A = emb[rows_of(acad_prof, acad.vocab_list)]
    S = M @ A.T
    maxs = S[:SEM_K, :SEM_K].max(axis=1)
    sem_cov = float((maxs >= SEM_TAU).mean())
    sgi_sem = 1.0 - sem_cov
    sem_ok = abs(sgi_sem - SEM_EXPECTED) <= SEM_TOL
    print(f"   semantic K={SEM_K} tau={SEM_TAU} P=all -> coverage={sem_cov:.6f} "
          f"SGI={sgi_sem:.6f} (expect {SEM_EXPECTED} +/- {SEM_TOL}) "
          f"{'OK' if sem_ok else 'FAIL'}", flush=True)

    passed = bool(lex_ok and sem_ok)
    report = {
        "experiment_id": "ALIGN06_onet_demand_profile",
        "phase": "6.1 instrument control",
        "status": "passed" if passed else "failed",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runtime_sec": round(time.time() - t0, 3),
        "prereg": "experiments/ALIGN06_PREREG.md#6.1",
        "reads_onet_or_oews": False,
        "imported_from": str(SENS01_PATH.relative_to(ROOT)),
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "sentence_transformers": __import__(
                "sentence_transformers").__version__,
            "device": device,
            "numpy": np.__version__,
        },
        "cells": {
            "lexical_K100_P_all": {
                "sgi": sgi_lex, "coverage": lex_cov[LEX_K],
                "expected": LEX_EXPECTED, "rule": "exact at 2dp",
                "ok": bool(lex_ok),
            },
            "semantic_K100_tau0.5_P_all": {
                "sgi": sgi_sem, "coverage": sem_cov,
                "expected": SEM_EXPECTED, "tol": SEM_TOL,
                "rule": "+/- 0.02 device tolerance", "ok": bool(sem_ok),
            },
        },
        "corpora": {
            "market": {"name": "hf_skill_gap (HF postings)",
                       "n_rows": mkt.n_rows},
            "academic": {"name": "academic reference profile",
                         "n_rows": acad.n_rows},
        },
        "profiles": {"market_top": len(mkt_prof),
                     "academic_top": len(acad_prof)},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True),
                        encoding="utf-8")
    print(f"\nwrote {OUT_PATH.relative_to(ROOT)}", flush=True)
    print(f"CONTROL {'PASSED' if passed else 'FAILED'}", flush=True)
    if not passed:
        print("ALIGN06 must not run: section 6.1 is blocking.",
              flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
