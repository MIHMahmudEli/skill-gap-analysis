"""Generator-signature checks for the datasets audited in
datasets/REAL_VS_SYNTHETIC.csv (author instruction 2026-10-12).

Purpose: turn the informal "generator signs" column into executable,
reproducible checks. These checks NEVER assert that a dataset is synthetic;
they report whether observable regularities are *consistent with* common
synthetic-generation patterns. Classification stays in REAL_VS_SYNTHETIC.csv,
which ranks each dataset on a four-step evidence tier (author ruling,
2026-10-12).  THE TIER IS COMPUTED, NOT CHOSEN: evidence_tier() below counts
the applicable checks in the DISCRIMINATING families and takes the share that
fired, with these cut points --

      strong / moderate   >= 0.80 of applicable discriminating checks fired
      moderate / weak     >= 0.50
      weak / none found   >= 0.20
      no generator signatures found                          below 0.20

The discriminating families are exactly those that did NOT fire on the
real-data control: uniformity and coin-flip binary.  Coupling and missingness
DO fire on 1,348,454 genuine postings (pipeline flags; a 19-of-1.35M
missingness share), and the sequential-ID family fires on nine of the ten
audited files while not firing on the real corpus, so none of those three
influences a tier.  They are still executed and recorded as evidence.

  * declared synthetic          — the source itself states the data are
                                  generated (only the India Skills dataset,
                                  per its bundled README).  This is the only
                                  dataset any file in this repository calls
                                  "synthetic"; it carries this label whatever
                                  its checks say.
  * strong / moderate / weak-partial / no generator signatures found
                               — the computed tier, above.

LIMITS OF THESE CHECKS (read before citing a flag):

  * The thresholds (ALPHA, COUPLING_V, BALANCE_RATIO_MAX, BINARY_BALANCE_EPS,
    the 0.01 missingness tolerance) are ANALYST-CHOSEN, not pre-registered.
    They were fixed before the tier labels were assigned, but no power
    analysis or false-discovery control was performed.
  * These checks are DESCRIPTIVE SCREENING. A flag is a reason to look
    harder, never evidence that a dataset is generated; non-rejection of
    uniformity is also compatible with design-based or quota sampling.
  * The real-data control (datasets/synthetic_checks_control_linkedin.json,
    1,348,454 genuine LinkedIn postings, same functions, same thresholds)
    shows two families give FALSE POSITIVES on real data: the coupling check
    fires on the scraper's own processing flags (got_summary ~ got_ner,
    V = 0.985) and the missingness check fires on a column with 19 missing
    values out of 1.35M (its share tolerance is absolute, so near zero both
    sides round to 0.0 and only the independence term decides).
  * The id-sequence family DOES NOT DISCRIMINATE. It fires on nine of the ten
    audited files, and it does not fire on the real LinkedIn corpus (whose
    job_link URLs end in opaque counters) while real systems routinely use
    sequential primary keys. It is recorded for completeness and is NOT
    counted towards a dataset's evidence tier.

Check families (each returns a structured result with a boolean flag and the
raw statistic; flags mean "consistent with the pattern", never "synthetic"):

  1. uniformity_chi2   — chi-square goodness-of-fit against a uniform
                         categorical distribution (low-cardinality columns
                         only). A non-rejection + near-1.0 max/min balance
                         ratio is the classic uniform-draw signature.
  2. binary_balance    — |p - 0.5| for 0/1 columns (coin-flip draws).
  3. cross_field       — near-deterministic coupling between two categorical
                         columns (Cramer's V >= coupling_threshold).  On real
                         data this fires for pipeline-produced column pairs
                         (see the control above), so it only discriminates
                         when the pair is not a processing artifact.
  4. id_sequence       — sequential / templated identifiers (1..N numeric,
                         zero-padded counters, prefix+counter templates).
  5. missingness       — "missing as one more equal class": for a column with
                         k non-missing classes, missing share ~= 1/(k+1)
                         (missing drawn like a class, then blanked) AND
                         missingness independent of an external companion
                         column (chi-square test of independence not rejected).

Usage:  python datasets/synthetic_checks.py
Output: datasets/synthetic_checks_output.json  (cited in the claim ledger)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "datasets" / "kaggle"
OUT = ROOT / "datasets" / "synthetic_checks_output.json"
ALPHA = 0.05
COUPLING_V = 0.95          # Cramer's V above which a categorical pair is "near-deterministic"
BALANCE_RATIO_MAX = 1.10   # max/min category-count ratio treated as "near-equal"
BINARY_BALANCE_EPS = 0.02

# ------------------------------------------------------------------ evidence-tier rule
# Families that DISCRIMINATE are exactly the families that did NOT fire on the
# real-data control (datasets/synthetic_checks_control_linkedin.json, 1,348,454
# genuine postings, same thresholds): uniformity and coin-flip binary.  The
# coupling and missingness families DO fire on that real corpus (scraper
# pipeline flags; a 19-of-1.35M missingness share), and the sequential-ID family
# is non-discriminating in both directions, so all three are EXCLUDED from tier
# assignment and are recorded only as evidence.
DISCRIMINATING_FAMILIES = ("uniformity", "binary")
DISCRIMINATING_FLAGS = ("uniform_draw_consistent", "coin_flip_consistent")
STRONG_MIN_SHARE = 0.80     # share of applicable discriminating checks fired
MODERATE_MIN_SHARE = 0.50
WEAK_MIN_SHARE = 0.20       # at/below this a dataset is "no generator signatures found"


def evidence_tier(fired: int, applicable: int) -> str:
    """Mechanical tier from the discriminating-check share (author ruling,
    2026-10-12).  cut points: >=0.80 strong; >=0.50 moderate; >=0.20
    weak/partial; below that, no generator signatures found.  Zero applicable
    discriminating checks means nothing could fire, hence 'not assessable',
    which is reported as no signatures found."""
    if applicable == 0:
        return "no_signatures_found"
    share = fired / applicable
    if share >= STRONG_MIN_SHARE:
        return "strong_signatures"
    if share >= MODERATE_MIN_SHARE:
        return "moderate_signatures"
    if share >= WEAK_MIN_SHARE:
        return "weak_partial_signatures"
    return "no_signatures_found"


# ------------------------------------------------------------------ checks
def uniformity_chi2(s: pd.Series, max_categories: int = 20) -> dict:
    vc = s.dropna().value_counts()
    n_cat = len(vc)
    if n_cat < 2 or n_cat > max_categories or (vc.min() == 0):
        return {"applicable": False, "n_categories": int(n_cat)}
    expected = np.full(n_cat, vc.sum() / n_cat)
    chi2, p = sps.chisquare(vc.values, f_exp=expected)
    ratio = float(vc.max() / vc.min())
    return {
        "applicable": True,
        "n_categories": n_cat,
        "chi2": round(float(chi2), 3),
        "df": n_cat - 1,
        "p_value": round(float(p), 4),
        "balance_ratio_max_min": round(ratio, 3),
        "uniform_draw_consistent": bool(p >= ALPHA and ratio <= BALANCE_RATIO_MAX),
    }


def binary_balance(s: pd.Series) -> dict:
    v = pd.to_numeric(s, errors="coerce").dropna()
    if v.empty or not set(v.unique()) <= {0, 1}:
        return {"applicable": False}
    p = float(v.mean())
    return {
        "applicable": True,
        "n": int(len(v)),
        "share_positive": round(p, 4),
        "coin_flip_consistent": bool(abs(p - 0.5) <= BINARY_BALANCE_EPS),
    }


def cramers_v(a: pd.Series, b: pd.Series) -> dict:
    ct = pd.crosstab(a, b)
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return {"applicable": False}
    chi2, p, dof, _ = sps.chi2_contingency(ct)
    n = ct.values.sum()
    v = float(np.sqrt(chi2 / (n * (min(ct.shape) - 1))))
    # degeneracy: share of rows and columns explained by their modal cell
    row_dom = float(ct.max(axis=1).sum() / n)
    col_dom = float(ct.max(axis=0).sum() / n)
    return {
        "applicable": True,
        "table_shape": list(ct.shape),
        "cramers_v": round(v, 4),
        "independence_p": round(float(p), 6),
        "row_modal_share": round(row_dom, 4),
        "col_modal_share": round(col_dom, 4),
        "near_deterministic_coupling": bool(v >= COUPLING_V),
    }


def id_sequence(s: pd.Series) -> dict:
    vals = s.dropna().astype(str)
    if vals.empty:
        return {"applicable": False}
    out: dict = {"applicable": True, "n": int(len(vals)), "n_unique": int(vals.nunique())}
    # pure integer sequence 1..N (any starting point, unit step)
    if vals.str.fullmatch(r"\d+").all():
        arr = vals.astype(np.int64).values
        out["integer_sequence"] = bool(np.array_equal(np.diff(np.sort(arr)), np.ones(len(arr) - 1, dtype=np.int64)))
    # templated prefix+counter: constant alpha prefix/suffix, zero-padded counter,
    # counters forming a contiguous consecutive block
    m = vals.str.extract(r"^(?P<pre>[A-Za-z_\-]*)(?P<num>\d+)(?P<post>[A-Za-z_\-]*)$")
    if m["num"].notna().all() and m["pre"].nunique() == 1 and m["post"].nunique() == 1:
        nums = m["num"].astype(np.int64).values
        widths = m["num"].str.len()
        out["template"] = f"{m['pre'].iloc[0]}<counter>{m['post'].iloc[0]}"
        out["zero_padded_uniform_width"] = bool(widths.nunique() == 1)
        out["counter_contiguous"] = bool(np.array_equal(np.diff(np.sort(nums)), np.ones(len(nums) - 1, dtype=np.int64)))
    out["sequential_id_consistent"] = bool(out.get("integer_sequence") or
                                          (out.get("counter_contiguous") and out.get("zero_padded_uniform_width")))
    return out


def missingness_pattern(s: pd.Series, companion: pd.Series | None = None) -> dict:
    miss = s.isna()
    if miss.mean() == 0 or miss.mean() == 1:
        return {"applicable": False}
    k = s.dropna().nunique()          # non-missing classes of s itself
    share = float(miss.mean())
    # would 'missing' look like the (k+1)-th class of a uniform draw
    # (a class sampled uniformly, then blanked)?
    expected_share = 1.0 / (k + 1)
    # is missingness independent of an external companion column?
    p_ind, chi2 = None, None
    if companion is not None:
        ct = pd.crosstab(companion, miss)
        if ct.shape[1] >= 2:
            chi2, p_ind, dof, _ = sps.chi2_contingency(ct)
    independent = True if p_ind is None else bool(p_ind >= ALPHA)
    return {
        "applicable": True,
        "missing_share": round(share, 4),
        "nonmissing_classes": int(k),
        "uniform_class_expected_share": round(expected_share, 4),
        "share_matches_equal_class": bool(abs(share - expected_share) <= 0.01),
        "independence_chi2": None if chi2 is None else round(float(chi2), 3),
        "independence_p": None if p_ind is None else round(float(p_ind), 4),
        "missing_independent_of_companion": independent,
        "missing_as_equal_class_consistent": bool(abs(share - expected_share) <= 0.01 and independent),
    }


# ------------------------------------------------------------------ per-dataset spec
def _p(*parts) -> Path:
    return K.joinpath(*parts)


SPECS = [
    dict(key="AI Trends 2020-2026", file=_p("ai-and-data-science-job-market-dataset-20202026", "AI Job Market Dataset.csv"),
         basis="strong_signatures",
         categorical=["job_title", "country", "company_industry", "remote_type", "experience_level", "job_posting_year"],
         binary=["skills_python", "skills_sql", "skills_ml", "skills_deep_learning", "skills_cloud"],
         couple=[("experience_level", "remote_type")],
         ids="job_id", miss=None),
    dict(key="AI Job Market & Salary Trends (15,000)", file=_p("global-ai-job-market-and-salary-trends-2025", "ai_job_dataset.csv"),
         basis="moderate_signatures",
         categorical=["company_name", "company_location", "experience_level", "employment_type", "company_size"],
         binary=[], couple=[], ids="job_id", miss=None),
    dict(key="India Skills Intelligence (12,000)", file=_p("india-professional-skills-intelligence-dataset", "india_professional_skills_intelligence.csv"),
         basis="declared_synthetic_source_readme",
         categorical=["seniority_level", "company_size", "work_mode", "employment_type"],
         binary=["uses_generative_ai_tools"], couple=[], ids="profile_id", miss=None),
    dict(key="College Student Placement (10,000)", file=_p("college-student-placement", "college_student_placement_dataset.csv"),
         basis="moderate_signatures",
         categorical=["Academic_Performance", "Communication_Skills", "Projects_Completed", "Internship_Experience"],
         binary=["Internship_Experience"], couple=[], ids="College_ID", miss=None),
    dict(key="Global Student Placement (10,000)", file=_p("global-student-placement-2025-dataset", "global_placement.csv"),
         basis="moderate_signatures",
         categorical=["country", "specialization", "industry", "college_tier"],
         binary=[], couple=[], ids=None, miss=None),
    dict(key="Student Career Success (50,000)", file=_p("student-career-success-prediction-dataset", "student_career_success_dataset.csv"),
         basis="no_signatures_found",
         categorical=["Gender", "Major", "Placement_Status", "Company_Tier", "Placement_Mode"],
         binary=["GitHub_Profile", "LinkedIn_Profile"], couple=[], ids="Student_ID", miss=None),
    dict(key="International Graduates (300,000)", file=_p("international-graduates-employment-dataset", "dataset.csv"),
         basis="weak_partial_signatures",
         categorical=["Gender", "Field_of_Study", "Employment_Status", "Country_of_Origin",
                      "Language_Proficiency", "Years_Since_Graduation"],
         binary=["Internship_Experience"], couple=[], ids=None, miss=None),
    dict(key="NGESS Graduate Employment (7,200)", file=_p("ngess-graduate-employment-dataset", "NGESS Graduate Employment Dataset.csv"),
         basis="no_signatures_found",
         categorical=["Survey_Year", "Gender", "Religion", "NYSC_Status", "Employment_Status", "Field_of_Study"],
         binary=["Internship_Completed", "Student_Loan"], couple=[], ids="Respondent_ID", miss=None),
    dict(key="Career Change Prediction (38,444)", file=_p("field-of-study-vs-occupation", "career_change_prediction_dataset.csv"),
         basis="moderate_signatures",
         categorical=["Field of Study", "Current Occupation", "Education Level", "Industry Growth Rate"],
         binary=["Career Change Interest", "Mentorship Available"], couple=[],
         ids=None, miss=("Family Influence", "Field of Study")),
    dict(key="India Fresher Market (5,000)", file=_p("indian-fresher-job-market-who-gets-hired-and-why", "fresher_hiring_india_dataset.csv"),
         basis="no_signatures_found",
         categorical=["backlogs", "degree", "age", "gender", "graduation_year"],
         binary=["prior_internship"], couple=[], ids="candidate_id", miss=None),
]


def run() -> dict:
    results = {"generated_by": "datasets/synthetic_checks.py",
               "alpha": ALPHA, "coupling_v_threshold": COUPLING_V,
               "balance_ratio_max": BALANCE_RATIO_MAX,
               "binary_balance_eps": BINARY_BALANCE_EPS,
               "thresholds_status": ("analyst-chosen, not pre-registered; the checks are "
                                     "descriptive screening, not a hypothesis test of "
                                     "synthetic origin"),
               "note": ("Flags mean 'consistent with a generator signature', never 'synthetic'. "
                        "Only the declared_synthetic_source_readme basis asserts generation; every "
                        "other tier is computed by evidence_tier() from the share of applicable "
                        "DISCRIMINATING checks fired (uniformity + binary only: the families that "
                        "did not fire on the real-data control), cut points >=0.80 strong, "
                        ">=0.50 moderate, >=0.20 weak/partial, else none found. Coupling, "
                        "missingness and id_sequence are executed and recorded but never "
                        "influence a tier; see "
                        "datasets/synthetic_checks_control_linkedin.json."),
               "datasets": {}}
    for spec in SPECS:
        df = pd.read_csv(spec["file"], low_memory=False)
        entry: dict = {"file": str(spec["file"].relative_to(ROOT)), "basis": spec["basis"], "rows": len(df),
                       "checks": {}}
        for c in spec["categorical"]:
            if c in df.columns:
                entry["checks"][f"uniformity::{c}"] = uniformity_chi2(df[c])
        for c in spec["binary"]:
            if c in df.columns:
                entry["checks"][f"binary::{c}"] = binary_balance(df[c])
        for a, b in spec["couple"]:
            if a in df.columns and b in df.columns:
                entry["checks"][f"coupling::{a}~{b}"] = cramers_v(df[a], df[b])
        if spec["ids"] and spec["ids"] in df.columns:
            entry["checks"][f"ids::{spec['ids']}"] = id_sequence(df[spec["ids"]])
        if spec["miss"] and spec["miss"][0] in df.columns and spec["miss"][1] in df.columns:
            entry["checks"][f"missingness::{spec['miss'][0]}|{spec['miss'][1]}"] = missingness_pattern(
                df[spec["miss"][0]], df[spec["miss"][1]])
        # summary count of triggered signatures (uniform-consistent categoricals etc.)
        trig = []
        disc_fired = disc_applicable = 0
        for name, res in entry["checks"].items():
            fam = name.split("::")[0]
            for flag in ("uniform_draw_consistent", "coin_flip_consistent",
                         "near_deterministic_coupling", "sequential_id_consistent",
                         "missing_as_equal_class_consistent"):
                if res.get(flag):
                    trig.append(fam)
            if fam in DISCRIMINATING_FAMILIES and res.get("applicable"):
                disc_applicable += 1
                if any(res.get(f) for f in DISCRIMINATING_FLAGS):
                    disc_fired += 1
        entry["signatures_consistent_count"] = len(trig)
        entry["discriminating_signatures_count"] = disc_fired
        entry["discriminating_checks_applicable"] = disc_applicable
        entry["discriminating_share"] = (round(disc_fired / disc_applicable, 3)
                                         if disc_applicable else 0.0)
        # mechanical tier (declared files keep their declared label regardless)
        entry["evidence_tier"] = (spec["basis"] if spec["basis"] == "declared_synthetic_source_readme"
                                  else evidence_tier(disc_fired, disc_applicable))
        entry["signature_families_triggered"] = sorted(set(trig))
        results["datasets"][spec["key"]] = entry
        print(f"{spec['key']:45s} signatures triggered: {len(trig):2d}  {sorted(set(trig))}")
    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"wrote {OUT}")
    return results


if __name__ == "__main__":
    run()
