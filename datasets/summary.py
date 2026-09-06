import pandas as pd
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data_loader import (
    load_college_placement, load_ngess, load_global_placement,
    load_hf_skill_gap_skills, load_hf_job_skill_set
)

print('='*60)
print('STATISTICAL ANALYSIS SUMMARY')
print('='*60)

# College Placement Analysis
df = load_college_placement()
print('\n--- COLLEGE STUDENT PLACEMENT (N=10,000) ---')
placed_mask = df['Placement'] == 'Yes'
print(f'Placement Rate: {placed_mask.mean()*100:.1f}%')
print(f'Avg CGPA (Placed): {df.loc[placed_mask, "CGPA"].mean():.2f}')
print(f'Avg CGPA (Not Placed): {df.loc[~placed_mask, "CGPA"].mean():.2f}')
print(f'Avg Communication (Placed): {df.loc[placed_mask, "Communication_Skills"].mean():.2f}')
print(f'Avg Communication (Not Placed): {df.loc[~placed_mask, "Communication_Skills"].mean():.2f}')
intern_yes = df['Internship_Experience'] == 'Yes'
intern_placed_with = (df.loc[intern_yes, 'Placement'] == 'Yes').mean() * 100
intern_placed_without = (df.loc[~intern_yes, 'Placement'] == 'Yes').mean() * 100
print(f'Internship Impact: With={intern_placed_with:.1f}% vs Without={intern_placed_without:.1f}%')
proj_placed = (df.loc[df['Projects_Completed']>=3, 'Placement'] == 'Yes').mean() * 100
proj_not_placed = (df.loc[df['Projects_Completed']<3, 'Placement'] == 'Yes').mean() * 100
print(f'Projects Impact: 3+ projects={proj_placed:.1f}% vs 0-2 projects={proj_not_placed:.1f}%')

# NGESS Graduate Employment
df2 = load_ngess()
print('\n--- NGESS GRADUATE EMPLOYMENT (N=7,200) ---')
employed = ~df2['Employment_Status'].isin(['Unemployed', 'Not Applicable'])
print(f'Employment Rate: {employed.mean()*100:.1f}%')
print(f'Skills-Job Match Distribution:')
match_dist = df2['Skills_Job_Match'].value_counts()
for k, v in match_dist.items():
    print(f'  {k}: {v} ({v/len(df2)*100:.1f}%)')
print(f'Avg Job Satisfaction: {df2["Job_Satisfaction"].mean():.2f}/10')

# Skills-Job Match vs Satisfaction
for match in ['Good', 'Fair', 'Poor']:
    sub = df2[df2['Skills_Job_Match'] == match]
    if len(sub) > 0:
        print(f'  {match} match avg satisfaction: {sub["Job_Satisfaction"].mean():.2f}')

# Global Placement
df3 = load_global_placement()
print('\n--- GLOBAL STUDENT PLACEMENT (N=10,000) ---')
placed_g = df3['placement_status'] == 'Placed'
print(f'Placement Rate: {placed_g.mean()*100:.1f}%')
print(f'Avg Salary (Placed): ${df3.loc[placed_g, "salary"].mean():,.0f}')
print(f'Avg CGPA: {df3["cgpa"].mean():.2f}')
print(f'Avg Communication Score: {df3["communication_score"].mean():.1f}')

# Skills Demand
df4 = load_hf_skill_gap_skills()
all_skills = []
for s in df4['job_skills'].dropna():
    all_skills.extend([x.strip() for x in str(s).split(',')])
skill_counts = pd.Series(all_skills).value_counts()
print('\n--- TOP 10 EMPLOYER-DEMANDED SKILLS ---')
for i, (skill, count) in enumerate(skill_counts.head(10).items(), 1):
    print(f'  {i}. {skill}: {count:,} job postings ({count/len(df4)*100:.1f}%)')

# Category Skills
df5 = load_hf_job_skill_set()
print('\n--- JOB CATEGORIES (N=1,167) ---')
for cat in df5['category'].value_counts().index:
    print(f'  {cat}: {len(df5[df5["category"]==cat])} jobs')

print('\n' + '='*60)
