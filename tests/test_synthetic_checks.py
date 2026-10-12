"""Unit tests for the generator-signature checkers in datasets/synthetic_checks.py,
plus a structural check of the committed artifact datasets/synthetic_checks_output.json
(author instruction 2026-10-12, step 2)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "datasets"))
from synthetic_checks import (  # noqa: E402
    binary_balance,
    cramers_v,
    id_sequence,
    missingness_pattern,
    uniformity_chi2,
)

ROOT = Path(__file__).resolve().parents[1]


def test_uniformity_flags_uniform_draw():
    rng = np.random.default_rng(42)
    s = pd.Series(rng.choice(list("ABCD"), size=12000))
    r = uniformity_chi2(s)
    assert r["applicable"] and r["uniform_draw_consistent"]
    assert r["n_categories"] == 4 and r["df"] == 3


def test_uniformity_rejects_skewed_distribution():
    rng = np.random.default_rng(42)
    # zipf-like: strongly non-uniform categorical
    s = pd.Series(rng.choice(list("ABCD"), size=12000, p=[0.7, 0.2, 0.07, 0.03]))
    r = uniformity_chi2(s)
    assert r["applicable"] and not r["uniform_draw_consistent"]
    assert r["balance_ratio_max_min"] > 1.10


def test_uniformity_not_applicable_outside_cardinality_window():
    s = pd.Series(["only-one-category"] * 50)
    assert not uniformity_chi2(s)["applicable"]
    s2 = pd.Series([f"c{i}" for i in range(30)]) * 5   # > max_categories
    assert not uniformity_chi2(s2)["applicable"]


def test_binary_balance():
    rng = np.random.default_rng(42)
    assert binary_balance(pd.Series(rng.integers(0, 2, size=20000)))["coin_flip_consistent"]
    skewed = pd.Series(np.where(np.arange(10000) < 7000, 1, 0))
    r = binary_balance(skewed)
    assert r["applicable"] and not r["coin_flip_consistent"]
    assert abs(r["share_positive"] - 0.7) < 0.01
    # non 0/1 content -> not applicable
    assert not binary_balance(pd.Series(["yes", "no"] * 10))["applicable"]


def test_coupling_detects_deterministic_mapping():
    rng = np.random.default_rng(42)
    a = pd.Series(rng.choice(["x", "y", "z"], size=6000))
    b = a.map({"x": "u", "y": "v", "z": "w"})          # perfect 1:1
    r = cramers_v(a, b)
    assert r["applicable"] and r["near_deterministic_coupling"]
    assert r["cramers_v"] > 0.95


def test_coupling_flags_independence_as_low_v():
    rng = np.random.default_rng(42)
    a = pd.Series(rng.choice(["x", "y", "z"], size=6000))
    b = pd.Series(rng.choice(["u", "v", "w"], size=6000))
    r = cramers_v(a, b)
    assert r["applicable"] and not r["near_deterministic_coupling"]
    assert r["cramers_v"] < 0.1


def test_id_sequence_integer_and_templated():
    assert id_sequence(pd.Series(range(1, 501)))["sequential_id_consistent"]
    templ = [f"AI{i:05d}" for i in range(1, 501)]
    r = id_sequence(pd.Series(templ))
    assert r["sequential_id_consistent"] and r["counter_contiguous"]
    assert r["template"] == "AI<counter>"
    # gapped / random identifiers -> not sequential
    rng = np.random.default_rng(42)
    assert not id_sequence(pd.Series(rng.integers(1, 10**6, size=500)))["sequential_id_consistent"]
    assert not id_sequence(pd.Series([f"ID{v:06d}" for v in rng.integers(0, 10**6, size=500)]))["sequential_id_consistent"]


def test_missingness_equal_class_signature():
    # 3 classes + blanked column: missing behaves as the 4th uniform class
    rng = np.random.default_rng(42)
    draw = rng.choice(["High", "Medium", "Low", "GONE"], size=10000)
    s = pd.Series(draw).replace({"GONE": np.nan})
    comp = pd.Series(rng.choice(list("pqrs"), size=10000))  # independent companion
    r = missingness_pattern(s, comp)
    assert r["applicable"] and r["missing_as_equal_class_consistent"]
    assert abs(r["missing_share"] - 0.25) < 0.02


def test_missingness_not_equal_class_when_share_wrong():
    rng = np.random.default_rng(42)
    draw = rng.choice(["A"] * 9 + ["GONE"], size=10000)   # 9 classes + missing
    s = pd.Series(draw).replace({"GONE": np.nan})
    r = missingness_pattern(s, None)
    assert r["applicable"] and not r["missing_as_equal_class_consistent"]


def test_committed_output_artifact_structure():
    p = ROOT / "datasets" / "synthetic_checks_output.json"
    assert p.exists(), "run: python datasets/synthetic_checks.py"
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["generated_by"] == "datasets/synthetic_checks.py"
    assert len(d["datasets"]) >= 10
    TIERS = {"declared_synthetic_source_readme", "strong_signatures",
             "moderate_signatures", "weak_partial_signatures", "no_signatures_found"}
    for entry in d["datasets"].values():
        assert entry["basis"] in TIERS
        assert entry["rows"] > 0 and entry["checks"], "every audited dataset must carry >=1 check"
        assert "signature_families_triggered" in entry
        assert entry["discriminating_signatures_count"] <= entry["signatures_consistent_count"]
    # the ONE declared-synthetic source must remain the India Skills dataset
    declared = [k for k, v in d["datasets"].items() if v["basis"] == "declared_synthetic_source_readme"]
    assert declared == ["India Skills Intelligence (12,000)"]
    # a dataset whose only flagged family is the non-discriminating id sequence
    # must report zero discriminating signatures (tier = no_signatures_found)
    sccs = d["datasets"]["Student Career Success (50,000)"]
    assert sccs["signature_families_triggered"] == ["ids"]
    assert sccs["discriminating_signatures_count"] == 0


def test_tier_rule_is_mechanical():
    """Tiers must be recomputable from the committed checks: only the
    discriminating families (uniformity + binary, i.e. the families that did
    not fire on the real-data control) count, and the cut points are fixed."""
    import csv as _csv
    import re as _re
    from synthetic_checks import (DISCRIMINATING_FAMILIES, DISCRIMINATING_FLAGS,
                                  STRONG_MIN_SHARE, MODERATE_MIN_SHARE, WEAK_MIN_SHARE,
                                  evidence_tier)
    d = json.loads((ROOT / "datasets" / "synthetic_checks_output.json").read_text(encoding="utf-8"))
    assert (STRONG_MIN_SHARE, MODERATE_MIN_SHARE, WEAK_MIN_SHARE) == (0.80, 0.50, 0.20)
    for key, e in d["datasets"].items():
        fired = applicable = 0
        for name, res in e["checks"].items():
            if name.split("::")[0] in DISCRIMINATING_FAMILIES and res.get("applicable"):
                applicable += 1
                fired += int(any(res.get(f) for f in DISCRIMINATING_FLAGS))
        assert (fired, applicable) == (e["discriminating_signatures_count"],
                                       e["discriminating_checks_applicable"]), key
        expected = ("declared_synthetic_source_readme" if e["basis"] == "declared_synthetic_source_readme"
                    else evidence_tier(fired, applicable))
        assert e["evidence_tier"] == expected, key
    # the one tier the mechanical rule changed on 2026-10-12: India Fresher's
    # share (2/5 = 0.40) clears the 0.20 floor, so it is weak/partial, not none
    assert d["datasets"]["India Fresher Market (5,000)"]["evidence_tier"] == "weak_partial_signatures"
    assert d["datasets"]["Career Change Prediction (38,444)"]["evidence_tier"] == "moderate_signatures"
    # ... and the CSV must carry the same computed tier, with counts
    TIER_PHRASE = {
        "declared_synthetic_source_readme": "declared synthetic",
        "strong_signatures": "strong generator signatures",
        "moderate_signatures": "moderate generator signatures",
        "weak_partial_signatures": "weak/partial generator signatures",
        "no_signatures_found": "provenance unverified, no generator signatures found",
    }
    rows = {r["dataset"]: r for r in _csv.DictReader(
        (ROOT / "datasets" / "REAL_VS_SYNTHETIC.csv").open(encoding="utf-8"))}
    for key in d["datasets"]:
        e, label = d["datasets"][key], rows[key]["evidence_tier"]
        assert label.startswith(TIER_PHRASE[e["evidence_tier"]]), (key, label)
        share_in_label = float(_re.search(r"share ([0-9.]+)\]", label).group(1))
        assert abs(share_in_label - e["discriminating_share"]) < 0.005, (key, label)
    # the corrected record: experience_level~remote_type must NOT be flagged as
    # near-deterministic (an earlier informal note claimed 1:1; checks say independent)
    ai = d["datasets"]["AI Trends 2020-2026"]["checks"]["coupling::experience_level~remote_type"]
    assert not ai["near_deterministic_coupling"] and ai["cramers_v"] < 0.1


def test_real_data_control_artifact():
    """The same checks/thresholds on 1.35M genuine postings must document the
    two false-positive families and the non-discriminating id family
    (datasets/synthetic_checks_control.py -> ..._control_linkedin.json)."""
    p = ROOT / "datasets" / "synthetic_checks_control_linkedin.json"
    assert p.exists(), "run: python datasets/synthetic_checks_control.py"
    c = json.loads(p.read_text(encoding="utf-8"))
    d = json.loads((ROOT / "datasets" / "synthetic_checks_output.json").read_text(encoding="utf-8"))
    assert c["generated_by"] == "datasets/synthetic_checks_control.py"
    assert c["rows"] > 1_300_000 and len(c["checks"]) >= 15
    # identical thresholds to the audited-file suite
    assert (c["alpha"], c["coupling_v_threshold"]) == (d["alpha"], d["coupling_v_threshold"])
    # on REAL data the coupling check fires on the scraper's own pipeline flags
    coup = c["checks"]["coupling::got_summary~got_ner"]
    assert coup["near_deterministic_coupling"] and coup["cramers_v"] > 0.95
    # ... and the missingness check fires on a 19-missing-of-1.35M column
    miss = c["checks"]["missingness::job_location|search_country"]
    assert miss["missing_as_equal_class_consistent"] and miss["missing_share"] < 1e-4
    # ... while uniformity and the id sequence fire on nothing
    assert not any(c["checks"][k]["uniform_draw_consistent"]
                   for k in c["checks"] if k.startswith("uniformity::"))
    assert not c["checks"]["ids::job_link"]["sequential_id_consistent"]
    # the artifact must name those families as documented false positives
    fams = {f["family"] for f in c["false_positive_families"]}
    assert fams == {"coupling", "missingness"}
    assert {f["family"] for f in c["non_discriminating_families"]} == {"id_sequence"}
