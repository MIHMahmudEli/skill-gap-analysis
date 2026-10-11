"""Score the hand-labelling package once labels are filled. SAMPLING/SCORING
ONLY — this never runs CURR02 or ALIGN05 and never computes an SGI.

Files (labelling/ = author-facing; key = sealed, do not open before finishing):
  curriculum_precision_100.csv  rater_label, rater2_label in {yes,no}
  curriculum_recall_100.csv     rater_label in {yes_keep,no_drop}
  align05_titles_200.csv        author_label in {tech,non-tech} — BLINDED file
                                (sample_id, job_title, author_label only; row
                                order shuffled seed 42)
  experiments/align05_titles_200_key.csv   sealed key (sample_id -> stratum,
                                sampling_weight, rule_matched, predicted_soc,
                                predicted_tech); read here only, never shown

Reported per file:
  * curriculum precision   = share yes (proportional allocation -> unweighted
                             mean is design-valid), Wilson 95% CI
  * curriculum recall      = design-weighted: estimated missed =
                             sum_c N_c * (wrong_c / n_c) over
                             (vintage_group, drop_reason) cells (N_c from
                             datasets/curriculum/extracted/
                             extraction_summary.json::recall_design);
                             recall = est_correct / (est_correct + missed)
                             where est_correct = precision_hat * kept_total;
                             stratified-bootstrap 95% CI (B=1000, seed 42)
  * rater agreement        = Cohen's kappa (rater1 vs rater2, precision file)
  * ALIGN05 gate           = design-weighted tech precision (plain mean over
                             the predicted-tech stratum) and recall via the
                             two-stratum estimator
                             recall = (w_T*TP_T) / (w_T*TP_T + w_N*FP_N),
                             stratified-bootstrap 95% CIs (B=1000, seed 42);
                             F1; kappa vs rule predictions; disagreement rows.
                             Gate: precision >= 0.90 AND recall >= 0.90.

Labels are never written by this script; missing labels are reported and it
exits cleanly. Re-run any time after editing label columns.
Usage:  python labelling/score_labels.py
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# LABELLING_DIR exists only so the scorer can be smoke-tested against scratch
# copies; normal runs always read the committed labelling/ files.
import os  # noqa: E402
LAB = Path(os.environ.get("LABELLING_DIR", ROOT / "labelling"))
# A5_KEY exists only so the scorer can be smoke-tested against scratch copies.
A5_KEY = Path(os.environ.get("A5_KEY", ROOT / "experiments" / "align05_titles_200_key.csv"))
PREC_CSV = LAB / "curriculum_precision_100.csv"
RECALL_CSV = LAB / "curriculum_recall_100.csv"
A5_CSV = LAB / "align05_titles_200.csv"
EXTRACT_SUMMARY = ROOT / "datasets" / "curriculum" / "extracted" / "extraction_summary.json"
B, SEED, Z = 1000, 42, 1.96  # bootstrap draws, seed, normal quantile

YES = {"yes", "y", "1", "true", "yes_keep"}
NO = {"no", "n", "0", "false", "no_drop"}
TECH = {"tech", "1", "yes", "true"}
NONTECH = {"non-tech", "nontech", "non_tech", "0", "no", "false"}


def norm_label(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip().lower()
    if s in YES:
        return 1
    if s in NO:
        return 0
    if s in TECH:
        return 1
    if s in NONTECH:
        return 0
    return None  # blank or unrecognized


def wilson_ci(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    if n == 0 or len(set(a + b)) < 2:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in set(ca) | set(cb))
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def boot_ci(vals_by_cell: dict, combine, rng) -> tuple[float, float]:
    """Stratified bootstrap: resample with replacement inside each cell."""
    out = []
    for _ in range(B):
        draw = {c: rng.choice(v, size=len(v), replace=True)
                for c, v in vals_by_cell.items() if len(v)}
        out.append(combine(draw))
    return (float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)))


def partial_warn(n: int, total: int, name: str) -> None:
    if 0 < n < total:
        print(f"    NOTE: partial fill ({n}/{total}) — all estimates provisional "
              f"until every row is labelled.")


print("=" * 72)
print("LABELLING SCORES (labels are read-only inputs; nothing else is computed)")
print("=" * 72)

# ---------------------------------------------------------------- curriculum precision
p = pd.read_csv(PREC_CSV)
p["lab"] = p["rater_label"].map(norm_label)
n_filled = int(p.lab.notna().sum())
print(f"\n[1] curriculum precision ({PREC_CSV.name}): {n_filled}/{len(p)} rater_label filled")
partial_warn(n_filled, len(p), "precision")
if n_filled:
    k = int(p.lab.sum())
    prec_hat = k / n_filled
    lo, hi = wilson_ci(k, n_filled)
    print(f"    precision = {prec_hat:.3f}  (Wilson 95% CI [{lo:.3f}, {hi:.3f}])")
    print(f"    bar: >= 0.90 -> {'PASS' if prec_hat >= 0.90 else 'FAIL (review)'}")
    p["lab2"] = p["rater2_label"].map(norm_label) if "rater2_label" in p else None
    if p.lab2 is not None and p.lab2.notna().any():
        both = p.dropna(subset=["lab", "lab2"])
        print(f"    rater2 filled: {int(p.lab2.notna().sum())}/{len(p)}")
        print(f"    Cohen's kappa (rater1 vs rater2, n={len(both)}) = "
              f"{kappa(both.lab.astype(int).tolist(), both.lab2.astype(int).tolist()):.3f}")
    else:
        print("    rater2_label: not filled (optional)")

# ---------------------------------------------------------------- curriculum recall
r = pd.read_csv(RECALL_CSV)
r["lab"] = r["rater_label"].map(norm_label)
n_filled = int(r.lab.notna().sum())
print(f"\n[2] curriculum recall ({RECALL_CSV.name}): {n_filled}/{len(r)} rater_label filled")
partial_warn(n_filled, len(r), "recall")
if n_filled:
    summary = json.loads(EXTRACT_SUMMARY.read_text(encoding="utf-8"))
    sizes = summary["recall_design"]["stratum_population_sizes"]
    N = summary["recall_design"]["population_n"]
    kept_total = summary["phrases_kept_total"]
    cells = {}
    for (v, dr), g in r.groupby([r["vintage_group"], r["drop_reason"]]):
        lab = g.lab.dropna()
        cells[f"{v}|{dr}"] = (g.shape[0], lab.values.astype(int))
    missed, per_rule = 0.0, {}
    for c, (n_c, labs) in cells.items():
        N_c = sizes.get(c, 0)
        wrong_rate = labs.mean() if len(labs) else 0.0
        missed += N_c * wrong_rate
        per_rule[c] = (int(labs.sum()) if len(labs) else 0, len(labs), N_c)
    prec_hat = float(p.lab.dropna().mean()) if n_filled else float("nan")
    est_correct = kept_total * prec_hat if not math.isnan(prec_hat) else float("nan")
    recall_hat = est_correct / (est_correct + missed) if not math.isnan(est_correct) else float("nan")
    print(f"    design-weighted estimated missed phrases = {missed:.1f} "
          f"(population drops N = {N}; kept_total = {kept_total})")
    print(f"    estimated recall = {recall_hat:.3f}  (est_correct = {est_correct:.0f})")
    rng = np.random.RandomState(SEED)
    cells_labs = {c: labs for c, (_n_c, labs) in cells.items()}
    ci = boot_ci(cells_labs, lambda d: (
        (lambda m: (kept_total * prec_hat) / (kept_total * prec_hat + m))(
            sum(sizes.get(c, 0) * (np.mean(v) if len(v) else 0.0) for c, v in d.items()))
    ), rng) if not math.isnan(prec_hat) else (float("nan"),) * 2
    print(f"    stratified-bootstrap 95% CI = [{ci[0]:.3f}, {ci[1]:.3f}] (B={B}, seed={SEED})")
    print("    per (vintage, drop_reason) cell — wrongly-dropped / labelled / N_c:")
    for c, (w, n_c, N_c) in sorted(per_rule.items()):
        print(f"      {c:38s} {w:2d}/{n_c:2d}  N_c={N_c:3d}  rate={w/n_c if n_c else float('nan'):.2f}")
else:
    print("    (fill rater_label to score; estimator documented in INSTRUCTIONS.md)")

# ---------------------------------------------------------------- ALIGN05 gate
a = pd.read_csv(A5_CSV)
a["lab"] = a["author_label"].map(norm_label)
key = pd.read_csv(A5_KEY)  # sealed design columns (stratum/weights/predictions)
a = a.merge(key, on="sample_id", how="left", validate="one_to_one")
assert a["stratum"].notna().all(), "every sample_id must exist in the sealed key"
n_filled = int(a.lab.notna().sum())
print(f"\n[3] ALIGN05 title gate ({A5_CSV.name}): {n_filled}/{len(a)} author_label filled")
partial_warn(n_filled, len(a), "ALIGN05")
if n_filled:
    tech_rows = a[a.stratum == "predicted_tech"].dropna(subset=["lab"])
    non_rows = a[a.stratum == "predicted_nontech"].dropna(subset=["lab"])
    w_T = float(tech_rows.sampling_weight.iloc[0]) if len(tech_rows) else float("nan")
    w_N = float(non_rows.sampling_weight.iloc[0]) if len(non_rows) else float("nan")
    TP = int(tech_rows.lab.sum())
    FP = int(non_rows.lab.sum())
    precision = TP / len(tech_rows) if len(tech_rows) else float("nan")
    TP_w, FP_w = w_T * TP, w_N * FP
    recall = TP_w / (TP_w + FP_w) if (TP_w + FP_w) else float("nan")
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall else float("nan"))
    print(f"    strata: predicted_tech n={len(tech_rows)} (w={w_T:.2f}), "
          f"predicted_nontech n={len(non_rows)} (w={w_N:.2f})")
    print(f"    design-weighted TECH precision = {precision:.3f}")
    print(f"    design-weighted TECH recall    = {recall:.3f}  "
          f"(TP_w={TP_w:.0f}, FP_w={FP_w:.0f})")
    print(f"    F1 = {f1:.3f}")
    rng = np.random.RandomState(SEED)
    cells2 = {"predicted_tech": tech_rows.lab.values.astype(int),
              "predicted_nontech": non_rows.lab.values.astype(int)}
    ci_p = boot_ci(cells2, lambda d: np.mean(d["predicted_tech"]), np.random.RandomState(SEED))
    ci_r = boot_ci(cells2, lambda d: (w_T * np.sum(d["predicted_tech"])) /
                   (w_T * np.sum(d["predicted_tech"]) + w_N * np.sum(d["predicted_nontech"]))
                   if (np.sum(d["predicted_tech"]) + np.sum(d["predicted_nontech"])) else 0.0,
                   np.random.RandomState(SEED))
    print(f"    95% CIs (B={B}, seed={SEED}): precision [{ci_p[0]:.3f}, {ci_p[1]:.3f}], "
          f"recall [{ci_r[0]:.3f}, {ci_r[1]:.3f}]")
    print(f"    GATE: precision >= 0.90 AND recall >= 0.90 -> "
          f"{'PASS' if precision >= 0.90 and recall >= 0.90 else 'FAIL (revision rule applies)'}")
    a["pred"] = (a.stratum == "predicted_tech").astype(int)
    both = a.dropna(subset=["lab"])
    print(f"    Cohen's kappa (author labels vs v1 rule predictions, n={len(both)}) = "
          f"{kappa(both.lab.astype(int).tolist(), both.pred.astype(int).tolist()):.3f}")
    dis = both[both.lab.astype(int) != both.pred]
    print(f"    disagreement rows ({len(dis)}):")
    for _, row in dis.iterrows():
        print(f"      {row.sample_id}  pred={'tech' if row.pred else 'non-tech'} "
              f"label={'tech' if int(row.lab) else 'non-tech'}  {row.job_title!r}")
else:
    print("    (fill author_label to score; estimator fixed in ALIGN05_PREREG.md 5.3)")

print("\nDone. This script computes no SGI and runs no experiment.")
