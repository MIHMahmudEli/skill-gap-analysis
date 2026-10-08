import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import os
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import (
    load_hf_skill_gap_skills, load_hf_skill_gap_jobs, load_linkedin_skills,
    load_hf_job_skill_set, load_ai_market_trends, load_india_skills,
    load_usa_jobs
)


SKILL_CATEGORIES = {
    'Programming & Development': [
        'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'r', 'scala', 'go', 'rust',
        'typescript', 'php', 'ruby', 'swift', 'kotlin', 'html', 'css', 'react', 'angular',
        'vue', 'node.js', 'django', 'flask', 'spring', 'rails', 'git', 'docker', 'kubernetes'
    ],
    'Data Science & Analytics': [
        'machine learning', 'deep learning', 'data analysis', 'data visualization',
        'statistical analysis', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn',
        'tableau', 'power bi', 'hadoop', 'spark', 'data mining', 'neural networks',
        'natural language processing', 'nlp', 'computer vision', 'ai', 'artificial intelligence'
    ],
    'Cloud & Infrastructure': [
        'aws', 'azure', 'gcp', 'cloud computing', 'devops', 'ci/cd', 'jenkins',
        'terraform', 'ansible', 'linux', 'windows server', 'networking', 'security',
        'microservices', 'rest api', 'graphql', 'serverless'
    ],
    'Soft Skills': [
        'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
        'time management', 'project management', 'analytical skills', 'creativity',
        'adaptability', 'collaboration', 'presentation', 'negotiation', 'mentoring'
    ],
    'Business & Domain': [
        'agile', 'scrum', 'product management', 'business analysis', 'stakeholder management',
        'requirements gathering', 'process improvement', 'quality assurance', 'compliance',
        'risk management', 'strategic planning', 'budget management', 'client management'
    ],
    'Design & UX': [
        'ui/ux', 'figma', 'sketch', 'adobe xd', 'user research', 'wireframing',
        'prototyping', 'user interface', 'user experience', 'graphic design', 'css'
    ],
    'Data Engineering': [
        'etl', 'data pipeline', 'airflow', 'kafka', 'database design', 'data warehousing',
        'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'data governance'
    ],
    'Cybersecurity': [
        'information security', 'penetration testing', 'vulnerability assessment',
        'incident response', 'forensics', 'encryption', 'firewall', 'siem',
        'compliance', 'gdpr', 'iso 27001', 'nist'
    ]
}


def extract_skills_from_text(text):
    if pd.isna(text):
        return []
    text = str(text).lower()
    skills = []
    for category, skill_list in SKILL_CATEGORIES.items():
        for skill in skill_list:
            if skill in text:
                skills.append(skill)
    return list(set(skills))


def build_skill_taxonomy():
    all_skills = set()
    for category, skills in SKILL_CATEGORIES.items():
        all_skills.update(skills)
    return sorted(all_skills)


def compute_tfidf_alignment(corpus_a, corpus_b, max_features=5000):
    vectorizer = TfidfVectorizer(max_features=max_features, stop_words='english', ngram_range=(1, 2))
    all_texts = corpus_a + corpus_b
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    n_a = len(corpus_a)
    matrix_a = tfidf_matrix[:n_a]
    matrix_b = tfidf_matrix[n_a:]
    similarity = cosine_similarity(matrix_a, matrix_b)
    return similarity, vectorizer.get_feature_names_out()


def compute_skill_gap_index(demand_skills, supply_skills):
    demand_set = set(s.lower().strip() for s in demand_skills)
    supply_set = set(s.lower().strip() for s in supply_skills)
    if len(demand_set) == 0:
        return 1.0, [], list(supply_set)
    covered = demand_set & supply_set
    missing = demand_set - supply_set
    extra = supply_set - demand_set
    coverage = len(covered) / len(demand_set)
    return coverage, list(missing), list(extra)


def extract_skills_from_dataset(df, text_columns, skill_columns=None):
    all_skills = []
    for _, row in df.iterrows():
        row_skills = set()
        if skill_columns:
            for col in skill_columns:
                if pd.notna(row.get(col)):
                    for s in str(row[col]).split(','):
                        s = s.strip().lower()
                        if s:
                            row_skills.add(s)
        for col in text_columns:
            if pd.notna(row.get(col)):
                extracted = extract_skills_from_text(row[col])
                row_skills.update(extracted)
        all_skills.append(list(row_skills))
    return all_skills


def get_market_skills():
    df_hf = load_hf_skill_gap_skills()
    market_skills = []
    for s in df_hf['job_skills'].dropna():
        for skill in str(s).split(','):
            skill = skill.strip().lower()
            if skill:
                market_skills.append(skill)
    skill_counts = Counter(market_skills)
    return pd.DataFrame(skill_counts.most_common(500), columns=['skill', 'job_postings'])


def get_academic_skills():
    df_college = load_hf_job_skill_set()
    academic_skills = []
    for _, row in df_college.iterrows():
        if pd.notna(row.get('job_skill_set')):
            skills_str = str(row['job_skill_set']).strip('[]').replace("'", "")
            for s in skills_str.split(','):
                s = s.strip().lower()
                if s:
                    academic_skills.append(s)
    skill_counts = Counter(academic_skills)
    return pd.DataFrame(skill_counts.most_common(500), columns=['skill', 'frequency'])


def compute_alignment_metrics(market_df, academic_df, top_n=100):
    market_top = set(market_df['skill'].head(top_n).tolist())
    academic_top = set(academic_df['skill'].head(top_n).tolist())
    covered = market_top & academic_top
    missing_in_academic = market_top - academic_top
    extra_in_academic = academic_top - market_top
    coverage = len(covered) / len(market_top) if len(market_top) > 0 else 0
    return {
        'market_skills': len(market_top),
        'academic_skills': len(academic_top),
        'covered': len(covered),
        'missing': len(missing_in_academic),
        'extra': len(extra_in_academic),
        'coverage_rate': coverage,
        'gap_index': 1 - coverage,
        'missing_skills': sorted(missing_in_academic),
        'covered_skills': sorted(covered)
    }


def compute_semantic_alignment(market_df, academic_df, top_n=100, thresholds=[0.4, 0.5, 0.6, 0.7]):
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    market_skills = market_df['skill'].head(top_n).tolist()
    academic_skills = academic_df['skill'].head(top_n).tolist()

    model = SentenceTransformer('all-MiniLM-L6-v2')
    market_emb = model.encode(market_skills, show_progress_bar=False)
    academic_emb = model.encode(academic_skills, show_progress_bar=False)

    sim_matrix = cosine_similarity(market_emb, academic_emb)
    max_sims = np.max(sim_matrix, axis=1)
    best_matches = [academic_skills[idx] for idx in np.argmax(sim_matrix, axis=1)]

    matches_df = pd.DataFrame({
        'market_skill': market_skills,
        'best_academic_match': best_matches,
        'cosine_similarity': np.round(max_sims, 4)
    })

    results = []
    np.random.seed(42)
    default_covered = max_sims >= 0.5
    default_sgi = 1.0 - np.mean(default_covered)

    for tau in thresholds:
        covered = max_sims >= tau
        cov_rate = np.mean(covered)
        sgi = 1.0 - cov_rate
        boot_sgis = []
        for _ in range(1000):
            sample = np.random.choice(covered, size=len(covered), replace=True)
            boot_sgis.append(1.0 - np.mean(sample))
        ci_lower = np.percentile(boot_sgis, 2.5)
        ci_upper = np.percentile(boot_sgis, 97.5)
        results.append({
            'tau': tau,
            'SGI': round(sgi, 4),
            'Coverage_Rate': round(cov_rate, 4),
            'CI_Lower': round(ci_lower, 4),
            'CI_Upper': round(ci_upper, 4),
            'Delta_SGI': round(sgi - default_sgi, 4)
        })

    sensitivity_df = pd.DataFrame(results)
    return matches_df, sensitivity_df


def analyze_skill_evolution():
    df_ai = load_ai_market_trends()
    if 'job_posting_year' in df_ai.columns:
        yearly = df_ai.groupby('job_posting_year').agg({
            'skills_python': 'sum',
            'skills_sql': 'sum',
            'skills_ml': 'sum',
            'skills_deep_learning': 'sum',
            'skills_cloud': 'sum'
        }).reset_index()
        return yearly
    return None


def get_geographic_skill_distribution():
    df_jobs = load_hf_skill_gap_jobs()
    if 'search_country' in df_jobs.columns:
        country_stats = df_jobs.groupby('search_country').agg({
            'job_link': 'count',
            'job_level': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown',
            'job_type': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'Unknown'
        }).reset_index()
        country_stats.columns = ['country', 'job_count', 'most_common_level', 'most_common_type']
        return country_stats.sort_values('job_count', ascending=False)
    return None


if __name__ == '__main__':
    print("=== Skill Extraction & Analysis ===\n")

    print("1. Building market skill profile...")
    market = get_market_skills()
    print(f"   Top 10 market skills:")
    for _, row in market.head(10).iterrows():
        print(f"     {row['skill']}: {row['job_postings']:,} postings")

    print("\n2. Building academic skill profile...")
    academic = get_academic_skills()
    print(f"   Top 10 academic skills:")
    for _, row in academic.head(10).iterrows():
        print(f"     {row['skill']}: {row['frequency']} occurrences")

    print("\n3. Computing alignment metrics...")
    metrics = compute_alignment_metrics(market, academic)
    print(f"   String-match coverage rate: {metrics['coverage_rate']:.1%}")
    print(f"   String-match gap index: {metrics['gap_index']:.1%}")
    print(f"   Missing skills: {metrics['missing_skills'][:10]}")

    print("\n3b. Computing SentenceTransformer semantic alignment (all-MiniLM-L6-v2)...")
    matches_df, sensitivity_df = compute_semantic_alignment(market, academic)
    print("   Sensitivity across tau thresholds:")
    print(sensitivity_df.to_string(index=False))

    base_dir = os.path.dirname(os.path.abspath(__file__))
    derived_dir = os.path.join(base_dir, 'derived_matrices')
    os.makedirs(derived_dir, exist_ok=True)

    sensitivity_df.to_csv(os.path.join(base_dir, 'table_sensitivity_tau.csv'), index=False)
    sensitivity_df.to_csv(os.path.join(derived_dir, 'table_sensitivity_tau.csv'), index=False)
    matches_df.to_csv(os.path.join(base_dir, 'skill_semantic_matches.csv'), index=False)
    matches_df.to_csv(os.path.join(derived_dir, 'skill_semantic_matches.csv'), index=False)
    print("   Saved: table_sensitivity_tau.csv and skill_semantic_matches.csv")

    print("\n4. Analyzing skill evolution...")
    evolution = analyze_skill_evolution()
    if evolution is not None:
        print(evolution.to_string(index=False))

    print("\n5. Geographic distribution...")
    geo = get_geographic_skill_distribution()
    if geo is not None:
        print(geo.head(10).to_string(index=False))

    print("\n=== Analysis Complete ===")
