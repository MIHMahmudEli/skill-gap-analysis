"""VALID01: External validation of the skill matcher against expert gold.

Gold source: Decorte et al. (2022/2023) skill-extraction benchmark (CC-BY-4.0,
HF `jensjorisdecorte/skill-extraction-{tech,house}`) -- SkillSpan job postings
whose skill mentions were manually mapped to ESCO skills by human experts.
Files are fetched from the upstream GitHub repo at a pinned commit (no
redistribution, immutable reference).

Inputs : tech/house test annotation CSVs + ESCO preferred-label inventory
         (skills_en_label.txt, ESCO v1.1.0) + market/academic corpora from the
         primary Kaggle bundle (top-100 profiles regenerated as in ALIGN01).
Outputs: metrics.json, table_valid_pairs.csv, table_valid_coverage.csv,
         pair_results.csv

Protocol (seed 42, 1000x bootstrap over pairs):
  mention = (sentence, span) with >=1 real ESCO label; rows labelled
  LABEL NOT PRESENT / UNDERSPECIFIED are excluded (no valid expert mapping).
  TECHWOLF is excluded: it annotates labels at sentence level without span
  offsets, so mention->label pairs cannot be formed.
  positives = mention x each gold label;
  negatives = (i) one uniform random non-gold label per mention, (ii) hard
  negatives = labels of other mentions inside the same sentence.
  Matchers: lexical exact and lexical containment (normalized), and SBERT
  (all-MiniLM-L6-v2) cosine at tau in {0.4, 0.5, 0.6, 0.7}.
  Metrics vs expert mapping: accuracy, precision, recall, F1, Cohen's kappa
  (system vs expert), ROC-AUC for the cosine score.
  Coverage check: ESCO-inventory coverage of the market/academic top-100
  (lexical exact + semantic tau=0.5).
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
BOOTSTRAP_N = 1000
TOP_N = 100
PROFILE_N = 500
TAUS = [0.4, 0.5, 0.6, 0.7]
MODEL_NAME = "all-MiniLM-L6-v2"
REPO_PIN = "19305c85e35a74fb2a5128d8ee3798b06470b596"
RAW = (f"https://raw.githubusercontent.com/jensjorisdecorte/"
       f"Skill-Extraction-benchmark/{REPO_PIN}/data")
UPSTREAM = {
    "tech_test_annotations.csv": f"{RAW}/tech_test_annotations.csv",
    "house_test_annotations.csv": f"{RAW}/house_test_annotations.csv",
    "skills_en_label.txt": f"{RAW}/skills_en_label.txt",
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().strip("*").lower()).strip()


def resolve(name: str) -> Path:
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
        candidates.append(Path(env_dir) / "valid1" / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    for c in candidates:
        if c.exists():
            return c
    # not staged: fetch from the pinned upstream commit into the output dir
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    cache = out_dir / "_upstream"
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / name
    if not dest.exists():
        print(f"downloading pinned input {name}", flush=True)
        with urllib.request.urlopen(UPSTREAM[name], timeout=120) as r:
            dest.write_bytes(r.read())
    return dest


def resolve_bundle(name: str) -> Path:
    """Bundle CSVs only (never fetched remotely)."""
    env_dir = os.environ.get("SKILLGAP_INPUT_DIR")
    candidates = []
    if env_dir:
        candidates.append(Path(env_dir) / name)
    for root in [Path("/kaggle/input/datasets/studyhub991/skill-gap-inputs-v1"),
                 Path("/kaggle/input/skill-gap-inputs-v1/bundle"),
                 Path("/kaggle/input/skill-gap-inputs-v1")]:
        candidates.append(root / name)
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"bundle input {name} not found")


def load_gold() -> pd.DataFrame:
    frames = []
    for name in ["tech_test_annotations.csv", "house_test_annotations.csv"]:
        df = pd.read_csv(resolve(name))
        df = df[["sentence", "span", "label"]].dropna(subset=["span", "label"])
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    raw["label"] = raw["label"].astype(str)
    bad = raw.label.isin(["LABEL NOT PRESENT", "UNDERSPECIFIED"])
    real = raw[~bad].copy()
    real["sentence"] = real.sentence.astype(str)
    real["span"] = real.span.astype(str)
    return real.drop_duplicates(["sentence", "span", "label"])


def build_pairs(real: pd.DataFrame, rng: np.random.RandomState):
    mentions: dict[tuple, list] = defaultdict(list)
    for _, r in real.iterrows():
        mentions[(r.sentence, r.span)].append(r.label)
    mentions = {k: sorted(set(v)) for k, v in mentions.items()}
    pool = sorted({lab for labs in mentions.values() for lab in labs})
    by_sent: dict[str, list] = defaultdict(list)
    for (sent, span) in mentions:
        by_sent[sent].append(span)

    rows = []
    for key in sorted(mentions):
        sent, span = key
        gold = mentions[key]
        for lab in gold:
            rows.append({"sentence": sent, "span": span, "label": lab,
                         "gold": 1, "neg_type": "positive"})
        # (i) uniform random non-gold label
        others = [l for l in pool if l not in gold]
        rows.append({"sentence": sent, "span": span,
                     "label": others[rng.randint(len(others))],
                     "gold": 0, "neg_type": "random_neg"})
        # (ii) hard negative: another mention's label in the same sentence
        siblings = [s for s in by_sent[sent] if s != span]
        if siblings:
            for _ in range(12):
                sib = siblings[rng.randint(len(siblings))]
                cand = mentions[(sent, sib)]
                cand = [l for l in cand if l not in gold]
                if cand:
                    rows.append({"sentence": sent, "span": span,
                                 "label": cand[rng.randint(len(cand))],
                                 "gold": 0, "neg_type": "hard_neg"})
                    break
    return pd.DataFrame(rows), mentions, pool


def safe_kappa(y_true, y_pred) -> float:
    from sklearn.metrics import cohen_kappa_score
    k = cohen_kappa_score(y_true, y_pred)
    return float(k) if np.isfinite(k) else 0.0


def eval_rule(pairs: pd.DataFrame, pred: np.ndarray, score=None) -> dict:
    from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                                 recall_score, roc_auc_score)
    y = pairs.gold.values
    acc = float(accuracy_score(y, pred))
    rec = {"accuracy": round(acc, 4),
           "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
           "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
           "f1": round(float(f1_score(y, pred, zero_division=0)), 4),
           "kappa": round(safe_kappa(y, pred), 4)}
    if score is not None:
        rec["auc"] = round(float(roc_auc_score(y, score)), 4)
    rng = np.random.RandomState(SEED)
    idx = np.arange(len(y))
    accs, kappas = [], []
    for _ in range(BOOTSTRAP_N):
        b = rng.choice(idx, size=len(idx), replace=True)
        accs.append(accuracy_score(y[b], pred[b]))
        kappas.append(safe_kappa(y[b], pred[b]))
    rec["accuracy_ci"] = [round(float(v), 4) for v in np.percentile(accs, [2.5, 97.5])]
    rec["kappa_ci"] = [round(float(v), 4) for v in np.percentile(kappas, [2.5, 97.5])]
    return rec


def main() -> None:
    t0 = time.time()
    out_dir = Path(os.environ.get("SKILLGAP_OUTPUT_DIR", "/kaggle/working"))
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(SEED)

    real = load_gold()
    pairs, mentions, label_pool = build_pairs(real, rng)

    # --- regenerate top-100 profiles exactly as ALIGN01 -------------------
    market_rows = []
    for s in pd.read_csv(resolve_bundle("hf_skill_gap_skills.csv"),
                         usecols=["job_skills"])["job_skills"].dropna():
        market_rows += [x.strip().lower() for x in str(s).split(",")
                        if x.strip()]
    market_top = [s for s, _ in
                  Counter(market_rows).most_common(PROFILE_N)][:TOP_N]
    acad_rows = []
    for s in pd.read_csv(resolve_bundle("hf_job_skill_set.csv"),
                         usecols=["job_skill_set"])["job_skill_set"].dropna():
        txt = str(s).strip().strip("[]").replace("'", "")
        acad_rows += [x.strip().lower() for x in txt.split(",") if x.strip()]
    acad_top = [s for s, _ in
                Counter(acad_rows).most_common(PROFILE_N)][:TOP_N]

    esco_labels = [norm(l) for l in
                   resolve("skills_en_label.txt").read_text(
                       encoding="utf-8").splitlines() if l.strip()]
    esco_labels = sorted(set(esco_labels))

    # --- embeddings -------------------------------------------------------
    import torch
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL_NAME, device=device)

    span_texts = sorted(set(pairs.span))
    pair_labels = sorted(set(pairs.label))
    span_emb = {s: e for s, e in zip(
        span_texts, model.encode(span_texts, show_progress_bar=False,
                                 convert_to_numpy=True))}
    lab_emb = {s: e for s, e in zip(
        pair_labels, model.encode(pair_labels, show_progress_bar=False,
                                  convert_to_numpy=True))}
    pairs["cosine"] = [
        float(cosine_similarity(span_emb[s].reshape(1, -1),
                                lab_emb[l].reshape(1, -1))[0, 0])
        for s, l in zip(pairs.span, pairs.label)]

    ns = [norm(x) for x in pairs.span]
    nl = [norm(x) for x in pairs.label]
    pairs["lexical_exact"] = np.array([int(a == b) for a, b in zip(ns, nl)])
    pairs["lexical_contains"] = [
        int((a and b) and (a in b or b in a)) for a, b in zip(ns, nl)]

    results = {}
    results["lexical_exact"] = eval_rule(pairs, pairs.lexical_exact.values)
    results["lexical_contains"] = eval_rule(
        pairs, pairs.lexical_contains.values)
    for tau in TAUS:
        pred = (pairs.cosine.values >= tau).astype(int)
        results[f"sbert_tau_{tau}"] = eval_rule(
            pairs, pred, score=pairs.cosine.values)

    # --- ESCO coverage of the top-100 profiles ----------------------------
    inv_emb = model.encode(esco_labels, show_progress_bar=False,
                           convert_to_numpy=True)
    cov_rows = []
    for corpus, skills in [("market_top100", market_top),
                           ("academic_top100", acad_top)]:
        sk_emb = model.encode(skills, show_progress_bar=False,
                              convert_to_numpy=True)
        cos = cosine_similarity(sk_emb, inv_emb)
        maxc = cos.max(axis=1)
        best = np.array(esco_labels)[cos.argmax(axis=1)]
        lex = float(np.mean([norm(s) == b for s, b in zip(skills, best)]))
        lex_direct = float(np.mean(
            [norm(s) in set(esco_labels) for s in skills]))
        sem = float(np.mean(maxc >= 0.5))
        rng_c = np.random.RandomState(SEED)
        boot_sem = [float(np.mean(rng_c.choice(maxc >= 0.5, size=TOP_N,
                                               replace=True)))
                    for _ in range(BOOTSTRAP_N)]
        boot_lex = [float(np.mean(rng_c.choice(
            np.array([norm(s) in set(esco_labels) for s in skills]),
            size=TOP_N, replace=True)))
            for _ in range(BOOTSTRAP_N)]
        cov_rows.append({
            "corpus": corpus,
            "lexical_coverage": round(lex_direct, 4),
            "lexical_ci": [round(float(v), 4)
                           for v in np.percentile(boot_lex, [2.5, 97.5])],
            "semantic_coverage_tau0.5": round(sem, 4),
            "semantic_ci": [round(float(v), 4)
                            for v in np.percentile(boot_sem, [2.5, 97.5])],
            "mean_best_cosine": round(float(maxc.mean()), 4),
        })

    # --- outputs ----------------------------------------------------------
    flat_rows = []
    for rule, m in results.items():
        if "_tau_" in rule:
            matcher, tau = rule.rpartition("_tau_")[0], rule.rpartition("_tau_")[2]
        else:
            matcher, tau = rule, ""
        flat_rows.append({
            "matcher": matcher, "tau": tau,
            "accuracy": m["accuracy"],
            "acc_ci_lo": m["accuracy_ci"][0], "acc_ci_hi": m["accuracy_ci"][1],
            "precision": m["precision"], "recall": m["recall"],
            "f1": m["f1"], "kappa": m["kappa"],
            "kappa_ci_lo": m["kappa_ci"][0], "kappa_ci_hi": m["kappa_ci"][1],
            "auc": m.get("auc", ""),
        })
    pd.DataFrame(flat_rows).to_csv(out_dir / "table_valid_pairs.csv",
                                   index=False)
    pd.DataFrame(cov_rows).to_csv(out_dir / "table_valid_coverage.csv",
                                  index=False)
    pairs_out = pairs[["sentence", "span", "label", "gold", "neg_type",
                       "cosine", "lexical_exact", "lexical_contains"]].copy()
    pairs_out["sentence"] = pairs_out.sentence.str.slice(0, 160)
    pairs_out.to_csv(out_dir / "pair_results.csv", index=False)

    s5 = results["sbert_tau_0.5"]
    metrics = {
        "experiment_id": "VALID01_esco_gold",
        "status": "completed",
        "runtime_sec": round(time.time() - t0, 2),
        "seed": SEED,
        "bootstrap_n": BOOTSTRAP_N,
        "model": MODEL_NAME,
        "device": device,
        "gold_source": ("Decorte et al. 2022/2023 skill-extraction benchmark "
                        f"(CC-BY-4.0), pinned commit {REPO_PIN}"),
        "esco_inventory": "skills_en_label.txt (ESCO v1.1.0 preferred labels)",
        "n_mentions": len(mentions),
        "n_label_pool": len(label_pool),
        "n_pairs": int(len(pairs)),
        "n_positive": int(pairs.gold.sum()),
        "n_negative": int(len(pairs) - pairs.gold.sum()),
        "n_positive_by_type": {k: int(v) for k, v in
                               pairs.groupby("neg_type").gold.sum().items()},
        "tau_thresholds": TAUS,
        "kappa_at_tau_0.5": s5["kappa"],
        "kappa_ci_at_tau_0.5": s5["kappa_ci"],
        "accuracy_at_tau_0.5": s5["accuracy"],
        "accuracy_ci_at_tau_0.5": s5["accuracy_ci"],
        "precision_at_tau_0.5": s5["precision"],
        "recall_at_tau_0.5": s5["recall"],
        "auc_cosine": s5.get("auc"),
        "kappa_lexical_exact": results["lexical_exact"]["kappa"],
        "kappa_lexical_contains": results["lexical_contains"]["kappa"],
        "sensitivity": results,
        "esco_coverage": cov_rows,
    }
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps({k: metrics[k] for k in
                      ["runtime_sec", "n_pairs", "n_positive", "n_negative",
                       "kappa_at_tau_0.5", "accuracy_at_tau_0.5",
                       "auc_cosine", "kappa_lexical_exact",
                       "kappa_lexical_contains"]}, indent=2))
    print(json.dumps(cov_rows, indent=2))


if __name__ == "__main__":
    sys.exit(main())
