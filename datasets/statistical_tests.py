import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score, precision_score, recall_score
import os
import sys
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import (
    load_college_placement, load_ngess, load_global_placement,
    load_ai_jobs, load_india_skills, load_student_career,
    load_international_graduates, load_india_fresher,
    load_ai_market_trends, load_career_change
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = BASE_DIR


def print_header(title):
    print(f"\n{'='*70}")
    print(title)
    print('='*70)


def cohens_d(g1, g2):
    n1, n2 = len(g1), len(g2)
    var1, var2 = g1.var(), g2.var()
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    return (g1.mean() - g2.mean()) / pooled_std if pooled_std > 0 else 0


def significance(p):
    if p < 0.001: return '***'
    if p < 0.01: return '**'
    if p < 0.05: return '*'
    return 'ns'


def table1_descriptive():
    print_header("TABLE 1: Descriptive Statistics - College Student Placement (N=10,000)")
    df = load_college_placement()
    df['Placement_Binary'] = (df['Placement'] == 'Yes').astype(int)
    placed = df[df['Placement'] == 'Yes']
    not_placed = df[df['Placement'] == 'No']

    vars_list = ['CGPA', 'IQ', 'Prev_Sem_Result', 'Communication_Skills',
                 'Projects_Completed', 'Academic_Performance', 'Extra_Curricular_Score']

    rows = []
    print(f"\n{'Variable':<25} {'Placed (n={})'.format(len(placed)):>22} {'Not Placed (n={})'.format(len(not_placed)):>24} {'t-stat':>10} {'p-value':>10} {'Cohen d':>10} {'Sig':>5}")
    print('-' * 105)

    for var in vars_list:
        g1 = placed[var].dropna()
        g2 = not_placed[var].dropna()
        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
        d = cohens_d(g1, g2)
        sig = significance(p_val)
        print(f"{var:<25} {g1.mean():>10.2f} +/- {g1.std():<6.2f} {g2.mean():>12.2f} +/- {g2.std():<6.2f} {t_stat:>8.3f}  {p_val:>10.4f} {d:>8.3f} {sig:>5}")
        rows.append({
            'Variable': var,
            'Placed_Mean': round(g1.mean(), 2), 'Placed_SD': round(g1.std(), 2),
            'NotPlaced_Mean': round(g2.mean(), 2), 'NotPlaced_SD': round(g2.std(), 2),
            't_statistic': round(t_stat, 3), 'p_value': round(p_val, 4),
            'Cohens_d': round(d, 3), 'Significance': sig
        })

    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_DIR, 'table1_descriptive_statistics.csv'), index=False)
    print(f"\nSaved: table1_descriptive_statistics.csv")
    return rows


def table2_chi_square():
    print_header("TABLE 2: Chi-Square Tests of Independence")
    df = load_college_placement()
    df['Placement_Binary'] = (df['Placement'] == 'Yes').astype(int)
    df['Projects_Group'] = pd.cut(df['Projects_Completed'], bins=[-1, 1, 2, 10], labels=['0-1', '2', '3+'])

    tests = [
        ('Placement vs Internship Experience', 'Placement', 'Internship_Experience'),
        ('Placement vs Projects Grouped', 'Placement', 'Projects_Group'),
    ]

    rows = []
    print(f"\n{'Test':<45} {'chi2':>10} {'df':>6} {'p-value':>10} {'Cramers V':>10} {'Sig':>5}")
    print('-' * 90)

    for test_name, var1, var2 in tests:
        ct = pd.crosstab(df[var1], df[var2])
        chi2, p, dof, expected = stats.chi2_contingency(ct)
        cramers_v = np.sqrt(chi2 / (len(df) * (min(ct.shape) - 1)))
        sig = significance(p)
        print(f"{test_name:<45} {chi2:>10.3f} {dof:>6} {p:>10.4f} {cramers_v:>8.3f} {sig:>5}")
        rows.append({'Test': test_name, 'chi2': round(chi2, 3), 'df': dof,
                     'p_value': round(p, 4), 'Cramers_V': round(cramers_v, 3), 'Sig': sig})

    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_DIR, 'table2_chi_square_tests.csv'), index=False)
    print(f"\nSaved: table2_chi_square_tests.csv")
    return rows


def table3_correlation():
    print_header("TABLE 3: Pearson Correlation Matrix")
    df = load_college_placement()
    df['Placement_Binary'] = (df['Placement'] == 'Yes').astype(int)
    df['Internship_Binary'] = (df['Internship_Experience'] == 'Yes').astype(int)

    corr_vars = ['CGPA', 'IQ', 'Prev_Sem_Result', 'Communication_Skills',
                 'Projects_Completed', 'Academic_Performance', 'Extra_Curricular_Score',
                 'Placement_Binary', 'Internship_Binary']
    corr_matrix = df[corr_vars].corr()
    print(corr_matrix.round(3).to_string())
    corr_matrix.to_csv(os.path.join(OUTPUT_DIR, 'table3_correlation_matrix.csv'))
    print(f"\nSaved: table3_correlation_matrix.csv")
    return corr_matrix


def table4_logistic():
    print_header("TABLE 4: Logistic Regression - Placement Prediction (College)")
    df = load_college_placement()
    df['Placement_Binary'] = (df['Placement'] == 'Yes').astype(int)
    df['Internship_Binary'] = (df['Internship_Experience'] == 'Yes').astype(int)

    X = df[['CGPA', 'Communication_Skills', 'Projects_Completed', 'Internship_Binary', 'IQ', 'Academic_Performance']].dropna()
    y = df.loc[X.index, 'Placement_Binary']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)

    print(f"\nModel Accuracy: {accuracy_score(y, y_pred)*100:.1f}%")
    print(f"\n{'Feature':<25} {'Coefficient':>12} {'Odds Ratio':>12} {'Std Error':>12}")
    print('-' * 65)

    rows = []
    for name, coef in zip(X.columns, model.coef_[0]):
        odds_ratio = np.exp(coef)
        sig = significance(abs(coef))
        print(f"{name:<25} {coef:>12.4f} {odds_ratio:>12.4f} {sig:>5}")
        rows.append({'Feature': name, 'Coefficient': round(coef, 4),
                     'Odds_Ratio': round(odds_ratio, 4), 'Sig': sig})

    print(f"\nIntercept: {model.intercept_[0]:.4f}")
    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_DIR, 'table4_logistic_regression.csv'), index=False)
    print(f"\nSaved: table4_logistic_regression.csv")
    return rows


def table5_random_forest():
    print_header("TABLE 5: Random Forest - Placement Prediction")
    df = load_college_placement()
    df['Placement_Binary'] = (df['Placement'] == 'Yes').astype(int)
    df['Internship_Binary'] = (df['Internship_Experience'] == 'Yes').astype(int)

    X = df[['CGPA', 'Communication_Skills', 'Projects_Completed', 'Internship_Binary', 'IQ', 'Academic_Performance']].dropna()
    y = df.loc[X.index, 'Placement_Binary']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)

    print(f"\nModel Accuracy: {accuracy_score(y, y_pred)*100:.1f}%")
    print(f"\n{'Feature':<25} {'Importance':>12}")
    print('-' * 40)

    rows = []
    for name, imp in sorted(zip(X.columns, model.feature_importances_), key=lambda x: -x[1]):
        print(f"{name:<25} {imp:>12.4f}")
        rows.append({'Feature': name, 'Importance': round(imp, 4)})

    pd.DataFrame(rows).to_csv(os.path.join(OUTPUT_DIR, 'table5_random_forest_importance.csv'), index=False)
    print(f"\nSaved: table5_random_forest_importance.csv")
    return rows


def table_vif_analysis():
    print_header("MULTICOLLINEARITY ASSESSMENT (Variance Inflation Factors)")
    df = load_college_placement()
    df['Internship_Binary'] = (df['Internship_Experience'] == 'Yes').astype(int)
    features = ['CGPA', 'Communication_Skills', 'Projects_Completed', 'Internship_Binary', 'IQ', 'Academic_Performance']
    X = df[features].dropna()
    corr_matrix = X.corr().values
    vif_values = np.diag(np.linalg.inv(corr_matrix))
    vif_df = pd.DataFrame({
        'Feature': features,
        'VIF': np.round(vif_values, 3),
        'Tolerance': np.round(1.0 / vif_values, 3),
        'Status': ['Acceptable (<5)' if v < 5 else 'Collinear (>=5)' for v in vif_values]
    })
    print(vif_df.to_string(index=False))
    derived_dir = os.path.join(OUTPUT_DIR, 'derived_matrices')
    os.makedirs(derived_dir, exist_ok=True)
    vif_df.to_csv(os.path.join(OUTPUT_DIR, 'table_vif.csv'), index=False)
    vif_df.to_csv(os.path.join(derived_dir, 'table_vif.csv'), index=False)
    print("Saved: table_vif.csv")
    return vif_df


def table_cross_validation_models():
    print_header("5-FOLD STRATIFIED CROSS-VALIDATION MODEL COMPARISON")
    df = load_college_placement()
    df['Placement_Binary'] = (df['Placement'] == 'Yes').astype(int)
    df['Internship_Binary'] = (df['Internship_Experience'] == 'Yes').astype(int)
    features = ['CGPA', 'Communication_Skills', 'Projects_Completed', 'Internship_Binary', 'IQ', 'Academic_Performance']
    X = df[features].dropna()
    y = df.loc[X.index, 'Placement_Binary'].values

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42),
        'SVM (RBF)': SVC(kernel='rbf', C=1.0, probability=True, random_state=42),
        'Decision Tree': DecisionTreeClassifier(max_depth=6, random_state=42),
        'Baseline (Majority)': DummyClassifier(strategy='most_frequent')
    }

    results = []
    scaler = StandardScaler()
    for name, model in models.items():
        accs, f1s, aucs, precs, recs = [], [], [], [], []
        for train_idx, test_idx in skf.split(X, y):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            X_tr_sc = scaler.fit_transform(X_train)
            X_te_sc = scaler.transform(X_test)

            model.fit(X_tr_sc, y_train)
            y_pred = model.predict(X_te_sc)
            accs.append(accuracy_score(y_test, y_pred))
            f1s.append(f1_score(y_test, y_pred, average='weighted', zero_division=0))
            precs.append(precision_score(y_test, y_pred, average='weighted', zero_division=0))
            recs.append(recall_score(y_test, y_pred, average='weighted', zero_division=0))
            if hasattr(model, 'predict_proba'):
                y_prob = model.predict_proba(X_te_sc)[:, 1]
                aucs.append(roc_auc_score(y_test, y_prob))
            else:
                aucs.append(0.5)

        results.append({
            'Model': name,
            'Accuracy_Mean': round(np.mean(accs), 4),
            'Accuracy_SD': round(np.std(accs), 4),
            'F1_Mean': round(np.mean(f1s), 4),
            'F1_SD': round(np.std(f1s), 4),
            'Precision_Mean': round(np.mean(precs), 4),
            'Recall_Mean': round(np.mean(recs), 4),
            'AUC_Mean': round(np.mean(aucs), 4),
            'AUC_SD': round(np.std(aucs), 4)
        })

    cv_df = pd.DataFrame(results)
    print(cv_df.to_string(index=False))
    derived_dir = os.path.join(OUTPUT_DIR, 'derived_matrices')
    os.makedirs(derived_dir, exist_ok=True)
    cv_df.to_csv(os.path.join(OUTPUT_DIR, 'table6_model_comparison_cv.csv'), index=False)
    cv_df.to_csv(os.path.join(derived_dir, 'table6_model_comparison_cv.csv'), index=False)
    print("Saved: table6_model_comparison_cv.csv")
    return cv_df


def table6_ngess_analysis():
    print_header("TABLE 6: NGESS Graduate Employment Analysis (N=7,200)")
    df = load_ngess()

    print("\n--- Employment Status Distribution ---")
    emp_counts = df['Employment_Status'].value_counts()
    for status, count in emp_counts.items():
        print(f"  {status}: {count} ({count/len(df)*100:.1f}%)")

    print("\n--- Skills-Job Match vs Job Satisfaction (ANOVA) ---")
    match_groups = [group['Job_Satisfaction'].dropna()
                    for name, group in df.groupby('Skills_Job_Match')
                    if len(group['Job_Satisfaction'].dropna()) > 0]
    if len(match_groups) >= 2:
        f_stat, p_val = stats.f_oneway(*match_groups)
        sig = significance(p_val)
        print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.4f} {sig}")

        print("\nMean satisfaction by match level:")
        for name, group in df.groupby('Skills_Job_Match'):
            sat = group['Job_Satisfaction'].dropna()
            if len(sat) > 0:
                print(f"  {name}: {sat.mean():.2f} +/- {sat.std():.2f} (n={len(sat)})")

    print("\n--- CGPA vs Employment Status (ANOVA) ---")
    emp_groups = [group['CGPA'].dropna()
                  for name, group in df.groupby('Employment_Status')
                  if len(group['CGPA'].dropna()) > 1]
    if len(emp_groups) >= 2:
        f_stat, p_val = stats.f_oneway(*emp_groups)
        sig = significance(p_val)
        print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.4f} {sig}")

    print("\n--- Salary vs Skills-Job Match (ANOVA) ---")
    salary_groups = [group['Monthly_Salary_000'].dropna()
                     for name, group in df.groupby('Skills_Job_Match')
                     if len(group['Monthly_Salary_000'].dropna()) > 1]
    if len(salary_groups) >= 2:
        f_stat, p_val = stats.f_oneway(*salary_groups)
        sig = significance(p_val)
        print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.4f} {sig}")


def table7_global_placement():
    print_header("TABLE 7: Global Student Placement Analysis (N=10,000)")
    df = load_global_placement()
    df['Placement_Binary'] = (df['placement_status'] == 'Placed').astype(int)
    placed = df[df['placement_status'] == 'Placed']
    not_placed = df[df['placement_status'] == 'Not Placed']

    print(f"\n{'Variable':<25} {'Placed (n={})'.format(len(placed)):>20} {'Not Placed (n={})'.format(len(not_placed)):>22} {'t-stat':>10} {'p-value':>10} {'Sig':>5}")
    print('-' * 95)

    global_vars = ['cgpa', 'communication_score', 'aptitude_score', 'internship_count']
    for var in global_vars:
        g1 = placed[var].dropna()
        g2 = not_placed[var].dropna()
        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
        sig = significance(p_val)
        print(f"{var:<25} {g1.mean():>10.2f} +/- {g1.std():<6.2f} {g2.mean():>12.2f} +/- {g2.std():<6.2f} {t_stat:>8.3f}  {p_val:>10.4f} {sig:>5}")

    print("\n--- Placement by Specialization (Chi-Square) ---")
    ct_spec = pd.crosstab(df['placement_status'], df['specialization'])
    chi2, p, dof, expected = stats.chi2_contingency(ct_spec)
    cramers_v = np.sqrt(chi2 / (len(df) * (min(ct_spec.shape) - 1)))
    sig = significance(p)
    print(f"chi2 = {chi2:.3f}, df = {dof}, p = {p:.4f}, Cramer's V = {cramers_v:.3f} {sig}")

    print("\n--- Logistic Regression: Global Placement Prediction ---")
    X = df[['cgpa', 'communication_score', 'aptitude_score', 'internship_count']].dropna()
    y = df.loc[X.index, 'Placement_Binary']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)
    print(f"Model Accuracy: {accuracy_score(y, y_pred)*100:.1f}%")
    print(f"\n{'Feature':<25} {'Coefficient':>12} {'Odds Ratio':>12}")
    print('-' * 55)
    for name, coef in zip(X.columns, model.coef_[0]):
        odds_ratio = np.exp(coef)
        sig = significance(abs(coef))
        print(f"{name:<25} {coef:>12.4f} {odds_ratio:>12.4f} {sig:>5}")


def table8_student_career():
    print_header("TABLE 8: Student Career Success Analysis (N=50,000)")
    df = load_student_career()

    print("\n--- Placement Rate ---")
    placed = df[df['Placement_Status'] == 'Placed']
    not_placed = df[df['Placement_Status'] == 'Not Placed']
    print(f"Placed: {len(placed)} ({len(placed)/len(df)*100:.1f}%)")
    print(f"Not Placed: {len(not_placed)} ({len(not_placed)/len(df)*100:.1f}%)")

    print("\n--- Key Variables by Placement Status ---")
    vars_list = ['CGPA', 'Programming_Skill', 'Communication_Skills', 'Internships',
                 'Projects_Completed', 'Certifications', 'Interview_Score']
    print(f"\n{'Variable':<25} {'Placed (mean)':>15} {'Not Placed (mean)':>18} {'t-stat':>10} {'p-value':>10} {'Sig':>5}")
    print('-' * 85)

    for var in vars_list:
        g1 = placed[var].dropna()
        g2 = not_placed[var].dropna()
        t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
        sig = significance(p_val)
        print(f"{var:<25} {g1.mean():>15.2f} {g2.mean():>18.2f} {t_stat:>8.3f}  {p_val:>10.4f} {sig:>5}")

    print("\n--- Logistic Regression: Career Success Prediction ---")
    df['Placement_Binary'] = (df['Placement_Status'] == 'Placed').astype(int)
    X = df[['CGPA', 'Programming_Skill', 'Communication_Skills', 'Internships',
            'Projects_Completed', 'Certifications', 'Interview_Score']].dropna()
    y = df.loc[X.index, 'Placement_Binary']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)
    print(f"Model Accuracy: {accuracy_score(y, y_pred)*100:.1f}%")
    print(f"\n{'Feature':<25} {'Coefficient':>12} {'Odds Ratio':>12}")
    print('-' * 55)
    for name, coef in zip(X.columns, model.coef_[0]):
        odds_ratio = np.exp(coef)
        sig = significance(abs(coef))
        print(f"{name:<25} {coef:>12.4f} {odds_ratio:>12.4f} {sig:>5}")


def table9_ai_market():
    print_header("TABLE 9: AI Job Market Trends (N=10,345)")
    df = load_ai_market_trends()

    print("\n--- Salary by Experience Level (ANOVA) ---")
    exp_groups = [group['salary'].dropna()
                  for name, group in df.groupby('experience_level')
                  if len(group['salary'].dropna()) > 1]
    f_stat, p_val = stats.f_oneway(*exp_groups)
    sig = significance(p_val)
    print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.4f} {sig}")

    print("\nMean salary by experience level:")
    for name, group in df.groupby('experience_level'):
        print(f"  {name}: ${group['salary'].mean():,.0f} +/- ${group['salary'].std():,.0f}")

    print("\n--- Skill Demand Trends (2020-2026) ---")
    yearly = df.groupby('job_posting_year').agg({
        'skills_python': 'mean',
        'skills_sql': 'mean',
        'skills_ml': 'mean',
        'skills_deep_learning': 'mean',
        'skills_cloud': 'mean'
    }).round(3)
    print(yearly.to_string())

    print("\n--- Remote Work Trends ---")
    remote_stats = df['remote_type'].value_counts()
    for rt, count in remote_stats.items():
        print(f"  {rt}: {count} ({count/len(df)*100:.1f}%)")


def table10_international_graduates():
    print_header("TABLE 10: International Graduates Employment (N=300,000)")
    df = load_international_graduates()

    print("\n--- Employment Status ---")
    emp_counts = df['Employment_Status'].value_counts()
    for status, count in emp_counts.items():
        print(f"  {status}: {count} ({count/len(df)*100:.1f}%)")

    print("\n--- GPA by Employment Status (ANOVA) ---")
    emp_groups = [group['GPA'].dropna()
                  for name, group in df.groupby('Employment_Status')
                  if len(group['GPA'].dropna()) > 1]
    f_stat, p_val = stats.f_oneway(*emp_groups)
    sig = significance(p_val)
    print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.4f} {sig}")

    print("\n--- Internship Impact on Employment ---")
    intern_emp = pd.crosstab(df['Internship_Experience'], df['Employment_Status'], normalize='index') * 100
    print(intern_emp.round(1).to_string())

    print("\n--- Salary by Field of Study (ANOVA) ---")
    field_groups = [group['Salary'].dropna()
                    for name, group in df.groupby('Field_of_Study')
                    if len(group['Salary'].dropna()) > 1]
    f_stat, p_val = stats.f_oneway(*field_groups)
    sig = significance(p_val)
    print(f"F-statistic: {f_stat:.3f}, p-value: {p_val:.4f} {sig}")


def table11_india_fresher():
    print_header("TABLE 11: India Fresher Job Market (N=5,000)")
    df = load_india_fresher()

    print("\n--- Hiring Stage Distribution ---")
    stage_counts = df['hiring_stage'].value_counts()
    for stage, count in stage_counts.items():
        print(f"  {stage}: {count} ({count/len(df)*100:.1f}%)")

    print("\n--- CGPA by Hiring Outcome ---")
    hired = df[df['hiring_stage'].isin(['Offered', 'Joined'])]
    not_hired = df[~df['hiring_stage'].isin(['Offered', 'Joined'])]
    t_stat, p_val = stats.ttest_ind(hired['cgpa'].dropna(), not_hired['cgpa'].dropna(), equal_var=False)
    sig = significance(p_val)
    print(f"Hired CGPA: {hired['cgpa'].mean():.2f} +/- {hired['cgpa'].std():.2f}")
    print(f"Not Hired CGPA: {not_hired['cgpa'].mean():.2f} +/- {not_hired['cgpa'].std():.2f}")
    print(f"t-statistic: {t_stat:.3f}, p-value: {p_val:.4f} {sig}")

    print("\n--- Skills Analysis ---")
    all_skills = []
    for s in df['top_skills'].dropna():
        for skill in str(s).split('|'):
            skill = skill.strip().lower()
            if skill:
                all_skills.append(skill)
    skill_counts = pd.Series(all_skills).value_counts().head(15)
    print("Top 15 skills:")
    for skill, count in skill_counts.items():
        print(f"  {skill}: {count}")


def table12_career_change():
    print_header("TABLE 12: Career Change & Skills Gap (N=38,444)")
    df = load_career_change()

    print("\n--- Skills Gap Distribution ---")
    gap_stats = df['Skills Gap'].describe()
    print(gap_stats)

    print("\n--- Skills Gap by Education Level ---")
    for edu in df['Education Level'].unique():
        sub = df[df['Education Level'] == edu]
        print(f"  {edu}: {sub['Skills Gap'].mean():.2f} +/- {sub['Skills Gap'].std():.2f}")

    print("\n--- Career Change Interest by Skills Gap ---")
    high_gap = df[df['Skills Gap'] >= df['Skills Gap'].median()]
    low_gap = df[df['Skills Gap'] < df['Skills Gap'].median()]
    t_stat, p_val = stats.ttest_ind(high_gap['Career Change Interest'].dropna(),
                                     low_gap['Career Change Interest'].dropna(), equal_var=False)
    sig = significance(p_val)
    print(f"High Gap Career Change Interest: {high_gap['Career Change Interest'].mean():.2f}")
    print(f"Low Gap Career Change Interest: {low_gap['Career Change Interest'].mean():.2f}")
    print(f"t-statistic: {t_stat:.3f}, p-value: {p_val:.4f} {sig}")

    print("\n--- Logistic Regression: Likely to Change Occupation ---")
    df['Change_Binary'] = (df['Likely to Change Occupation'] == 1).astype(int)
    le = LabelEncoder()
    df['Education_Encoded'] = le.fit_transform(df['Education Level'].astype(str))
    X = df[['Age', 'Years of Experience', 'Job Satisfaction', 'Work-Life Balance',
            'Job Opportunities', 'Salary', 'Job Security', 'Skills Gap',
            'Education_Encoded']].dropna()
    y = df.loc[X.index, 'Change_Binary']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)
    print(f"Model Accuracy: {accuracy_score(y, y_pred)*100:.1f}%")
    print(f"\n{'Feature':<25} {'Coefficient':>12} {'Odds Ratio':>12}")
    print('-' * 55)
    for name, coef in zip(X.columns, model.coef_[0]):
        odds_ratio = np.exp(coef)
        sig = significance(abs(coef))
        print(f"{name:<25} {coef:>12.4f} {odds_ratio:>12.4f} {sig:>5}")


if __name__ == '__main__':
    print("STATISTICAL ANALYSIS FOR PUBLICATION")
    print("Gap Between Academic Knowledge and Job Market Skills")

    table1_descriptive()
    table2_chi_square()
    table3_correlation()
    table4_logistic()
    table5_random_forest()
    table_vif_analysis()
    table_cross_validation_models()
    table6_ngess_analysis()
    table7_global_placement()
    table8_student_career()
    table9_ai_market()
    table10_international_graduates()
    table11_india_fresher()
    table12_career_change()

    print(f"\n{'='*70}")
    print("ALL STATISTICAL TESTS COMPLETE")
    print('='*70)
