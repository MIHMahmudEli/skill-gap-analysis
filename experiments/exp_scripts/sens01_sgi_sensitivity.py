"""SENS01: SGI sensitivity surface over (K, P, tau) x lexical/semantic x corpus.

Pre-registered grid (fixed in code before this experiment was executed; no
sensitivity result existed when the grid was chosen):

  K      in {50, 100, 200, 500}     profile size: market top-K vs academic top-K
  P      in {100, 250, 500, 1000}   market posting sample size
                                    (plus a P=all anchor row set reproducing
                                    the full-corpus published experiments)
  tau    in {0.4, 0.5, 0.6, 0.7}    semantic threshold (semantic rows only)
  match  in {lexical, semantic}
  corpus in {hf_2024 (519,814 postings), linkedin_2024 (1,294,296 postings)}
  seed   42;  B_SKILL = 1000;  B_POST = 500

Two confidence intervals per cell (the "dual bootstrap" of Q1_REVISION_PLAN
Phase 2 / P2-2):

  CI_skill : resample of the K coverage indicators (within-profile
             uncertainty). Same *method* as the published ALIGN01/02/04 CIs;
             per-cell fresh RandomState streams, so bounds are method-replicated
             rather than bit-replicated against those artifacts.
  CI_post  : resample of P market postings AND all 1,167 academic rows with
             replacement, rebuilding both top-K profiles per replicate
             (profile-estimation uncertainty: "which postings did you happen
             to observe?"). NaN at the P=all anchor rows, where only CI_skill
             is reported (full-corpus posting resampling is both computationally
             prohibitive here and scientifically uninformative).

Point estimate per grid cell: ONE seeded draw of P postings
(seed = SEED + 1000*corpus_index + 10*P_index), i.e. exactly what an analyst
holding P postings would observe; CI_post then quantifies how far a different
draw of the same size could move that number.

Anchor reproduction (P=all rows must reproduce the published experiments;
checked against embedded constants sourced from
results/ALIGN01_lexical_bootstrap/metrics.json, results/ALIGN02_semantic_sbert/
metrics.json, results/ALIGN04_crosscorpus_linkedin/metrics.json):

  HF       lexical K=100              SGI = 0.52
  HF       semantic K=100 tau=0.5     SGI = 0.32
  LinkedIn lexical K=100              SGI = 0.37
  LinkedIn semantic K=100 tau=0.5     SGI = 0.14

Lexical anchors must match exactly (no model involved). Semantic anchors are
tolerated at +/- 0.02 because the published values were computed on a
different device stack (GPU vs this CPU run); MiniLM float differences can
flip a skill sitting within ~1e-3 of tau. Larger deviations fail the run.

Tokenization replicates ALIGN01/02/04 exactly, including Counter.most_common
tie-breaking (first-seen order), so profile construction is bit-identical to
the published pipeline.

Usage
-----
    # full run (~15-30 min CPU; writes into results/SENS01_sgi_sensitivity)
    SKILLGAP_OUTPUT_DIR=results/SENS01_sgi_sensitivity \
        python experiments/exp_scripts/sens01_sgi_sensitivity.py

    # smoke run (tiny bootstraps; validates end-to-end in a few minutes)
    ... python experiments/exp_scripts/sens01_sgi_sensitivity.py --smoke
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
K_GRID = [50, 100, 200, 500]
P_GRID = [100, 250, 500, 1000]
TAUS = [0.4, 0.5, 0.6, 0.7]
PROFILE_N = 500
B_SKILL = 1000
B_POST = 500
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK = 200_000
SEMANTIC_ANCHOR_TOL = 0.02

# Anchor reproduction (P=all rows must reproduce the published experiments).
#
# IMPORTANT: the published experiments do NOT share one definition.
#   ALIGN01 (HF lexical) and ALIGN02 (HF semantic) compare market top-K against
#     academic top-K -- SYMMETRIC. This is the definition SENS01's grid uses.
#   ALIGN04 (LinkedIn) compares LinkedIn market top-100 against academic
#     top-500 (it omits .head(TOP_N) on the academic side) -- ASYMMETRIC.
# So the HF anchors are reproduced by the symmetric grid below; the LinkedIn
# ALIGN04 numbers are instead reproduced by the dedicated
# align04_asymmetric_replication() block, which uses ALIGN04's own definition.
# (Found by this anchor check on 2026-10-11; the symmetric LinkedIn grid value
# at K=100 is genuinely ~0.52 lexical, not a failed 0.37 reproduction.)
ANCHOR_EXPECTED = {
    ("hf_2024", "lexical", 100, None): 0.52,
    ("hf_2024", "semantic", 100, 0.5): 0.32,
}

# ALIGN04's own asymmetric definition (LinkedIn market top-100 vs academic
# top-500), validated separately to prove the LinkedIn loading+embedding path.
ALIGN04_ASYMMETRIC_EXPECTED = {
    "linkedin_2024_lexical_K100": 0.37,
    "linkedin_2024_semantic_K100_tau0.5": 0.14,
}

CORPORA = ["hf_2024", "linkedin_2024"]


def resolve(name: str) -> Path:
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    repo = Path(__file__).resolve().parents[2] / "datasets"
    mapping = {
        "hf_skill_gap_skills.csv": repo / "hf_skill_gap_skills.csv",
        "hf_job_skill_set.csv": repo / "hf_job_skill_set.csv",
        "job_skills.csv": (repo / "kaggle" / "1-3m-linkedin-jobs-and-skills-2024"
                           / "job_skills.csv"),
    }
    if name in mapping:
        candidates.append(mapping[name])
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"{name} not found; tried {candidates}")


# ---------------------------------------------------------------------------
# tokenization + int-row construction (replicates ALIGN01/02/04 exactly)
# ---------------------------------------------------------------------------

class TokenIndex:
    """First-seen-ordered skill vocab + ragged int rows for one corpus."""

    def __init__(self) -> None:
        self.vocab: dict[str, int] = {}
        self.vocab_list: list[str] = []
        self.parts: list[np.ndarray] = []
        self.offsets = [0]

    def add_cell(self, cell) -> None:
        idxs = []
        for sk in str(cell).split(","):
            sk = sk.strip().lower()
            if sk:
                i = self.vocab.get(sk)
                if i is None:
                    i = len(self.vocab_list)
                    self.vocab[sk] = i
                    self.vocab_list.append(sk)
                idxs.append(i)
        self.parts.append(np.asarray(idxs, np.int32))
        self.offsets.append(self.offsets[-1] + len(idxs))

    def finish(self) -> None:
        self.flat = (np.concatenate(self.parts) if self.parts
                     else np.empty(0, np.int32))
        self.offsets = np.asarray(self.offsets, np.int64)
        self.n_rows = len(self.offsets) - 1
        lens = np.diff(self.offsets)
        self.maxlen = int(lens.max()) if len(lens) else 0
        self.parts = []  # free the per-row arrays


def load_market_hf() -> TokenIndex:
    ti = TokenIndex()
    for s in pd.read_csv(resolve("hf_skill_gap_skills.csv"),
                         usecols=["job_skills"])["job_skills"].dropna():
        ti.add_cell(s)
    ti.finish()
    return ti


def load_market_linkedin() -> TokenIndex:
    ti = TokenIndex()
    for chunk in pd.read_csv(resolve("job_skills.csv"), usecols=["job_skills"],
                             chunksize=CHUNK):
        for cell in chunk["job_skills"].dropna():
            ti.add_cell(cell)
    ti.finish()
    return ti


def load_academic() -> TokenIndex:
    ti = TokenIndex()
    for s in pd.read_csv(resolve("hf_job_skill_set.csv"),
                         usecols=["job_skill_set"])["job_skill_set"].dropna():
        # exact ALIGN01/02/04 parsing of the stringified python list
        skills_str = str(s).strip().strip("[]").replace("'", "")
        ti.add_cell(skills_str)
    ti.finish()
    return ti


# ---------------------------------------------------------------------------
# profile machinery (numpy path; tie-break = first-seen idx == Counter order)
# ---------------------------------------------------------------------------

def full_counts(ti: TokenIndex) -> np.ndarray:
    return np.bincount(ti.flat, minlength=len(ti.vocab_list)).astype(np.int64)


def top_profile(counts: np.ndarray, backing: int = PROFILE_N) -> np.ndarray:
    """Top-backing skills by (count desc, first-seen idx asc).

    Equivalent to Counter.most_common(backing): Python's sorted() over
    counter.items() is stable on dict (insertion) order, and our vocab index
    IS first-seen order. The nz/cutoff narrowing below is exact: entries with
    count < the k-th largest count cannot enter the top-k, and among ties at
    the cutoff we keep idx-ascending order -- identical to a full lexsort, but
    O(V) instead of O(V log V), which matters because this runs once per
    bootstrap replicate over 1.4M-2.8M-entry count arrays.
    """
    nz = np.flatnonzero(counts)
    k = min(backing, len(nz))
    sub = counts[nz]
    if len(nz) > 4 * backing:
        cutoff = np.partition(sub, -k)[-k]
        keep = sub >= cutoff
        nz, sub = nz[keep], sub[keep]
    order = np.lexsort((nz, -sub))
    return nz[order[:k]].astype(np.int32)


def sample_counts(ti: TokenIndex, rng: np.random.RandomState, n: int):
    """Counts over n postings drawn with replacement (vectorized ragged gather)."""
    rows = rng.randint(0, ti.n_rows, size=n)
    starts = ti.offsets[rows]
    lens = ti.offsets[rows + 1] - starts
    cols = np.arange(ti.maxlen)
    mask = cols[None, :] < lens[:, None]
    idx = starts[:, None] + np.where(mask, cols[None, :], 0)
    toks = ti.flat[idx]
    return np.bincount(toks[mask], minlength=len(ti.vocab_list)).astype(np.int64)


def lexical_coverages(mkt: np.ndarray, acd: np.ndarray,
                      mkt_vocab: list, acd_vocab: list) -> dict[int, float]:
    """Exact-match coverage of market top-K in academic top-K, by skill STRING.

    Market and academic profiles live in *separate* vocab index spaces (each
    TokenIndex numbers its own skills from 0), so intersection must be done on
    the decoded skill strings -- comparing raw int indices is meaningless and
    silently produces near-zero coverage. ALIGN01/02 both compare top-K vs
    top-K (symmetric), which is what we replicate here.
    """
    acd_sets = {k: {acd_vocab[i] for i in acd[:k]} for k in K_GRID}
    out = {}
    for k in K_GRID:
        m = [mkt_vocab[i] for i in mkt[:k]]
        out[k] = (len(acd_sets[k].intersection(m)) / len(m)) if m else 0.0
    return out


def lexical_indicator(mkt: np.ndarray, acd: np.ndarray, k: int,
                      mkt_vocab: list, acd_vocab: list) -> np.ndarray:
    """Binary coverage indicator of market top-K in academic top-K (by string)."""
    acd_set = {acd_vocab[i] for i in acd[:k]}
    return np.array([1.0 if mkt_vocab[i] in acd_set else 0.0
                     for i in mkt[:k]], dtype=float)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true",
                    help="tiny bootstraps for end-to-end validation")
    ap.add_argument("--vocab-only", action="store_true",
                    help="run phase 1 only and report the embedding-vocabulary "
                         "size (exit before encoding) -- used to size the full "
                         "run's memory/time cost")
    args = ap.parse_args()

    t0 = time.time()
    b_post = 8 if args.smoke else B_POST
    b_skill = 40 if args.smoke else B_SKILL

    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)

    print("loading corpora ...", flush=True)
    acad = load_academic()
    markets = {"hf_2024": load_market_hf(), "linkedin_2024": load_market_linkedin()}
    n_postings = {c: markets[c].n_rows for c in CORPORA}
    print(f"  academic rows={acad.n_rows} vocab={len(acad.vocab_list)}", flush=True)
    for c in CORPORA:
        print(f"  {c}: rows={markets[c].n_rows} vocab={len(markets[c].vocab_list)}",
              flush=True)

    acad_full = full_counts(acad)

    # -----------------------------------------------------------------
    # phase 1: profiles + lexical coverages; collect embedding vocabulary
    # -----------------------------------------------------------------
    # stored_profiles[corpus][P] = (mkt_profiles (B,500), acd_profiles (B,500))
    stored_profiles: dict[str, dict] = {c: {} for c in CORPORA}
    point_profiles: dict[str, dict] = {}   # corpus -> P -> (mkt, acd)
    anchor_profiles: dict[str, tuple] = {}  # corpus -> (mkt500, acd500)
    lex_point: dict[tuple, dict] = {}       # (corpus, P_label, 'anchor'|pi) -> {K: cov}
    lex_reps: dict[tuple, list] = {}        # (corpus, pi, K) -> [sgi per rep]
    embed_needed: dict[str, set] = {c: set() for c in CORPORA}
    embed_needed["academic"] = set()

    # anchor profiles (full corpus; numpy path == Counter path exactly)
    acad_prof500 = top_profile(acad_full)
    acd_vocab = acad.vocab_list
    embed_needed["academic"].update(acad_prof500.tolist())
    for c in CORPORA:
        mkt_vocab = markets[c].vocab_list
        mkt_prof500 = top_profile(full_counts(markets[c]))
        anchor_profiles[c] = (mkt_prof500, acad_prof500)
        embed_needed[c].update(mkt_prof500.tolist())
        lex_point[(c, "all", "anchor")] = lexical_coverages(
            mkt_prof500, acad_prof500, mkt_vocab, acd_vocab)

    for ci, c in enumerate(CORPORA):
        ti = markets[c]
        mkt_vocab = ti.vocab_list
        for pi, P in enumerate(P_GRID):
            # --- single seeded point draw for this grid cell ---
            rng_pt = np.random.RandomState(SEED + 1000 * ci + 10 * pi)
            mkt_pt = top_profile(sample_counts(ti, rng_pt, P))
            acd_pt = top_profile(sample_counts(acad, rng_pt, acad.n_rows))
            point_profiles[(c, P)] = (mkt_pt, acd_pt)
            embed_needed[c].update(mkt_pt.tolist())
            embed_needed["academic"].update(acd_pt.tolist())
            lex_point[(c, P, pi)] = lexical_coverages(
                mkt_pt, acd_pt, mkt_vocab, acd_vocab)

            # --- posting bootstrap replicates ---
            rng_bp = np.random.RandomState(SEED + 100_000 + 1000 * ci + 10 * pi)
            mkt_reps = np.empty((b_post, PROFILE_N), np.int32)
            acd_reps = np.empty((b_post, PROFILE_N), np.int32)
            for b in range(b_post):
                mkt_b = top_profile(sample_counts(ti, rng_bp, P))
                acd_b = top_profile(sample_counts(acad, rng_bp, acad.n_rows))
                mkt_reps[b, :len(mkt_b)] = mkt_b
                acd_reps[b, :len(acd_b)] = acd_b
                covs = lexical_coverages(mkt_b, acd_b, mkt_vocab, acd_vocab)
                for k in K_GRID:
                    lex_reps.setdefault((c, pi, k), []).append(1.0 - covs[k])
            stored_profiles[c][P] = (mkt_reps, acd_reps)
            embed_needed[c].update(mkt_reps.ravel().tolist())
            embed_needed["academic"].update(acd_reps.ravel().tolist())
        print(f"  phase1 {c}: profiles + lexical done "
              f"({time.time()-t0:.0f}s)", flush=True)

    # -----------------------------------------------------------------
    # phase 2: embeddings (union vocabulary), semantic coverages
    # -----------------------------------------------------------------
    if args.vocab_only:
        # de-duplicate across keys the same way the real encoder will
        seen: set = set()
        per_key = {}
        for key in embed_needed:
            strs = {(acad if key == "academic" else markets[key]).vocab_list[i]
                    for i in embed_needed[key]}
            per_key[key] = len(strs)
            seen |= strs
        print(f"VOCAB-ONLY: per-key distinct {per_key}", flush=True)
        print(f"VOCAB-ONLY: union to encode = {len(seen)}", flush=True)
        return

    import torch
    from sentence_transformers import SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL_NAME, device=device)

    str2row: dict[str, int] = {}
    all_strings: list[str] = []
    for key in list(embed_needed):
        ti = acad if key == "academic" else markets[key]
        for i in sorted(embed_needed[key]):
            s = ti.vocab_list[i]
            if s not in str2row:
                str2row[s] = len(all_strings)
                all_strings.append(s)
    print(f"embedding {len(all_strings)} distinct profile skills ...", flush=True)
    emb = model.encode(all_strings, show_progress_bar=False,
                       convert_to_numpy=True, batch_size=256)
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    def row_map(ti: TokenIndex, key: str) -> np.ndarray:
        """Vocab-index -> embedding-row for the skills that ever entered a
        profile. Everything else is -1 and must never be indexed."""
        m = np.full(len(ti.vocab_list), -1, np.int64)
        for i in embed_needed[key]:
            m[i] = str2row[ti.vocab_list[i]]
        return m

    emb_rows = {c: row_map(markets[c], c) for c in CORPORA}
    emb_rows["academic"] = row_map(acad, "academic")
    # every skill that can appear in a profile must have an embedding row
    for key, ti in [("academic", acad), *[(c, markets[c]) for c in CORPORA]]:
        used = np.unique(np.fromiter(embed_needed[key], np.int64))
        if used.size and (emb_rows[key][used] < 0).any():
            raise RuntimeError(f"unmapped profile skill in {key}")

    tau_arr = np.asarray(TAUS)

    def semantic_coverages(mkt_prof: np.ndarray, acd_prof: np.ndarray,
                           rows_m: np.ndarray, rows_a: np.ndarray) -> dict:
        """{K: {tau: coverage}} from one profile pair."""
        M = emb[rows_m[mkt_prof]]
        A = emb[rows_a[acd_prof]]
        S = M @ A.T
        out = {}
        for k in K_GRID:
            maxs = S[:k, :k].max(axis=1)
            out[k] = {float(t): float((maxs >= t).mean()) for t in tau_arr}
        return out

    sem_point: dict[tuple, dict] = {}
    sem_reps: dict[tuple, list] = {}
    for ci, c in enumerate(CORPORA):
        rows_m, rows_a = emb_rows[c], emb_rows["academic"]
        # anchor
        m5, a5 = anchor_profiles[c]
        covs = semantic_coverages(m5, a5, rows_m, rows_a)
        for k in K_GRID:
            sem_point[(c, "all", "anchor", k)] = covs[k]
        # grid point draws + bootstrap reps
        for pi, P in enumerate(P_GRID):
            m5, a5 = point_profiles[(c, P)]
            covs = semantic_coverages(m5, a5, rows_m, rows_a)
            for k in K_GRID:
                sem_point[(c, P, pi, k)] = covs[k]
            mkt_reps, acd_reps = stored_profiles[c][P]
            for b in range(b_post):
                covs = semantic_coverages(mkt_reps[b], acd_reps[b], rows_m, rows_a)
                for k in K_GRID:
                    for t in TAUS:
                        sem_reps.setdefault((c, pi, k, t), []).append(1.0 - covs[k][t])
        print(f"  phase2 {c}: semantic done ({time.time()-t0:.0f}s)", flush=True)

    # -----------------------------------------------------------------
    # phase 3: skill-list CIs + table assembly
    # -----------------------------------------------------------------
    rows_out = []

    def skill_ci(indicator: np.ndarray, seed: int):
        rng = np.random.RandomState(seed)
        k = len(indicator)
        draws = rng.randint(0, k, size=(b_skill, k))
        boot = 1.0 - indicator[draws].mean(axis=1)
        return [float(x) for x in np.percentile(boot, [2.5, 97.5])]

    def post_ci(vals: list):
        return [float(x) for x in np.percentile(np.asarray(vals), [2.5, 97.5])]

    for ci, c in enumerate(CORPORA):
        rows_m_full, rows_a_full = emb_rows[c], emb_rows["academic"]
        # ---- anchor rows (P = all) ----
        m5, a5 = anchor_profiles[c]
        lex_cov = lex_point[(c, "all", "anchor")]
        mkt_vocab_c, acd_vocab_c = markets[c].vocab_list, acad.vocab_list
        for k in K_GRID:
            ind = lexical_indicator(m5, a5, k, mkt_vocab_c, acd_vocab_c)
            lo, hi = skill_ci(ind, SEED)
            rows_out.append({
                "corpus": c, "match": "lexical", "K": k, "P": "all", "tau": "",
                "SGI": round(1.0 - lex_cov[k], 4), "coverage": round(lex_cov[k], 4),
                "CI_skill_lo": round(lo, 4), "CI_skill_hi": round(hi, 4),
                "CI_post_lo": "", "CI_post_hi": "",
            })
        # anchor semantic: replicate published rng pattern (fresh per tau,
        # taus in order) so K=100 tau=0.5 is method-identical to ALIGN02/04
        for k in K_GRID:
            M = emb[rows_m_full[m5]]
            A = emb[rows_a_full[a5]]
            S = M @ A.T
            maxs = S[:k, :k].max(axis=1)
            rng_pub = np.random.RandomState(SEED)
            for t in TAUS:
                covered = maxs >= t
                draws = rng_pub.randint(0, k, size=(b_skill, k))
                boot = 1.0 - covered[draws].mean(axis=1)
                lo, hi = np.percentile(boot, [2.5, 97.5])
                cov = float(covered.mean())
                rows_out.append({
                    "corpus": c, "match": "semantic", "K": k, "P": "all", "tau": t,
                    "SGI": round(1.0 - cov, 4), "coverage": round(cov, 4),
                    "CI_skill_lo": round(float(lo), 4),
                    "CI_skill_hi": round(float(hi), 4),
                    "CI_post_lo": "", "CI_post_hi": "",
                })
        # ---- grid rows (P in P_GRID) ----
        for pi, P in enumerate(P_GRID):
            for k in K_GRID:
                cov_l = lex_point[(c, P, pi)][k]
                ind = lexical_indicator(point_profiles[(c, P)][0],
                                        point_profiles[(c, P)][1],
                                        k, mkt_vocab_c, acd_vocab_c)
                lo, hi = skill_ci(ind, SEED + 2000 + 1000 * ci + 10 * pi)
                plo, phi = post_ci(lex_reps[(c, pi, k)])
                rows_out.append({
                    "corpus": c, "match": "lexical", "K": k, "P": P, "tau": "",
                    "SGI": round(1.0 - cov_l, 4), "coverage": round(cov_l, 4),
                    "CI_skill_lo": round(lo, 4), "CI_skill_hi": round(hi, 4),
                    "CI_post_lo": round(plo, 4), "CI_post_hi": round(phi, 4),
                })
            for k in K_GRID:
                for t in TAUS:
                    cov_s = sem_point[(c, P, pi, k)][t]
                    ind = (np.asarray(
                        [1.0 if s >= t else 0.0 for s in
                         (emb[rows_m_full[point_profiles[(c, P)][0][:k]]]
                          @ emb[rows_a_full[point_profiles[(c, P)][1][:k]]].T)
                         .max(axis=1)]))
                    lo, hi = skill_ci(ind, SEED + 2000 + 1000 * ci + 10 * pi)
                    plo, phi = post_ci(sem_reps[(c, pi, k, t)])
                    rows_out.append({
                        "corpus": c, "match": "semantic", "K": k, "P": P, "tau": t,
                        "SGI": round(1.0 - cov_s, 4), "coverage": round(cov_s, 4),
                        "CI_skill_lo": round(lo, 4), "CI_skill_hi": round(hi, 4),
                        "CI_post_lo": round(plo, 4), "CI_post_hi": round(phi, 4),
                    })

    grid = pd.DataFrame(rows_out)
    grid.to_csv(out_dir / "table_sensitivity_grid.csv", index=False)

    # ---- summary: SGI range over the KxP grid per (corpus, match, tau) ----
    summary_rows = []
    g = grid[grid.P != "all"]
    for c in CORPORA:
        sub = g[(g.corpus == c) & (g.match == "lexical")]
        anchor = grid[(grid.corpus == c) & (grid.match == "lexical")
                      & (grid.P == "all") & (grid.K == 100)]
        summary_rows.append({
            "corpus": c, "match": "lexical", "tau": "",
            "SGI_min": sub.SGI.min(), "SGI_max": sub.SGI.max(),
            "SGI_median": sub.SGI.median(),
            "anchor_SGI_K100": float(anchor.SGI.iloc[0]),
        })
        for t in TAUS:
            sub = g[(g.corpus == c) & (g.match == "semantic") & (g.tau == t)]
            anchor = grid[(grid.corpus == c) & (grid.match == "semantic")
                          & (grid.P == "all") & (grid.K == 100) & (grid.tau == t)]
            summary_rows.append({
                "corpus": c, "match": "semantic", "tau": t,
                "SGI_min": sub.SGI.min(), "SGI_max": sub.SGI.max(),
                "SGI_median": sub.SGI.median(),
                "anchor_SGI_K100": float(anchor.SGI.iloc[0]),
            })
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(out_dir / "table_sensitivity_summary.csv", index=False)

    # ---- anchor reproduction checks ----
    anchor_report = {}
    anchor_ok = True
    for (c, match, k, t), expected in ANCHOR_EXPECTED.items():
        row = grid[(grid.corpus == c) & (grid.match == match)
                   & (grid.K == k) & (grid.P == "all")]
        if t is not None:
            row = row[row.tau == t]
        got = float(row.SGI.iloc[0])
        if match == "lexical":
            ok = round(got, 2) == expected
        else:
            ok = abs(got - expected) <= SEMANTIC_ANCHOR_TOL
        anchor_ok = anchor_ok and ok
        anchor_report[f"{c}_{match}_K{k}" + (f"_tau{t}" if t else "")] = {
            "expected_published": expected, "got": got, "ok": bool(ok),
        }
    if not anchor_ok:
        raise RuntimeError(f"anchor reproduction failed: {anchor_report}")

    # ---- matched-profile replication (market top-100 vs academic top-500).
    # The manuscript (paper/main.tex, "Profile-size sensitivity") claims that
    # at academic covering-set P=500 BOTH corpora give lexical/semantic SGI
    # 0.37/0.14, and at P=100 both give 0.52/0.32. ALIGN04's artifact only
    # backs the LinkedIn P=500 half, so this block recomputes all four
    # matched-profile cells from scratch, giving the full claim a single
    # registered artifact. The LinkedIn P=500 cells are hard-asserted against
    # the published ALIGN04 numbers (0.37/0.14); every cell is additionally
    # recorded as a manuscript-claim check (non-fatal here; surfaced in
    # metrics and by verify.py, so a manuscript/artifact mismatch is caught
    # before publication rather than silently shipped).
    acd500 = acad_prof500[:500]
    acd500_set = {acd_vocab[i] for i in acd500}
    rows_a_full = emb_rows["academic"]
    matched_profile: dict[str, dict] = {}
    for c in CORPORA:
        m100 = anchor_profiles[c][0][:100]
        m_vocab = markets[c].vocab_list
        lex_cov = sum(1 for i in m100 if m_vocab[i] in acd500_set) / len(m100)
        S = emb[emb_rows[c][m100]] @ emb[rows_a_full[acd500]].T
        sem_cov = float((S.max(axis=1) >= 0.5).mean())
        sym_lex = float(grid[(grid.corpus == c) & (grid.match == "lexical")
                             & (grid.K == 100) & (grid.P == "all")].SGI.iloc[0])
        sym_sem = float(grid[(grid.corpus == c) & (grid.match == "semantic")
                             & (grid.K == 100) & (grid.P == "all")
                             & (grid.tau == 0.5)].SGI.iloc[0])
        matched_profile[c] = {
            "P100_symmetric_lexical": sym_lex,
            "P100_symmetric_semantic_tau0.5": sym_sem,
            "P500_asymmetric_lexical": round(1.0 - lex_cov, 4),
            "P500_asymmetric_semantic_tau0.5": round(1.0 - sem_cov, 4),
        }
    li_matched = matched_profile["linkedin_2024"]
    align04_report = {
        "linkedin_2024_lexical_K100": {
            "expected_published":
                ALIGN04_ASYMMETRIC_EXPECTED["linkedin_2024_lexical_K100"],
            "got": li_matched["P500_asymmetric_lexical"],
            "ok": round(li_matched["P500_asymmetric_lexical"], 2)
            == ALIGN04_ASYMMETRIC_EXPECTED["linkedin_2024_lexical_K100"],
        },
        "linkedin_2024_semantic_K100_tau0.5": {
            "expected_published":
                ALIGN04_ASYMMETRIC_EXPECTED["linkedin_2024_semantic_K100_tau0.5"],
            "got": li_matched["P500_asymmetric_semantic_tau0.5"],
            "ok": abs(li_matched["P500_asymmetric_semantic_tau0.5"]
                      - ALIGN04_ASYMMETRIC_EXPECTED[
                          "linkedin_2024_semantic_K100_tau0.5"])
            <= SEMANTIC_ANCHOR_TOL,
        },
    }
    if not all(v["ok"] for v in align04_report.values()):
        raise RuntimeError(f"ALIGN04 replication failed: {align04_report}")
    # manuscript line claims: both corpora 0.52/0.32 @ P=100 and 0.37/0.14 @ P=500
    manuscript_claim_checks: dict[str, dict] = {}
    for c in CORPORA:
        for cell, expected in [("P100_symmetric_lexical", 0.52),
                               ("P100_symmetric_semantic_tau0.5", 0.32),
                               ("P500_asymmetric_lexical", 0.37),
                               ("P500_asymmetric_semantic_tau0.5", 0.14)]:
            got = matched_profile[c][cell]
            ok = (round(got, 2) == expected if "lexical" in cell
                  else abs(got - expected) <= SEMANTIC_ANCHOR_TOL)
            manuscript_claim_checks[f"{c}_{cell}"] = {
                "expected_manuscript": expected, "got": got, "ok": bool(ok)}

    # ---- figure: SGI heatmap over K x P ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        for ri, c in enumerate(CORPORA):
            for ci2, (match, t) in enumerate([("lexical", None), ("semantic", 0.5)]):
                ax = axes[ri][ci2]
                sub = g[(g.corpus == c) & (g.match == match)]
                if t is not None:
                    sub = sub[sub.tau == t]
                pivot = sub.pivot_table(index="K", columns="P", values="SGI")
                im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto",
                               vmin=0.0, vmax=1.0)
                ax.set_xticks(range(len(pivot.columns)), pivot.columns)
                ax.set_yticks(range(len(pivot.index)), pivot.index)
                ax.set_xlabel("P (postings sampled)")
                ax.set_ylabel("K (profile size)")
                title = f"{c} — {match}" + (f" @ tau={t}" if t else "")
                ax.set_title(title, fontsize=9)
                for yi in range(pivot.shape[0]):
                    for xi in range(pivot.shape[1]):
                        ax.text(xi, yi, f"{pivot.values[yi, xi]:.2f}",
                                ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=axes, shrink=0.6, label="SGI")
        fig.suptitle("SENS01: SGI over the (K, P) grid — seed 42", fontsize=11)
        fig.savefig(out_dir / "figure_sensitivity_heatmap.png", dpi=150,
                    bbox_inches="tight")
        plt.close(fig)
        figure_written = True
    except Exception as e:  # pragma: no cover
        figure_written = False
        print(f"figure skipped: {e}", flush=True)

    # ---- metrics ----
    ranges = {}
    for c in CORPORA:
        ranges[c] = {}
        sub = g[(g.corpus == c) & (g.match == "lexical")]
        ranges[c]["lexical"] = {"min": float(sub.SGI.min()),
                                "max": float(sub.SGI.max())}
        for t in TAUS:
            sub = g[(g.corpus == c) & (g.match == "semantic") & (g.tau == t)]
            ranges[c][f"semantic_tau_{t}"] = {"min": float(sub.SGI.min()),
                                              "max": float(sub.SGI.max())}
    metrics = {
        "experiment_id": "SENS01_sgi_sensitivity",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n_skill": b_skill,
        "bootstrap_n_post": b_post,
        "smoke": bool(args.smoke),
        "grid": {"K": K_GRID, "P": P_GRID, "tau": TAUS,
                 "match": ["lexical", "semantic"], "corpora": CORPORA},
        "n_table_rows": int(len(grid)),
        "n_postings": n_postings,
        "academic_rows": acad.n_rows,
        "sbert_model": MODEL_NAME,
        "device": device,
        "distinct_profile_skills_embedded": len(all_strings),
        "anchor_reproduction": anchor_report,
        "matched_profile_replication": matched_profile,
        "align04_asymmetric_replication": align04_report,
        "manuscript_claim_checks": manuscript_claim_checks,
        "sgi_ranges_over_KP_grid": ranges,
        "figure_written": figure_written,
    }
    # ---- self-consistency guard: reported ranges/anchors must be exactly
    # derivable from the tables we just wrote. Catches any divergence between
    # the in-memory state and the on-disk artifacts (e.g. a stale or mutated
    # DataFrame) instead of shipping a metrics.json that contradicts its own
    # table_sensitivity_grid.csv. (Such a divergence was observed once on
    # 2026-10-11 in an aborted intermediate run; this guard exists so it can
    # never pass silently again.)
    written = pd.read_csv(out_dir / "table_sensitivity_grid.csv")
    wg = written[written.P != "all"]
    for c in CORPORA:
        sub = wg[(wg.corpus == c) & (wg.match == "lexical")]
        r = ranges[c]["lexical"]
        assert (abs(float(sub.SGI.min()) - r["min"]) < 1e-9
                and abs(float(sub.SGI.max()) - r["max"]) < 1e-9), \
            f"range mismatch vs written grid (lexical, {c}): " \
            f"csv [{sub.SGI.min()}, {sub.SGI.max()}] vs metrics {r}"
        for t in TAUS:
            sub = wg[(wg.corpus == c) & (wg.match == "semantic")
                     & (wg.tau == t)]
            r = ranges[c][f"semantic_tau_{t}"]
            assert (abs(float(sub.SGI.min()) - r["min"]) < 1e-9
                    and abs(float(sub.SGI.max()) - r["max"]) < 1e-9), \
                f"range mismatch vs written grid (semantic tau={t}, {c}): " \
                f"csv [{sub.SGI.min()}, {sub.SGI.max()}] vs metrics {r}"
    for _, srow in summary_df.iterrows():
        if srow["match"] == "lexical":
            a = written[(written.corpus == srow["corpus"])
                        & (written.match == "lexical")
                        & (written.K == 100) & (written.P == "all")]
        else:
            a = written[(written.corpus == srow["corpus"])
                        & (written.match == "semantic")
                        & (written.K == 100) & (written.P == "all")
                        & (written.tau == float(srow["tau"]))]
        assert abs(float(a.SGI.iloc[0]) - float(srow["anchor_SGI_K100"])) < 1e-9, \
            f"summary anchor mismatch vs written grid: {dict(srow)}"

    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps({k: v for k, v in metrics.items()
                      if k not in ("anchor_reproduction",
                                   "align04_asymmetric_replication",
                                   "matched_profile_replication",
                                   "manuscript_claim_checks")}, indent=2),
          flush=True)
    print("anchor_reproduction:", json.dumps(anchor_report, indent=2), flush=True)
    print("align04_asymmetric_replication:",
          json.dumps(align04_report, indent=2), flush=True)
    print("matched_profile_replication:",
          json.dumps(matched_profile, indent=2), flush=True)
    print("manuscript_claim_checks:",
          json.dumps(manuscript_claim_checks, indent=2), flush=True)
    failed_claims = {k: v for k, v in manuscript_claim_checks.items()
                     if not v["ok"]}
    if failed_claims:
        print("WARNING: manuscript claims not reproduced (non-fatal; "
              "resolve at the P2-3 manuscript edit):",
              json.dumps(failed_claims, indent=2), flush=True)


if __name__ == "__main__":
    sys.exit(main())
