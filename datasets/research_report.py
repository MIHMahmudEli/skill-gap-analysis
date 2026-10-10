import pandas as pd
import numpy as np
import os
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import (
    load_hf_skill_gap_skills, load_hf_skill_gap_jobs, load_hf_job_skill_set,
    load_college_placement, load_ngess, load_global_placement,
    load_ai_jobs, load_india_skills, load_student_career,
    load_international_graduates, load_india_fresher,
    load_ai_market_trends, load_career_change, load_linkedin_skills,
    load_usa_jobs
)
from skill_extractor import get_market_skills, get_academic_skills, compute_alignment_metrics

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_report():
    report = []
    report.append("=" * 80)
    report.append("RESEARCH SUMMARY REPORT")
    report.append("Gap Between Academic Knowledge and Job Market Skills")
    report.append("=" * 80)
    report.append("NOTE: Legacy exploratory summary. Authoritative, GPU-verified")
    report.append("results are in results/<EXP_ID>/ and reports/EXPERIMENT_REPORT.md;")
    report.append("the manuscript (paper/main.pdf) uses only VERIFIED outputs.")

    # Dataset Overview
    report.append("\n\n1. DATASET OVERVIEW")
    report.append("-" * 40)

    datasets_info = [
        ("LinkedIn Job Skills (1.3M)", load_linkedin_skills, "skill profiles"),
        ("HuggingFace Skill Gap Skills", load_hf_skill_gap_skills, "job skill requirements"),
        ("HuggingFace Skill Gap Jobs", load_hf_skill_gap_jobs, "job postings"),
        ("HF Job Skill Set", load_hf_job_skill_set, "job categories"),
        ("College Student Placement", load_college_placement, "student records"),
        ("NGESS Graduate Employment", load_ngess, "graduate records"),
        ("Global Student Placement", load_global_placement, "student records"),
        ("AI Job Market", load_ai_jobs, "job records"),
        ("India Professional Skills", load_india_skills, "professional profiles"),
        ("Student Career Success", load_student_career, "student records"),
        ("USA Job Market Skills", load_usa_jobs, "job-skill pairs"),
        ("International Graduates", load_international_graduates, "graduate records"),
        ("India Fresher Job Market", load_india_fresher, "candidate records"),
        ("AI Market Trends 2020-2026", load_ai_market_trends, "job records"),
        ("Career Change Dataset", load_career_change, "professional records"),
    ]

    total_rows = 0
    for name, loader, desc in datasets_info:
        try:
            df = loader()
            rows = df.shape[0]
            total_rows += rows
            report.append(f"  {name}: {rows:,} {desc}")
        except Exception as e:
            report.append(f"  {name}: ERROR - {str(e)[:50]}")

    report.append(f"\n  TOTAL DATASETS: {len(datasets_info)}")
    report.append(f"  TOTAL RECORDS: {total_rows:,}")

    # Skill Gap Analysis
    report.append("\n\n2. SKILL GAP ANALYSIS")
    report.append("-" * 40)

    market = get_market_skills()
    academic = get_academic_skills()
    metrics = compute_alignment_metrics(market, academic)

    report.append(f"\n  Market Skills Analyzed: {metrics['market_skills']}")
    report.append(f"  Academic Skills Analyzed: {metrics['academic_skills']}")
    report.append(f"  Skills Covered: {metrics['covered']}")
    report.append(f"  Skills Missing: {metrics['missing']}")
    report.append(f"  Coverage Rate: {metrics['coverage_rate']:.1%}")
    report.append(f"  GAP INDEX: {metrics['gap_index']:.1%}")

    report.append(f"\n  Top 10 Market Skills:")
    for _, row in market.head(10).iterrows():
        report.append(f"    {row['skill']}: {row['job_postings']:,} postings")

    report.append(f"\n  Top 10 Academic Skills:")
    for _, row in academic.head(10).iterrows():
        report.append(f"    {row['skill']}: {row['frequency']} occurrences")

    report.append(f"\n  Skills Missing from Academic Curriculum:")
    for skill in metrics['missing_skills'][:15]:
        report.append(f"    - {skill}")

    # Statistical Findings
    report.append("\n\n3. KEY STATISTICAL FINDINGS")
    report.append("-" * 40)

    # College Placement
    df_college = load_college_placement()
    df_college['Placement_Binary'] = (df_college['Placement'] == 'Yes').astype(int)
    placed = df_college[df_college['Placement'] == 'Yes']
    not_placed = df_college[df_college['Placement'] == 'No']

    report.append("\n  3.1 College Student Placement (N=10,000)")
    report.append(f"    Placement Rate: {len(placed)/len(df_college)*100:.1f}%")
    report.append(f"    CGPA (Placed): {placed['CGPA'].mean():.2f} +/- {placed['CGPA'].std():.2f}")
    report.append(f"    CGPA (Not Placed): {not_placed['CGPA'].mean():.2f} +/- {not_placed['CGPA'].std():.2f}")
    report.append(f"    Communication (Placed): {placed['Communication_Skills'].mean():.2f}")
    report.append(f"    Communication (Not Placed): {not_placed['Communication_Skills'].mean():.2f}")

    # NGESS
    df_ngess = load_ngess()
    report.append("\n  3.2 NGESS Graduate Employment (N=7,200)")
    employed = ~df_ngess['Employment_Status'].isin(['Unemployed', 'Not Applicable'])
    report.append(f"    Employment Rate: {employed.mean()*100:.1f}%")
    report.append(f"    Avg Job Satisfaction: {df_ngess['Job_Satisfaction'].mean():.2f}/10")

    # Global Placement
    df_global = load_global_placement()
    placed_g = df_global[df_global['placement_status'] == 'Placed']
    report.append("\n  3.3 Global Student Placement (N=10,000)")
    report.append(f"    Placement Rate: {len(placed_g)/len(df_global)*100:.1f}%")
    report.append(f"    Avg Salary (Placed): ${df_global.loc[df_global['placement_status']=='Placed', 'salary'].mean():,.0f}")

    # Student Career
    df_career = load_student_career()
    report.append("\n  3.4 Student Career Success (N=50,000)")
    placed_c = df_career[df_career['Placement_Status'] == 'Placed']
    report.append(f"    Placement Rate: {len(placed_c)/len(df_career)*100:.1f}%")
    report.append(f"    Avg Starting Salary: ${placed_c['Starting_Salary_USD'].mean():,.0f}")

    # International Graduates
    df_intl = load_international_graduates()
    report.append("\n  3.3 International Graduates (N=300,000)")
    employed_intl = df_intl[df_intl['Employment_Status'] == 'Employed']
    report.append(f"    Employment Rate: {len(employed_intl)/len(df_intl)*100:.1f}%")

    # AI Market Trends
    df_ai = load_ai_market_trends()
    report.append("\n  3.6 AI Market Trends (N=10,345)")
    report.append(f"    Avg Salary: ${df_ai['salary'].mean():,.0f}")
    report.append(f"    Salary Range: ${df_ai['salary'].min():,.0f} - ${df_ai['salary'].max():,.0f}")

    # Career Change
    df_change = load_career_change()
    report.append("\n  3.7 Career Change & Skills Gap (N=38,444)")
    report.append(f"    Avg Skills Gap Score: {df_change['Skills Gap'].mean():.2f}/10")
    report.append(f"    Skills Gap Std Dev: {df_change['Skills Gap'].std():.2f}")

    # Research Questions
    report.append("\n\n4. RESEARCH QUESTIONS ADDRESSED")
    report.append("-" * 40)

    report.append("""
  RQ1: What are the most in-demand skills in the current job market?
    - Exact tokens: communication (148,765 postings), customer service (111,342),
      teamwork (91,559), communication skills (78,182), leadership (74,517)
    - Technical: Python 47.5-52.2%, SQL 48.2-51.9%, ML 48.8-53.5% (2020-2026)

  RQ2: To what extent do academic curricula align with industry requirements?
    - Lexical coverage 48% (SGI 52%, 95% CI [42, 63])
    - Semantic coverage 68% at tau=0.5 (SGI 32%, 95% CI [23, 41])

  RQ3: What is the magnitude and nature of the skill gap?
    - Largest posting-level deficits: Cloud & Infrastructure 2.45 pp (Critical),
      Programming 1.69 pp, Data Science 1.20 pp; Soft Skills fully covered
    - Semantic alignment reduces deficits by up to 74% per category

  RQ4: Which factors best predict graduate employability?
    - Communication OR=6.55, CGPA OR=6.28, IQ OR=5.16, Projects OR=3.20
      (statsmodels MLE, standardized; all p<0.001)
    - CV accuracy 90.11%, ROC-AUC 0.9406; tree ensembles reach 99.99% because
      labels follow a deterministic k-of-n rule (99.92% agreement)

  RQ5: How does the skill gap vary across regions/industries?
    - LinkedIn postings: USA 85.2%, UK 8.4%, Canada 4.2%, Australia 2.2%
    - Internship effect: +15.34 pp employment (N=300,000)

  See reports/EXPERIMENT_REPORT.md and results/registry.json for provenance.
  """)

    # Recommendations
    report.append("\n5. RECOMMENDATIONS")
    report.append("-" * 40)

    report.append("""
  For Higher Education Institutions:
    1. Integrate emerging technologies (AI, Cloud, Data Science) into curricula
    2. Strengthen industry-academia collaboration through internships and projects
    3. Develop soft skills training programs (Communication, Leadership)
    4. Implement continuous curriculum review processes
    5. Create industry advisory boards for curriculum guidance

  For Industry:
    1. Provide structured internship and mentorship programs
    2. Share real-time skill requirements with educational institutions
    3. Invest in employee upskilling and reskilling programs
    4. Participate in curriculum development and review
    5. Offer apprenticeship programs for emerging technologies

  For Policymakers:
    1. Develop national skill gap monitoring frameworks
    2. Fund industry-academia collaboration initiatives
    3. Create incentives for curriculum modernization
    4. Support lifelong learning and reskilling programs
    5. Establish skill certification standards

  For Students:
    1. Pursue continuous learning beyond formal education
    2. Seek internships and practical experience
    3. Develop both technical and soft skills
    4. Build professional networks and portfolios
    5. Stay updated with industry trends and emerging technologies
    """)

    # Methodology
    report.append("\n6. METHODOLOGY SUMMARY")
    report.append("-" * 40)

    report.append("""
  Data Sources:
    - 15 datasets from Kaggle and HuggingFace
    - Total: 3,176,266 records across multiple domains
    - Time period: 2020-2026

  Analytical Methods:
    - NLP-based skill extraction (TF-IDF, BERT embeddings)
    - Semantic alignment analysis (Cosine similarity)
    - Statistical testing (t-tests, ANOVA, Chi-square)
    - Machine Learning (Logistic Regression, Random Forest)
    - Effect size calculation (Cohen's d, Cramer's V)

  Tools & Libraries:
    - Python 3.14
    - pandas, numpy, scipy, scikit-learn
    - sentence-transformers (BERT)
    - matplotlib (visualization)
    """)

    # Output Files
    report.append("\n7. OUTPUT FILES")
    report.append("-" * 40)

    report.append("""
  Statistical Tables:
    - table1_descriptive_statistics.csv
    - table2_chi_square_tests.csv
    - table3_correlation_matrix.csv
    - table4_logistic_regression.csv
    - table5_random_forest_importance.csv

  Figures (PDF + PNG, 300 DPI):
    - fig1_top_skills.pdf/png
    - fig2_job_distribution.pdf/png
    - fig3_skills_by_category.pdf/png
    - fig4_placement_vs_academic.pdf/png
    - fig5_skills_job_match.pdf/png
    - fig6_global_placement.pdf/png
    - fig7_skill_gap_summary.pdf/png
    - fig8_geographic_distribution.pdf/png
    - fig9_student_career_success.pdf/png
    - fig10_ai_market_trends.pdf/png
    - fig11_international_graduates.pdf/png
    - fig12_comprehensive_gap_dashboard.pdf/png

  Data Files:
    - data_loader.py (unified data loading)
    - skill_extractor.py (NLP skill analysis)
    - statistical_tests.py (statistical analysis)
    - analysis.py (visualization)
    - research_report.py (this report)
    """)

    report.append("\n" + "=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    return "\n".join(report)


if __name__ == '__main__':
    report = generate_report()
    print(report)

    report_path = os.path.join(OUTPUT_DIR, 'research_summary_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")
