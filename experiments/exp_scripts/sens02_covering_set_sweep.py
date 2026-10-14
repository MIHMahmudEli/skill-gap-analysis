"""SENS02: occupational reference-profile covering-set sweep at fixed K = 100.

Pre-registered in experiments/SENS02_PREREG.md (committed before this script
was ever executed).  Registered as results/registry.json ->
SENS02_covering_set_sweep with status REGISTERED before the first run.

What is swept (the ONLY axis):

    P_acad in {100, 250, 500, 1000, all}   occupational reference-profile
                                           covering-set size ("all" = every
                                           skill in the 1,167-row reference
                                           profile, 5,047 distinct skills)
    K = 100                                market profile size, taken from the
                                           FULL corpus -- never sub-sampled
    corpora {hf_2024, linkedin_2024}       both, identical treatment
    match  {lexical, semantic tau in 0.4..0.7}
    seed 42;  B_SKILL = 1000;  B_POST = 500

Question (prereg section 1): is the headline level change 0.52/0.32 ->
0.37/0.14 a covering-set-size effect or a corpus effect?

P_acad is NOT SENS01's grid dimension.  SENS01's grid P is the market posting
sample size, which the manuscript renamed n_post on 2026-10-14; SENS02 never
touches that axis and reports nothing about it.

Two confidence intervals per cell, the same definitions SENS01 uses:

  CI_skill : resample of the K = 100 binary coverage indicators (B_SKILL).
  CI_post  : resample of the market postings AND all 1,167 reference-profile
             rows, rebuilding BOTH profiles inside every replicate (B_POST),
             then the percentile over replicate SGIs.

  Deviation in arithmetic only, fixed before the run and disclosed in
  SENS02_PREREG.md section 4: SENS01's sample_counts materialises an
  (n, maxlen) gather, which is ~2 GB at the full corpus, so SENS01 marks its
  n_post=all rows NaN.  SENS02 needs that draw at every replicate and uses the
  algebraically identical sparse form counts = w @ T (w = bincount of the
  same randint draw, T = sparse row x skill counts).  Probed bit-identical to
  sample_counts on the same RNG draw.

Outputs (results/SENS02_covering_set_sweep/):
  table_covering_set_sweep.csv   50 rows = 2 corpora x 5 P_acad x (1+4)
  metrics.json                   status, grid, registered contrasts R1..R7

Run:
    SKILLGAP_OUTPUT_DIR=results/SENS02_covering_set_sweep \\
        python experiments/exp_scripts/sens02_covering_set_sweep.py
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

REPO = Path(__file__).resolve().parents[2]
EXP_ID = "SENS02_covering_set_sweep"

# ---------------------------------------------------------------------------
# the instrument is imported, not rewritten (prereg section 3.2)
# ---------------------------------------------------------------------------
_SENS01 = Path(__file__).resolve().parent / "sens01_sgi_sensitivity.py"
_spec = importlib.util.spec_from_file_location("sens01_for_sens02", _SENS01)
s1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s1)

SEED = s1.SEED                       # 42
CORPORA = s1.CORPORA                 # ["hf_2024", "linkedin_2024"]
TAUS = s1.TAUS                       # [0.4, 0.5, 0.6, 0.7]
B_SKILL = s1.B_SKILL                 # 1000
B_POST = s1.B_POST                   # 500
MODEL_NAME = s1.MODEL_NAME           # all-MiniLM-L6-v2
SEM_TOL = s1.SEMANTIC_ANCHOR_TOL     # 0.02

K = 100                              # market profile size, fixed
P_ACAD_GRID = [100, 250, 500, 1000, "all"]

# Manuscript headline / ALIGN04 values the two ends of the sweep must reproduce.
EXPECTED = {
    "lex_P100": 0.52, "sem_P100_tau0.5": 0.32,
    "lex_P500": 0.37, "sem_P500_tau0.5": 0.14,
    "level_change_lex": 0.15,
}


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# sparse, memory-safe equivalent of s1.sample_counts at full corpus size
# ---------------------------------------------------------------------------
def build_T(ti) -> sparse.csr_matrix:
    """(n_rows x vocab) integer matrix of how often each skill occurs per row."""
    row_ids = np.repeat(np.arange(ti.n_rows, dtype=np.int32),
                        np.diff(ti.offsets))
    return sparse.coo_matrix(
        (np.ones(ti.flat.size, np.int64), (row_ids, ti.flat)),
        shape=(ti.n_rows, len(ti.vocab_list))).tocsr()


def resample_counts(ti, T, rng: np.random.RandomState) -> np.ndarray:
    """Full-corpus n-out-of-n row resample -> per-skill counts.

    Bit-identical to s1.sample_counts(ti, rng, ti.n_rows) for the same rng
    state: both draw the same rows and sum their skill multiplicities.  The
    cast guarantees an exact integer vector whatever dtype the sparse
    product returns (the values are counts <= n_rows, so it is lossless).
    """
    rows = rng.randint(0, ti.n_rows, size=ti.n_rows)
    w = np.bincount(rows, minlength=ti.n_rows).astype(np.int64)
    return (w @ T).astype(np.int64, copy=False)


# ---------------------------------------------------------------------------
# coverage machinery
# ---------------------------------------------------------------------------
def lex_indicator(mkt: np.ndarray, acd: np.ndarray, p,
                  mkt_vocab: list, acd_vocab: list) -> np.ndarray:
    """Binary coverage of market top-K in occupational top-P_acad, by STRING.

    Asymmetric on purpose: mkt is always top-K (K = 100), acd is top-P_acad.
    """
    n = len(acd) if p == "all" else min(int(p), len(acd))
    acd_set = {acd_vocab[i] for i in acd[:n]}
    return np.fromiter(
        (1.0 if mkt_vocab[i] in acd_set else 0.0 for i in mkt[:K]),
        np.float64, min(K, len(mkt)))


def skill_ci(indicator: np.ndarray, b: int) -> list[float]:
    """Same construction as the headline interval: resample the K indicators."""
    rng = np.random.RandomState(SEED)
    k = len(indicator)
    draws = rng.randint(0, k, size=(b, k))
    boot = 1.0 - indicator[draws].mean(axis=1)
    return [float(x) for x in np.percentile(boot, [2.5, 97.5])]


def pct(vals) -> list[float]:
    return [float(x) for x in np.percentile(np.asarray(vals, float), [2.5, 97.5])]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="tiny bootstraps, written outside the registered dir")
    args = ap.parse_args()
    t0 = time.time()

    b_post = 8 if args.smoke else B_POST
    b_skill = 40 if args.smoke else B_SKILL

    default_out = (REPO / "results" / f"{EXP_ID}_smoke") if args.smoke \
        else (REPO / "results" / EXP_ID)
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", str(default_out)))
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ load
    log("loading corpora ...")
    acad = s1.load_academic()
    loaders = {"hf_2024": s1.load_market_hf, "linkedin_2024": s1.load_market_linkedin}
    markets = {c: loaders[c]() for c in CORPORA}
    n_postings = {c: int(markets[c].n_rows) for c in CORPORA}

    acad_full = s1.full_counts(acad)
    n_acad_skills = int((acad_full > 0).sum())
    log(f"  reference profile: {acad.n_rows} rows, {n_acad_skills} distinct skills")
    for c in CORPORA:
        log(f"  {c}: {n_postings[c]} postings, "
            f"{len(markets[c].vocab_list)} distinct skills")

    def acad_profile(counts: np.ndarray, p) -> np.ndarray:
        return s1.top_profile(counts, n_acad_skills if p == "all" else int(p))

    # -------------------------------------------------------- point profiles
    acad_point = {p: acad_profile(acad_full, p) for p in P_ACAD_GRID}
    mkt_point = {c: s1.top_profile(s1.full_counts(markets[c]), K) for c in CORPORA}

    # ------------------------------------------------- sparse row x skill maps
    log("building sparse row->skill matrices ...")
    acad_T = build_T(acad)
    mkt_T = {c: build_T(markets[c]) for c in CORPORA}

    # ------------------------------------- phase 1: posting-level replicates
    log(f"posting-level bootstrap: {b_post} replicates at FULL corpus size ...")
    log("  reference-profile rows (shared across corpora) ...")
    acad_reps: list[dict] = []
    for i in range(b_post):
        rng = np.random.RandomState(SEED + 5000 + i)
        counts = resample_counts(acad, acad_T, rng)
        acad_reps.append({p: acad_profile(counts, p) for p in P_ACAD_GRID})

    mkt_reps: dict[str, list[np.ndarray]] = {c: [] for c in CORPORA}
    for ci, c in enumerate(CORPORA):
        ti, T = markets[c], mkt_T[c]
        log(f"  {c}: {b_post} x {n_postings[c]} posting resample ...")
        for i in range(b_post):
            rng = np.random.RandomState(SEED + 1000 * ci + i)
            counts = resample_counts(ti, T, rng)
            mkt_reps[c].append(s1.top_profile(counts, K))

    # ------------------------------------------------- embedding vocabulary
    str2row: dict[str, int] = {}
    all_strings: list[str] = []

    def add_strings(ti, idxs) -> None:
        for i in idxs:
            s = ti.vocab_list[int(i)]
            if s not in str2row:
                str2row[s] = len(all_strings)
                all_strings.append(s)

    add_strings(acad, acad_point["all"])          # P_acad = all needs every skill
    for c in CORPORA:
        add_strings(markets[c], mkt_point[c])
        for prof in mkt_reps[c]:
            add_strings(markets[c], prof)

    def build_rows(ti, prof_lists) -> np.ndarray:
        needed: set[int] = set()
        for prof in prof_lists:
            needed.update(int(x) for x in prof)
        m = np.full(len(ti.vocab_list), -1, np.int64)
        for i in needed:
            m[i] = str2row[ti.vocab_list[i]]
        return m

    acad_rows = build_rows(acad, acad_point.values())
    mkt_rows = {c: build_rows(markets[c], [mkt_point[c]] + mkt_reps[c])
                for c in CORPORA}

    # ------------------------------------------------------------- embed
    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL_NAME, device=device)
    log(f"embedding {len(all_strings)} distinct profile skills on {device} ...")
    emb = model.encode(all_strings, show_progress_bar=False,
                       convert_to_numpy=True, batch_size=256)
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    # ------------------------------------------------------------- cells
    log("computing cells ...")
    rows_out: list[dict] = []

    for c in CORPORA:
        mkt_vocab, acd_vocab = markets[c].vocab_list, acad.vocab_list
        mp, mp_e = mkt_point[c], mkt_rows[c][mkt_point[c]]
        log(f"-- {c}")

        for p in P_ACAD_GRID:
            ap, ap_e = acad_point[p], acad_rows[acad_point[p]]
            ind = lex_indicator(mp, ap, p, mkt_vocab, acd_vocab)
            cov_lex = float(ind.mean())
            ci_lex_skill = skill_ci(ind, b_skill)

            # semantic: one similarity matrix per (corpus, P_acad), reused by tau
            S = emb[mp_e] @ emb[ap_e].T
            maxs = S.max(axis=1)

            # posting-level replicates for this cell
            lex_reps: list[float] = []
            sem_reps: dict[float, list[float]] = {t: [] for t in TAUS}
            for i in range(b_post):
                mp_i, ap_i = mkt_reps[c][i], acad_reps[i][p]
                ind_i = lex_indicator(mp_i, ap_i, p, mkt_vocab, acd_vocab)
                lex_reps.append(1.0 - float(ind_i.mean()))
                mx = (emb[mkt_rows[c][mp_i]] @ emb[acad_rows[ap_i]].T).max(axis=1)
                for t in TAUS:
                    sem_reps[t].append(1.0 - float((mx >= t).mean()))
            ci_lex_post = pct(lex_reps)

            # lexical row
            rows_out.append({
                "corpus": c, "match": "lexical", "tau": "", "K": K,
                "P_acad": str(p), "SGI": round(1.0 - cov_lex, 4),
                "coverage": round(cov_lex, 4),
                "CI_skill_lo": round(ci_lex_skill[0], 4),
                "CI_skill_hi": round(ci_lex_skill[1], 4),
                "CI_post_lo": round(ci_lex_post[0], 4),
                "CI_post_hi": round(ci_lex_post[1], 4),
            })

            # semantic rows (one per tau), same posting-level resamples
            for t in TAUS:
                cov_t = float((maxs >= t).mean())
                ind_t = (maxs >= t).astype(float)
                ci_t_skill = skill_ci(ind_t, b_skill)
                ci_t_post = pct(sem_reps[t])
                rows_out.append({
                    "corpus": c, "match": "semantic", "tau": str(t), "K": K,
                    "P_acad": str(p), "SGI": round(1.0 - cov_t, 4),
                    "coverage": round(cov_t, 4),
                    "CI_skill_lo": round(ci_t_skill[0], 4),
                    "CI_skill_hi": round(ci_t_skill[1], 4),
                    "CI_post_lo": round(ci_t_post[0], 4),
                    "CI_post_hi": round(ci_t_post[1], 4),
                })
            log(f"   P_acad={str(p):<4} lex SGI={1.0 - cov_lex:.4f}  "
                f"sem(tau=.5)={1.0 - float((maxs >= 0.5).mean()):.4f}")

    grid = pd.DataFrame(rows_out, columns=[
        "corpus", "match", "tau", "K", "P_acad", "SGI", "coverage",
        "CI_skill_lo", "CI_skill_hi", "CI_post_lo", "CI_post_hi"])
    grid.to_csv(out_dir / "table_covering_set_sweep.csv", index=False)

    # ------------------------------------------------ registered contrasts
    def cell(corpus: str, match: str, p, tau: str = "") -> dict:
        q = grid[(grid.corpus == corpus) & (grid.match == match)
                 & (grid.P_acad == str(p)) & (grid.tau == tau)]
        assert len(q) == 1, (corpus, match, p, tau, len(q))
        return q.iloc[0].to_dict()

    def lex(c, p):
        return float(cell(c, "lexical", p)["SGI"])

    def sem(c, p, t=0.5):
        return float(cell(c, "semantic", p, str(t))["SGI"])

    def chk(name: str, ok: bool, **kw):
        out = {"ok": bool(ok)}
        out.update(kw)
        return name, out

    contrasts: dict[str, dict] = {}
    items = [
        chk("R1_lex_P100_is_0.52",
            all(lex(c, 100) == EXPECTED["lex_P100"] for c in CORPORA),
            got={c: lex(c, 100) for c in CORPORA},
            expected=EXPECTED["lex_P100"]),
        chk("R2_sem_P100_is_0.32",
            all(abs(sem(c, 100) - EXPECTED["sem_P100_tau0.5"]) <= SEM_TOL
                for c in CORPORA),
            got={c: sem(c, 100) for c in CORPORA},
            expected=EXPECTED["sem_P100_tau0.5"], tol=SEM_TOL),
        chk("R3_lex_P500_is_0.37",
            all(lex(c, 500) == EXPECTED["lex_P500"] for c in CORPORA),
            got={c: lex(c, 500) for c in CORPORA},
            expected=EXPECTED["lex_P500"]),
        chk("R4_sem_P500_is_0.14",
            all(abs(sem(c, 500) - EXPECTED["sem_P500_tau0.5"]) <= SEM_TOL
                for c in CORPORA),
            got={c: sem(c, 500) for c in CORPORA},
            expected=EXPECTED["sem_P500_tau0.5"], tol=SEM_TOL),
    ]
    for name, val in items:
        contrasts[name] = val

    # R5: the level change itself, per corpus
    chg = {c: round(lex(c, 100) - lex(c, 500), 4) for c in CORPORA}
    contrasts["R5_level_change_lex_100_to_500"] = {
        "ok": all(abs(chg[c] - EXPECTED["level_change_lex"]) < 1e-9 for c in CORPORA),
        "got": chg, "expected": EXPECTED["level_change_lex"],
        "interpretation": "equal on both corpora => the 0.52->0.37 level change "
                          "is a covering-set-size effect, not a corpus effect",
    }

    # R6: cross-corpus gap at every P_acad
    gaps = {}
    worst_lex = worst_sem = 0.0
    for p in P_ACAD_GRID:
        gl = abs(lex("hf_2024", p) - lex("linkedin_2024", p))
        gs = abs(sem("hf_2024", p) - sem("linkedin_2024", p))
        gaps[str(p)] = {"lexical": round(gl, 4), "semantic_tau0.5": round(gs, 4)}
        worst_lex, worst_sem = max(worst_lex, gl), max(worst_sem, gs)
    contrasts["R6_cross_corpus_gap"] = {
        "ok": worst_lex <= 0.01 and worst_sem <= 0.02,
        "per_P_acad": gaps, "worst_lexical": round(worst_lex, 4),
        "worst_semantic_tau0.5": round(worst_sem, 4),
        "limits": {"lexical": 0.01, "semantic_tau0.5": 0.02},
    }

    # R7: coverage non-decreasing in P_acad (SGI non-increasing)
    mono = {}
    for c in CORPORA:
        for match in ("lexical", "semantic"):
            for t in ([""] if match == "lexical" else [str(x) for x in TAUS]):
                seq = [float(cell(c, match, p, t)["SGI"]) for p in P_ACAD_GRID]
                mono[f"{c}_{match}_tau{t}"] = {
                    "sgi": [round(x, 4) for x in seq],
                    "non_increasing": all(
                        seq[i] >= seq[i + 1] - 1e-9 for i in range(len(seq) - 1)),
                }
    contrasts["R7_monotone_in_P_acad"] = {
        "ok": all(v["non_increasing"] for v in mono.values()),
        "curves": mono,
    }

    all_ok = all(v["ok"] for v in contrasts.values())

    # ------------------------------------------------------------- metrics
    sgi_by_p = {}
    for c in CORPORA:
        sgi_by_p[c] = {}
        for p in P_ACAD_GRID:
            sgi_by_p[c][str(p)] = {
                "lexical": lex(c, p),
                "semantic": {str(t): sem(c, p, t) for t in TAUS},
            }

    metrics = {
        "status": "completed",
        "experiment_id": EXP_ID,
        "prereg": "experiments/SENS02_PREREG.md",
        "seed": SEED,
        "K": K,
        "P_acad_grid": [str(p) for p in P_ACAD_GRID],
        "P_acad_note": ("occupational reference-profile covering-set size; "
                        "not SENS01's posting sample size (n_post)"),
        "tau": TAUS,
        "B_SKILL": b_skill,
        "B_POST": b_post,
        "n_postings": n_postings,
        "n_reference_rows": int(acad.n_rows),
        "n_reference_skills": n_acad_skills,
        "distinct_profile_skills_embedded": len(all_strings),
        "model": MODEL_NAME,
        "grid": {"corpus": CORPORA, "match": ["lexical", "semantic"],
                 "P_acad": [str(p) for p in P_ACAD_GRID], "tau": TAUS},
        "counts": {"grid_rows": int(len(grid))},
        "sgi_by_p_acad": sgi_by_p,
        "registered_contrasts": contrasts,
        "all_registered_contrasts_ok": all_ok,
        "smoke": bool(args.smoke),
        "runtime_sec": round(time.time() - t0, 2),
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    log("")
    log("registered contrasts:")
    for k, v in contrasts.items():
        log(f"  {'PASS' if v['ok'] else 'FAIL'}  {k}")
    log(f"all ok: {all_ok}")
    log(f"wrote {out_dir}")
    log(f"runtime {metrics['runtime_sec']} s")
    if not all_ok:
        raise SystemExit("registered contrast failed")


if __name__ == "__main__":
    main()
