# Skill Gap Analysis

A data-driven framework for analyzing the gap between academic education and industry skill requirements using NLP, statistical analysis, and machine learning.

## Overview

This project quantifies the misalignment between academic curricula and market demands by analyzing 15 publicly available datasets comprising 3.18M+ records from LinkedIn, Kaggle, and HuggingFace. The framework employs:

- **NLP-based skill extraction** using TF-IDF and semantic alignment
- **Statistical analysis** with chi-square tests, logistic regression, and random forests
- **Machine learning prediction** models for graduate employability
- **Skill Gap Index (SGI)** quantification across 8 skill categories

## Project Structure

```
skill-gap-analysis/
├── datasets/
│   ├── data_loader.py          # Dataset loading and management
│   ├── skill_extractor.py      # NLP skill extraction pipeline
│   ├── statistical_tests.py    # Statistical analysis and ML models
│   ├── analysis.py             # Figure generation and visualization
│   ├── summary.py              # Dataset summary utilities
│   ├── search_kaggle.py        # Kaggle dataset search
│   ├── download_kaggle.py      # Kaggle dataset download
│   ├── research_report.py      # Research report generation
│   └── hf_*.csv                # HuggingFace datasets (local copies)
├── requirements.txt
├── .gitignore
└── README.md
```

## Installation

```bash
git clone https://github.com/MIHMahmudEli/skill-gap-analysis.git
cd skill-gap-analysis
pip install -r requirements.txt
```

## Dependencies

- Python 3.12+
- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- scikit-learn >= 1.2.0
- matplotlib >= 3.7.0
- sentence-transformers >= 2.2.0

## Usage

### 1. Data Loading

```python
from datasets.data_loader import load_linkedin_skills, load_hf_skill_gap_skills

# Load LinkedIn skills data
linkedin_skills = load_linkedin_skills()

# Load HuggingFace skill gap data
hf_skills = load_hf_skill_gap_skills()
```

### 2. Skill Extraction

```python
from datasets.skill_extractor import (
    get_market_skills,
    get_academic_skills,
    compute_alignment_metrics,
    SKILL_CATEGORIES
)

# Get market skill profile
market_skills = get_market_skills()

# Get academic skill profile
academic_skills = get_academic_skills()

# Compute alignment metrics
metrics = compute_alignment_metrics(market_skills, academic_skills)
print(f"Skill Gap Index: {metrics['gap_index']:.1%}")
```

### 3. Statistical Analysis

```python
from datasets.statistical_tests import (
    table1_descriptive,
    table2_chi_square,
    table3_correlation,
    table4_logistic_regression,
    table5_random_forest
)

# Run all statistical analyses
table1_descriptive()
table2_chi_square()
table3_correlation()
table4_logistic_regression()
table5_random_forest()
```

### 4. Visualization

```python
from datasets.analysis import (
    fig1_top_skills,
    fig2_skill_gap,
    fig3_employability,
    fig4_geographic_ai,
    fig5_model_comparison,
    fig6_internship
)

# Generate all figures
fig1_top_skills()
fig2_skill_gap()
fig3_employability()
fig4_geographic_ai()
fig5_model_comparison()
fig6_internship()
```

## Skill Categories

The framework uses an 8-category taxonomy for skill classification:

| Category | Examples |
|----------|----------|
| Programming & Development | Python, Java, JavaScript, SQL, React |
| Data Science & Analytics | Machine Learning, Deep Learning, TensorFlow |
| Cloud & Infrastructure | AWS, Azure, GCP, Docker, Kubernetes |
| Soft Skills | Communication, Leadership, Teamwork |
| Business & Domain | Agile, Scrum, Product Management |
| Design & UX | UI/UX, Figma, User Research |
| Data Engineering | ETL, Airflow, Kafka, PostgreSQL |
| Cybersecurity | Information Security, Penetration Testing |

## Key Metrics

- **Skill Gap Index (SGI)**: 52% (95% CI: 49-55%)
- **Top Missing Skills**: Data Science (18pp gap), Cloud Computing (15pp gap)
- **Strongest Employability Predictors**: Communication (OR=6.47), CGPA (OR=6.20), Projects (OR=3.18)

## Data Sources

This project uses 15 publicly available datasets:

- **LinkedIn Jobs & Skills** (1.35M records)
- **HuggingFace Skill Gap** (519K records)
- **USA Job Market Skills** (316K records)
- **International Graduates** (300K records)
- **College Student Placement** (10K records)
- And 10 more datasets from Kaggle and HuggingFace

## Datasets Not Included

Large datasets (>10MB) are excluded from the repository due to size constraints. To download them:

1. Install Kaggle CLI: `pip install kaggle`
2. Set up credentials: `kaggle.json` in `~/.kaggle/`
3. Run: `python datasets/download_kaggle.py`

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{skill_gap_analysis,
  title={Skill Gap Analysis: Academic-Industry Skills Gap Quantification},
  author={MIHMahmudEli},
  year={2025},
  url={https://github.com/MIHMahmudEli/skill-gap-analysis}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Dataset providers on Kaggle and HuggingFace
- scikit-learn and pandas communities
- Research on skill gap analysis in higher education
