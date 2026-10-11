"""Step 2: real-vs-synthetic provenance audit for every dataset that feeds an
experiment (plus the AI/India/placement benchmark families the author named).

For each dataset we record:
  * unit_type                 what a row physically is
  * generator_signs           quantitative evidence of synthetic generation
  * classification            real_scraped / synthetic / aggregate_unverified
  * feeds_experiment          which registered experiment reads it
  * paper_treats_as_real      whether main.tex currently implies real data

Generator-sign tests applied (each returns a flagged string when triggered):
  1. categorical balance: max/min share across a low-cardinality column (near-
     equal counts => uniform categorical draw).
  2. binary balance: |p - 0.5| for 0/1 columns (near-0.5 => coin flip).
  3. year balance: max/min count across observed years (near-equal => the
     "longitudinal" series is a balanced draw, not a time process).
  4. coupled-column identity: two categoricals mapping ~1:1 (impossible
     independence-breaking regularity in real data).
  5. sequential/synthetic ID: job_id or profile_id of the form AI00001/IN-PROF-.
  6. generator tell: 16 near-generic company_name values across 15,000 rows.

Writes datasets/REAL_VS_SYNTHETIC.csv. No download; no manuscript edit here.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "datasets" / "kaggle"
OUT = ROOT / "datasets" / "REAL_VS_SYNTHETIC.csv"


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
    unit_type="synthetic row (one generated AI/data job listing)",
    feeds_experiment="TRENDS01 (RQ1 trends; Fig. 6b)",
    dataset_card="no local card; manifest label 'Longitudinal AI/data science job postings'",
    generator_signs=(f"6 titles ~1,700 each (ratio {r_t:.2f}); 7 countries ~1,480 each (ratio {r_c:.2f}); "
                     f"7 years ~1,470 each (ratio {r_y:.2f}); binary skills ~coin-flip ({binary_balance(d,['skills_python','skills_sql','skills_ml','skills_deep_learning','skills_cloud'])}); "
                     f"experience_level<->remote_type map 1:1 ({coupled:.3f} of rows on the diagonal); "
                     "job_id = 1..10345; 9901 distinct salaries in a 10345-row file"),
    classification="SYNTHETIC",
    paper_treats_as_real="YES - Table I calls it 'Longitudinal AI/data science job postings'; abstract & Sec III-A cite 'multi-year AI job market series (2020-2026)'; Fig.6b 'AI skill demand trajectories'")

# ---------------------------------------------------------------- AI 15,000 (bundled)
p = K / "global-ai-job-market-and-salary-trends-2025" / "ai_job_dataset.csv"
d = pd.read_csv(p, low_memory=False)
n_cm, r_cm = bal(d.company_name); n_loc, r_loc = bal(d.company_location)
add(dataset="AI Job Market & Salary Trends (15,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic row (one generated AI job listing)",
    feeds_experiment="none executed (sibling file only)",
    dataset_card="no local card",
    generator_signs=(f"16 generic company_name values across 15,000 rows (ratio {r_cm:.2f}; e.g. 'TechCorp Inc','Smart Analytics'); "
                     f"20 countries ~750 each (ratio {r_loc:.2f}); experience_level/employment_type/company_size/remote_ratio all ~equal 4-way/3-way splits; "
                     "job_id = AI00001..; 95 of 15,000 deadlines land exactly 20 days after posting"),
    classification="SYNTHETIC",
    paper_treats_as_real="NO - not in Table I as postings (manifest discloses it as unused sibling)")

# ---------------------------------------------------------------- India Skills
p = K / "india-professional-skills-intelligence-dataset" / "india_professional_skills_intelligence.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="India Skills Intelligence (12,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic professional profile (no real person)",
    feeds_experiment="none executed (calibration reference only)",
    dataset_card=("PRESENT locally: 'This dataset contains 12,000 synthetic professional profiles... Every value in "
                  "this dataset is generated, not collected from any real person or any real platform'; calibrated to "
                  "India Skills Report 2026 (Wheebox/CII/AICTE/AIU) and NASSCOM"),
    generator_signs=("profile_id = IN-PROF-######; seniority/skills/company_size/work_mode near-uniform; "
                     "uses_generative_ai_tools = 88% Yes (calibrated to a headline figure); card states generation"),
    classification="SYNTHETIC (by explicit card)",
    paper_treats_as_real="PARTIAL - Table I already says 'Synthetic profiles calibrated on India Skills Report 2026' (good), but Sec III-A groups it under 'open datasets acquired from Kaggle' without marking it synthetic in prose")

# ---------------------------------------------------------------- placement benchmarks
p = K / "college-student-placement" / "college_student_placement_dataset.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="College Student Placement (10,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic student row",
    feeds_experiment="STAT01 (H6/H7); STAT02",
    dataset_card="no local card",
    generator_signs=("100 College_IDs x 100 students each (uniform cluster); Academic_Performance & Communication_Skills ~uniform 1-10; "
                     "Projects_Completed ~uniform 0-5; Placement 16.6% with a hard label boundary (STAT01 records ROC-AUC 0.9406)"),
    classification="SYNTHETIC",
    paper_treats_as_real="PARTIAL - limitation 1 calls Tier 2 'semi-deterministic decision boundaries' but they are presented as placement/graduate outcomes")

p = K / "global-student-placement-2025-dataset" / "global_placement.csv"
d = pd.read_csv(p, low_memory=False)
n_co, r_co = bal(d.country); n_sp, r_sp = bal(d.specialization); n_in, r_in = bal(d.industry)
add(dataset="Global Student Placement (10,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic student row",
    feeds_experiment="STAT02; PLAC01 (country rates)",
    dataset_card="no local card",
    generator_signs=(f"5 countries ~2,000 each (ratio {r_co:.2f}); 5 specializations ~2,000 each (ratio {r_sp:.2f}); "
                     f"6 industries ~1,670 each (ratio {r_in:.2f}); cgpa/communication/salary to 15 decimal places"),
    classification="SYNTHETIC",
    paper_treats_as_real="PARTIAL - PLAC01 reports 'placement rates by country (India 63.2% ... Germany 60.0%)' as if country observations")

p = K / "student-career-success-prediction-dataset" / "student_career_success_dataset.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="Student Career Success (50,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic student row",
    feeds_experiment="STAT02 (external cohort)",
    dataset_card="no local card",
    generator_signs=("Student_ID = ST######; 8 majors ~uneven but templated; Gender near-exact 50/50; "
                     "Placement_Status 78% with Company_Tier/Placement_Mode templated; Starting_Salary_USD = 0 for all 10,960 not-placed"),
    classification="SYNTHETIC",
    paper_treats_as_real="PARTIAL - used as an 'external validation cohort' in STAT02")

p = K / "international-graduates-employment-dataset" / "dataset.csv"
d = pd.read_csv(p, low_memory=False)
n_g, r_g = bal(d.Gender); n_e, r_e = bal(d.Employment_Status); n_f, r_f = bal(d.Field_of_Study)
add(dataset="International Graduates (300,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic alumni row",
    feeds_experiment="INTL01 (internship->employment)",
    dataset_card="no local card",
    generator_signs=(f"8 origin countries ~37,500 each (ratio {r_g:.2f}); Gender near-exact split 143,890/143,850/12,260; "
                     f"6 fields ~50,000 each (ratio {r_f:.2f}); 4 languages ~exactly 90,1xx/59,8xx; Years_Since_Graduation ~uniform 0-9"),
    classification="SYNTHETIC",
    paper_treats_as_real="PARTIAL - INTL01 reports internship->employment odds ratio (1.48x) as a graduate-outcome finding")

p = K / "ngess-graduate-employment-dataset" / "NGESS Graduate Employment Dataset.csv"
d = pd.read_csv(p, low_memory=False)
add(dataset="NGESS Graduate Employment (7,200)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic survey respondent",
    feeds_experiment="none executed",
    dataset_card="no local card",
    generator_signs=("6 survey years ~uneven but 2023 max; Religion ~exact 3,413/3,404 Islam/Christianity split; "
                     "Gender near-50/50; NYSC_Status Nigeria-specific templated categories"),
    classification="SYNTHETIC (plausible survey-like template)",
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
    paper_treats_as_real="YES - treated as real throughout (correct)")

add(dataset="HF Skill Gap Jobs+Skills (519,814 linked pair)", path="datasets/hf_skill_gap_jobs.csv + hf_skill_gap_skills.csv",
    rows=519814, unit_type="real scraped job posting (+linked skill rows)",
    feeds_experiment="ALIGN01-04, SENS01, VALID01, CURR01; ALIGN05 planned primary",
    dataset_card="HuggingFace skill-gap-analytics (CC-BY 4.0); enterprise postings w/ occupational metadata",
    generator_signs=("none detected: 266,917 distinct titles, long tail identical in shape to LinkedIn "
                     "(same top titles - it is a strict subset of the LinkedIn scrape, OVERLAP_AUDIT.csv)"),
    classification="REAL (web-scraped; subset of LinkedIn)",
    paper_treats_as_real="YES (correct)")

add(dataset="HF Job Skill Set academic reference (1,167)", path="datasets/hf_job_skill_set.csv", rows=1167,
    unit_type="real posting-derived skill list (academic reference profile)",
    feeds_experiment="ALIGN01-04, CURR01, SENS01 (covering set)",
    dataset_card="HuggingFace skill-gap-analytics (CC-BY 4.0)",
    generator_signs="no generation; a 1,167-posting subsample of the same real scrape, not a taxonomy",
    classification="REAL (posting-derived reference)",
    paper_treats_as_real="YES (correct)")

# ---------------------------------------------------------------- Tier 2 (remaining)
p = K / "field-of-study-vs-occupation" / "career_change_prediction_dataset.csv"
d = pd.read_csv(p, low_memory=False)
n_fs, r_fs = bal(d["Field of Study"]); n_oc, r_oc = bal(d["Current Occupation"])
add(dataset="Career Change Prediction (38,444)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic student/alumni row",
    feeds_experiment="none executed (Tier 2 inventory; counts toward headline only)",
    dataset_card="no local card",
    generator_signs=(f"10 fields of study ~3,850 each (ratio {r_fs:.2f}); 10 occupations ~3,890 each (ratio {r_oc:.2f}); "
                     "Gender near-exact split 19,299/19,145; 1-10 rating columns ~uniform (~3,850 per level); "
                     "Family Influence missingness itself uniform (nan 9,632 vs ~9,600 per class)"),
    classification="SYNTHETIC",
    paper_treats_as_real="OVERSTATED - Table I lists it as 'Field of study vs. occupation transition records' (Tier 2)")

p = (K / "indian-fresher-job-market-who-gets-hired-and-why" / "fresher_hiring_india_dataset.csv")
d = pd.read_csv(p, low_memory=False)
n_deg, r_deg = bal(d.degree); n_bk, r_bk = bal(d.backlogs)
add(dataset="India Fresher Market (5,000)", path=str(p.relative_to(ROOT)), rows=len(d),
    unit_type="synthetic candidate row (fabricated names)",
    feeds_experiment="none executed (Tier 2 inventory; counts toward headline only)",
    dataset_card="no local card",
    generator_signs=(f"backlogs ~uniform 0-3 (ratio {r_bk:.2f}); degree ~uniform 10 values (ratio {r_deg:.2f}); "
                     "age near-uniform 8 values; projects_count ~uniform 0-6; candidate_id = 1..5000; "
                     "4,315 distinct full_name values drawn from a name pool"),
    classification="SYNTHETIC",
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
    paper_treats_as_real="OVERSTATED - Tier 1 says '316K records ... direct observations of employer skill specifications' (reads as postings)")

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False)
print(f"wrote {OUT} rows={len(out)}")
print(out[["dataset", "classification", "feeds_experiment"]].to_string(index=False))
