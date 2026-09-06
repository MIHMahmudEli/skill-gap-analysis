import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KAGGLE_DIR = os.path.join(BASE_DIR, 'kaggle')
OUTPUT_DIR = os.path.join(BASE_DIR, 'figures')

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_linkedin_skills():
    df = pd.read_csv(os.path.join(KAGGLE_DIR, '1-3m-linkedin-jobs-and-skills-2024', 'job_skills.csv'))
    skills = []
    for _, row in df.iterrows():
        if pd.notna(row['job_skills']):
            for s in str(row['job_skills']).split(','):
                skills.append(s.strip().lower())
    skill_counts = pd.Series(skills).value_counts()
    return pd.DataFrame({'skill': skill_counts.index, 'count': skill_counts.values})


def load_linkedin_jobs():
    return pd.read_csv(os.path.join(KAGGLE_DIR, '1-3m-linkedin-jobs-and-skills-2024', 'linkedin_job_postings.csv'))


def load_hf_skill_gap_skills():
    return pd.read_csv(os.path.join(BASE_DIR, 'hf_skill_gap_skills.csv'))


def load_hf_skill_gap_jobs():
    return pd.read_csv(os.path.join(BASE_DIR, 'hf_skill_gap_jobs.csv'))


def load_hf_job_skill_set():
    return pd.read_csv(os.path.join(BASE_DIR, 'hf_job_skill_set.csv'))


def load_college_placement():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'college-student-placement', 'college_student_placement_dataset.csv'))


def load_ngess():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'ngess-graduate-employment-dataset', 'NGESS Graduate Employment Dataset.csv'))


def load_global_placement():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'global-student-placement-2025-dataset', 'global_placement.csv'))


def load_ai_jobs():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'global-ai-job-market-and-salary-trends-2025', 'ai_job_dataset.csv'))


def load_india_skills():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'india-professional-skills-intelligence-dataset', 'india_professional_skills_intelligence.csv'))


def load_student_career():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'student-career-success-prediction-dataset', 'student_career_success_dataset.csv'))


def load_usa_jobs():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'usa-job-market-skills-and-title-analysis', 'usa_job_posting_dataset.csv'))


def load_international_graduates():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'international-graduates-employment-dataset', 'dataset.csv'))


def load_india_fresher():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'indian-fresher-job-market-who-gets-hired-and-why', 'fresher_hiring_india_dataset.csv'))


def load_ai_market_trends():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'ai-and-data-science-job-market-dataset-20202026', 'AI Job Market Dataset.csv'))


def load_career_change():
    return pd.read_csv(os.path.join(KAGGLE_DIR, 'field-of-study-vs-occupation', 'career_change_prediction_dataset.csv'))


def get_dataset_summary():
    summary = []
    loaders = [
        ('linkedin_skills', load_linkedin_skills),
        ('linkedin_jobs', load_linkedin_jobs),
        ('hf_skills', load_hf_skill_gap_skills),
        ('hf_jobs', load_hf_skill_gap_jobs),
        ('college_placement', load_college_placement),
        ('ngess', load_ngess),
        ('global_placement', load_global_placement),
        ('ai_jobs', load_ai_jobs),
        ('india_skills', load_india_skills),
        ('student_career', load_student_career),
        ('usa_jobs', load_usa_jobs),
        ('international_grad', load_international_graduates),
        ('india_fresher', load_india_fresher),
        ('ai_market_trends', load_ai_market_trends),
        ('career_change', load_career_change),
    ]
    for name, loader in loaders:
        try:
            df = loader()
            summary.append({'dataset': name, 'rows': df.shape[0], 'cols': df.shape[1]})
            del df
        except Exception as e:
            summary.append({'dataset': name, 'rows': 0, 'cols': 0, 'error': str(e)})
    return pd.DataFrame(summary)


if __name__ == '__main__':
    print("Dataset summary:")
    summary = get_dataset_summary()
    print(summary.to_string(index=False))
