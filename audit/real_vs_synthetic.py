"""Step 2: real-vs-synthetic provenance audit for every dataset that feeds an
experiment (plus the AI/India/placement benchmark families the author named).

For each dataset we record:
  * unit_type                 what a row physically is
  * generator_signs           quantitative evidence bearing on provenance
  * classification            REAL / DECLARED SYNTHETIC / UNVERIFIED PROVENANCE
                              / AGGREGATE UNVERIFIED
  * evidence_tier             four-step evidence ranking (author ruling
                              2026-10-12): declared synthetic > strong
                              signatures > moderate signatures > weak/partial
                              signatures > provenance unverified (no
                              generator signatures found)
  * feeds_experiment          which registered experiment reads it
  * paper_treats_as_real      whether main.tex currently implies real data

VOCABULARY RULE (author ruling 2026-10-12): only the India Skills file, whose
own bundled README states the values are generated, is called synthetic.  Every
other non-real file is UNVERIFIED PROVENANCE carrying an evidence_tier; the
word "synthetic" must not be asserted about it in this repository's papers,
tables or READMEs.

Generator-sign tests applied (each returns a flagged string when triggered):
  1. categorical balance: max/min share across a low-cardinality column (near-
     equal counts => uniform categorical draw).
  2. binary balance: |p - 0.5| for 0/1 columns (near-0.5 => coin flip).
  3. year balance: max/min count across observed years (near-equal => the
     "longitudinal" series is a balanced draw, not a time process).
  4. coupled-column identity: two categoricals mapping ~1:1 (checked; note the
     AI-trends experience_level<->remote_type pair is INDEPENDENT, V=0.015 --
     an earlier informal note claiming a 1:1 map was wrong, corrected 2026-10-12).
  5. sequential/synthetic ID: job_id or profile_id of the form AI00001/IN-PROF-.
  6. generator tell: 16 near-generic company_name values across 15,000 rows.

Columns:
  classification      REAL / DECLARED SYNTHETIC / UNVERIFIED PROVENANCE /
                      AGGREGATE UNVERIFIED (author ruling 2026-10-12: the
                      word "synthetic" is asserted for the declared file only)
  evidence_tier       computed, not hand-assigned: read from
                      datasets/synthetic_checks_output.json, where
                      evidence_tier() applies fixed cut points to the share of
                      applicable DISCRIMINATING checks that fired (uniformity +
                      coin-flip binary -- the families that did not fire on the
                      1.35M-posting real-data control; coupling, missingness
                      and the sequential-ID family are excluded).  Cut points:
                      >=0.80 strong, >=0.50 moderate, >=0.20 weak/partial,
                      below that no generator signatures found.  The row also
                      carries the fired/applicable counts and share.
  synthetic_basis     declared by source | signature-tier evidence only (not
                      asserted synthetic) | n/a
  signature_checks    datasets/synthetic_checks_output.json for rows whose
                      signs are backed by the executable checker suite.

Writes datasets/REAL_VS_SYNTHETIC.csv. No download; no manuscript edit here.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "datasets" / "kaggle"
OUT = ROOT / "datasets" / "REAL_VS_SYNTHETIC.csv"

# ---------------------------------------------------------------- computed tier
# The evidence tier is NOT hand-assigned: it is read from the executable
# checker suite, where evidence_tier() applies fixed cut points to the share of
# applicable DISCRIMINATING checks that fired (uniformity + coin-flip binary:
# the only families that did not also fire on the real-data control,
# datasets/synthetic_checks_control_linkedin.json).  Cut points, in
# datasets/synthetic_checks.py: >=0.80 strong, >=0.50 moderate, >=0.20
# weak/partial, below that no generator signatures found.  Coupling,
# missingness and the sequential-ID family never influence a tier.
_CHECKS = json.loads((ROOT / "datasets" / "synthetic_checks_output.json").read_text(encoding="utf-8"))
TIER_LABEL = {
    "declared_synthetic_source_readme": "declared synthetic (source states it)",
    "strong_signatures": "strong generator signatures",
    "moderate_signatures": "moderate generator signatures",
    "weak_partial_signatures": "weak/partial generator signatures",
    "no_signatures_found": "provenance unverified, no generator signatures found",
}


def tier(dataset_key: str) -> str:
    """Display label of the tier computed by datasets/synthetic_checks.py.

    Rows that are not in the generator-signature audit at all (the real
    scraped corpora and the aggregate file) carry no tier."""
    e = _CHECKS["datasets"].get(dataset_key)
    if e is None:
        return "n/a (not audited: real or aggregate rows)"
    return "%s [discriminating checks %d/%d, share %.2f]" % (
        TIER_LABEL[e["evidence_tier"]], e["discriminating_signatures_count"],
        e["discriminating_checks_applicable"], e["discriminating_share"])



def bal(vals: pd.Series) -> tuple[int, float]:
    vc = vals.value_counts(dropna=True)
    return len(vc), (vc.max() / vc.min()) if len(vc) > 1 and vc.min() > 0 else float("nan")


def binary_balance(df: pd.DataFrame, cols: list[str]) -> str:
    out = []
    for c in cols:
        p = df[c].astype(float).mean()
        out.append(f"{c}={p:.2f}")
    return ", ".join(out)


rows: list[dict] = []
add = lambda **kw: rows.append(kw)

# ---------------------------------------------------------------- TRENDS01 (AI 2020-2026)
p = K / "ai-and-data-science-job-market-dataset-20202026" / "AI Job Market Dataset.csv"
d = pd.read_csv(p, low_memory=False)
n_t, r_t = bal(d.job_title); n_c, r_c = bal(d.country); n_y, r_y = bal(d.job_posting_year)
coupled = (pd.crosstab(d.experience_level, d.remote_type).max(axis=1).sum() / len(d))
add(dataset="AI Trends 2020-2026", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="benchmark row (one AI/data job listing)",
    feeds_experiment="none executed; TRENDS01 moved to the supplement provenance table 2026-10-12",
    dataset_card="no local card; manifest label 'Longitudinal AI/data science job postings'",
    generator_signs=(f"6 titles ~1,700 each (ratio {r_t:.2f}); 7 countries ~1,480 each (ratio {r_c:.2f}); "
                     f"7 years ~1,470 each (ratio {r_y:.2f}); binary skills ~coin-flip ({binary_balance(d,['skills_python','skills_sql','skills_ml','skills_deep_learning','skills_cloud'])}); "
                     f"job_id = 1..10345 (sequential); 9901 distinct salaries in a 10345-row file; "
                     f"experience_level and remote_type are INDEPENDENT (crosstab modal share {coupled:.2f}; "
                     "executable chi2/Cramer's V check = 0.015 -- an earlier informal note claiming a "
                     "1:1 map was wrong, corrected 2026-10-12)"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("AI Trends 2020-2026"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="NO - removed from the manuscript 2026-10-12 (RQ1 trends, Fig. 6b); retained only as a non-inferential row in the supplement provenance table")

# ---------------------------------------------------------------- AI 15,000 (bundled)
p = K / "global-ai-job-market-and-salary-trends-2025" / "ai_job_dataset.csv"
d = pd.read_csv(p, low_memory=False)
n_cm, r_cm = bal(d.company_name); n_loc, r_loc = bal(d.company_location)
add(dataset="AI Job Market & Salary Trends (15,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="benchmark row (one AI job listing)",
    feeds_experiment="none executed (sibling file only)",
    dataset_card="no local card",
    generator_signs=(f"16 generic company_name values across 15,000 rows (ratio {r_cm:.2f}; e.g. 'TechCorp Inc','Smart Analytics'); "
                     f"20 countries ~750 each (ratio {r_loc:.2f}); experience_level/employment_type/company_size uniform-consistent "
                     "(chi2 p=0.90/0.63/0.99); job_id = sequential AI<counter>; 95 of 15,000 deadlines land exactly 20 days after posting"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("AI Job Market & Salary Trends (15,000)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="NO - not in Table I as postings (manifest discloses it as unused sibling)")

# ---------------------------------------------------------------- India Skills
p = K / "india-professional-skills-intelligence-dataset" / "india_professional_skills_intelligence.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="India Skills Intelligence (12,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="declared-synthetic professional profile (source states no real person)",
    feeds_experiment="none executed (calibration reference only)",
    dataset_card=("PRESENT locally: 'This dataset contains 12,000 synthetic professional profiles... Every value in "
                  "this dataset is generated, not collected from any real person or any real platform'; calibrated to "
                  "India Skills Report 2026 (Wheebox/CII/AICTE/AIU) and NASSCOM"),
    generator_signs=("DECLARED by bundled README (see dataset_card); corroborating checks: profile_id = "
                     "sequential IN-PROF-###### (contiguous 12,000); uses_generative_ai_tools = 88% Yes "
                     "(calibrated to a headline figure); categorical columns NOT uniform-consistent "
                     "(calibrated distributions, chi2 p=0.00), consistent with a calibrated rather than flat generator"),
    classification="DECLARED SYNTHETIC",
    evidence_tier=tier("India Skills Intelligence (12,000)"),
    synthetic_basis="declared by source",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="PARTIAL - Table I already says 'Synthetic profiles calibrated on India Skills Report 2026' (good), but Sec III-A groups it under 'open datasets acquired from Kaggle' without marking it synthetic in prose")

# ---------------------------------------------------------------- placement benchmarks
p = K / "college-student-placement" / "college_student_placement_dataset.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="College Student Placement (10,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="student row (one candidate record)",
    feeds_experiment="STAT01 (H6/H7); STAT02",
    dataset_card="no local card",
    generator_signs=("36 College_IDs with 75-133 students each (uneven cluster, an earlier informal note claiming "
                     "'100 IDs x 100 students' was wrong, corrected 2026-10-12); Academic_Performance & "
                     "Projects_Completed uniform-consistent (chi2 p=0.77/0.48); Communication_Skills borderline "
                     "(p=0.044); Placement 16.6% with a hard label boundary (STAT01 records ROC-AUC 0.9406)"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("College Student Placement (10,000)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="PARTIAL - limitation 1 calls Tier 2 'semi-deterministic decision boundaries' but they are presented as placement/graduate outcomes")

p = K / "global-student-placement-2025-dataset" / "global_placement.csv"
d = pd.read_csv(p, low_memory=False)
n_co, r_co = bal(d.country); n_sp, r_sp = bal(d.specialization); n_in, r_in = bal(d.industry)
add(dataset="Global Student Placement (10,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="student row (one candidate record)",
    feeds_experiment="STAT02; PLAC01 (country rates)",
    dataset_card="no local card",
    generator_signs=(f"5 countries ~2,000 each (ratio {r_co:.2f}); 5 specializations ~2,000 each (ratio {r_sp:.2f}); "
                     f"6 industries ~1,670 each (ratio {r_in:.2f}); cgpa/communication/salary to 15 decimal places"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("Global Student Placement (10,000)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="PARTIAL - PLAC01 reports 'placement rates by country (India 63.2% ... Germany 60.0%)' as if country observations")

p = K / "student-career-success-prediction-dataset" / "student_career_success_dataset.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="Student Career Success (50,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="student row (one candidate record)",
    feeds_experiment="STAT02 (external cohort)",
    dataset_card="no local card",
    generator_signs=("Student_ID = ST###### (sequential zero-padded); Gender M/F near-equal 24,533/24,465 "
                     "(Other 1,002); Major non-uniform (CS 12,407 down to EE 2,548); Company_Tier heavily "
                     "skewed (max/min 271); Starting_Salary_USD = 0 for all 10,960 not-placed (deterministic rule); "
                      "checker verdict: all 5 categorical columns REJECT uniformity, no coupling, no "
                      "missingness flag -- only the non-discriminating ID-sequence family fires, hence the tier"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("Student Career Success (50,000)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="PARTIAL - used as an 'external validation cohort' in STAT02")

p = K / "international-graduates-employment-dataset" / "dataset.csv"
d = pd.read_csv(p, low_memory=False)
n_g, r_g = bal(d.Gender); n_e, r_e = bal(d.Employment_Status); n_f, r_f = bal(d.Field_of_Study)
add(dataset="International Graduates (300,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="alumni row (one graduate record)",
    feeds_experiment="INTL01 (internship->employment)",
    dataset_card="no local card",
    generator_signs=(f"8 origin countries ~37,500 each (uniform-consistent, chi2 p=0.53, ratio {d['Country_of_Origin'].value_counts().max()/d['Country_of_Origin'].value_counts().min():.2f}); "
                     "Gender 143,890/143,850/12,260 (max/min 11.7); "
                     f"6 fields ~50,000 each (uniform-consistent, ratio {r_f:.2f}); 4 languages ~exactly 90,1xx/59,8xx; "
                     "Years_Since_Graduation near-uniform but rejected (p=0.014)"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("International Graduates (300,000)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="PARTIAL - INTL01 reports internship->employment odds ratio (1.48x) as a graduate-outcome finding")

p = K / "ngess-graduate-employment-dataset" / "NGESS Graduate Employment Dataset.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="NGESS Graduate Employment (7,200)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="survey respondent row",
    feeds_experiment="none executed",
    dataset_card="no local card",
    generator_signs=("sequential templated Respondent_ID NGR00001..NGR07200 (contiguous); survey-like schema "
                     "with Nigeria-specific templated categories (NYSC_Status, Religion); uniformity "
                     "signatures NOT detected (Gender 3,893/3,232/75, Religion 3,413/3,404/297 and "
                     "Survey_Year uneven all reject uniformity) -- no discriminating signature: the only flagged family "
                      "is the non-discriminating ID-sequence, hence the 'no generator signatures found' tier"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("NGESS Graduate Employment (7,200)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="NO in results (not run) but listed in Table I among placement benchmarks")

# ---------------------------------------------------------------- posting family (real)
p = ROOT / "datasets" / "kaggle" / "1-3m-linkedin-jobs-and-skills-2024" / "linkedin_job_postings.csv"
d = pd.read_csv(p, usecols=["job_title"], dtype=str)
add(dataset="LinkedIn Jobs & Skills (1,348,454)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="real scraped job posting",
    feeds_experiment="GEO01 (geography); superset of the whole HF pair",
    dataset_card="Kaggle asaniczka/1-3m-linkedin-jobs-and-skills-2024 (ODbL); 2024 scrape",
    generator_signs=("none detected: 584,544 distinct titles with a realistic long tail (top title 'LEAD SALES ASSOCIATE-FT' 0.54%); "
                     "messy casing, typos, employer-specific strings - consistent with organic scrape"),
    classification="REAL (web-scraped)",
    evidence_tier=tier("LinkedIn Jobs & Skills (1,348,454)"),
    synthetic_basis="n/a",
    signature_checks="",
    paper_treats_as_real="YES - treated as real throughout (correct)")

add(dataset="HF Skill Gap Jobs+Skills (519,814 linked pair)", path="datasets/hf_skill_gap_jobs.csv + hf_skill_gap_skills.csv",
    rows=519814, unit_type="real scraped job posting (+linked skill rows)",
    feeds_experiment="ALIGN01-04, SENS01, VALID01, CURR01; ALIGN05 planned primary",
    dataset_card="HuggingFace skill-gap-analytics (CC-BY 4.0); enterprise postings w/ occupational metadata",
    generator_signs=("none detected: 266,917 distinct titles, long tail identical in shape to LinkedIn "
                     "(same top titles - it is a strict subset of the LinkedIn scrape, OVERLAP_AUDIT.csv)"),
    classification="REAL (web-scraped; subset of LinkedIn)",
    evidence_tier=tier("HF Skill Gap Jobs+Skills (519,814 linked pair)"),
    synthetic_basis="n/a",
    signature_checks="",
    paper_treats_as_real="YES (correct)")

add(dataset="HF Job Skill Set academic reference (1,167)", path="datasets/hf_job_skill_set.csv", rows=1167,
    unit_type="real posting-derived skill list (academic reference profile)",
    feeds_experiment="ALIGN01-04, CURR01, SENS01 (covering set)",
    dataset_card="HuggingFace skill-gap-analytics (CC-BY 4.0)",
    generator_signs="no generation; a 1,167-posting subsample of the same real scrape, not a taxonomy",
    classification="REAL (posting-derived reference)",
    evidence_tier=tier("HF Job Skill Set academic reference (1,167)"),
    synthetic_basis="n/a",
    signature_checks="",
    paper_treats_as_real="YES (correct)")

# ---------------------------------------------------------------- Tier 2 (remaining)
p = K / "field-of-study-vs-occupation" / "career_change_prediction_dataset.csv"
d = pd.read_csv(p, low_memory=False)
n_fs, r_fs = bal(d["Field of Study"]); n_oc, r_oc = bal(d["Current Occupation"])
add(dataset="Career Change Prediction (38,444)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="student/alumni row",
    feeds_experiment="none executed (Tier 2 inventory; counts toward headline only)",
    dataset_card="no local card",
    generator_signs=(f"10 fields of study ~3,850 each (uniform-consistent, ratio {r_fs:.2f}, chi2 p=0.051); "
                     f"10 occupations ~3,890 each (uniform-consistent, ratio {r_oc:.2f}); "
                     "Gender near-exact split 19,299/19,145; Education Level uniform-consistent; "
                     "deliberate class weights (Career Change Interest 20.0%, Mentorship 30.0%, not coin flips); "
                     "Family Influence missingness = 0.2505 vs 1/(3+1)=0.25 expected, independent of Field of Study "
                     "(p=0.455) -- missing drawn as one more uniform class, then blanked"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("Career Change Prediction (38,444)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="OVERSTATED - Table I lists it as 'Field of study vs. occupation transition records' (Tier 2)")

p = (K / "indian-fresher-job-market-who-gets-hired-and-why" / "fresher_hiring_india_dataset.csv")
d = pd.read_csv(p, low_memory=False)
n_deg, r_deg = bal(d.degree); n_bk, r_bk = bal(d.backlogs)
add(dataset="India Fresher Market (5,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="candidate row (name-pool generated identities)",
    feeds_experiment="none executed (Tier 2 inventory; counts toward headline only)",
    dataset_card="no local card",
    generator_signs=(f"backlogs ~uniform 0-3 (uniform-consistent, ratio {r_bk:.2f}, chi2 p=0.996); "
                     f"graduation_year uniform-consistent (p=0.973); degree/age NOT uniform-consistent "
                     f"(ratios {r_deg:.2f}/1.16); candidate_id = sequential 1..5000; "
                     "4,315 distinct full_name values drawn from a name pool (fabricated identities); "
                      "checker verdict: the discriminating columns (degree, age, gender) reject uniformity and "
                      "there is no coupling or missingness flag -- only two narrow columns and the "
                      "non-discriminating ID-sequence flag, hence the 'no generator signatures found' tier"),
    classification="UNVERIFIED PROVENANCE",
    evidence_tier=tier("India Fresher Market (5,000)"),
    synthetic_basis="signature-tier evidence only (not asserted synthetic)",
    signature_checks="datasets/synthetic_checks_output.json",
    paper_treats_as_real="OVERSTATED - Table I lists it as 'Entry-level engineering recruitment outcomes' (Tier 2)")

# ---------------------------------------------------------------- aggregate / unverified
p = K / "usa-job-market-skills-and-title-analysis" / "usa_job_posting_dataset.csv"
d = pd.read_csv(p, dtype=str)
add(dataset="USA Job Market Skills (316,279)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="AGGREGATE row = (title x skill keyword x count); 316,279 rows over only 6,328 distinct titles",
    feeds_experiment="none executed (Tier 1 inventory; counts toward headline only)",
    dataset_card="Kaggle batuhanklac/usa-job-market-skills-and-title-analysis (CC0); scrape source unstated",
    generator_signs=("not individual postings: aggregate triples; source scrape unverifiable; "
                     "all 6,328 titles also occur in the LinkedIn scrape (title-string overlap only)"),
    classification="AGGREGATE / UNVERIFIED provenance",
    evidence_tier=tier("USA Job Market Skills (316,279)"),
    synthetic_basis="n/a (provenance unverified, not classified synthetic)",
    signature_checks="",
    paper_treats_as_real="OVERSTATED - Tier 1 says '316K records ... direct observations of employer skill specifications' (reads as postings)")

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False)
print(f"wrote {OUT} rows={len(out)}")
print(out[["dataset", "classification", "synthetic_basis", "feeds_experiment"]].to_string(index=False))
